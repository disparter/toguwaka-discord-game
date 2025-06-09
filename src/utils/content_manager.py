"""
Content Management System for Tokugawa Discord Game.
This script provides a command-line interface for managing game content.
"""
import argparse
import json
import os
import sys
from typing import Dict, List, Any, Optional, Union
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('content_manager.log')
    ]
)
logger = logging.getLogger('content_manager')

# Import our JSON tools
try:
    from src.utils.json_tools import JSONValidator, JSONGenerator, load_json_config, merge_json_files
except ImportError:
    # If running as a standalone script
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from src.utils.json_tools import JSONValidator, JSONGenerator, load_json_config, merge_json_files

class ContentManager:
    """
    Main class for managing game content.
    """
    def __init__(self, data_dir: str = "data"):
        """
        Initialize the content manager.
        
        Args:
            data_dir: Path to the directory containing game data
        """
        self.data_dir = data_dir
        self.config_dir = os.path.join(data_dir, "config")
        self.schemas_dir = os.path.join(data_dir, "schemas")
        self.templates_dir = os.path.join(data_dir, "templates")
        
        # Create directories if they don't exist
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.config_dir, exist_ok=True)
        os.makedirs(self.schemas_dir, exist_ok=True)
        os.makedirs(self.templates_dir, exist_ok=True)
        
        # Initialize components
        self.validator = JSONValidator(self.schemas_dir)
        self.generator = JSONGenerator(self.templates_dir)
        
        # Load configuration
        self.config = load_json_config(os.path.join(self.config_dir, "content_manager_config.json"), {})
        
        logger.info("Content Manager initialized")
    
    def list_content(self, content_type: str = None) -> List[str]:
        """
        Lists available content of a specific type.
        
        Args:
            content_type: Type of content to list (e.g., "chapters", "events", "npcs")
                         If None, lists all content types
        
        Returns:
            List of content items
        """
        if content_type:
            content_dir = os.path.join(self.data_dir, content_type)
            if not os.path.exists(content_dir):
                logger.warning(f"Content directory not found: {content_dir}")
                return []
            
            # List JSON files in the directory
            return [f for f in os.listdir(content_dir) if f.endswith(".json")]
        else:
            # List all content types (subdirectories in data_dir)
            return [d for d in os.listdir(self.data_dir) 
                   if os.path.isdir(os.path.join(self.data_dir, d)) 
                   and not d.startswith(".")]
    
    def create_content(self, content_type: str, content_id: str, template_name: str = None, 
                      data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Creates new content from a template or data.
        
        Args:
            content_type: Type of content to create (e.g., "chapters", "events", "npcs")
            content_id: ID for the new content
            template_name: Name of the template to use (optional)
            data: Data to use for creating the content (optional)
            
        Returns:
            The created content
        """
        content_dir = os.path.join(self.data_dir, content_type)
        os.makedirs(content_dir, exist_ok=True)
        
        # Determine the file path
        file_path = os.path.join(content_dir, f"{content_id}.json")
        
        # Check if file already exists
        if os.path.exists(file_path):
            logger.warning(f"Content already exists: {file_path}")
            raise ValueError(f"Content already exists: {content_id}")
        
        # Create content
        if template_name:
            # Use template
            try:
                content = self.generator.generate_from_template(template_name, data or {})
            except ValueError as e:
                logger.error(f"Error generating content from template: {e}")
                raise
        elif data:
            # Use provided data
            content = data
        else:
            # Create empty content
            content = {"id": content_id}
        
        # Save content
        try:
            with open(file_path, 'w') as f:
                json.dump(content, f, indent=2)
            
            logger.info(f"Created content: {content_type}/{content_id}")
            return content
        except Exception as e:
            logger.error(f"Error creating content: {e}")
            raise
    
    def edit_content(self, content_type: str, content_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Edits existing content.
        
        Args:
            content_type: Type of content to edit
            content_id: ID of the content to edit
            data: New data for the content
            
        Returns:
            The updated content
        """
        file_path = os.path.join(self.data_dir, content_type, f"{content_id}.json")
        
        # Check if file exists
        if not os.path.exists(file_path):
            logger.warning(f"Content not found: {file_path}")
            raise ValueError(f"Content not found: {content_id}")
        
        # Load existing content
        try:
            with open(file_path, 'r') as f:
                content = json.load(f)
        except Exception as e:
            logger.error(f"Error loading content: {e}")
            raise
        
        # Update content
        content.update(data)
        
        # Save updated content
        try:
            with open(file_path, 'w') as f:
                json.dump(content, f, indent=2)
            
            logger.info(f"Updated content: {content_type}/{content_id}")
            return content
        except Exception as e:
            logger.error(f"Error updating content: {e}")
            raise
    
    def delete_content(self, content_type: str, content_id: str) -> bool:
        """
        Deletes existing content.
        
        Args:
            content_type: Type of content to delete
            content_id: ID of the content to delete
            
        Returns:
            True if the content was deleted, False otherwise
        """
        file_path = os.path.join(self.data_dir, content_type, f"{content_id}.json")
        
        # Check if file exists
        if not os.path.exists(file_path):
            logger.warning(f"Content not found: {file_path}")
            return False
        
        # Delete file
        try:
            os.remove(file_path)
            logger.info(f"Deleted content: {content_type}/{content_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting content: {e}")
            return False
    
    def validate_content(self, content_type: str, content_id: str = None) -> bool:
        """
        Validates content against its schema.
        
        Args:
            content_type: Type of content to validate
            content_id: ID of the content to validate (optional)
                       If None, validates all content of the specified type
            
        Returns:
            True if the content is valid, False otherwise
        """
        # Determine schema name
        schema_name = content_type
        
        # Check if schema exists
        if schema_name not in self.validator.schemas:
            logger.warning(f"Schema not found: {schema_name}")
            return False
        
        # Validate specific content or all content of the type
        if content_id:
            file_path = os.path.join(self.data_dir, content_type, f"{content_id}.json")
            
            # Check if file exists
            if not os.path.exists(file_path):
                logger.warning(f"Content not found: {file_path}")
                return False
            
            # Validate file
            try:
                self.validator.validate_file(file_path, schema_name)
                logger.info(f"Content is valid: {content_type}/{content_id}")
                return True
            except Exception as e:
                logger.error(f"Content validation failed: {e}")
                return False
        else:
            # Validate all content of the type
            content_dir = os.path.join(self.data_dir, content_type)
            
            if not os.path.exists(content_dir):
                logger.warning(f"Content directory not found: {content_dir}")
                return False
            
            all_valid = True
            
            for filename in os.listdir(content_dir):
                if filename.endswith(".json"):
                    file_path = os.path.join(content_dir, filename)
                    
                    try:
                        self.validator.validate_file(file_path, schema_name)
                        logger.info(f"Content is valid: {file_path}")
                    except Exception as e:
                        logger.error(f"Content validation failed for {file_path}: {e}")
                        all_valid = False
            
            return all_valid
    
    def create_schema(self, content_type: str, example_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Creates a schema for a content type.
        
        Args:
            content_type: Type of content to create a schema for
            example_data: Example data to create the schema from (optional)
            
        Returns:
            The created schema
        """
        if example_data:
            # Create schema from example data
            return self.validator.create_schema_from_example(example_data, content_type)
        else:
            # Try to find an example file
            content_dir = os.path.join(self.data_dir, content_type)
            
            if not os.path.exists(content_dir):
                logger.warning(f"Content directory not found: {content_dir}")
                raise ValueError(f"Content directory not found: {content_type}")
            
            # Find the first JSON file
            for filename in os.listdir(content_dir):
                if filename.endswith(".json"):
                    file_path = os.path.join(content_dir, filename)
                    
                    try:
                        with open(file_path, 'r') as f:
                            example_data = json.load(f)
                        
                        return self.validator.create_schema_from_example(example_data, content_type)
                    except Exception as e:
                        logger.error(f"Error creating schema from {file_path}: {e}")
                        raise
            
            logger.warning(f"No example files found in {content_dir}")
            raise ValueError(f"No example files found for content type: {content_type}")
    
    def create_template(self, template_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Creates a template for generating content.
        
        Args:
            template_name: Name of the template
            data: Template data
            
        Returns:
            The created template
        """
        template_path = os.path.join(self.templates_dir, f"{template_name}.json")
        
        # Save template
        try:
            with open(template_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            # Reload templates
            self.generator._load_templates()
            
            logger.info(f"Created template: {template_name}")
            return data
        except Exception as e:
            logger.error(f"Error creating template: {e}")
            raise

def main():
    """
    Main function for the command-line interface.
    """
    parser = argparse.ArgumentParser(description="Content Management System for Tokugawa Discord Game")
    
    # Add subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List available content")
    list_parser.add_argument("--type", help="Type of content to list")
    
    # Create command
    create_parser = subparsers.add_parser("create", help="Create new content")
    create_parser.add_argument("type", help="Type of content to create")
    create_parser.add_argument("id", help="ID for the new content")
    create_parser.add_argument("--template", help="Template to use")
    create_parser.add_argument("--data", help="JSON data for the content")
    
    # Edit command
    edit_parser = subparsers.add_parser("edit", help="Edit existing content")
    edit_parser.add_argument("type", help="Type of content to edit")
    edit_parser.add_argument("id", help="ID of the content to edit")
    edit_parser.add_argument("--data", help="JSON data to update")
    
    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete existing content")
    delete_parser.add_argument("type", help="Type of content to delete")
    delete_parser.add_argument("id", help="ID of the content to delete")
    
    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate content against schema")
    validate_parser.add_argument("type", help="Type of content to validate")
    validate_parser.add_argument("--id", help="ID of the content to validate")
    
    # Schema command
    schema_parser = subparsers.add_parser("schema", help="Create schema from example data")
    schema_parser.add_argument("type", help="Type of content to create schema for")
    schema_parser.add_argument("--example", help="JSON example data")
    
    # Template command
    template_parser = subparsers.add_parser("template", help="Create template for generating content")
    template_parser.add_argument("name", help="Name of the template")
    template_parser.add_argument("--data", help="JSON template data")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Create content manager
    manager = ContentManager()
    
    # Execute command
    if args.command == "list":
        content_list = manager.list_content(args.type)
        print(f"Available {args.type or 'content types'}:")
        for item in content_list:
            print(f"  {item}")
    
    elif args.command == "create":
        data = json.loads(args.data) if args.data else None
        content = manager.create_content(args.type, args.id, args.template, data)
        print(f"Created content: {args.type}/{args.id}")
        print(json.dumps(content, indent=2))
    
    elif args.command == "edit":
        if not args.data:
            print("Error: --data is required for edit command")
            return
        
        data = json.loads(args.data)
        content = manager.edit_content(args.type, args.id, data)
        print(f"Updated content: {args.type}/{args.id}")
        print(json.dumps(content, indent=2))
    
    elif args.command == "delete":
        success = manager.delete_content(args.type, args.id)
        if success:
            print(f"Deleted content: {args.type}/{args.id}")
        else:
            print(f"Failed to delete content: {args.type}/{args.id}")
    
    elif args.command == "validate":
        valid = manager.validate_content(args.type, args.id)
        if valid:
            print(f"Content is valid: {args.type}/{args.id or '*'}")
        else:
            print(f"Content validation failed: {args.type}/{args.id or '*'}")
    
    elif args.command == "schema":
        example_data = json.loads(args.example) if args.example else None
        schema = manager.create_schema(args.type, example_data)
        print(f"Created schema for {args.type}")
        print(json.dumps(schema, indent=2))
    
    elif args.command == "template":
        if not args.data:
            print("Error: --data is required for template command")
            return
        
        data = json.loads(args.data)
        template = manager.create_template(args.name, data)
        print(f"Created template: {args.name}")
        print(json.dumps(template, indent=2))
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()