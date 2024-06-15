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
    # will terminate DAG but not ECS task if ECS task is running longer unless IAM role is allowed to terminate ECS task
    dagrun_timeout=timedelta(minutes=3),
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
                "command": [
                    " && ".join(
                        [
                            "pip3 freeze ",
                            "aws s3 cp s3://mwaa-practice-bucket-${AWS_REGION}/dags/ecs_dag/ecs_requirements.txt .",  # container automatically knows region
                            "pip3 install -r ecs_requirements.txt",
                            "pip3 freeze",
                            "aws s3 cp s3://mwaa-practice-bucket-${AWS_REGION}/dags/ecs_dag/silly_app.py .",  # container automatically knows region
                            "black silly_app.py",
                            "python3 silly_app.py",
                        ]
                    )
                ],
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
            "securityGroups": ["sg-07b171f318d5b9382"],  ### hard coded
            # "subnets": ["subnet-0d6942191f4f3ca9d"],  ### hard coded public subnet
            "subnets": ["subnet-076a4385ed5176eba"],  ### hard coded private subnet
        },
    },
    awslogs_group="airflow-mwaa-practice-cluster-Task",  ### hard coded
    awslogs_stream_prefix="ecs/ecs-task-for-mwaa",  ### hard coded
)
