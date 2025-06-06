#!/bin/bash

# AWS Subnet and Security Group Query Commands
# This script contains example AWS CLI commands for querying and working with
# VPC resources such as subnets, security groups, and DHCP options.
# Replace placeholder values with your actual resource IDs before using.

# Associate DHCP options with a VPC
aws ec2 associate-dhcp-options \
  --dhcp-options-id <YOUR-DHCP-OPTIONS-ID> \
  --vpc-id <YOUR-VPC-ID>

# List all subnets in a VPC with their availability zones
aws ec2 describe-subnets \
  --filters Name=vpc-id,Values=<YOUR-VPC-ID> \
  --query "Subnets[].[SubnetId, AvailabilityZone]" \
  --output table

# List all security groups in a VPC with their names and descriptions
aws ec2 describe-security-groups \
  --filters Name=vpc-id,Values=<YOUR-VPC-ID> \
  --query "SecurityGroups[].[GroupId, GroupName, Description]" \
  --output table

# Create a Lambda function in a VPC
aws lambda create-function \
  --function-name test-resolve-dns \
  --runtime python3.9 \
  --role arn:aws:iam::<YOUR-ACCOUNT-ID>:role/LambdaEC2StopRole \
  --handler dns_resolution_lambda.lambda_handler \
  --timeout 15 \
  --memory-size 128 \
  --zip-file fileb://function.zip \
  --vpc-config SubnetIds=<YOUR-SUBNET-ID>,SecurityGroupIds=<YOUR-SECURITY-GROUP-ID>

# Describe an ECS task definition
aws ecs describe-task-definition \
  --task-definition tokugawa-bot-task-definition \
  --query "taskDefinition.containerDefinitions" \
  --output json