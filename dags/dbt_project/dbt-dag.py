from datetime import datetime

from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from airflow.operators.python_operator import PythonOperator


dag = DAG(
    "dbt-dag",
    description="Trying to get dbt to work",
    schedule_interval=None,
    start_date=datetime(2017, 3, 20),
    catchup=False,
    is_paused_upon_creation=False,
)

def current_env(**kwargs):
    import pathlib
    print(pathlib.Path(__file__).parent.resolve())


python_op = PythonOperator(
    task_id="print_the_context",
    provide_context=True,
    python_callable=current_env,
    # op_kwargs={"name": "Data Rocks"},
    dag=dag,
)

bash_op0 = BashOperator(task_id="dbt0", bash_command="pwd", dag=dag)
bash_op1 = BashOperator(task_id="dbt1", bash_command="dbt --version", dag=dag)
bash_op2 = BashOperator(
    task_id="dbt2",
    bash_command="cp -R /usr/local/airflow/dags/dbt_project /tmp && cd /tmp/dbt_project && dbt debug",
#     bash_command="cd /usr/local/airflow/dags/dbt_project  && DBT_LOG_PATH=/usr/local/airflow/tmp/logs && dbt debug",
# #     --log-path /usr/local/airflow/tmp/logs
    dag=dag,
)
bash_op3 = BashOperator(
    task_id="dbt3",
    bash_command="cp -R /usr/local/airflow/dags/dbt_project /tmp && cd /tmp/dbt_project && dbt run",
    dag=dag,
)
bash_op4 = BashOperator(
    task_id="dbt4",
    bash_command="cp -R /usr/local/airflow/dags/dbt_project /tmp && cd /tmp/dbt_project && dbt test",
    dag=dag,
)

python_op >> bash_op0 >> bash_op1 >> [bash_op2, bash_op3, bash_op4]