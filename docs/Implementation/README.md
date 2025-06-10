# Tokugawa Academy Deployment Guide

This guide covers all aspects of deploying Tokugawa Academy, from local development to production environments on AWS.

## Table of Contents

1. [Local Development](#local-development)
2. [Docker Deployment](#docker-deployment)
3. [AWS Deployment](#aws-deployment)
4. [Monitoring and Maintenance](#monitoring-and-maintenance)
5. [Security](#security)
6. [Troubleshooting](#troubleshooting)

## Local Development

### Prerequisites
- Python 3.8+
- pip
- Git
- Discord Bot Token
- Docker (optional)

### Setup
1. Clone the repository
2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate  # Windows
```
3. Install dependencies:
```bash
pip install -r requirements.txt
```
4. Configure environment variables
5. Start the development server:
```bash
python bot.py
```

## Docker Deployment

### Building the Image
```bash
docker build -t tokugawa-bot .
```

### Running the Container
```bash
docker run -d \
  --name tokugawa-bot \
  -e DISCORD_TOKEN=your_token \
  tokugawa-bot
```

### Docker Compose
```yaml
version: '3'
services:
  bot:
    build: .
    environment:
      - DISCORD_TOKEN=your_token
    volumes:
      - ./data:/app/data
```

## AWS Deployment

### Prerequisites
- AWS Account
- AWS CLI configured
- Docker installed
- Basic knowledge of AWS services
- Discord Developer Account and Bot Token

### Required AWS Services
- Amazon ECS (Fargate)
- Amazon DynamoDB
- Amazon S3
- Amazon CloudWatch
- AWS Secrets Manager

### Setup Steps

1. **ECR Repository Setup**
```bash
aws ecr create-repository --repository-name tokugawa-discord-bot --region us-east-1
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com
```

2. **Build and Push Image**
```bash
docker build -t tokugawa-discord-bot .
docker tag tokugawa-discord-bot:latest ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/tokugawa-discord-bot:latest
docker push ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/tokugawa-discord-bot:latest
```

3. **ECS Task Definition**
```json
{
  "family": "tokugawa-bot-task-definition",
  "executionRoleArn": "arn:aws:iam::ACCOUNT_ID:role/<TASK_EXECUTION_ROLE>",
  "taskRoleArn": "arn:aws:iam::ACCOUNT_ID:role/<TASK_ROLE>",
  "networkMode": "awsvpc",
  "containerDefinitions": [
    {
      "name": "tokugawa-bot",
      "image": "ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/tokugawa-discord-bot:latest",
      "memoryReservation": 512,
      "cpu": 256,
      "essential": true,
      "environment": [
        { "name": "DISCORD_TOKEN", "value": "<seu-token-discord>" },
        { "name": "USE_PRIVILEGED_INTENTS", "value": "True" },
        { "name": "GUILD_ID", "value": "<seu-id-guild>" }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/tokugawa-bot",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ],
  "cpu": "512",
  "memory": "1024",
  "requiresCompatibilities": ["FARGATE"]
}
```

4. **ECS Service Setup**
- Create ECS cluster
- Configure service with Fargate launch type
- Set up networking (VPC, subnets, security groups)
- Enable public IP for Discord API access

### Environment Variables
```env
NODE_ENV=production
DISCORD_TOKEN=your_bot_token
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=your_region
S3_BUCKET=your_bucket_name
DYNAMODB_TABLE_PREFIX=prod_
```

## Monitoring and Maintenance

### CloudWatch Setup
- Log groups for application logs
- Metrics for performance monitoring
- Alarms for critical events
- Dashboards for visualization

### Regular Maintenance
1. Update dependencies
2. Monitor performance
3. Check logs
4. Backup data
5. Review costs

### Cost Optimization
- Configure auto-scaling
- Use Savings Plans
- Monitor resource usage
- Implement cost alerts

## Security

### Best Practices
1. Use AWS Secrets Manager
2. Implement IAM roles
3. Enable VPC
4. Regular updates
5. Encrypt data at rest
6. Use HTTPS
7. Regular security audits

### Environment Variables
- Store sensitive data in Secrets Manager
- Use environment-specific configs
- Rotate credentials regularly

## Troubleshooting

### Common Issues

1. **Container Health Checks Failing**
   - Check application logs
   - Verify environment variables
   - Check network connectivity
   - Verify DynamoDB access

2. **High Latency**
   - Check CloudWatch metrics
   - Verify DynamoDB performance
   - Check instance size
   - Monitor DynamoDB throttling

3. **Cost Issues**
   - Review DynamoDB capacity units
   - Optimize instance sizes
   - Clean up unused resources
   - Monitor S3 usage

### Getting Help
1. Check the [FAQ](../Guides/FAQ.md)
2. Open an issue on GitHub
3. Contact the development team

## Support

For deployment-related issues:
1. Check the [FAQ](../Guides/FAQ.md)
2. Open an issue on GitHub
3. Contact the development team 