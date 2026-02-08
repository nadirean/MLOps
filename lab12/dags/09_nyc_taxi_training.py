import io
import os
import pendulum

from airflow import DAG
from airflow.decorators import task
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.standard.operators.python import PythonVirtualenvOperator

PROC_BUCKET = "nyc-taxi-processed"
MODEL_BUCKET = "nyc-taxi-models"
S3_CONN_ID = "aws_default"
STORAGE_CONN_ID = "storage_db"

with DAG(
    dag_id="nyc_taxi_training",
    schedule=None,
    start_date=pendulum.datetime(2025, 1, 1),
    catchup=False,
    max_active_runs=1,
    description="Train models on aggregated NYC taxi data from S3",
):

    @task
    def load_processed() -> list[dict]:
        import polars as pl

        hook = S3Hook(aws_conn_id=S3_CONN_ID)
        keys = hook.list_keys(bucket_name=PROC_BUCKET, prefix="processed/") or []
        if not keys:
            raise ValueError("No processed datasets found in S3")

        frames = []
        for key in keys:
            obj = hook.get_key(key=key, bucket_name=PROC_BUCKET)
            if obj is None:
                raise FileNotFoundError(f"Missing processed object s3://{PROC_BUCKET}/{key}")
            buf = io.BytesIO(obj.get()["Body"].read())
            frames.append(pl.read_parquet(buf))
        df = pl.concat(frames).sort("ride_date")
        if df["ride_date"].dtype == pl.Utf8:
            df = df.with_columns(pl.col("ride_date").str.to_date())
        return df.to_dicts()

    @task
    def split_train_test(rows: list[dict]) -> dict:
        import polars as pl

        df = pl.DataFrame(rows)
        df = df.with_columns(pl.col("ride_date").cast(pl.Date))
        max_date = df["ride_date"].max()
        test_month_start = pendulum.date(max_date.year, max_date.month, 1)
        train = df.filter(pl.col("ride_date") < test_month_start)
        test = df.filter(pl.col("ride_date") >= test_month_start)
        if train.is_empty() or test.is_empty():
            raise ValueError("Train/test split is empty; need at least two months of data")
        return {"train": train.to_dicts(), "test": test.to_dicts()}

    def _train_model(model_type: str, params: dict, split: dict, model_bucket: str) -> dict:
        import io
        import joblib
        import boto3
        import pendulum
        import pandas as pd
        from sklearn.metrics import mean_absolute_error
        from sklearn.linear_model import Ridge
        from sklearn.ensemble import RandomForestRegressor
        from sklearn.svm import SVR

        def featurize(frame: pd.DataFrame):
            frame = frame.copy()
            frame["ride_date"] = pd.to_datetime(frame["ride_date"])
            features = pd.DataFrame(
                {
                    "dow": frame["ride_date"].dt.dayofweek,
                    "month": frame["ride_date"].dt.month,
                }
            )
            target = frame["rides"].astype(float)
            return features, target

        train_df = pd.DataFrame(split["train"])
        test_df = pd.DataFrame(split["test"])
        if train_df.empty or test_df.empty:
            raise ValueError("No data to train")

        X_train, y_train = featurize(train_df)
        X_test, y_test = featurize(test_df)

        if model_type == "ridge":
            model = Ridge(**params)
        elif model_type == "random_forest":
            model = RandomForestRegressor(**params)
        elif model_type == "svr":
            model = SVR(**params)
        else:
            raise ValueError(f"Unsupported model type: {model_type}")

        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        mae = float(mean_absolute_error(y_test, preds))

        buf = io.BytesIO()
        joblib.dump(model, buf)
        buf.seek(0)

        s3 = boto3.client("s3", endpoint_url=os.getenv("AWS_ENDPOINT_URL"))
        key = f"models/tmp/{model_type}_{pendulum.now('UTC').int_timestamp}.joblib"
        s3.put_object(Bucket=model_bucket, Key=key, Body=buf.getvalue())

        return {
            "model_name": model_type,
            "mae": mae,
            "model_key": key,
            "train_size": int(len(train_df)),
        }

    def _make_train_task(task_id: str, model_type: str, params: dict):
        return PythonVirtualenvOperator(
            task_id=task_id,
            python_callable=_train_model,
            op_kwargs={
                "model_type": model_type,
                "params": params,
                "split": split,
                "model_bucket": MODEL_BUCKET,
            },
            requirements=[
                "pandas",
                "numpy",
                "scikit-learn",
                "joblib",
                "boto3",
                "pendulum",
                "cloudpickle",
                "lazy_object_proxy",
            ],
            system_site_packages=False,
            serializer="cloudpickle",
        )

    split = split_train_test(load_processed())

    ridge = _make_train_task("train_ridge", "ridge", {"alpha": 1.0})
    rf = _make_train_task(
        "train_random_forest",
        "random_forest",
        {"n_estimators": 200, "max_depth": None, "random_state": 42},
    )
    svr = _make_train_task("train_svr", "svr", {"C": 10.0, "kernel": "rbf"})

    @task
    def select_best(results: list[dict]):
        import boto3
        import os

        if not results:
            raise ValueError("No model results provided")

        best = min(results, key=lambda r: r["mae"])
        s3 = boto3.client("s3", endpoint_url=os.getenv("AWS_ENDPOINT_URL"))
        final_key = f"models/best/model_{pendulum.now('UTC').format('YYYYMMDDHHmmss')}.joblib"

        s3.copy_object(
            Bucket=MODEL_BUCKET,
            CopySource={"Bucket": MODEL_BUCKET, "Key": best["model_key"]},
            Key=final_key,
        )

        for res in results:
            if res["model_key"] != best["model_key"]:
                s3.delete_object(Bucket=MODEL_BUCKET, Key=res["model_key"])

        hook = PostgresHook(postgres_conn_id=STORAGE_CONN_ID)
        for res in results:
            hook.run(
                "INSERT INTO model_performance (training_date, model_name, train_size, test_mae)"
                " VALUES (%s, %s, %s, %s)",
                parameters=(pendulum.now("UTC"), res["model_name"], res["train_size"], res["mae"]),
            )

        return {"best_model": best["model_name"], "mae": best["mae"], "final_key": final_key}

    split >> [ridge, rf, svr]
    select_best([ridge.output, rf.output, svr.output])
