import os
from datetime import timedelta

from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from airflow.operators.python_operator import PythonOperator
from airflow.utils.dates import days_ago

# These args will get passed on to each operator
# You can override them on a per-task basis during operator initialization
default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": days_ago(2),
    "email": ["airflow@example.com"],
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}


def hello(**kwargs):
    if kwargs.get("name"):
        print(f"Hello {kwargs['name']}!")
        return f"Hello {kwargs['name']}!"
    else:
        print(f"Hello Stranger")
        return f"Hello Stranger"


dag = DAG(
    os.path.basename(__file__).replace(".py", ""),  # "example-dag",
    default_args=default_args,
    description="A simple tutorial DAG",
    schedule_interval="*/5 * * * *",
    # schedule_interval=timedelta(days=1),
    catchup=False,
    is_paused_upon_creation=False,
)

# t1, t2 and t3 are examples of tasks created by instantiating operators
t1 = BashOperator(
    task_id="print_date",
    bash_command="date",
    dag=dag,
)

t2 = BashOperator(
    task_id="sleep",
    depends_on_past=False,
    bash_command="sleep 5",
    retries=3,
    dag=dag,
)
dag.doc_md = __doc__

t1.doc_md = """\
#### Task Documentation
You can document your task using the attributes `doc_md` (markdown),
`doc` (plain text), `doc_rst`, `doc_json`, `doc_yaml` which gets
rendered in the UI's Task Instance Details page.
![img](http://montcs.bloomu.edu/~bobmon/Semesters/2012-01/491/import%20soul.png)
"""
templated_command = """
{% for i in range(5) %}
    echo "{{ python src/example.py }}"
{% endfor %}
"""

t3 = PythonOperator(
    task_id="print_the_context",
    provide_context=True,
    python_callable=hello,
    op_kwargs={"name": "Data Rocks"},
    dag=dag,
)

t1 >> [t2, t3]
