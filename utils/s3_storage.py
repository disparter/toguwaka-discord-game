import os
import boto3
import logging
from pathlib import Path
from botocore.exceptions import ClientError

logger = logging.getLogger('tokugawa_bot')

# Default S3 bucket name
DEFAULT_S3_BUCKET = 'tokugawa-db-storage'

# Get S3 bucket name from environment variable or use default
S3_BUCKET = os.environ.get('S3_DB_BUCKET', DEFAULT_S3_BUCKET)

# Local database path
LOCAL_DB_PATH = Path('data/tokugawa.db')

def get_s3_client():
    """
    Get an S3 client using boto3.
    Uses AWS credentials from environment variables or IAM role.
    """
    try:
        # Get the AWS region from environment or default to us-east-1
        aws_region = os.environ.get('AWS_REGION', 'us-east-1')

        # Create a session with the default credential provider chain
        # This will check for credentials in the following order:
        # 1. Environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
        # 2. Shared credential file (~/.aws/credentials)
        # 3. IAM role for EC2/ECS
        session = boto3.Session(region_name=aws_region)

        # Create and return S3 client from the session
        return session.client('s3')
    except Exception as e:
        logger.error(f"Failed to create S3 client: {e}")
        return None

def upload_db_to_s3():
    """
    Upload the local database file to S3.
    Returns True if successful, False otherwise.
    """
    if not LOCAL_DB_PATH.exists():
        logger.error(f"Local database file not found at {LOCAL_DB_PATH}")
        return False

    s3_client = get_s3_client()
    if not s3_client:
        return False

    try:
        # Upload the file
        s3_client.upload_file(
            str(LOCAL_DB_PATH),
            S3_BUCKET,
            'tokugawa.db'
        )
        logger.info(f"Successfully uploaded database to S3 bucket {S3_BUCKET}")
        return True
    except ClientError as e:
        logger.error(f"Error uploading database to S3: {e}")
        return False

def download_db_from_s3():
    """
    Download the database file from S3 to the local path.
    Returns True if successful, False otherwise.
    """
    # Ensure the data directory exists
    os.makedirs(os.path.dirname(LOCAL_DB_PATH), exist_ok=True)

    s3_client = get_s3_client()
    if not s3_client:
        return False

    try:
        # Check if the file exists in S3
        s3_client.head_object(Bucket=S3_BUCKET, Key='tokugawa.db')

        # Download the file
        s3_client.download_file(
            S3_BUCKET,
            'tokugawa.db',
            str(LOCAL_DB_PATH)
        )
        logger.info(f"Successfully downloaded database from S3 bucket {S3_BUCKET}")
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == '404':
            logger.warning(f"Database file not found in S3 bucket {S3_BUCKET}")
        else:
            logger.error(f"Error downloading database from S3: {e}")
        return False

def ensure_s3_bucket_exists():
    """
    Ensure the S3 bucket exists, create it if it doesn't.
    Returns True if the bucket exists or was created successfully, False otherwise.
    """
    s3_client = get_s3_client()
    if not s3_client:
        return False

    try:
        # Check if the bucket exists
        s3_client.head_bucket(Bucket=S3_BUCKET)
        logger.info(f"S3 bucket {S3_BUCKET} exists")
        return True
    except ClientError as e:
        # If the bucket doesn't exist, create it
        if e.response['Error']['Code'] == '404':
            try:
                # Get the AWS region from environment or default to us-east-1
                aws_region = os.environ.get('AWS_REGION', 'us-east-1')

                # Create the bucket
                s3_client.create_bucket(
                    Bucket=S3_BUCKET,
                    CreateBucketConfiguration={
                        'LocationConstraint': aws_region
                    }
                )
                logger.info(f"Created S3 bucket {S3_BUCKET}")
                return True
            except ClientError as create_error:
                logger.error(f"Error creating S3 bucket: {create_error}")
                return False
        else:
            logger.error(f"Error checking S3 bucket: {e}")
            return False