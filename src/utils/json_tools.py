"""
JSON Tools for generating and validating game content.
This module provides utilities for working with JSON data files in the game.
"""
import json
import os
import logging
from typing import Dict, List, Any, Optional, Union

# Try to import jsonschema, but don't fail if it's not available
try:
    import jsonschema
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False
    print("Warning: jsonschema module not found. Schema validation will be disabled.")
    print("To enable schema validation, install jsonschema: pip install jsonschema")

logger = logging.getLogger('tokugawa_bot')

class JSONValidator:
    """
    Validates JSON files against schemas to ensure data integrity.
    """
    def __init__(self, schemas_dir: str = "data/schemas"):
        """
        Initialize the validator with the directory containing schema files.

        Args:
            schemas_dir: Path to the directory containing JSON schema files
        """
        self.schemas_dir = schemas_dir
        self.schemas = {}

        # Create schemas directory if it doesn't exist
        os.makedirs(schemas_dir, exist_ok=True)

        # Load all schema files
        self._load_schemas()

    def _load_schemas(self) -> None:
        """
        Loads all schema files from the schemas directory.
        """
        if not os.path.exists(self.schemas_dir):
            logger.warning(f"Schemas directory not found: {self.schemas_dir}")
            return

        for filename in os.listdir(self.schemas_dir):
            if filename.endswith(".json"):
                try:
                    file_path = os.path.join(self.schemas_dir, filename)
                    with open(file_path, 'r') as f:
                        schema = json.load(f)

                    # Use the filename without extension as the schema name
                    schema_name = os.path.splitext(filename)[0]
                    self.schemas[schema_name] = schema

                    logger.info(f"Loaded schema: {schema_name}")
                except Exception as e:
                    logger.error(f"Error loading schema from {filename}: {e}")

    def validate(self, data: Dict[str, Any], schema_name: str) -> Dict[str, Any]:
        """
        Validates data against a schema.

        Args:
            data: The data to validate
            schema_name: The name of the schema to validate against

        Returns:
            The validated data

        Raises:
            ValueError: If the schema is not found
            jsonschema.exceptions.ValidationError: If the data does not match the schema
        """
        if schema_name not in self.schemas:
            raise ValueError(f"Schema not found: {schema_name}")

        jsonschema.validate(instance=data, schema=self.schemas[schema_name])
        return data

    def validate_file(self, file_path: str, schema_name: str) -> Dict[str, Any]:
        """
        Validates a JSON file against a schema.

        Args:
            file_path: Path to the JSON file to validate
            schema_name: The name of the schema to validate against

        Returns:
            The validated data

        Raises:
            ValueError: If the schema is not found or the file cannot be read
            jsonschema.exceptions.ValidationError: If the data does not match the schema
        """
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
        except Exception as e:
            raise ValueError(f"Error reading file {file_path}: {e}")

        return self.validate(data, schema_name)

    def create_schema_from_example(self, example_data: Dict[str, Any], schema_name: str) -> Dict[str, Any]:
        """
        Creates a schema from example data.

        Args:
            example_data: Example data to create a schema from
            schema_name: The name of the schema to create

        Returns:
            The created schema
        """
        # This is a simple implementation that could be expanded
        schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": schema_name,
            "type": "object",
            "properties": {}
        }

        # Add properties based on example data
        for key, value in example_data.items():
            if isinstance(value, dict):
                schema["properties"][key] = {
                    "type": "object"
                }
            elif isinstance(value, list):
                schema["properties"][key] = {
                    "type": "array"
                }
            elif isinstance(value, str):
                schema["properties"][key] = {
                    "type": "string"
                }
            elif isinstance(value, int):
                schema["properties"][key] = {
                    "type": "integer"
                }
            elif isinstance(value, float):
                schema["properties"][key] = {
                    "type": "number"
                }
            elif isinstance(value, bool):
                schema["properties"][key] = {
                    "type": "boolean"
                }
            else:
                schema["properties"][key] = {}

        # Save the schema
        schema_path = os.path.join(self.schemas_dir, f"{schema_name}.json")
        with open(schema_path, 'w') as f:
            json.dump(schema, f, indent=2)

        # Add to loaded schemas
        self.schemas[schema_name] = schema

        logger.info(f"Created schema: {schema_name}")

        return schema

