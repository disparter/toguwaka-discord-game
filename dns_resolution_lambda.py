import socket

def lambda_handler(event, context):
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