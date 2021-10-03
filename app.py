#!/usr/bin/env python3
"""
AWS CDK definition to run the Servian Tech Challenge App
https://github.com/servian/TechChallengeApp
By Barry Dawson
"""

import os

from aws_cdk import (
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
    core as cdk,
    aws_rds as rds,
)

# Name of the image from DockerHub to use for the Fargate service
IMAGE = "servian/techchallengeapp"

# AWS tags to assign to all taggable resources
STACK_TAGS = {
    "app": "tech-challenge-app",
    "environment": "poc",
}


# Definition of resources needed to run the app
class TcaStack(cdk.Stack):
    def __init__(self, scope: cdk.Construct, construct_id: str,
                 **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # VPC with 2 AZs, each with private and public subnets
        vpc = ec2.Vpc(self, "TcaVpc", max_azs=2)

        # ECS cluster
        cluster = ecs.Cluster(self, "TcaCluster", vpc=vpc)

        # Fargate service
        tca_service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self,
            "TcaService",
            cluster=cluster,
            cpu=256,
            desired_count=1,
            task_image_options=ecs_patterns.
            ApplicationLoadBalancedTaskImageOptions(
                image=ecs.ContainerImage.from_registry(IMAGE)),
            memory_limit_mib=512,
            public_load_balancer=True,
        )

        # Fargate service auto scaling
        scaling = tca_service.service.auto_scale_task_count(
            min_capacity=1,
            max_capacity=2,
        )
        scaling.scale_on_cpu_utilization(
            "CpuScaling",
            target_utilization_percent=50,
            scale_in_cooldown=cdk.Duration.seconds(60),
            scale_out_cooldown=cdk.Duration.seconds(60),
        )

        # RDS postgres instance
        rds.DatabaseInstance(
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
        )


# Create the app
app = cdk.App()
TcaStack(app, "TcaStack", tags=STACK_TAGS)
app.synth()
