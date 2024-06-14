import os

import aws_cdk as cdk
import boto3

from mwaa_practice import MwaaPracticeStack


AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")

app = cdk.App()

environment = app.node.try_get_context("environment")[AWS_REGION]
environment["AWS_REGION"] = AWS_REGION
shared_variables = app.node.try_get_context("environment")["shared_variables"]
for key, value in shared_variables.items():
    environment[key] = (
        value.format(AWS_REGION=AWS_REGION) if isinstance(value, str) else value
    )

account = boto3.client("sts").get_caller_identity()["Account"]
response = (
    boto3.Session(region_name=environment["AWS_REGION"])
    .client("ec2")
    .describe_availability_zones()
)
all_availability_zones = [az["ZoneName"] for az in response["AvailabilityZones"]]
environment["ALL_AVAILABILITY_ZONES"] = all_availability_zones

MwaaPracticeStack(
    app,
    "MwaaPracticeStack",
    env=cdk.Environment(account=account, region=environment["AWS_REGION"]),
    environment=environment,
)
app.synth()
