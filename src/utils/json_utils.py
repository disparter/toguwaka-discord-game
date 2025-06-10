import json
from datetime import datetime
from decimal import Decimal

def default_serializer(obj):
    """
    Custom JSON serializer that handles datetime objects and Decimal objects.

    Args:
        obj: The object to serialize

    Returns:
        str: ISO format string for datetime objects
        float: Float value for Decimal objects

    Raises:
        TypeError: If the object type is not serializable
    """
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Type {type(obj)} not serializable")

def dumps(obj, **kwargs):
    """
    Wrapper for json.dumps that uses the default_serializer.

    Args:
        obj: The object to serialize
        **kwargs: Additional arguments to pass to json.dumps

    Returns:
        str: JSON string representation of the object
    """
    if 'default' not in kwargs:
        kwargs['default'] = default_serializer
    return json.dumps(obj, **kwargs)

def loads(s, **kwargs):
    """
    Wrapper for json.loads.

    Args:
        s: The JSON string to parse
        **kwargs: Additional arguments to pass to json.loads

    Returns:
        object: The parsed JSON object
    """
    return json.loads(s, **kwargs)
