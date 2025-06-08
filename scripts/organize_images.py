#!/usr/bin/env python3
"""
Script to organize and validate image files for the story mode.
"""

import os
import json
import shutil
from pathlib import Path
from typing import List, Dict, Set

class ImageOrganizer:
    """Organizes and validates image files for the story mode."""
    
    def __init__(self, base_dir: str = "data"):
        """
        Initialize the image organizer.
        
        Args:
            base_dir: Base directory for the project
        """
        self.base_dir = Path(base_dir)
        self.images_dir = self.base_dir / "assets" / "images" / "story"
        self.story_dir = self.base_dir / "story_mode"
        
        # Create images directory if it doesn't exist
        self.images_dir.mkdir(parents=True, exist_ok=True)
    
    def organize_images(self, source_dir: str) -> None:
        """
        Organize images from source directory into the story images directory.
        
        Args:
            source_dir: Directory containing the source images
        """
        source_path = Path(source_dir)
        if not source_path.exists():
            print(f"Source directory not found: {source_dir}")
            return
        
        # Get list of images to organize
        image_files = list(source_path.glob("*.png"))
        print(f"Found {len(image_files)} images to organize")
        
        # Copy images to story directory
        for image_file in image_files:
            dest_path = self.images_dir / image_file.name
            shutil.copy2(image_file, dest_path)
            print(f"Copied {image_file.name}")
        
        print(f"Organized {len(image_files)} images")
    
    def validate_images(self) -> Dict[str, List[str]]:
        """
        Validate image references in story files.
        
        Returns:
            Dictionary of validation results
        """
        results = {
            "missing_images": [],
            "unused_images": [],
            "broken_references": []
        }
        
        # Get all image files
        image_files = {f.stem for f in self.images_dir.glob("*.png")}
        
        # Get all story files
        story_files = list(self.story_dir.glob("**/*.json"))
        
        # Track used images
        used_images = set()
        
        # Check each story file
        for story_file in story_files:
            try:
                with open(story_file, 'r') as f:
                    story_data = json.load(f)
                
                # Check chapters
                for chapter_id, chapter in story_data.get("chapters", {}).items():
                    # Check background image
                    if "background_image" in chapter:
                        image_name = chapter["background_image"].replace(".png", "")
                        used_images.add(image_name)
                        if image_name not in image_files:
                            results["missing_images"].append(f"{image_name} (referenced in {story_file.name})")
                    
                    # Check character images
                    for char_image in chapter.get("character_images", []):
                        image_name = char_image.replace(".png", "")
                        used_images.add(image_name)
                        if image_name not in image_files:
                            results["missing_images"].append(f"{image_name} (referenced in {story_file.name})")
                    
                    # Check choice images
                    for choice in chapter.get("choices", []):
                        if "image" in choice:
                            image_name = choice["image"].replace(".png", "")
                            used_images.add(image_name)
                            if image_name not in image_files:
                                results["missing_images"].append(f"{image_name} (referenced in {story_file.name})")
            
            except Exception as e:
                results["broken_references"].append(f"Error in {story_file.name}: {str(e)}")
        
        # Find unused images
        results["unused_images"] = list(image_files - used_images)
        
        return results
    
    def generate_manifest(self) -> None:
        """Generate image manifest file."""
        manifest = {
            "images": {},
            "categories": {
                "characters": [],
                "locations": [],
                "events": [],
                "romantic": [],
                "clubs": []
            }
        }
        
        # Process each image
        for image_file in self.images_dir.glob("*.png"):
            if image_file.name == "image_not_found.png":
                continue
            
            image_name = image_file.stem
            category = self._determine_category(image_name)
            
            manifest["images"][image_name] = {
                "path": str(image_file.relative_to(self.images_dir)),
                "category": category
            }
            
            manifest["categories"][category].append(image_name)
        
        # Save manifest
        manifest_path = self.images_dir / "image_manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        print(f"Generated image manifest at {manifest_path}")
    
    def _determine_category(self, image_name: str) -> str:
        """Determine the category of an image based on its name."""
        if "romantic" in image_name:
            return "romantic"
        elif "clube" in image_name:
            return "clubs"
        elif any(name in image_name for name in ["professor", "estudante", "colega"]):
            return "characters"
        elif "tokugawa_academy" in image_name:
            return "locations"
        else:
            return "events"

def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Organize and validate story mode images")
    parser.add_argument("--source", help="Source directory containing images to organize")
    parser.add_argument("--validate", action="store_true", help="Validate image references")
    parser.add_argument("--manifest", action="store_true", help="Generate image manifest")
    args = parser.parse_args()
    
    organizer = ImageOrganizer()
    
    if args.source:
        organizer.organize_images(args.source)
    
    if args.validate:
        results = organizer.validate_images()
        
        print("\nValidation Results:")
        print(f"Missing Images: {len(results['missing_images'])}")
        for image in results["missing_images"]:
            print(f"  - {image}")
        
        print(f"\nUnused Images: {len(results['unused_images'])}")
        for image in results["unused_images"]:
            print(f"  - {image}")
        
        print(f"\nBroken References: {len(results['broken_references'])}")
        for ref in results["broken_references"]:
            print(f"  - {ref}")
    
    if args.manifest:
        organizer.generate_manifest()

if __name__ == "__main__":
    main() 