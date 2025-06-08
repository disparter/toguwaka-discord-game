# AWS Deployment Guide for Tokugawa Discord Bot

This document provides an overview of the AWS resources and deployment process for the Tokugawa Discord Bot project.

## Table of Contents
1. [Overview](#overview)
2. [AWS Resources](#aws-resources)
3. [Deployment Process](#deployment-process)
4. [Lambda Functions](#lambda-functions)
5. [Cost Management](#cost-management)
6. [Database Backup](#database-backup)

## Overview

The Tokugawa Discord Bot is deployed on AWS using various services to ensure reliability, scalability, and cost efficiency. The primary deployment method is using AWS ECS (Elastic Container Service) with Fargate for running the bot in a containerized environment.

## AWS Resources

The following AWS resources are used in the deployment:

- **VPC and Subnets**: A Virtual Private Cloud with public subnets in multiple availability zones for high availability
- **ECS Cluster**: A Fargate cluster for running the bot container
- **IAM Roles and Policies**: For secure access to AWS resources
- **S3 Bucket**: For database backups
- **Lambda Functions**: For utility operations like DNS resolution testing and EC2 instance management
- **CloudWatch**: For monitoring and alarms
- **SNS**: For notifications about cost alerts

## Deployment Process

The deployment process involves:

1. Building a Docker container for the bot
2. Pushing the container to Amazon ECR
3. Creating an ECS task definition
4. Running the task or creating a service for continuous operation

Example commands for these steps can be found in the `deployment_tools/aws_scripts` directory.

## Lambda Functions

Several Lambda functions are used for utility operations:

1. **DNS Resolution Test**: Tests DNS resolution within the VPC
   - Code: `deployment_tools/aws_lambda/dns_resolution_lambda.py`

2. **EC2 Instance Management**:
   - Stop EC2 instances: `deployment_tools/aws_lambda/lambda_function.py`
   - Start EC2 instances: `deployment_tools/aws_lambda/lambda_religar.py`

These Lambda functions help with testing and cost management.

## Cost Management

To manage AWS costs, the project uses:

1. CloudWatch alarms to monitor estimated charges
2. Lambda functions to automatically stop EC2 instances when costs exceed thresholds
3. SNS notifications to alert administrators about cost issues

## Database Backup

The SQLite database is backed up to an S3 bucket using a script:
- Script: `deployment_tools/aws_scripts/s3_db_backup_script.sh`

This ensures data persistence and allows for recovery if needed.

---

For detailed AWS CLI commands and examples, refer to the scripts in the `deployment_tools/aws_scripts` directory.