import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    AWS Lambda function to start (reconnect) EC2 instances that are in a stopped state.
    
    This function is designed to be triggered manually or by scheduled events to
    restart EC2 instances that were previously stopped, possibly by the StopEC2Instances
    Lambda function. This allows for automated management of EC2 instance lifecycle
    to optimize costs.
    
    Args:
        event (dict): The event data passed to the Lambda function
        context (LambdaContext): The runtime information of the Lambda function
        
    Returns:
        dict: A response containing the status code and information about the instances
              that were started or a message indicating no instances were started
        
    Raises:
        Exception: If there's an error starting the instances
    """
    try:
        ec2 = boto3.client('ec2', region_name='us-east-1')  # Replace with your region if different
        
        # List stopped instances
        instances = ec2.describe_instances(
            Filters=[{'Name': 'instance-state-name', 'Values': ['stopped']}]
        )
        
        instance_ids = [
            instance['InstanceId']
            for reservation in instances['Reservations']
            for instance in reservation['Instances']
        ]

        if instance_ids:
            # Start instances
            ec2.start_instances(InstanceIds=instance_ids)
            logger.info(f"Starting instances: {instance_ids}")
        else:
            logger.info("No stopped instances found to start.")
            
        return {
            "statusCode": 200,
            "body": f"Instances started: {instance_ids}" if instance_ids else "No instances to start."
        }
    except Exception as e:
        logger.error(f"Error starting instances: {str(e)}")
        raise