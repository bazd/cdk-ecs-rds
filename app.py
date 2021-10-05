#!/usr/bin/env python3
"""
AWS CDK definition to run the Servian Tech Challenge App
https://github.com/servian/TechChallengeApp
By Barry Dawson
"""

import json

from aws_cdk import (
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
    aws_rds as rds,
    aws_secretsmanager as secretsmanager,
    core as cdk,
)


# Tags to assign to all taggable resources
STACK_TAGS = {
    "app": "tech-challenge-app",
    "environment": "poc",
}


# Definition of resources needed to run the app
class TcaStack(cdk.Stack):
    def __init__(self, scope: cdk.Construct, construct_id: str,
                 **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Generate secure password in secrets manager for RDS
        secret_template = {"username": "postgres"}
        rds_secret = secretsmanager.Secret(
            self,
            "TcaRdsSecret",
            description="RDS secret",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template=json.dumps(secret_template),
                generate_string_key="password",
                exclude_punctuation=True,
            )
        )

        # VPC with 2 AZs, each with private and public subnets
        vpc = ec2.Vpc(self, "TcaVpc", max_azs=2)

        # RDS postgres instance on private subnet
        rds_instance = rds.DatabaseInstance(
            self,
            "TcaDatabase",
            database_name="app",
            engine=rds.DatabaseInstanceEngine.postgres(
                version=rds.PostgresEngineVersion.VER_10_17),
            vpc=vpc,
            port=5432,
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.BURSTABLE2,
                ec2.InstanceSize.MICRO,
            ),
            allocated_storage=20,
            multi_az=True,
            removal_policy=cdk.RemovalPolicy.DESTROY,
            deletion_protection=False,
            backup_retention=cdk.Duration.days(1),
            credentials=rds.Credentials.from_secret(rds_secret)
        )

        # ECS cluster
        cluster = ecs.Cluster(self, "TcaCluster", vpc=vpc)

        # Fargate task definition
        task_definition = ecs.FargateTaskDefinition(
            self, "TcaTask", cpu=256, memory_limit_mib=512)
        image = ecs.ContainerImage.from_registry("servian/techchallengeapp")
        log_driver = ecs.LogDriver.aws_logs(stream_prefix="tca")
        container = task_definition.add_container(
            "TcaContainer",
            image=image,
            environment={
                "VTT_DBHOST": rds_instance.db_instance_endpoint_address,
                "VTT_LISTENPORT": "80",
            },
            secrets={
                "VTT_DBUSER": ecs.Secret.from_secrets_manager(
                    rds_secret, "username"),
                "VTT_DBPASSWORD": ecs.Secret.from_secrets_manager(
                    rds_secret, "password"),
            },
            command=["updatedb", "-s"],
            # command=["serve"],
            logging=log_driver,
        )
        port_mapping = ecs.PortMapping(container_port=80)
        container.add_port_mappings(port_mapping)

        # Fargate service
        service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self,
            "TcaService",
            cluster=cluster,
            task_definition=task_definition,
            desired_count=1,
            public_load_balancer=True,
        )

        # Fargate service auto scaling
        scaling = service.service.auto_scale_task_count(
            min_capacity=1,
            max_capacity=2,
        )
        scaling.scale_on_cpu_utilization(
            "CpuScaling",
            target_utilization_percent=50,
            scale_in_cooldown=cdk.Duration.seconds(60),
            scale_out_cooldown=cdk.Duration.seconds(60),
        )


# Create the app
app = cdk.App()
TcaStack(app, "TcaStack", tags=STACK_TAGS)
app.synth()
