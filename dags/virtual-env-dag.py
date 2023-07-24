import os

from airflow import DAG
from airflow.operators.python_operator import PythonOperator, PythonVirtualenvOperator
from airflow.utils.dates import days_ago


def print_dependencies(**kwargs):
    import subprocess

    print("kwargs", kwargs)
    proc = subprocess.run(["pip3", "list"], capture_output=True)
    print(proc.stdout.decode("utf-8"))


with DAG(
    os.path.basename(__file__).replace(".py", ""),  # "virtual-env-dag",
    description="Python Virtual Env practice",
    schedule_interval=None,
    start_date=days_ago(1),
    catchup=False,
    is_paused_upon_creation=False,
    tags=["eugene"],
) as dag:
    print_dependencies_task = PythonOperator(
        task_id="print_dependencies_task",
        python_callable=print_dependencies,
        # dag=dag,
    )
    print_virtualenv_dependencies_task = PythonVirtualenvOperator(
        task_id="print_virtualenv_dependencies_task",
        python_callable=print_dependencies,
        requirements=["black", "isort", "fastapi"],
        # if you get "cannot pickle 'module' object", then use `dill` (for serialization) or `op_kwargs``
        op_kwargs={
            "execution_date_str": "{{ execution_date }}"
        },  # this is how you pass in arguments
        system_site_packages=False,  # needs to be False for `op_kwargs` to work
        # python_version="3.8",  # actually only works with the same version as your MWAA cluster
        # dag=dag
    )

    print_dependencies_task >> print_virtualenv_dependencies_task
