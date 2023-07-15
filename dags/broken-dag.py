from datetime import datetime

from airflow import DAG
from airflow.operators.bash_operator import BashOperator


dag = DAG(
    "broken-dag",
    description="Trying to break MWAA",
    schedule_interval=None,
    start_date=datetime(2017, 3, 20),
    catchup=False,
    is_paused_upon_creation=False,
)


bash_op0 = BashOperator(task_id="dbt0", bash_command="ls", dag=dag  # broken here
