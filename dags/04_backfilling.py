import datetime

import pendulum

from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator


def get_weather_forecast(**kwargs):
    import requests

    logical_date: pendulum.DateTime = kwargs["logical_date"]
    start_date = logical_date.to_date_string()
    # Inclusive range of 7 days: start + 6 days
    end_date = logical_date.add(days=6).to_date_string()

    print(f"Fetching weather forecast from {start_date} to {end_date}")

    url = (
        f"https://historical-forecast-api.open-meteo.com/v1/forecast?"
        f"latitude=40.7143&longitude=-74.006&start_date={start_date}&end_date={end_date}&"
        f"daily=temperature_2m_max,temperature_2m_min&timezone=auto"
    )

    resp = requests.get(url)
    resp.raise_for_status()
    data = resp.json()

    return {
        "time": data["daily"]["time"],
        "temp_max": data["daily"]["temperature_2m_max"],
        "temp_min": data["daily"]["temperature_2m_min"],
    }


def save_to_csv(data: dict):
    import pandas as pd
    import os

    print("Saving forecast data to CSV")
    df = pd.DataFrame(data)
    file_path = "weather_forecasts.csv"
    
    # Append to CSV if it exists, otherwise create it
    if not os.path.exists(file_path):
        df.to_csv(file_path, index=False)
    else:
        df.to_csv(file_path, mode='a', header=False, index=False)


with DAG(
        dag_id="weather_backfilling",
        start_date=pendulum.datetime(2025, 1, 1),
        end_date=pendulum.datetime(2025, 1, 31),
        schedule=datetime.timedelta(days=7),
        catchup=True,
) as dag:
    get_data_op = PythonOperator(
        task_id="get_forecast",
        python_callable=get_weather_forecast,
    )

    save_data_op = PythonOperator(
        task_id="save_forecast",
        python_callable=save_to_csv,
        op_kwargs={"data": get_data_op.output}
    )

    get_data_op >> save_data_op
