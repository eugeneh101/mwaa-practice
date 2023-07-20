from datetime import datetime

from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from airflow.operators.python_operator import PythonOperator

# Needed since MWAA workers only allow you to write to specific directories
# and DBT writes to target/, logs/, and dbt_packages/ folders.
# Based on guide in https://docs.aws.amazon.com/mwaa/latest/userguide/samples-dbt.html
MWAA_DBT_PREFIX_COMMAND = (
    "cp -R /usr/local/airflow/dags/dbt_project /tmp && cd /tmp/dbt_project"
)

dag = DAG(
    "dbt-dag-secrets-manager",
    description="Trying to get dbt to work",
    schedule_interval=None,
    start_date=datetime(2017, 3, 20),
    catchup=False,
    is_paused_upon_creation=False,
)


bash_op1 = BashOperator(task_id="dbt1", bash_command="dbt --version", dag=dag)
bash_op2 = BashOperator(
    task_id="dbt2",  # task fails because does not have permissions to run git
    bash_command=f"{MWAA_DBT_PREFIX_COMMAND} && export REDSHIFT_HOST={{{{ var.value.redshift_host }}}} && export REDSHIFT_PASSWORD={{{{ var.value.redshift_password }}}} && dbt debug --profiles-dir profile_secrets_manager/",  # --log-path CLI doesn't seem to work
    dag=dag,
)
bash_op3 = BashOperator(
    task_id="dbt3",  ### have to manually click to create the Redshift database
    bash_command=f"{MWAA_DBT_PREFIX_COMMAND} && export REDSHIFT_HOST={{{{ var.value.redshift_host }}}} && export REDSHIFT_PASSWORD={{{{ var.value.redshift_password }}}} && dbt run --profiles-dir profile_secrets_manager/",
    # bash_command=" ".join([
    #     "DBT_TARGET_PATH=/tmp/dbt/target",  # if don't use `target-path` in dbt_project.yml
    #     "DBT_LOG_PATH=/tmp/dbt/logs",  # if don't use `log-path` in dbt_project.yml
    #     # "DBT_PACKAGE_PATH=/tmp/dbt/dbt_packages",  # doesn't work, so need `packages-install-path` in dbt_project.yml
    #     "sh -c 'cd /usr/local/airflow/dags/dbt_project && dbt run'",
    # ]),
    dag=dag,
)
bash_op4 = BashOperator(
    task_id="dbt4",  ### have to manually click to create the Redshift database
    bash_command=f"{MWAA_DBT_PREFIX_COMMAND} && export REDSHIFT_HOST={{{{ var.value.redshift_host }}}} && export REDSHIFT_PASSWORD={{{{ var.value.redshift_password }}}} && dbt test --profiles-dir profile_secrets_manager/",
    dag=dag,
)

bash_op1 >> [bash_op2, bash_op3, bash_op4]
