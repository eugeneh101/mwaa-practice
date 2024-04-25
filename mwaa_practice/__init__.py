import json

from aws_cdk import (
    CfnOutput,
    RemovalPolicy,
    SecretValue,
    Stack,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_mwaa as mwaa,
    aws_redshift as redshift,
    aws_s3 as s3,
    aws_s3_deployment as s3_deploy,
    aws_secretsmanager as secrets_manager,
)
from constructs import Construct


class RedshiftService(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        vpc: ec2.Vpc,
        security_group: ec2.SecurityGroup,
        environment: dict,
    ) -> None:
        super().__init__(scope, construct_id)  # required
        redshift_cluster_subnet_group = redshift.CfnClusterSubnetGroup(
            self,
            "RedshiftClusterSubnetGroup",
            subnet_ids=vpc.select_subnets(  # Redshift can exist within only 1 AZs, though no longer true for RA3 nodes
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            ).subnet_ids
            # need at least 1 public subnet to be publicly accessible though MWAA can still
            # connect to Redshift if Redshift has only PRIVATE_WITH_EGRESS subnets
            + vpc.select_subnets(subnet_type=ec2.SubnetType.PUBLIC).subnet_ids,
            description="Redshift Cluster Subnet Group",
        )
        self.redshift_cluster = redshift.CfnCluster(
            self,
            "RedshiftCluster",
            cluster_type="single-node",  # for demo purposes
            number_of_nodes=1,  # for demo purposes
            node_type="ra3.xlplus",  # for demo purposes
            cluster_identifier=environment["REDSHIFT_DETAILS"]["REDSHIFT_CLUSTER_NAME"],
            db_name=environment["REDSHIFT_DETAILS"]["REDSHIFT_DATABASE_NAME"],
            master_username=environment["REDSHIFT_DETAILS"]["REDSHIFT_USERNAME"],
            master_user_password=environment["REDSHIFT_DETAILS"]["REDSHIFT_PASSWORD"],
            # iam_roles=[self.redshift_full_commands_full_access_role.role_arn],
            cluster_subnet_group_name=redshift_cluster_subnet_group.ref,  # needed or will use default VPC
            vpc_security_group_ids=[security_group.security_group_id],
            publicly_accessible=True,  # hard coded
        )


