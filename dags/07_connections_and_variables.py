import pendulum

from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator, PythonVirtualenvOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook


def get_data_venv(data_interval_start, api_key):
    from twelvedata import TDClient
    import pendulum

    # data_interval_start is passed as a string from Jinja template
    td = TDClient(apikey=api_key)
    ts = td.exchange_rate(symbol="USD/EUR", date=data_interval_start)
    data = ts.as_json()
    return data


def load_to_postgres(data: dict):
    print("Loading data to Postgres")
    if not data:
        raise ValueError("No data received")

    # Use the connection defined in compose.yml
    pg_hook = PostgresHook(postgres_conn_id="storage_db")
    
    symbol = data.get("symbol", "USD/EUR")
    rate = float(data["rate"])
    
    print(f"Inserting {symbol}: {rate}")
    
    pg_hook.run(
        "INSERT INTO exchange_rates (symbol, rate) VALUES (%s, %s)",
        parameters=(symbol, rate)
    )


with DAG(
        dag_id="connections_and_variables",
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
            # Pass Airflow variable via Jinja
            "api_key": "{{ var.value.TWELVEDATA_API_KEY }}"
        },
        serializer="cloudpickle",
    )

    load_op = PythonOperator(
        task_id="load_to_db",
        python_callable=load_to_postgres,
        op_kwargs={"data": get_data_op.output}
    )

    get_data_op >> load_op