class JSONGenerator:
    """
    Generates JSON files from templates or examples.
    """
    def __init__(self, templates_dir: str = "data/templates"):
        """
        Initialize the generator with the directory containing template files.

        Args:
            templates_dir: Path to the directory containing JSON template files
        """
        self.templates_dir = templates_dir
        self.templates = {}

        # Create templates directory if it doesn't exist
        os.makedirs(templates_dir, exist_ok=True)

        # Load all template files
        self._load_templates()

    def _load_templates(self) -> None:
        """
        Loads all template files from the templates directory.
        """
        if not os.path.exists(self.templates_dir):
            logger.warning(f"Templates directory not found: {self.templates_dir}")
            return

        for filename in os.listdir(self.templates_dir):
            if filename.endswith(".json"):
                try:
                    file_path = os.path.join(self.templates_dir, filename)
                    with open(file_path, 'r') as f:
                        template = json.load(f)

                    # Use the filename without extension as the template name
                    template_name = os.path.splitext(filename)[0]
                    self.templates[template_name] = template

                    logger.info(f"Loaded template: {template_name}")
                except Exception as e:
                    logger.error(f"Error loading template from {filename}: {e}")

    def generate_from_template(self, template_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates a new JSON object by filling in a template with data.

        Args:
            template_name: The name of the template to use
            data: The data to fill in the template with

        Returns:
            The generated JSON object

        Raises:
            ValueError: If the template is not found
        """
        if template_name not in self.templates:
            raise ValueError(f"Template not found: {template_name}")

        template = self.templates[template_name]

        # Deep copy the template to avoid modifying it
        result = json.loads(json.dumps(template))

        # Fill in the template with data
        for key, value in data.items():
            if key in result:
                result[key] = value

        return result

    def save_json(self, data: Dict[str, Any], file_path: str) -> None:
        """
        Saves data to a JSON file.

        Args:
            data: The data to save
            file_path: The path to save the data to
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)

            logger.info(f"Saved JSON to {file_path}")
        except Exception as e:
            logger.error(f"Error saving JSON to {file_path}: {e}")
            raise

def convert_constants_to_json(constants_module, output_dir: str = "data/config") -> None:
    """
    Converts constants from a Python module to JSON files.

    Args:
        constants_module: The module containing constants
        output_dir: The directory to save the JSON files to
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Get all uppercase variables from the module
    constants = {name: value for name, value in vars(constants_module).items() 
                if name.isupper() and not name.startswith('_')}

    # Save each constant to a separate file
    for name, value in constants.items():
        try:
            # Convert to JSON-serializable format if needed
            if callable(value):
                continue  # Skip functions

            # Create a JSON object with metadata
            json_data = {
                "name": name,
                "value": value,
                "type": str(type(value).__name__)
            }

            # Save to file
            file_path = os.path.join(output_dir, f"{name.lower()}.json")
            with open(file_path, 'w') as f:
                json.dump(json_data, f, indent=2)

            logger.info(f"Converted constant {name} to JSON: {file_path}")
        except Exception as e:
            logger.error(f"Error converting constant {name} to JSON: {e}")

def load_json_config(file_path: str, default_value: Any = None) -> Any:
    """
    Loads a JSON configuration file.

    Args:
        file_path: The path to the JSON file
        default_value: The default value to return if the file cannot be loaded

    Returns:
        The loaded JSON data or the default value
    """
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading JSON config from {file_path}: {e}")
        return default_value

def merge_json_files(file_paths: List[str], output_path: str) -> Dict[str, Any]:
    """
    Merges multiple JSON files into one.

    Args:
        file_paths: List of paths to JSON files to merge
        output_path: Path to save the merged JSON file

    Returns:
        The merged JSON data
    """
    merged_data = {}

    for file_path in file_paths:
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)

            # Merge data
            if isinstance(data, dict):
                merged_data.update(data)
            elif isinstance(data, list):
                if not isinstance(merged_data, list):
                    merged_data = []
                merged_data.extend(data)
            else:
                logger.warning(f"Cannot merge data from {file_path}: not a dict or list")
        except Exception as e:
            logger.error(f"Error merging JSON from {file_path}: {e}")

    # Save merged data
    try:
        with open(output_path, 'w') as f:
            json.dump(merged_data, f, indent=2)

        logger.info(f"Saved merged JSON to {output_path}")
    except Exception as e:
        logger.error(f"Error saving merged JSON to {output_path}: {e}")

    return merged_data
