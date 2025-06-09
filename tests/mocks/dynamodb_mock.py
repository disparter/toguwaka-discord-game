"""
Mock implementation of DynamoDB for testing.

This module provides a mock implementation of DynamoDB that simulates
the behavior of the actual service without making real API calls.
"""

import json
from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock

class MockDynamoDB:
    """Mock DynamoDB implementation."""
    
    def __init__(self):
        self.tables = {}
        self.meta = MagicMock()
        self.meta.client = self
        
    def reset(self):
        """Reset all tables."""
        self.tables.clear()
        
    def Table(self, name):
        """Get a table by name."""
        if name not in self.tables:
            self.tables[name] = MockTable(name)
        return self.tables[name]
        
    def create_table(self, **kwargs):
        """Create a new table."""
        table_name = kwargs['TableName']
        if table_name in self.tables:
            raise Exception(f"Table {table_name} already exists")
        self.tables[table_name] = MockTable(table_name)
        return {'TableDescription': {'TableName': table_name}}
        
    def describe_table(self, TableName):
        """Describe a table."""
        if TableName not in self.tables:
            raise Exception(f"Table {TableName} not found")
        return {'Table': {'TableName': TableName}}
        
    def get_waiter(self, waiter_name):
        """Get a mock waiter."""
        return MagicMock()

class MockTable:
    """Mock DynamoDB table."""
    
    def __init__(self, name):
        self.name = name
        self.items = {}
        
    def put_item(self, Item):
        """Put an item in the table."""
        key = self._get_key(Item)
        if key in self.items:
            raise Exception(f"Item with key {key} already exists")
        self.items[key] = Item
        return {'ResponseMetadata': {'HTTPStatusCode': 200}}
        
    def get_item(self, Key):
        """Get an item from the table."""
        key = self._get_key(Key)
        item = self.items.get(key)
        return {'Item': item} if item else {}
        
    def update_item(self, Key, UpdateExpression, ExpressionAttributeValues, ExpressionAttributeNames=None):
        """Update an item in the table."""
        key = self._get_key(Key)
        if key not in self.items:
            raise Exception(f"Item with key {key} not found")
            
        item = self.items[key]
        
        # Parse update expression
        updates = UpdateExpression.replace('SET ', '').split(', ')
        for update in updates:
            attr_name = update.split(' = ')[0].replace('#', '')
            attr_value = ExpressionAttributeValues[update.split(' = ')[1]]
            item[attr_name] = attr_value
            
        return {'ResponseMetadata': {'HTTPStatusCode': 200}}
        
    def delete_item(self, **kwargs):
        """Delete an item from the table."""
        key = self._get_key(kwargs.get('Key', {}))
        if key in self.items:
            del self.items[key]
        return {'ResponseMetadata': {'HTTPStatusCode': 200}}
        
    def scan(self, **kwargs):
        """Scan the table."""
        items = list(self.items.values())
        return {'Items': items, 'ResponseMetadata': {'HTTPStatusCode': 200}}
        
    def query(self, **kwargs):
        """Query the table."""
        items = list(self.items.values())
        return {'Items': items, 'ResponseMetadata': {'HTTPStatusCode': 200}}
        
    def _get_key(self, item):
        """Generate a key for an item."""
        if isinstance(item, dict):
            if 'PK' in item and 'SK' in item:
                return f"{item['PK']}#{item['SK']}"
            elif 'user_id' in item:
                return f"PLAYER#{item['user_id']}#PROFILE"
        return str(item)

# Create a singleton instance
mock_dynamodb = MockDynamoDB() 