
# Servian Tech Challenge App

This repo contains code for provisioning the Servian Tech Challenge App into AWS using the AWS Cloud Development Kit (CDK)

## High-Level Architecture

The CDK app provisions the following infrastructure in AWS, along with associated IAM roles, security groups and other dependant resources:

* A VPC with private and public subnets
* A Postgres RDS instance with multi-az enabled for the database
* An auto-generated secret for the RDS database password
* An ECS cluster with a load-balanced auto-scaled Fargate task to run the app container

Unfortunately I ran out of time to get the app fully working.  Connecting to the ALB after deployment returns an error - see <https://github.com/bazd/cdk-ecs-rds/issues/8> for details

## How to deploy

Note: The deployment process was tested on Windows 10, but should also work on Mac and Linux

### 1. Prerequisites

1. An AWS account for the infrastructure to be provisioned into (a single region is used)
1. An IAM user with an access key for programmatic access.  The user must have permission to provision the resources into AWS (the deployment process was developed and tested with AdministratorAccess permissions)
1. Node.js installed (tested with 14.17.6) <https://nodejs.org/en/download/>
1. AWS CLI v2 installed (tested with 2.0.26) <https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html>
1. AWS CDK v1 installed (tested with 1.124.0) <https://docs.aws.amazon.com/cdk/latest/guide/getting_started.html>
1. Python v3.x installed (tested with 3.9.5) <https://www.python.org/downloads/>
1. Git installed and configured (tested with 2.23.0). <https://gitforwindows.org/>

### 2. Configure the AWS CLI

1. Open a command prompt or terminal.  It should stay open for all of the steps in this deployment guide
1. Run `aws configure`
1. When prompted, enter values for `AWS Access Key ID` and `AWS Secret Access Key` for  the IAM user
1. When prompted for `Default region name`, enter the region that you want to deploy the app into (the app was developed and tested in ap-southeast-2)
1. When prompted for `Default output format`, press Enter

### 3. Clone the repo

Run the commands below to clone this repo locally

1. `git clone https://github.com/bazd/cdk-ecs-rds.git`
1. `cd cdk-ecs-rds`

### 4. Install Python requirements into virtual environment

Run the following commands according to the OS of the deployment environment

Windows

1. `python -m venv .venv`
1. `.venv\scripts\activate.bat`
1. `pip install -r requirements.txt`

Mac / Linux:

1. `python -m venv .venv`
1. `source .venv/bin/activate`
1. `pip install -r requirements.txt`

### 5. Deploy the app using CDK

1. Run `cdk synth`
    1. This executes the app, which causes the resources defined in it to be translated into an AWS CloudFormation template locally
    1. A list of the resources to be created is displayed
1. Run `cdk deploy` then enter `y` to confirm when prompted
    1. This provisions the resources into AWS using the automatically generated CloudFormation template
    1. The terminal window will display the status of the deployment of each resource
    1. You can optionally log in to the AWS Console and see that a CloudFormation stack has been created
1. Wait for the deployment to complete - it should take about 10 mins
    1. When all resources have finished deploying, 2 outputs will be displayed.  These are the Load Balancer DNS name and the ECS Service URL, and can be used to connect to the app (Unfortunately I wasn't able to get the app working, so connecting to this endpoint will return an error)

Note: The app container will have been started with the "updatedb -s" option to prove that connectivity to RDS is ok.  If you want the app to start serving requests, you can do the following:
1. Edit `app.py`
1. Comment out this line `command=["updatedb", "-s"],`
1. Remove comment from this line `# command=["serve"],`
1. Save the file
1. Run `cdk synth`
1. Run `cdk deploy`

The app container will now be reprovisioned to start with the `serve` option, although the endpoint will still return an error.  See https://github.com/bazd/cdk-ecs-rds/issues/9 for more details

## How to delete

If you want to completely remove all resources, do the following:

1. Run `cdk destroy` then `y` to confirm
2. From the AWS console, manually delete any CloudWatch log groups with a prefix of `TcaStack-TcaTaskTcaContainerLogGroup`

## Future improvements

Potential improvements that can be added as required

* Support for multiple environments, with different config in each (eg no multi-az database in dev)
* Split the CDK app into separate stacks for easier management (eg network, app and database stacks)
* IAM deployment user with permissions restricted to the minimum required
* CI/CD for deployment
* Nice DNS cname record pointing to the ALB name
* RDS storage autoscaling
* Monitoring

## Useful CDK commands

* `cdk ls`          list all stacks in the app
* `cdk synth`       emits the synthesized CloudFormation template
* `cdk deploy`      deploy this stack to your default AWS account/region
* `cdk diff`        compare deployed stack with current state
* `cdk docs`        open CDK documentation
