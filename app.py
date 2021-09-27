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
                    )

# Name of the image from DockerHub to use for the Fargate service
image = "servian/techchallengeapp"


# Definition of resources needed to run the app
class TcaStack(cdk.Stack):
    def __init__(self, scope: cdk.Construct, construct_id: str,
                 **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Construct for VPC with 2 AZs, each with private and public subnets
        vpc = ec2.Vpc(self, "TcaVpc", max_azs=2)

        # Construct for an ECS cluster
        cluster = ecs.Cluster(self, "TcaCluster", vpc=vpc)

        # Construct for Fargate service from techchallengeapp in Dockerhub
        ecs_patterns.ApplicationLoadBalancedFargateService(
            self,
            "TcaService",
            cluster=cluster,
            cpu=256,
            desired_count=1,
            task_image_options=ecs_patterns.
            ApplicationLoadBalancedTaskImageOptions(
                image=ecs.ContainerImage.from_registry(image)),
            memory_limit_mib=512,
            public_load_balancer=True)


# Create the app
app = cdk.App()
TcaStack(app, "TcaStack")
app.synth()
