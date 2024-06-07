import os
from datetime import timedelta

from airflow import DAG
from airflow.utils.dates import days_ago
from airflow.providers.amazon.aws.operators.ecs import EcsRunTaskOperator


dag = DAG(
    os.path.basename(__file__).replace(".py", ""),  # "example_ecs_operator",
    description="Example of ECS operator in Amazon MWAA",
    default_args={
        "start_date": days_ago(1),
    },
    is_paused_upon_creation=True,
    dagrun_timeout=timedelta(minutes=120),
)

task_ecs_operator = EcsRunTaskOperator(  # run Docker container via ECS operator
    task_id="ecs_operator",
    dag=dag,
    aws_conn_id="aws_ecs",
    cluster="ecs-cluster-for-mwaa",  ### hard coded
    task_definition="ecs-task-for-mwaa",  ### hard coded
    launch_type="FARGATE",
    overrides={
        "cpu": "1024",  # 1 CPU
        "memory": "2048",  # 2 GB RAM
        "containerOverrides": [
            {
                "name": "ecs-task-for-mwaa",  ### hard coded
                "cpu": 1024,  # yes, have to repeat "cpu"
                "memory": 2048,  # yes, have to repeat "memory"
                # "command": ["sleep", "3"],
                # "command": ["sleep", "3", "&&", "exit", "2"],
                "environment": [
                    {"name": "KEY1", "value": "VALUE1"},
                    {"name": "KEY2", "value": "VALUE2"},
                ],
            },
        ],
    },
    network_configuration={
        "awsvpcConfiguration": {
            "securityGroups": ["sg-034e71ddc9f9e009a"],  ### hard coded
            # "subnets": ["subnet-0d6942191f4f3ca9d"],  ### hard coded public subnet
            "subnets": ["subnet-029e4d8b04d643128"],  ### hard coded private subnet
        },
    },
    awslogs_group="airflow-mwaa-practice-cluster-Task",  ### hard coded
    awslogs_stream_prefix="ecs/ecs-task-for-mwaa",  ### hard coded
)
