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

# Get ECS configuration from SSM parameters
# ecs_cluster               = str(ssm.get_parameter(Name='/mwaa/ecs/cluster', WithDecryption=True)['Parameter']['Value'])
# ecs_task_definition       = str(ssm.get_parameter(Name='/mwaa/ecs/task_definition', WithDecryption=True)['Parameter']['Value'])
# ecs_subnets               = str(ssm.get_parameter(Name='/mwaa/vpc/private_subnets', WithDecryption=True)['Parameter']['Value'])
# ecs_security_group        = str(ssm.get_parameter(Name='/mwaa/vpc/security_group', WithDecryption=True)['Parameter']['Value'])
# ecs_awslogs_group         = str(ssm.get_parameter(Name='/mwaa/cw/log_group', WithDecryption=True)['Parameter']['Value'])
# ecs_awslogs_stream_prefix = str(ssm.get_parameter(Name='/mwaa/cw/log_stream', WithDecryption=True)['Parameter']['Value'])

# Run Docker container via ECS operator
task_ecs_operator = EcsRunTaskOperator(
    task_id="ecs_operator",
    dag=dag,
    aws_conn_id="aws_ecs",
    cluster="ecs-cluster-for-mwaa",  ### hard coded
    task_definition="ecs-task-for-mwaa",  ### hard coded
    launch_type="FARGATE",
    overrides={
        # "containerOverrides": [
        #     {  ### add in environment variables
        #         "name": "hello-world",
        #         "command": ["/hello"],
        #     },
        # ],
    },
    network_configuration={
        "awsvpcConfiguration": {
            "securityGroups": ["sg-034e71ddc9f9e009a"],  ### hard coded
            # "subnets": ["subnet-0d6942191f4f3ca9d"],  ### hard coded public subnet
            "subnets": ["subnet-029e4d8b04d643128"],  ### hard coded private subnet
        },
    },
    # awslogs_group=ecs_awslogs_group,
    # awslogs_stream_prefix=ecs_awslogs_stream_prefix
)