import os
import pytest
import boto3
from localstack_client.config import Config
from localstack_client.session import Session

@pytest.fixture(scope="session")
def localstack():
    """Initialize LocalStack services."""
    session = Session()
    
    # Configure AWS clients to use LocalStack
    dynamodb = session.client('dynamodb', endpoint_url='http://localhost:4566')
    s3 = session.client('s3', endpoint_url='http://localhost:4566')
    cloudwatch = session.client('cloudwatch', endpoint_url='http://localhost:4566')
    
    # Create DynamoDB tables
    dynamodb.create_table(
        TableName='players',
        KeySchema=[
            {'AttributeName': 'player_id', 'KeyType': 'HASH'}
        ],
        AttributeDefinitions=[
            {'AttributeName': 'player_id', 'AttributeType': 'S'}
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 5,
            'WriteCapacityUnits': 5
        }
    )
    
    # Create S3 bucket
    s3.create_bucket(Bucket='game-assets')
    
    yield {
        'dynamodb': dynamodb,
        's3': s3,
        'cloudwatch': cloudwatch
    }
    
    # Cleanup
    dynamodb.delete_table(TableName='players')
    s3.delete_bucket(Bucket='game-assets')

@pytest.fixture
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    os.environ['AWS_SECURITY_TOKEN'] = 'testing'
    os.environ['AWS_SESSION_TOKEN'] = 'testing'
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1' 