import json
import os
import argparse
from typing import Dict, List, Any, Optional, Union, Tuple

# Try to import jsonschema, but provide a fallback if not available
try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False
    print("Warning: jsonschema module not found. Using simplified validation.")

class ContentValidator:
    """
    A utility class for validating narrative content against schemas.
    """
    def __init__(self, schemas_dir: str = "data/schemas"):
        """
        Initialize the content validator.

        Args:
            schemas_dir: Directory containing schema files
        """
        self.schemas_dir = schemas_dir
        self.schemas = self._load_schemas()

    def _load_schemas(self) -> Dict[str, Dict[str, Any]]:
        """
        Load all schema files from the schemas directory.

        Returns:
            Dictionary mapping schema types to schema data
        """
        schemas = {}
        for filename in os.listdir(self.schemas_dir):
            if filename.endswith("_schema.json"):
                schema_type = filename.split("_schema")[0]
                file_path = os.path.join(self.schemas_dir, filename)
                with open(file_path, 'r', encoding='utf-8') as f:
                    schemas[schema_type] = json.load(f)
        return schemas

    def list_schemas(self) -> List[str]:
        """
        List all available schemas.

        Returns:
            List of schema names
        """
        return list(self.schemas.keys())

    def validate_file(self, file_path: str, schema_type: str) -> Tuple[bool, List[str]]:
        """
        Validate a JSON file against a schema.

        Args:
            file_path: Path to the JSON file to validate
            schema_type: Type of schema to validate against

        Returns:
            Tuple of (is_valid, error_messages)
        """
        if schema_type not in self.schemas:
            return False, [f"Schema '{schema_type}' not found"]

        schema = self.schemas[schema_type]

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = json.load(f)
        except json.JSONDecodeError as e:
            return False, [f"Invalid JSON in {file_path}: {str(e)}"]
        except FileNotFoundError:
            return False, [f"File not found: {file_path}"]

        return self.validate_content(content, schema_type)

    def validate_content(self, content: Dict[str, Any], schema_type: str) -> Tuple[bool, List[str]]:
        """
        Validate content against a schema.

        Args:
            content: Content to validate
            schema_type: Type of schema to validate against

        Returns:
            Tuple of (is_valid, error_messages)
        """
        if schema_type not in self.schemas:
            return False, [f"Schema '{schema_type}' not found"]

        schema = self.schemas[schema_type]
        errors = []

        # Validate each item in the content
        for content_id, item in content.items():
            if HAS_JSONSCHEMA:
                try:
                    jsonschema.validate(instance={"key": item}, schema={
                        "type": "object",
                        "properties": {
                            "key": schema["additionalProperties"]
                        },
                        "required": ["key"]
                    })
                except jsonschema.exceptions.ValidationError as e:
                    # Extract the relevant part of the error message
                    error_path = ".".join(str(p) for p in e.path if p != "key")
                    if error_path:
                        error_path = f".{error_path}"
                    errors.append(f"Validation error in {content_id}{error_path}: {e.message}")
            else:
                # Simple validation without jsonschema
                validation_errors = self._simple_validate(item, schema["additionalProperties"], content_id)
                errors.extend(validation_errors)

        return len(errors) == 0, errors

    def validate_directory(self, directory_path: str, schema_mapping: Dict[str, str]) -> Tuple[bool, Dict[str, List[str]]]:
        """
        Validate all JSON files in a directory against their respective schemas.

        Args:
            directory_path: Path to the directory containing JSON files
            schema_mapping: Mapping of file patterns to schema types

        Returns:
            Tuple of (all_valid, error_messages_by_file)
        """
        all_valid = True
        errors_by_file = {}

        for filename in os.listdir(directory_path):
            if filename.endswith(".json"):
                file_path = os.path.join(directory_path, filename)

                # Determine which schema to use
                schema_type = None
                for pattern, schema in schema_mapping.items():
                    if pattern in filename:
                        schema_type = schema
                        break

                if schema_type:
                    is_valid, errors = self.validate_file(file_path, schema_type)
                    if not is_valid:
                        all_valid = False
                        errors_by_file[filename] = errors
                else:
                    errors_by_file[filename] = [f"No schema mapping found for {filename}"]
                    all_valid = False

        return all_valid, errors_by_file

    def _simple_validate(self, instance: Any, schema: Dict[str, Any], path: str = "") -> List[str]:
        """
        Simple validation function that doesn't rely on jsonschema.

        Args:
            instance: Instance to validate
            schema: Schema to validate against
            path: Current path in the instance

        Returns:
            List of validation error messages
        """
        errors = []

        # Check type
        if "type" in schema:
            expected_type = schema["type"]
            if expected_type == "object" and not isinstance(instance, dict):
                errors.append(f"Expected object at {path}, got {type(instance).__name__}")
            elif expected_type == "array" and not isinstance(instance, list):
                errors.append(f"Expected array at {path}, got {type(instance).__name__}")
            elif expected_type == "string" and not isinstance(instance, str):
                errors.append(f"Expected string at {path}, got {type(instance).__name__}")
            elif expected_type == "number" and not isinstance(instance, (int, float)):
                errors.append(f"Expected number at {path}, got {type(instance).__name__}")
            elif expected_type == "integer" and not isinstance(instance, int):
                errors.append(f"Expected integer at {path}, got {type(instance).__name__}")
            elif expected_type == "boolean" and not isinstance(instance, bool):
                errors.append(f"Expected boolean at {path}, got {type(instance).__name__}")

        # Check required properties for objects
        if isinstance(instance, dict) and "required" in schema:
            for required_prop in schema["required"]:
                if required_prop not in instance:
                    errors.append(f"Missing required property '{required_prop}' at {path}")

        # Check properties for objects
        if isinstance(instance, dict) and "properties" in schema:
            for prop_name, prop_value in instance.items():
                if prop_name in schema["properties"]:
                    prop_schema = schema["properties"][prop_name]
                    prop_path = f"{path}.{prop_name}" if path else prop_name
                    errors.extend(self._simple_validate(prop_value, prop_schema, prop_path))

        # Check items for arrays
        if isinstance(instance, list) and "items" in schema:
            for i, item in enumerate(instance):
                item_path = f"{path}[{i}]"
                errors.extend(self._simple_validate(item, schema["items"], item_path))

        # Check enum values
        if "enum" in schema and instance not in schema["enum"]:
            errors.append(f"Value {instance} at {path} not in enum {schema['enum']}")

        # Check minimum for numbers
        if isinstance(instance, (int, float)) and "minimum" in schema:
            if instance < schema["minimum"]:
                errors.append(f"Value {instance} at {path} less than minimum {schema['minimum']}")

        # Check maximum for numbers
        if isinstance(instance, (int, float)) and "maximum" in schema:
            if instance > schema["maximum"]:
                errors.append(f"Value {instance} at {path} greater than maximum {schema['maximum']}")

        # Check minLength for strings
        if isinstance(instance, str) and "minLength" in schema:
            if len(instance) < schema["minLength"]:
                errors.append(f"String '{instance}' at {path} shorter than minLength {schema['minLength']}")

        return errors

    def fix_content(self, content: Dict[str, Any], schema_type: str) -> Tuple[Dict[str, Any], List[str]]:
        """
        Attempt to fix content to conform to a schema.

        Args:
            content: Content to fix
            schema_type: Type of schema to validate against

        Returns:
            Tuple of (fixed_content, fix_messages)
        """
        if schema_type not in self.schemas:
            return content, [f"Schema '{schema_type}' not found"]

        schema = self.schemas[schema_type]
        fixed_content = json.loads(json.dumps(content))  # Deep copy
        fix_messages = []

        # Fix each item in the content
        for content_id, item in content.items():
            # Check required properties
            required_props = schema["additionalProperties"].get("required", [])
            for prop in required_props:
                if prop not in item:
                    # Add default value for missing required property
                    if prop in schema["additionalProperties"]["properties"]:
                        prop_schema = schema["additionalProperties"]["properties"][prop]
                        if prop_schema["type"] == "string":
                            fixed_content[content_id][prop] = ""
                        elif prop_schema["type"] == "integer":
                            fixed_content[content_id][prop] = 0
                        elif prop_schema["type"] == "number":
                            fixed_content[content_id][prop] = 0.0
                        elif prop_schema["type"] == "boolean":
                            fixed_content[content_id][prop] = False
                        elif prop_schema["type"] == "array":
                            fixed_content[content_id][prop] = []
                        elif prop_schema["type"] == "object":
                            fixed_content[content_id][prop] = {}
                        fix_messages.append(f"Added default value for missing required property '{prop}' in {content_id}")

        return fixed_content, fix_messages

