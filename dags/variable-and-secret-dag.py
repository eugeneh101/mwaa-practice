from datetime import datetime

from airflow import DAG
from airflow.models import Variable
from airflow.operators.bash import BashOperator
from airflow.operators.python_operator import PythonOperator

# Variables with the follow words in the key name will have the value automatically encrypted:
# "access_token", "api_key", "apikey", "authorization", "keyfile_dict", "passphrase", "passwd", "password", "private_key", "secret", "service_account", "token"

def get_variable(**kwargs):
    print("kwargs", kwargs)
    value1 = Variable.get("variable_key")  # hard coded but first create Variable
    value2 = Variable.get("variable_private_key")  # hard coded but first create Variable
    print("value1", value1)
    from collections import Counter
    # `value2` is just "***" in logs, automatically suppressed in logs by value is still correct
    print("value2", value2, len(value2), value2[::-1], Counter(value2))
    print("non-existent value", Variable.get("non-existent key", default_var="non-existent value"))


def get_json_variable(**kwargs):
    value1 = Variable.get("json_key")  # hard coded but first create Variable
    value2 = Variable.get("json_key", deserialize_json=True)  # hard coded but first create Variable
    print("value1", value1, type(value1))
    print("value2", value2, type(value2))


def set_variable(**kwargs):
    now = datetime.now().strftime("%Y-%m-%d, %H:%M:%S")
    Variable.set("set_variable_key", now)  # hard coded, returns None


dag = DAG(
    "variable-and-secret-dag",
    description="variable/secret practice",
    schedule_interval=None,
    start_date=datetime(2017, 3, 20),
    catchup=False,
    is_paused_upon_creation=False,
    tags=["eugene"],
)

echo_var = BashOperator(
    task_id="echo_var",
    bash_command='echo "my value is: {{ var.value.variable_key }}"',  # hard coded but first create Variable
    dag=dag,
)
echo_json_var = BashOperator(
    task_id="echo_json_var",
    bash_command='echo "my value is: {{ var.value.json_key }}"',  # hard coded but first create Variable
)
echo_json_var_jsonified = BashOperator(
    task_id="echo_json_var_jsonified",
    bash_command='echo "my value is: {{ var.json.json_key }}"',  # hard coded but first create Variable
)
echo_json_var = BashOperator(
    task_id="echo_json_var",
    bash_command='echo "my value is: {{ var.value.json_key }}"',  # hard coded but first create Variable
)

get_var_task = PythonOperator(
    task_id="get_var_task", python_callable=get_variable
)
get_json_var_task = PythonOperator(
    task_id="get_json_var_task", python_callable=get_json_variable
)
set_var_task = PythonOperator(
   task_id="set_var_task", python_callable=set_variable
)
echo_var >> echo_json_var >> echo_json_var_jsonified >> get_var_task >> get_json_var_task >> set_var_task
