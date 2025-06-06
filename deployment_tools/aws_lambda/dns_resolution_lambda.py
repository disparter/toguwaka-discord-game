import socket

def lambda_handler(event, context):
    """
    AWS Lambda function to test DNS resolution within a VPC.
    
    This function attempts to resolve a DNS name to an IP address to verify
    that DNS resolution is working correctly within the VPC where the Lambda
    function is deployed.
    
    Args:
        event (dict): The event data passed to the Lambda function
        context (LambdaContext): The runtime information of the Lambda function
        
    Returns:
        dict: A response containing the status code and the resolved IP address
              or an error message
    """
    try:
        dns_name = "sts.us-east-1.amazonaws.com"
        ip = socket.gethostbyname(dns_name)
        return {
            "statusCode": 200,
            "body": f"{dns_name} resolved to {ip}"
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": str(e)
        }