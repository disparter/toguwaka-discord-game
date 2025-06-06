import os
import boto3
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Union
from botocore.exceptions import ClientError, NoCredentialsError, EndpointConnectionError

logger = logging.getLogger('tokugawa_bot')

# Default S3 bucket name
DEFAULT_S3_BUCKET = 'tokugawa-db-storage'

# Get S3 bucket name from environment variable or use default
S3_BUCKET = os.environ.get('S3_DB_BUCKET', DEFAULT_S3_BUCKET)

# Local database path
LOCAL_DB_PATH = Path('data/tokugawa.db')

# Default database key in S3
DEFAULT_DB_KEY = 'tokugawa.db'

class S3ClientError(Exception):
    """Base exception for S3 client errors."""
    pass

class S3ConnectionError(S3ClientError):
    """Exception raised when connection to S3 fails."""
    pass

class S3OperationError(S3ClientError):
    """Exception raised when an S3 operation fails."""
    pass

class S3Client:
    """
    A class to handle S3 operations with improved error handling and logging.
    """
    def __init__(self, bucket_name: str = S3_BUCKET, region: str = None, db_key: str = DEFAULT_DB_KEY):
        """
        Initialize the S3 client.

        Args:
            bucket_name: The name of the S3 bucket
            region: The AWS region (defaults to AWS_REGION environment variable or 'us-east-1')
            db_key: The key for the database file in S3
        """
        self.bucket_name = bucket_name
        self.region = region or os.environ.get('AWS_REGION', 'us-east-1')
        self.db_key = db_key
        self._client = None

    @property
    def client(self):
        """
        Lazy initialization of the S3 client.

        Returns:
            The boto3 S3 client

        Raises:
            S3ConnectionError: If connection to S3 fails
        """
        if self._client is None:
            try:
                # Create a session with the default credential provider chain
                session = boto3.Session(region_name=self.region)

                # Create S3 client from the session
                self._client = session.client('s3')
                logger.debug(f"S3 client initialized for region {self.region}")
            except (NoCredentialsError, EndpointConnectionError) as e:
                error_msg = f"Failed to create S3 client: {str(e)}"
                logger.error(error_msg)
                raise S3ConnectionError(error_msg) from e
            except Exception as e:
                error_msg = f"Unexpected error creating S3 client: {str(e)}"
                logger.error(error_msg)
                raise S3ConnectionError(error_msg) from e

        return self._client

    def upload_file(self, local_path: Union[str, Path], s3_key: str = None) -> bool:
        """
        Upload a file to S3.

        Args:
            local_path: The local path of the file to upload
            s3_key: The key to use in S3 (defaults to the filename)

        Returns:
            True if successful, False otherwise

        Raises:
            S3OperationError: If the upload operation fails
        """
        local_path = Path(local_path)
        if not local_path.exists():
            error_msg = f"Local file not found at {local_path}"
            logger.error(error_msg)
            return False

        s3_key = s3_key or local_path.name

        try:
            self.client.upload_file(
                str(local_path),
                self.bucket_name,
                s3_key
            )
            logger.info(f"Successfully uploaded {local_path} to S3 bucket {self.bucket_name} with key {s3_key}")
            return True
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            error_msg = f"Error uploading file to S3 (code: {error_code}): {str(e)}"
            logger.error(error_msg)
            raise S3OperationError(error_msg) from e
        except Exception as e:
            error_msg = f"Unexpected error uploading file to S3: {str(e)}"
            logger.error(error_msg)
            raise S3OperationError(error_msg) from e

    def download_file(self, s3_key: str, local_path: Union[str, Path]) -> bool:
        """
        Download a file from S3.

        Args:
            s3_key: The key of the file in S3
            local_path: The local path to save the file to

        Returns:
            True if successful, False otherwise

        Raises:
            S3OperationError: If the download operation fails
        """
        local_path = Path(local_path)

        # Ensure the directory exists
        os.makedirs(local_path.parent, exist_ok=True)

        try:
            # Check if the file exists in S3
            self.client.head_object(Bucket=self.bucket_name, Key=s3_key)

            # Download the file
            self.client.download_file(
                self.bucket_name,
                s3_key,
                str(local_path)
            )
            logger.info(f"Successfully downloaded {s3_key} from S3 bucket {self.bucket_name} to {local_path}")
            return True
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            if error_code == '404':
                logger.warning(f"File {s3_key} not found in S3 bucket {self.bucket_name}")
            else:
                error_msg = f"Error downloading file from S3 (code: {error_code}): {str(e)}"
                logger.error(error_msg)
                raise S3OperationError(error_msg) from e
            return False
        except Exception as e:
            error_msg = f"Unexpected error downloading file from S3: {str(e)}"
            logger.error(error_msg)
            raise S3OperationError(error_msg) from e

    def ensure_bucket_exists(self) -> bool:
        """
        Ensure the S3 bucket exists, create it if it doesn't.

        Returns:
            True if the bucket exists or was created successfully, False otherwise

        Raises:
            S3OperationError: If the operation fails
        """
        try:
            # Check if the bucket exists
            self.client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"S3 bucket {self.bucket_name} exists")
            return True
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            # If the bucket doesn't exist, create it
            if error_code == '404':
                try:
                    # Create the bucket
                    self.client.create_bucket(
                        Bucket=self.bucket_name,
                        CreateBucketConfiguration={
                            'LocationConstraint': self.region
                        }
                    )
                    logger.info(f"Created S3 bucket {self.bucket_name} in region {self.region}")
                    return True
                except ClientError as create_error:
                    error_msg = f"Error creating S3 bucket: {str(create_error)}"
                    logger.error(error_msg)
                    raise S3OperationError(error_msg) from create_error
            else:
                error_msg = f"Error checking S3 bucket (code: {error_code}): {str(e)}"
                logger.error(error_msg)
                raise S3OperationError(error_msg) from e
        except Exception as e:
            error_msg = f"Unexpected error checking S3 bucket: {str(e)}"
            logger.error(error_msg)
            raise S3OperationError(error_msg) from e

