import pendulum

from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from airflow.io.path import ObjectStoragePath


def get_data() -> dict:
    import requests

    print("Fetching data from API")

    # New York temperature in 2025
    url = "https://archive-api.open-meteo.com/v1/archive?latitude=40.7143&longitude=-74.006&start_date=2025-01-01&end_date=2025-12-31&hourly=temperature_2m&timezone=auto"

    resp = requests.get(url)
    resp.raise_for_status()

    data = resp.json()
    data = {
        "time": data["hourly"]["time"],
        "temperature": data["hourly"]["temperature_2m"],
    }
    return data


def transform(data: dict):
    import pandas as pd

    df = pd.DataFrame(data)
    df["temperature"] = df["temperature"].clip(lower=-20, upper=50)
    return df


def save_data_s3(df, logical_date_str: str) -> None:
    print(f"Saving the data to S3 for logical date {logical_date_str}")
    
    import pendulum

    logical_date = pendulum.parse(logical_date_str)
    date_str = logical_date.strftime("%Y-%m-%d")
    
    # Use ObjectStoragePath with the S3 connection defined in compose.yml
    base_path = ObjectStoragePath("s3://aws_default@weather-data/")
    file_path = base_path / f"weather_{date_str}.csv"
    
    print(f"Target path: {file_path}")
    
    # df.to_csv can work with any file-like object
    with file_path.open("wb") as f:
        df.to_csv(f, index=False)


with DAG(
        dag_id="weather_s3_integration",
        start_date=pendulum.datetime(2025, 1, 1),
        schedule=None,
        catchup=False,
) as dag:
    get_data_op = PythonOperator(task_id="get_data", python_callable=get_data)
    
    transform_op = PythonOperator(
        task_id="transform",
        python_callable=transform,
        op_kwargs={"data": get_data_op.output},
    )
    
    load_op = PythonOperator(
        task_id="load", 
        python_callable=save_data_s3, 
        op_kwargs={
            "df": transform_op.output,
            "logical_date_str": "{{ logical_date }}"
        }
    )

    get_data_op >> transform_op >> load_op
