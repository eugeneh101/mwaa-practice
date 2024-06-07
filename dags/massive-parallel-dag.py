import os
import socket
import time
from datetime import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators.python_operator import PythonOperator


def print_env_vars():
    keys = str(os.environ.keys()).replace("', '", "'|'").split("|")
    for key in sorted(keys):
        print(key)


def print_airflow_cfg():
    with open(f"{os.environ['AIRFLOW_HOME']}/airflow.cfg", "r") as airflow_cfg:
        file_contents = airflow_cfg.read()
        print(f"\n{file_contents}")


def get_data():
    time.sleep(60)
    return os.getpid(), socket.gethostname()


dag = DAG(
    os.path.basename(__file__).replace(".py", ""),  # "massively-parallel-dag",
    description="Massive fanout",
    schedule_interval=None,
    # schedule_interval="*/10 * * * *",
    start_date=datetime(2017, 3, 20),
    catchup=False,
    is_paused_upon_creation=False,
    tags=["eugene"],
    concurrency=14,  # bound by celery.worker_autoscale * max_workers
)

dummy_operator = DummyOperator(task_id="dummy_task", retries=3, dag=dag)
# task_accumulator = dummy_operator

list_python_packages_operator = BashOperator(
    task_id="list_python_packages", bash_command="python3 -m pip list"
)
# task_accumulator >> list_python_packages_operator

get_env_vars_operator = PythonOperator(
    task_id="get_env_vars_task", python_callable=print_env_vars
)
# task_accumulator >> get_env_vars_operator


get_airflow_cfg_operator = PythonOperator(
    task_id="get_airflow_cfg_task", python_callable=print_airflow_cfg
)
# task_accumulator >> get_airflow_cfg_operator

for i in range(30):
    data_operator = PythonOperator(
        task_id=f"hello_task_{i}", python_callable=get_data, dag=dag
    )
    # task_accumulator = task_accumulator >> data_operator
    [
        dummy_operator,
        list_python_packages_operator,
        get_env_vars_operator,
        get_airflow_cfg_operator,
    ] >> data_operator
