import pytest
from pytest_bdd import scenarios, given, when, then, parsers
import boto3
import json

scenarios('../features/inventory_management.feature')

@given(parsers.parse('a player with ID "{player_id}" exists'))
def player_exists(player_id, localstack):
    """Create a player record in DynamoDB."""
    dynamodb = localstack['dynamodb']
    
    # Create player record
    player_data = {
        'player_id': {'S': player_id},
        'name': {'S': 'TestPlayer'},
        'inventory': {'M': {}}
    }
    
    dynamodb.put_item(
        TableName='players',
        Item=player_data
    )
    
    return {'player_id': player_id}

@when(parsers.parse('he receives a new item "{item_name}" with quantity {quantity:d}'))
def receive_new_item(item_name, quantity, player_exists, localstack):
    """Add a new item to the player's inventory."""
    dynamodb = localstack['dynamodb']
    cloudwatch = localstack['cloudwatch']
    player_id = player_exists['player_id']
    
    # Update inventory
    dynamodb.update_item(
        TableName='players',
        Key={'player_id': {'S': player_id}},
        UpdateExpression='SET inventory.#item = :quantity',
        ExpressionAttributeNames={'#item': item_name},
        ExpressionAttributeValues={':quantity': {'N': str(quantity)}}
    )
    
    # Log the inventory update
    cloudwatch.put_metric_data(
        Namespace='Game/Inventory',
        MetricData=[{
            'MetricName': 'ItemAdded',
            'Value': quantity,
            'Unit': 'Count',
            'Dimensions': [
                {'Name': 'ItemName', 'Value': item_name},
                {'Name': 'PlayerId', 'Value': player_id}
            ]
        }]
    )
    
    return {
        'player_id': player_id,
        'item_name': item_name,
        'quantity': quantity
    }

@then("the item should be added to his inventory in DynamoDB")
def verify_item_added(receive_new_item, localstack):
    """Verify that the item was added to the inventory."""
    dynamodb = localstack['dynamodb']
    player_id = receive_new_item['player_id']
    item_name = receive_new_item['item_name']
    quantity = receive_new_item['quantity']
    
    response = dynamodb.get_item(
        TableName='players',
        Key={'player_id': {'S': player_id}}
    )
    
    assert 'Item' in response
    assert item_name in response['Item']['inventory']['M']
    assert int(response['Item']['inventory']['M'][item_name]['N']) == quantity

@then("the inventory update should be logged in CloudWatch")
def verify_inventory_log(receive_new_item, localstack):
    """Verify that the inventory update was logged."""
    cloudwatch = localstack['cloudwatch']
    
    response = cloudwatch.get_metric_statistics(
        Namespace='Game/Inventory',
        MetricName='ItemAdded',
        StartTime='2024-03-19T00:00:00Z',
        EndTime='2024-03-21T00:00:00Z',
        Period=3600,
        Statistics=['Sum']
    )
    
    assert len(response['Datapoints']) > 0
    assert response['Datapoints'][0]['Sum'] == receive_new_item['quantity']

@given(parsers.parse('a player with ID "{player_id}" has an item "{item_name}" with quantity {quantity:d}'))
def player_has_item(player_id, item_name, quantity, localstack):
    """Set up a player with an existing item."""
    dynamodb = localstack['dynamodb']
    
    # Create player with item
    player_data = {
        'player_id': {'S': player_id},
        'name': {'S': 'TestPlayer'},
        'inventory': {
            'M': {
                item_name: {'N': str(quantity)}
            }
        }
    }
    
    dynamodb.put_item(
        TableName='players',
        Item=player_data
    )
    
    return {
        'player_id': player_id,
        'item_name': item_name,
        'quantity': quantity
    }

@when(parsers.parse('he receives {quantity:d} more "{item_name}" items'))
def receive_more_items(quantity, item_name, player_has_item, localstack):
    """Add more items to the player's inventory."""
    dynamodb = localstack['dynamodb']
    cloudwatch = localstack['cloudwatch']
    player_id = player_has_item['player_id']
    current_quantity = player_has_item['quantity']
    new_quantity = current_quantity + quantity
    
    # Update inventory
    dynamodb.update_item(
        TableName='players',
        Key={'player_id': {'S': player_id}},
        UpdateExpression='SET inventory.#item = :quantity',
        ExpressionAttributeNames={'#item': item_name},
        ExpressionAttributeValues={':quantity': {'N': str(new_quantity)}}
    )
    
    # Log the update
    cloudwatch.put_metric_data(
        Namespace='Game/Inventory',
        MetricData=[{
            'MetricName': 'ItemQuantityUpdated',
            'Value': quantity,
            'Unit': 'Count',
            'Dimensions': [
                {'Name': 'ItemName', 'Value': item_name},
                {'Name': 'PlayerId', 'Value': player_id}
            ]
        }]
    )
    
    return {
        'player_id': player_id,
        'item_name': item_name,
        'quantity': new_quantity
    }

@then(parsers.parse('the item quantity should be updated to {expected_quantity:d} in DynamoDB'))
def verify_quantity_updated(receive_more_items, expected_quantity, localstack):
    """Verify that the item quantity was updated."""
    dynamodb = localstack['dynamodb']
    player_id = receive_more_items['player_id']
    item_name = receive_more_items['item_name']
    
    response = dynamodb.get_item(
        TableName='players',
        Key={'player_id': {'S': player_id}}
    )
    
    assert 'Item' in response
    assert item_name in response['Item']['inventory']['M']
    assert int(response['Item']['inventory']['M'][item_name]['N']) == expected_quantity

@when(parsers.parse('he uses the "{item_name}" item'))
def use_item(item_name, player_has_item, localstack):
    """Use an item from the player's inventory."""
    dynamodb = localstack['dynamodb']
    cloudwatch = localstack['cloudwatch']
    player_id = player_has_item['player_id']
    current_quantity = player_has_item['quantity']
    new_quantity = current_quantity - 1
    
    # Update inventory
    dynamodb.update_item(
        TableName='players',
        Key={'player_id': {'S': player_id}},
        UpdateExpression='SET inventory.#item = :quantity',
        ExpressionAttributeNames={'#item': item_name},
        ExpressionAttributeValues={':quantity': {'N': str(new_quantity)}}
    )
    
    # Log the usage
    cloudwatch.put_metric_data(
        Namespace='Game/Inventory',
        MetricData=[{
            'MetricName': 'ItemUsed',
            'Value': 1,
            'Unit': 'Count',
            'Dimensions': [
                {'Name': 'ItemName', 'Value': item_name},
                {'Name': 'PlayerId', 'Value': player_id}
            ]
        }]
    )
    
    return {
        'player_id': player_id,
        'item_name': item_name,
        'quantity': new_quantity
    }

@then(parsers.parse('the item quantity should be reduced to {expected_quantity:d} in DynamoDB'))
def verify_quantity_reduced(use_item, expected_quantity, localstack):
    """Verify that the item quantity was reduced."""
    dynamodb = localstack['dynamodb']
    player_id = use_item['player_id']
    item_name = use_item['item_name']
    
    response = dynamodb.get_item(
        TableName='players',
        Key={'player_id': {'S': player_id}}
    )
    
    assert 'Item' in response
    assert item_name in response['Item']['inventory']['M']
    assert int(response['Item']['inventory']['M'][item_name]['N']) == expected_quantity 