def main():
    parser = argparse.ArgumentParser(description="Validate narrative content against schemas")
    parser.add_argument("--list", action="store_true", help="List available schemas")
    parser.add_argument("--file", type=str, help="JSON file to validate")
    parser.add_argument("--schema", type=str, help="Schema to validate against")
    parser.add_argument("--directory", type=str, help="Directory containing JSON files to validate")
    parser.add_argument("--fix", action="store_true", help="Attempt to fix validation errors")

    args = parser.parse_args()

    validator = ContentValidator()

    if args.list:
        schemas = validator.list_schemas()
        print("Available schemas:")
        for schema in schemas:
            print(f"  {schema}")
        return

    if args.file and args.schema:
        is_valid, errors = validator.validate_file(args.file, args.schema)

        if is_valid:
            print(f"✅ {args.file} is valid according to {args.schema} schema")
        else:
            print(f"❌ {args.file} is NOT valid according to {args.schema} schema")
            for error in errors:
                print(f"  - {error}")

            if args.fix:
                try:
                    with open(args.file, 'r', encoding='utf-8') as f:
                        content = json.load(f)

                    fixed_content, fix_messages = validator.fix_content(content, args.schema)

                    if fix_messages:
                        print("\nAttempted fixes:")
                        for msg in fix_messages:
                            print(f"  - {msg}")

                        # Write fixed content back to file
                        with open(args.file, 'w', encoding='utf-8') as f:
                            json.dump(fixed_content, f, indent=2, ensure_ascii=False)

                        print(f"\nFixed content written to {args.file}")

                        # Validate again
                        is_valid, errors = validator.validate_content(fixed_content, args.schema)
                        if is_valid:
                            print("✅ Fixed content is now valid")
                        else:
                            print("❌ Fixed content still has validation errors:")
                            for error in errors:
                                print(f"  - {error}")
                    else:
                        print("\nNo automatic fixes available")
                except Exception as e:
                    print(f"\nError while attempting to fix: {str(e)}")

    elif args.directory:
        if not args.schema:
            parser.error("--schema is required with --directory")

        # Simple mapping: all files use the same schema
        schema_mapping = {"": args.schema}

        all_valid, errors_by_file = validator.validate_directory(args.directory, schema_mapping)

        if all_valid:
            print(f"✅ All files in {args.directory} are valid")
        else:
            print(f"❌ Some files in {args.directory} have validation errors:")
            for filename, errors in errors_by_file.items():
                print(f"\n{filename}:")
                for error in errors:
                    print(f"  - {error}")
    else:
        parser.error("Either --file and --schema, or --directory and --schema are required")

if __name__ == "__main__":
    main()
