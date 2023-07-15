from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from airflow.operators.docker_operator import DockerOperator
from airflow.operators.dummy_operator import DummyOperator


dag = DAG(
    "docker-dag",
    description="Trying to use a Docker image",
    schedule_interval=None,
    start_date=datetime(2017, 3, 20),
    catchup=False,
    is_paused_upon_creation=True,
)

dummy_operator = DummyOperator(task_id="dummy_task", retries=3, dag=dag)
bash_operator = BashOperator(task_id="print_hello", bash_command="echo 'hello world'")
docker_operator = DockerOperator(
    task_id="docker_command",
    image="centos:latest",
    api_version="auto",
    auto_remove=True,
    execution_timeout=timedelta(minutes=30),
    # command="/bin/sleep 30",
    command="echo 'hello world'",
    # docker_url="unix://var/run/docker.sock",
    # network_mode="bridge"
)
# might not be able to use Docker operator and might have to use ECS operator
# https://medium.com/@sohflp/how-to-work-with-airflow-docker-operator-in-amazon-mwaa-5c6b7ad36976

dummy_operator >> bash_operator >> docker_operator
