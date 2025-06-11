import decimal
import json
import logging
from datetime import datetime
from utils.persistence.dynamodb import (
    get_table,
    put_item,
    get_item,
    query_items,
    scan_items,
    update_item,
    delete_item,
    TABLES,
    handle_dynamo_error,
    DynamoDBOperationError
)

logger = logging.getLogger('tokugawa_bot')

@handle_dynamo_error
async def get_player(user_id):
    """Get player data from DynamoDB."""
    try:
        table = get_table(TABLES['players'])
        response = await table.get_item(
            Key={
                'PK': f'PLAYER#{user_id}',
                'SK': 'PROFILE'
            }
        )
        
        if 'Item' not in response:
            return None
            
        item = response['Item']
        
        # Handle inventory serialization
        if isinstance(item.get('inventory'), str):
            try:
                item['inventory'] = json.loads(item['inventory'])
            except Exception as e:
                logger.warning(f"Could not decode inventory for player {user_id}: {e}")
                item['inventory'] = {}
        
        # Ensure inventory is a dictionary
        if not isinstance(item.get('inventory'), dict):
            item['inventory'] = {}
            
        # Normalize inventory items
        for item_id, item_data in item['inventory'].items():
            if isinstance(item_data, str):
                try:
                    item['inventory'][item_id] = json.loads(item_data)
                except:
                    item['inventory'][item_id] = {
                        'id': item_id,
                        'quantity': 1
                    }
            elif not isinstance(item_data, dict):
                item['inventory'][item_id] = {
                    'id': item_id,
                    'quantity': 1
                }
                
        # If any attributes were missing, update the player record
        if missing_attrs:
            logger.info(f"Updating player {user_id} with missing attributes")
            update_item = {
                'PK': f"PLAYER#{user_id}",
                'SK': 'PROFILE',
                **item
            }
            # Convert numeric values to Decimal for DynamoDB
            for k, v in update_item.items():
                if isinstance(v, (int, float)):
                    update_item[k] = decimal.Decimal(str(v))
                elif k == 'inventory' and isinstance(v, dict):
                    update_item[k] = json.dumps(v)
            await table.put_item(Item=update_item)
            logger.info(f"Successfully updated player {user_id} with missing attributes")
            
        logger.info(f"Final player data after normalization: {item}")
        return item
    except Exception as e:
        logger.error(f"Error getting player: {e}")
        raise DynamoDBOperationError(f"Failed to get player: {e}") from e

@handle_dynamo_error
async def create_player(user_id, name, **kwargs):
    """Create a new player in DynamoDB."""
    if not user_id or not name:
        return False
    try:
        table = get_table(TABLES['players'])
        # Default values for required attributes
        defaults = {
            'power_stat': 10,
            'dexterity': 10,
            'intellect': 10,
            'charisma': 10,
            'club_id': None,
            'exp': 0,
            'hp': 100,
            'tusd': 1000,
            'inventory': {},
            'level': 1
        }
        # Create player item with proper key structure and default values
        item = {
            'PK': f"PLAYER#{user_id}",
            'SK': 'PROFILE',
            'user_id': user_id,
            'name': name,
            **defaults,  # Add default values
            **kwargs     # Override defaults with any provided values
        }
        # Convert numeric values to Decimal
        for key, value in item.items():
            if isinstance(value, (int, float)):
                item[key] = decimal.Decimal(str(value))
            elif key == 'inventory' and isinstance(value, dict):
                item[key] = json.dumps(value)
        await table.put_item(Item=item)
        return True
    except Exception as e:
        logger.error(f"Error creating player: {e}")
        return False

@handle_dynamo_error
async def update_player(user_id, **kwargs):
    """Update a player in DynamoDB."""
    if not user_id:
        return False
    try:
        table = get_table(TABLES['players'])
        # Build update expression
        update_expr = "SET "
        expr_attr_values = {}
        for key, value in kwargs.items():
            if isinstance(value, (int, float)):
                value = decimal.Decimal(str(value))
            update_expr += f"#{key} = :{key}, "
            expr_attr_values[f":{key}"] = value
        update_expr = update_expr[:-2]  # Remove trailing comma and space
        # Add expression attribute names
        expr_attr_names = {f"#{key}": key for key in kwargs.keys()}
        # Update player
        await table.update_item(
            Key={
                'PK': f"PLAYER#{user_id}",
                'SK': 'PROFILE'
            },
            UpdateExpression=update_expr,
            ExpressionAttributeValues=expr_attr_values,
            ExpressionAttributeNames=expr_attr_names
        )
        return True
    except Exception as e:
        logger.error(f"Error updating player: {e}")
        return False

@handle_dynamo_error
async def update_player_reputation(user_id, reputation):
    """Update a player's reputation in DynamoDB."""
    try:
        table = get_table(TABLES['players'])
        await table.update_item(
            Key={'user_id': user_id},
            UpdateExpression='SET reputation = :rep',
            ExpressionAttributeValues={':rep': int(reputation)}
        )
        return True
    except Exception as e:
        logger.error(f"Error updating reputation for user {user_id}: {e}")
        return False 