import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    AWS Lambda function to stop EC2 instances based on specified criteria.
    
    This function is designed to be triggered by events such as CloudWatch alarms
    or scheduled events. It stops EC2 instances that are currently running and
    match the specified filters (e.g., tagged with Environment=Production).
    
    This can be used as a cost-saving measure to automatically stop instances
    when they're not needed or when costs exceed a certain threshold.
    
    Args:
        event (dict): The event data passed to the Lambda function
        context (LambdaContext): The runtime information of the Lambda function
        
    Returns:
        None
        
    Raises:
        Exception: If there's an error stopping the instances
    """
    try:
        logger.info("Starting execution of StopEC2Instances Lambda function.")
        ec2 = boto3.client('ec2', region_name='us-east-1')  # Replace with your region if different
        
        # Get all running instances matching the filter criteria
        instances = ec2.describe_instances(
            Filters=[
                {'Name': 'instance-state-name', 'Values': ['running']},
                {'Name': 'tag:Environment', 'Values': ['Production']}  # Example tag filter
            ]
        )
        
        instance_ids = [
            instance['InstanceId']
            for reservation in instances['Reservations']
            for instance in reservation['Instances']
        ]

        if instance_ids:
            # Stop instances
            ec2.stop_instances(InstanceIds=instance_ids)
            logger.info(f"Stopping instances: {instance_ids}")
        else:
            logger.info("No active instances found matching the criteria.")
    except Exception as e:
        logger.error(f"Error stopping instances: {str(e)}")
        raise