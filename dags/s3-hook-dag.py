import os
from datetime import datetime

from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.utils.dates import days_ago


def s3_hook_examples():
    s3 = S3Hook()
    print(
        "Check for bucket",
        s3.check_for_bucket(bucket_name="mwaa-practice-bucket"),  # hard coded
    )
    print("conn", s3.get_conn())  # boto3 client
    print("bucket", s3.get_bucket(bucket_name="mwaa-practice-bucket"))  # boto3 resource


def read_s3_file(**kwargs):
    import boto3

    s3_bucket = boto3.resource("s3").Bucket("mwaa-practice-bucket")  # hard coded
    print(
        s3_bucket.Object(key="requirements/requirements.txt")  # hard coded
        .get()["Body"]
        .read()
        .decode()
    )
    return {"silly": "hi"}


def write_s3_file(**kwargs):
    # import boto3
    # print("identity", boto3.client("sts").get_caller_identity())
    # s3_bucket = boto3.resource("s3").Bucket("mwaa-practice-bucket")  # this also works
    s3_bucket = S3Hook().get_bucket(bucket_name="mwaa-practice-bucket")
    s3_file_name = f"data/{datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')}.txt"
    # fails since role for MWAA cluster does not have permission to write to this S3 bucket
    s3_bucket.Object(key=s3_file_name).put(Body="hi thanks bye".encode())


with DAG(
    os.path.basename(__file__).replace(".py", ""),  # "s3-hook-dag",
    description="S3 practice",
    schedule_interval=None,
    start_date=days_ago(1),
    catchup=False,
    is_paused_upon_creation=False,
    tags=["eugene"],
) as dag:
    s3_hook_examples_task = PythonOperator(
        task_id="s3_hook_examples_task",
        python_callable=s3_hook_examples,
        # dag=dag,
    )
    read_s3_file_task = PythonOperator(
        task_id="read_s3_file_task",
        python_callable=read_s3_file,
        # dag=dag,
    )
    write_s3_file_task = PythonOperator(
        task_id="write_s3_file_task",
        python_callable=write_s3_file,
        # dag=dag,
    )
