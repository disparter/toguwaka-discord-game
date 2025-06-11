"""
Custom logging configuration for Academia Tokugawa.

This module provides a custom logger that automatically includes line numbers
and other useful information in log messages.
"""

import logging
import sys
from typing import Optional

class CustomFormatter(logging.Formatter):
    """Custom formatter that includes line numbers and other useful information."""
    
    def format(self, record):
        # Add line number to the message if it's not already there
        if not hasattr(record, 'line_number'):
            record.line_number = f"{record.pathname}:{record.lineno}"
        
        # Add function name if it's not already there
        if not hasattr(record, 'function_name'):
            record.function_name = record.funcName
        
        return super().format(record)

def setup_logger(name: str = 'tokugawa_bot', level: int = logging.INFO) -> logging.Logger:
    """
    Set up a logger with custom formatting.
    
    Args:
        name: The name of the logger
        level: The logging level (default: INFO)
    
    Returns:
        A configured logger instance
    """
    # Get or create logger
    logger = logging.getLogger(name)
    
    # Only add handler if it doesn't already have one
    if not logger.handlers:
        logger.setLevel(level)
        
        # Create console handler with custom formatter
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        
        # Create formatter
        formatter = CustomFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(line_number)s] - %(message)s'
        )
        console_handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(console_handler)
    
    return logger

# Create default logger instance
logger = setup_logger()

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        name: Optional name for the logger. If not provided, returns the default logger.
    
    Returns:
        A logger instance
    """
    if name:
        return setup_logger(name)
    return logger 