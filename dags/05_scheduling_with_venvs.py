import os

import pendulum

from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator, PythonVirtualenvOperator
from dotenv import load_dotenv

load_dotenv()


def get_data_venv(data_interval_start, api_key):
    from twelvedata import TDClient
    import pendulum

    # data_interval_start is passed as a string from Jinja template
    td = TDClient(apikey=api_key)
    ts = td.exchange_rate(symbol="USD/EUR", date=data_interval_start)
    data = ts.as_json()
    return data


def save_data_venv(data):
    import json
    print("Saving the data")

    if not data:
        raise ValueError("No data received")

    with open("data_venv.jsonl", "a+") as file:
        file.write(json.dumps(data))
        file.write("\n")


with DAG(
        dag_id="scheduling_with_venvs",
        schedule="* * * * *",
        start_date=pendulum.datetime(2025, 1, 1),
        catchup=False,
) as dag:
    get_data_op = PythonVirtualenvOperator(
        task_id="get_data",
        python_callable=get_data_venv,
        requirements=["twelvedata", "pendulum", "lazy_object_proxy", "cloudpickle"],
        op_kwargs={
            "data_interval_start": "{{ data_interval_start }}",
            "api_key": os.getenv("TWELVEDATA_API_KEY", "")
        },
        serializer="cloudpickle",
    )

    save_data_op = PythonOperator(
        task_id="save_data",
        python_callable=save_data_venv,
        op_kwargs={"data": get_data_op.output},
    )

    get_data_op >> save_data_op
