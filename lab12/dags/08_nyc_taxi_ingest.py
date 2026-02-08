import io
import pendulum
import requests
from airflow.exceptions import AirflowSkipException

from airflow import DAG
from airflow.decorators import task
from airflow.providers.amazon.aws.hooks.s3 import S3Hook

RAW_BUCKET = "nyc-taxi-raw"
PROC_BUCKET = "nyc-taxi-processed"
S3_CONN_ID = "aws_default"
BASE_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data/green_tripdata_{year}-{month:02d}.parquet"

def _raw_key(year: int, month: int) -> str:
    return f"raw/year={year}/month={month:02d}/green_tripdata_{year}-{month:02d}.parquet"


def _processed_key(year: int, month: int) -> str:
    return f"processed/year={year}/month={month:02d}/daily_counts.parquet"


with DAG(
    dag_id="nyc_taxi_ingest",
    schedule="0 0 1 * *",
    start_date=pendulum.datetime(2024, 1, 1),
    catchup=True,
    max_active_runs=1,
    default_args={"owner": "airflow"},
    description="Download NYC taxi data monthly, aggregate daily rides, store in S3",
):

    @task
    def download_to_s3(data_interval_start: pendulum.DateTime) -> str:
        year = data_interval_start.year
        month = data_interval_start.month
        url = BASE_URL.format(year=year, month=month)

        resp = requests.get(url, stream=True, timeout=60)
        if resp.status_code in (403, 404):
            # dataset for the month not published yet
            raise AirflowSkipException(f"Dataset not available: {url} (status {resp.status_code})")
        resp.raise_for_status()

        buf = io.BytesIO(resp.content)
        key = _raw_key(year, month)
        S3Hook(aws_conn_id=S3_CONN_ID).load_file_obj(
            buf, key=key, bucket_name=RAW_BUCKET, replace=True
        )
        return key

    @task
    def aggregate_daily(raw_key: str, data_interval_start: pendulum.DateTime) -> str:
        import polars as pl

        year = data_interval_start.year
        month = data_interval_start.month

        hook = S3Hook(aws_conn_id=S3_CONN_ID)
        obj = hook.get_key(key=raw_key, bucket_name=RAW_BUCKET)
        if obj is None:
            raise FileNotFoundError(f"Missing raw object s3://{RAW_BUCKET}/{raw_key}")

        buf = io.BytesIO(obj.get()["Body"].read())
        df = (
            pl.read_parquet(buf)
            .with_columns(pl.col("lpep_pickup_datetime").dt.date().alias("ride_date"))
            .group_by("ride_date")
            .agg(pl.len().alias("rides"))
            .sort("ride_date")
        )

        out = io.BytesIO()
        df.write_parquet(out)
        out.seek(0)

        key = _processed_key(year, month)
        hook.load_file_obj(out, key=key, bucket_name=PROC_BUCKET, replace=True)
        return key

    raw = download_to_s3()
    aggregate_daily(raw)