class MwaaPracticeStack(Stack):
    @property  ### appears needed for Vpc()
    def availability_zones(self):
        return self.all_availability_zones

    def __init__(
        self, scope: Construct, construct_id: str, environment: dict, **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.all_availability_zones = environment[  ### appears needed for Vpc()
            "ALL_AVAILABILITY_ZONES"
        ]
        self.vpc = ec2.Vpc(
            self,
            "MwaaVpc",
            vpc_name="mwaa-vpc",  # hard coded
            max_azs=2,  # MWAA needs 2 private subnets in different AZs
            nat_gateways=1,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Private-Subnet",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24,
                ),
                ec2.SubnetConfiguration(
                    name="Public-Subnet",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24,
                ),
            ],
            # availability_zones=environment["ALL_AVAILABILITY_ZONES"],
            # enable_dns_hostnames=True,
            # enable_dns_support=True,
        )
        self.security_group = ec2.SecurityGroup(
            self, "MwaaSg", vpc=self.vpc, security_group_name="mwaa-sg"  # hard coded
        )
        self.security_group.connections.allow_internally(
            port_range=ec2.Port.all_traffic(), description="MWAA"
        )

        self.dags_bucket = s3.Bucket(
            self,
            "S3BucketForMwaa",
            bucket_name=environment["S3_BUCKET_NAME"],
            versioned=True,  # needed by MWAA
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )
        lambda_policy_document = iam.PolicyDocument(
            statements=[
                iam.PolicyStatement(
                    actions=["s3:GetObject*", "s3:GetBucket*", "s3:List*"],
                    resources=[
                        f"arn:aws:s3:::{environment['CLOUDFORMATION_BUCKET']}",
                        f"arn:aws:s3:::{environment['CLOUDFORMATION_BUCKET']}/*",
                    ],
                ),
                iam.PolicyStatement(
                    actions=[
                        "s3:GetObject*",
                        "s3:GetBucket*",
                        "s3:List*",
                        "s3:DeleteObject*",
                        "s3:PutObject",
                        "s3:PutObjectLegalHold",
                        "s3:PutObjectRetention",
                        "s3:PutObjectTagging",
                        "s3:PutObjectVersionTagging",
                        "s3:Abort*",
                    ],
                    resources=[
                        self.dags_bucket.bucket_arn,
                        self.dags_bucket.bucket_arn + "/*",
                    ],
                ),
            ]
        )
        s3_upload_delete_role = iam.Role(
            self,
            "S3UploadDeleteRole",
            role_name="s3-upload-delete-role",  # hard coded
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                )
            ],
            inline_policies={"LambdaPolicyDocument": lambda_policy_document},
        )
        airflow_dags = s3_deploy.BucketDeployment(  # upload dags to S3
            self,
            "DeployDAG",
            destination_bucket=self.dags_bucket,
            destination_key_prefix=environment["DAGS_FOLDER"],
            sources=[s3_deploy.Source.asset("./dags")],  # hard coded
            prune=True,  ### it seems that delete Lambda uses a different IAM role
            retain_on_delete=False,
            role=s3_upload_delete_role,
            # vpc=...,
            # vpc_subnets=...,
        )
        airflow_requirements = s3_deploy.BucketDeployment(  # upload requirements to S3
            self,
            "DeployRequirements",
            destination_bucket=self.dags_bucket,
            destination_key_prefix=environment["REQUIREMENTS_FOLDER"],
            sources=[
                s3_deploy.Source.asset("./requirements", exclude=[".venv/*"])
            ],  # hard coded
            prune=True,  ### it seems that delete Lambda uses a different IAM role
            retain_on_delete=False,
            role=s3_upload_delete_role,
            # vpc=...,
            # vpc_subnets=...,
        )

        mwaa_policy_document = iam.PolicyDocument(
            statements=[
                iam.PolicyStatement(
                    actions=["airflow:PublishMetrics"],
                    effect=iam.Effect.ALLOW,
                    resources=[
                        f"arn:aws:airflow:{self.region}:{self.account}:environment/{environment['MWAA_CLUSTER_NAME']}"
                    ],
                ),
                iam.PolicyStatement(
                    actions=["s3:ListAllMyBuckets"],
                    effect=iam.Effect.DENY,
                    resources=[
                        self.dags_bucket.bucket_arn,
                        self.dags_bucket.bucket_arn + "/*",
                    ],
                ),
                iam.PolicyStatement(
                    actions=[
                        "s3:GetObject*",
                        "s3:GetBucket*",
                        "s3:List*",
                    ],
                    effect=iam.Effect.ALLOW,
                    resources=[
                        self.dags_bucket.bucket_arn,
                        self.dags_bucket.bucket_arn + "/*",
                    ],
                ),
                iam.PolicyStatement(
                    actions=[
                        "logs:CreateLogStream",
                        "logs:CreateLogGroup",
                        "logs:PutLogEvents",
                        "logs:GetLogEvents",
                        "logs:GetLogRecord",
                        "logs:GetLogGroupFields",
                        "logs:GetQueryResults",
                    ],
                    effect=iam.Effect.ALLOW,
                    resources=[
                        f"arn:aws:logs:{self.region}:{self.account}:log-group:airflow-{environment['MWAA_CLUSTER_NAME']}-*"
                    ],
                ),
                iam.PolicyStatement(
                    actions=["logs:DescribeLogGroups"],
                    effect=iam.Effect.ALLOW,
                    resources=["*"],
                ),
                iam.PolicyStatement(
                    actions=["cloudwatch:PutMetricData"],
                    effect=iam.Effect.ALLOW,
                    resources=["*"],
                ),
                iam.PolicyStatement(
                    actions=[
                        "sqs:ChangeMessageVisibility",
                        "sqs:DeleteMessage",
                        "sqs:GetQueueAttributes",
                        "sqs:GetQueueUrl",
                        "sqs:ReceiveMessage",
                        "sqs:SendMessage",
                    ],
                    effect=iam.Effect.ALLOW,
                    resources=[f"arn:aws:sqs:{self.region}:*:airflow-celery-*"],
                ),
                iam.PolicyStatement(  # needed for Airflow tasks to actually run
                    actions=[
                        "kms:Decrypt",
                        "kms:DescribeKey",
                        "kms:GenerateDataKey*",
                        "kms:Encrypt",
                    ],
                    effect=iam.Effect.ALLOW,
                    not_resources=[f"arn:aws:kms:*:{self.account}:key/*"],
                    conditions={
                        "StringEquals": {
                            "kms:ViaService": [f"sqs.{self.region}.amazonaws.com"]
                        }
                    },
                ),
                # based on guidance from https://docs.aws.amazon.com/mwaa/latest/userguide/connections-secrets-manager.html
                iam.PolicyStatement(
                    actions=[
                        "secretsmanager:GetResourcePolicy",
                        "secretsmanager:GetSecretValue",
                        "secretsmanager:DescribeSecret",
                        "secretsmanager:ListSecretVersionIds",
                    ],
                    effect=iam.Effect.ALLOW,
                    resources=[
                        f"arn:aws:secretsmanager:{self.region}:{self.account}:secret:*"
                    ],
                ),
                iam.PolicyStatement(
                    actions=[
                        "secretsmanager:ListSecrets",
                    ],
                    effect=iam.Effect.ALLOW,
                    resources=["*"],
                ),
                # iam.PolicyStatement(
                #     actions=[
                #         "ecs:RunTask",
                #         "ecs:DescribeTasks",
                #         "ecs:RegisterTaskDefinition",
                #         "ecs:DescribeTaskDefinition",
                #         "ecs:ListTasks"
                #     ],
                #     effect=iam.Effect.ALLOW,
                #     resources=[
                #         "*"
                #         ],
                #     ),
                # iam.PolicyStatement(
                #     actions=[
                #         "iam:PassRole"
                #     ],
                #     effect=iam.Effect.ALLOW,
                #     resources=[ "*" ],
                #     conditions= { "StringLike": { "iam:PassedToService": "ecs-tasks.amazonaws.com" } },
                #     ),
            ]
        )
        self.mwaa_service_role = iam.Role(
            self,
            "MwaaServiceRole",  # hard coded
            assumed_by=iam.CompositePrincipal(
                iam.ServicePrincipal("airflow.amazonaws.com"),
                iam.ServicePrincipal("airflow-env.amazonaws.com"),
                # iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            ),
            inline_policies={"CDKmwaaPolicyDocument": mwaa_policy_document},
            path="/service-role/",
            role_name=environment["MWAA_ROLE_NAME"],
        )

        network_configuration = mwaa.CfnEnvironment.NetworkConfigurationProperty(
            security_group_ids=[self.security_group.security_group_id],
            subnet_ids=[subnet.subnet_id for subnet in self.vpc.private_subnets],
        )
        logging_configuration = mwaa.CfnEnvironment.LoggingConfigurationProperty(
            dag_processing_logs=mwaa.CfnEnvironment.ModuleLoggingConfigurationProperty(
                enabled=True, log_level="INFO"
            ),
            task_logs=mwaa.CfnEnvironment.ModuleLoggingConfigurationProperty(
                enabled=True, log_level="INFO"
            ),
            worker_logs=mwaa.CfnEnvironment.ModuleLoggingConfigurationProperty(
                enabled=True, log_level="INFO"
            ),
            scheduler_logs=mwaa.CfnEnvironment.ModuleLoggingConfigurationProperty(
                enabled=True, log_level="INFO"
            ),
            webserver_logs=mwaa.CfnEnvironment.ModuleLoggingConfigurationProperty(
                enabled=True, log_level="INFO"
            ),
        )

        requirements_s3_object_version = (  # look in S3 console for requirements.txt version
            environment["REQUIREMENTS_VERSION"]
            if environment[
                "REQUIREMENTS_VERSION"
            ]  # cdk.json can't seem to recognize null as a valid value, so use false instead
            else None
        )
        startup_script_object_version = (  # look in S3 console for startup.sh version
            environment["STARTUP_SCRIPT_VERSION"]
            if environment[
                "STARTUP_SCRIPT_VERSION"
            ]  # cdk.json can't seem to recognize null as a valid value, so use false instead
            else None
        )
        self.mwaa_cluster = mwaa.CfnEnvironment(
            self,
            "MwaaCluster",
            name=environment["MWAA_CLUSTER_NAME"],
            airflow_configuration_options={  # might put in cdk.json
                "core.default_timezone": "utc",  # "AIRFLOW__CORE__DEFAULT_TIMEZONE"
                "core.parallelism": "32",  # "AIRFLOW__CORE__PARALLELISM": maximum number of task instances that can run simultaneously across the entire environment in parallel, regardless of the worker count
                "core.max_active_tasks_per_dag": "16",  # AIRFLOW__CORE__MAX_ACTIVE_TASKS_PER_DAG: number of task instances allowed to run concurrently in each DAG
                "celery.worker_autoscale": "7,0",  # AIRFLOW__CELERY__WORKER_AUTOSCALE":  maximum and minimum number of tasks that can run concurrently on any worker. If autoscale option is available, worker_concurrency will be ignored.
                # "core.worker_concurrency": "15",  # "AIRFLOW__CELERY__WORKER_CONCURRENCY": number of task instances that a worker will take
                "webserver.web_server_master_timeout": "100",
                "secrets.backend": "airflow.providers.amazon.aws.secrets.secrets_manager.SecretsManagerBackend",  # needed for Secrets Manager
                "secrets.backend_kwargs": json.dumps(  # needed for Secrets Manager
                    {
                        "connections_prefix": "airflow/connections",
                        "variables_prefix": "airflow/variables",
                    }
                ),
            },
            dag_s3_path=environment["DAGS_FOLDER"],
            requirements_s3_path=f"{environment['REQUIREMENTS_FOLDER']}/requirements.txt",
            requirements_s3_object_version=requirements_s3_object_version,
            startup_script_s3_path=f"{environment['REQUIREMENTS_FOLDER']}/startup.sh",
            startup_script_s3_object_version=startup_script_object_version,
            environment_class=environment["MWAA_SIZE"],
            max_workers=2,  ### change later
            execution_role_arn=self.mwaa_service_role.role_arn,
            logging_configuration=logging_configuration,
            network_configuration=network_configuration,
            source_bucket_arn=self.dags_bucket.bucket_arn,
            webserver_access_mode="PUBLIC_ONLY",
            airflow_version=environment["MWAA_VERSION"],
            # plugins_s3_object_version=None,
            # plugins_s3_path=None,
            # weekly_maintenance_window_start=None,
            # kms_key=key.key_arn,
        )

        if environment["REDSHIFT_DETAILS"]["TURN_ON_REDSHIFT_CLUSTER"]:
            self.security_group.add_ingress_rule(
                peer=ec2.Peer.any_ipv4(),
                connection=ec2.Port.tcp(5439),
            )
            self.redshift_service = RedshiftService(
                self,  # still need to manual load sample data
                "RedshiftService",
                vpc=self.vpc,
                security_group=self.security_group,
                environment=environment,
            )
            redshift_host_secret = secrets_manager.Secret(
                self,
                "RedshiftHostSecret",
                removal_policy=RemovalPolicy.DESTROY,
                secret_name="airflow/variables/redshift_host",
                secret_string_value=SecretValue.unsafe_plain_text(
                    secret=self.redshift_service.redshift_cluster.attr_endpoint_address
                ),
                # description=None,
            )
            redshift_password_secret = secrets_manager.Secret(
                self,
                "RedshiftPasswordSecret",
                removal_policy=RemovalPolicy.DESTROY,
                secret_name="airflow/variables/redshift_password",
                secret_string_value=SecretValue.unsafe_plain_text(
                    secret=environment["REDSHIFT_DETAILS"]["REDSHIFT_PASSWORD"]
                ),
                # description=None,
            )

        # connect AWS resources together
        self.mwaa_cluster.node.add_dependency(airflow_requirements)

        # write Cloudformation Outputs
        CfnOutput(
            self,
            id="VPCId",  # Output omits underscores and hyphens
            value=self.vpc.vpc_id,
            description="VPC (with private subnets) for MWAA",
            export_name=f"{self.region}:{self.account}:{self.stack_name}:vpc-id",
        )
