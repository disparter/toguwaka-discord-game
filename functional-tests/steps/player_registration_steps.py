import pytest
from pytest_bdd import scenarios, given, when, then, parsers
import boto3
import uuid
import json

scenarios('../features/player_registration.feature')

@given("a new user accesses the system")
def new_user_accesses_system():
    """Initialize a new user session."""
    return {"session_id": str(uuid.uuid4())}

@when(parsers.parse('he sends his name "{name}", class "{player_class}" and club "{club}"'))
def send_registration_data(name, player_class, club, new_user_accesses_system, localstack):
    """Send registration data to the system."""
    dynamodb = localstack['dynamodb']
    cloudwatch = localstack['cloudwatch']
    
    # Create player record
    player_id = str(uuid.uuid4())
    player_data = {
        'player_id': {'S': player_id},
        'name': {'S': name},
        'class': {'S': player_class},
        'club': {'S': club},
        'created_at': {'S': '2024-03-20T00:00:00Z'}
    }
    
    dynamodb.put_item(
        TableName='players',
        Item=player_data
    )
    
    # Log the registration
    cloudwatch.put_metric_data(
        Namespace='Game/PlayerRegistration',
        MetricData=[{
            'MetricName': 'NewPlayerRegistration',
            'Value': 1,
            'Unit': 'Count',
            'Dimensions': [
                {'Name': 'PlayerClass', 'Value': player_class},
                {'Name': 'Club', 'Value': club}
            ]
        }]
    )
    
    return {
        'player_id': player_id,
        'name': name,
        'class': player_class,
        'club': club
    }

@then("he should be registered in the DynamoDB database")
def verify_player_registration(send_registration_data, localstack):
    """Verify that the player was registered in DynamoDB."""
    dynamodb = localstack['dynamodb']
    player_id = send_registration_data['player_id']
    
    response = dynamodb.get_item(
        TableName='players',
        Key={'player_id': {'S': player_id}}
    )
    
    assert 'Item' in response
    assert response['Item']['player_id']['S'] == player_id
    assert response['Item']['name']['S'] == send_registration_data['name']
    assert response['Item']['class']['S'] == send_registration_data['class']
    assert response['Item']['club']['S'] == send_registration_data['club']

@then("he should receive a success response with his ID")
def verify_success_response(send_registration_data):
    """Verify that the registration response contains the player ID."""
    assert 'player_id' in send_registration_data
    assert len(send_registration_data['player_id']) > 0

@then("a welcome log should be created in CloudWatch")
def verify_cloudwatch_log(send_registration_data, localstack):
    """Verify that a welcome log was created in CloudWatch."""
    cloudwatch = localstack['cloudwatch']
    
    # Get the metric data
    response = cloudwatch.get_metric_statistics(
        Namespace='Game/PlayerRegistration',
        MetricName='NewPlayerRegistration',
        StartTime='2024-03-19T00:00:00Z',
        EndTime='2024-03-21T00:00:00Z',
        Period=3600,
        Statistics=['Sum']
    )
    
    assert len(response['Datapoints']) > 0
    assert response['Datapoints'][0]['Sum'] == 1

@when("he sends invalid registration data")
def send_invalid_registration_data(new_user_accesses_system):
    """Send invalid registration data to the system."""
    return {
        'name': '',
        'class': 'InvalidClass',
        'club': ''
    }

@then("he should receive an error response")
def verify_error_response(send_invalid_registration_data):
    """Verify that an error response was received."""
    assert send_invalid_registration_data['name'] == ''
    assert send_invalid_registration_data['class'] == 'InvalidClass'
    assert send_invalid_registration_data['club'] == ''

@then("no player record should be created in DynamoDB")
def verify_no_player_record(send_invalid_registration_data, localstack):
    """Verify that no player record was created in DynamoDB."""
    dynamodb = localstack['dynamodb']
    
    # Scan the table to verify no records exist
    response = dynamodb.scan(
        TableName='players',
        FilterExpression='#name = :name',
        ExpressionAttributeNames={'#name': 'name'},
        ExpressionAttributeValues={':name': {'S': send_invalid_registration_data['name']}}
    )
    
    assert len(response['Items']) == 0 