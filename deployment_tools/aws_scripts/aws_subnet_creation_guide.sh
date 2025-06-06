#!/bin/bash

# AWS Subnet Creation and Configuration Guide
# This script contains example AWS CLI commands for creating and configuring
# subnets, ECS tasks, Lambda functions, and other AWS resources for the Tokugawa project.
# Replace placeholder values with your actual resource IDs before using.

# Create a subnet in the us-east-1a availability zone
aws ec2 create-subnet \
  --vpc-id <YOUR-VPC-ID> \
  --cidr-block 10.0.1.0/24 \
  --availability-zone us-east-1a \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=tokugawa-subnet-public-a}]'

# Create a subnet in the us-east-1b availability zone
aws ec2 create-subnet \
  --vpc-id <YOUR-VPC-ID> \
  --cidr-block 10.0.2.0/24 \
  --availability-zone us-east-1b \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=tokugawa-subnet-public-b}]'

# Create a route to the internet gateway
aws ec2 create-route \
  --route-table-id <YOUR-ROUTE-TABLE-ID> \
  --destination-cidr-block 0.0.0.0/0 \
  --gateway-id <YOUR-INTERNET-GATEWAY-ID>

# Run an ECS task
aws ecs run-task \
  --cluster my-cluster \
  --task-definition tokugawa-bot-task-definition \
  --launch-type FARGATE \
  --network-configuration 'awsvpcConfiguration={
      "subnets":["<YOUR-SUBNET-ID>"],
      "securityGroups":["<YOUR-SECURITY-GROUP-ID>"],
      "assignPublicIp":"ENABLED"}'

# Create an ECS service
aws ecs create-service \
  --cluster tokugawa-cluster \
  --service-name tokugawa-service \
  --task-definition tokugawa-bot-task-definition \
  --launch-type FARGATE \
  --desired-count 1 \
  --network-configuration "awsvpcConfiguration={subnets=[\"<YOUR-SUBNET-ID>\"],securityGroups=[\"<YOUR-SECURITY-GROUP-ID>\"],assignPublicIp=\"ENABLED\"}"

# Create an SNS topic for cost alerts
aws sns create-topic --name CostAlerts

# Create a Lambda function to stop EC2 instances
aws lambda create-function \
  --function-name StopEC2Instances \
  --runtime python3.9 \
  --role arn:aws:iam::<YOUR-ACCOUNT-ID>:role/LambdaEC2StopRole \
  --handler lambda_function.lambda_handler \
  --zip-file fileb://function.zip

# Create a CloudWatch alarm to monitor costs
aws cloudwatch put-metric-alarm \
  --alarm-name "CostExceeds5Dollars" \
  --metric-name "EstimatedCharges" \
  --namespace "AWS/Billing" \
  --statistic "Maximum" \
  --period 21600 \
  --threshold 5 \
  --comparison-operator "GreaterThanOrEqualToThreshold" \
  --evaluation-periods 1 \
  --treat-missing-data "notBreaching" \
  --alarm-actions arn:aws:lambda:<YOUR-REGION>:<YOUR-ACCOUNT-ID>:function:StopEC2Instances \
  --dimensions Name=Currency,Value=USD

# Create a Lambda function to start EC2 instances
aws lambda create-function \
  --function-name StartEC2Instances \
  --runtime python3.9 \
  --role arn:aws:iam::<YOUR-ACCOUNT-ID>:role/LambdaEC2StopRole \
  --handler lambda_religar.lambda_handler \
  --zip-file fileb://function_religar.zip

# Copy a database file to S3
aws s3 cp /path/to/tokugawa.db s3://<YOUR-S3-BUCKET>/tokugawa.db

# Subscribe to SNS topic for cost alerts
aws sns subscribe \
  --topic-arn arn:aws:sns:<YOUR-REGION>:<YOUR-ACCOUNT-ID>:CostAlerts \
  --protocol email \
  --notification-endpoint <YOUR-EMAIL>

# Attach a policy to an IAM role
aws iam attach-role-policy \
  --role-name S3AccessRoleForTokugawa \
  --policy-arn arn:aws:iam::<YOUR-ACCOUNT-ID>:policy/S3AccessPolicyForTokugawa

# Describe ECS tasks
aws ecs describe-tasks \
  --cluster tokugawa-cluster \
  --tasks arn:aws:ecs:<YOUR-REGION>:<YOUR-ACCOUNT-ID>:task/tokugawa-cluster/<YOUR-TASK-ID>