# Singleton instance of S3Client for reuse
_s3_client_instance = None

def get_s3_client_instance() -> S3Client:
    """
    Get a singleton instance of the S3Client class.

    This function ensures that only one instance of the S3Client is created
    and reused throughout the application, following the Singleton pattern.

    Returns:
        An instance of the S3Client class
    """
    global _s3_client_instance
    if _s3_client_instance is None:
        _s3_client_instance = S3Client(bucket_name=S3_BUCKET)
    return _s3_client_instance

def upload_db_to_s3() -> bool:
    """
    Upload the local database file to S3.

    Returns:
        True if successful, False otherwise
    """
    try:
        s3_client = get_s3_client_instance()
        return s3_client.upload_file(LOCAL_DB_PATH, DEFAULT_DB_KEY)
    except S3ClientError as e:
        logger.error(f"Failed to upload database to S3: {str(e)}")
        return False

def download_db_from_s3() -> bool:
    """
    Download the database file from S3 to the local path.

    Returns:
        True if successful, False otherwise
    """
    try:
        s3_client = get_s3_client_instance()
        return s3_client.download_file(DEFAULT_DB_KEY, LOCAL_DB_PATH)
    except S3ClientError as e:
        logger.error(f"Failed to download database from S3: {str(e)}")
        return False

def ensure_s3_bucket_exists() -> bool:
    """
    Ensure the S3 bucket exists, create it if it doesn't.

    Returns:
        True if the bucket exists or was created successfully, False otherwise
    """
    try:
        s3_client = get_s3_client_instance()
        return s3_client.ensure_bucket_exists()
    except S3ClientError as e:
        logger.error(f"Failed to ensure S3 bucket exists: {str(e)}")
        return False
