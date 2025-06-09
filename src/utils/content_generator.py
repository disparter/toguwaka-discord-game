import json
import os
import argparse
from typing import Dict, List, Any, Optional, Union
import re

class ContentGenerator:
    """
    A utility class for generating narrative content templates.
    """
    def __init__(self, templates_dir: str = "data/story_mode/narrative_templates", 
                 schemas_dir: str = "data/schemas",
                 output_dir: str = "data/story_mode"):
        """
        Initialize the content generator.
        
        Args:
            templates_dir: Directory containing template files
            schemas_dir: Directory containing schema files
            output_dir: Directory where generated content will be saved
        """
        self.templates_dir = templates_dir
        self.schemas_dir = schemas_dir
        self.output_dir = output_dir
        self.templates = self._load_templates()
        self.schemas = self._load_schemas()
        
    def _load_templates(self) -> Dict[str, Dict[str, Any]]:
        """
        Load all template files from the templates directory.
        
        Returns:
            Dictionary mapping template types to template data
        """
        templates = {}
        for filename in os.listdir(self.templates_dir):
            if filename.endswith(".json"):
                template_type = filename.split(".")[0]
                file_path = os.path.join(self.templates_dir, filename)
                with open(file_path, 'r', encoding='utf-8') as f:
                    templates[template_type] = json.load(f)
        return templates
    
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
    
    def list_templates(self) -> List[str]:
        """
        List all available templates.
        
        Returns:
            List of template names
        """
        templates = []
        for template_type, template_data in self.templates.items():
            for template_name in template_data.keys():
                templates.append(f"{template_type}.{template_name}")
        return templates
    
    def generate_content(self, template_name: str, output_file: str, 
                         content_id: str, interactive: bool = True) -> Dict[str, Any]:
        """
        Generate content based on a template.
        
        Args:
            template_name: Name of the template to use (format: template_type.template_name)
            output_file: Path to the output file
            content_id: ID for the generated content
            interactive: Whether to prompt for input interactively
            
        Returns:
            Generated content
        """
        template_type, template_subtype = template_name.split(".")
        
        if template_type not in self.templates:
            raise ValueError(f"Template type '{template_type}' not found")
        
        if template_subtype not in self.templates[template_type]:
            raise ValueError(f"Template '{template_subtype}' not found in '{template_type}'")
        
        template = self.templates[template_type][template_subtype]
        
        # Create a deep copy of the template to modify
        content = json.loads(json.dumps(template))
        
        if interactive:
            content = self._fill_template_interactive(content, template_type, template_subtype)
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # Check if file exists and has content
        if os.path.exists(output_file):
            with open(output_file, 'r', encoding='utf-8') as f:
                try:
                    existing_content = json.load(f)
                except json.JSONDecodeError:
                    existing_content = {}
        else:
            existing_content = {}
        
        # Add new content
        existing_content[content_id] = content
        
        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(existing_content, f, indent=2, ensure_ascii=False)
        
        print(f"Content generated and saved to {output_file}")
        return content
    
    def _fill_template_interactive(self, template: Dict[str, Any], 
                                  template_type: str, 
                                  template_subtype: str,
                                  prefix: str = "") -> Dict[str, Any]:
        """
        Fill a template interactively by prompting the user for input.
        
        Args:
            template: Template to fill
            template_type: Type of the template
            template_subtype: Subtype of the template
            prefix: Prefix for nested fields
            
        Returns:
            Filled template
        """
        result = {}
        
        for key, value in template.items():
            full_key = f"{prefix}.{key}" if prefix else key
            
            if isinstance(value, dict):
                result[key] = self._fill_template_interactive(value, template_type, template_subtype, full_key)
            elif isinstance(value, list):
                if value and isinstance(value[0], dict):
                    # Handle list of objects
                    result[key] = []
                    num_items = int(input(f"Enter number of {key} items: "))
                    for i in range(num_items):
                        item = self._fill_template_interactive(value[0], template_type, template_subtype, f"{full_key}[{i}]")
                        result[key].append(item)
                else:
                    # Handle list of primitives
                    items_str = input(f"Enter {key} (comma-separated): ")
                    result[key] = [item.strip() for item in items_str.split(",")]
            else:
                # Handle primitive values
                prompt = f"Enter {full_key} [{value}]: "
                user_input = input(prompt)
                
                # Use template value as default if no input provided
                if user_input.strip():
                    # Convert to appropriate type
                    if isinstance(value, int):
                        result[key] = int(user_input)
                    elif isinstance(value, float):
                        result[key] = float(user_input)
                    elif isinstance(value, bool):
                        result[key] = user_input.lower() in ("yes", "true", "t", "1")
                    else:
                        result[key] = user_input
                else:
                    result[key] = value
        
        return result
    
    def validate_content(self, content: Dict[str, Any], schema_type: str) -> bool:
        """
        Validate content against a schema.
        
        Args:
            content: Content to validate
            schema_type: Type of schema to validate against
            
        Returns:
            True if content is valid, False otherwise
        """
        if schema_type not in self.schemas:
            raise ValueError(f"Schema '{schema_type}' not found")
        
        # Simple validation - in a real implementation, use a proper JSON Schema validator
        schema = self.schemas[schema_type]
        
        # Check required fields
        for field in schema.get("required", []):
            if field not in content:
                print(f"Missing required field: {field}")
                return False
        
        return True

def main():
    parser = argparse.ArgumentParser(description="Generate narrative content from templates")
    parser.add_argument("--list", action="store_true", help="List available templates")
    parser.add_argument("--template", type=str, help="Template to use (format: template_type.template_name)")
    parser.add_argument("--output", type=str, help="Output file path")
    parser.add_argument("--id", type=str, help="ID for the generated content")
    parser.add_argument("--non-interactive", action="store_true", help="Generate content without prompting for input")
    
    args = parser.parse_args()
    
    generator = ContentGenerator()
    
    if args.list:
        templates = generator.list_templates()
        print("Available templates:")
        for template in templates:
            print(f"  {template}")
        return
    
    if not args.template:
        parser.error("--template is required unless --list is specified")
    
    if not args.output:
        parser.error("--output is required")
    
    if not args.id:
        parser.error("--id is required")
    
    generator.generate_content(args.template, args.output, args.id, not args.non_interactive)

if __name__ == "__main__":
    main()