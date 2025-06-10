import os
import json

def validate_chapter(chapter_data, file_path):
    """
    Simplified version of ChapterValidator.validate_chapter
    """
    # Get chapter ID from data
    chapter_id = chapter_data.get("chapter_id")
    if not chapter_id:
        print(f"Chapter in {file_path} is missing chapter_id")
        return False

    # Check required fields
    required_fields = ["type", "title", "description"]
    for field in required_fields:
        if field not in chapter_data:
            print(f"Chapter {chapter_id} in {file_path} is missing required field: {field}")
            return False

    # Check scenes
    if "scenes" not in chapter_data:
        print(f"Chapter {chapter_id} in {file_path} is missing 'scenes' field")
        return False

    scenes = chapter_data.get("scenes", [])
    if not isinstance(scenes, list):
        print(f"Chapter {chapter_id} in {file_path}: 'scenes' must be a list")
        return False

    # Validate each scene
    for i, scene in enumerate(scenes):
        if not isinstance(scene, dict):
            print(f"Chapter {chapter_id} in {file_path}: scene {i} must be a dictionary")
            return False

        # Check required scene fields
        scene_required_fields = ["scene_id", "title", "description"]
        for field in scene_required_fields:
            if field not in scene:
                print(f"Chapter {chapter_id} in {file_path}: scene {i} is missing required field: {field}")
                return False

        # Check dialogue
        if "dialogue" not in scene:
            print(f"Chapter {chapter_id} in {file_path}: scene {i} is missing 'dialogue' field")
            return False

        # Check choices
        if "choices" not in scene:
            print(f"Chapter {chapter_id} in {file_path}: scene {i} is missing 'choices' field")
            return False

    return True

def main():
    # Set up paths
    chapter_files = [
        "data/story_mode/narrative/academic/academic_1_1_first_class.json",
        "data/story_mode/narrative/academic/academic_1_2_study_group.json"
    ]

    # Validate each chapter file
    for file_path in chapter_files:
        print(f"Validating {file_path}...")
        if not os.path.exists(file_path):
            print(f"  ERROR: File not found: {file_path}")
            continue

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                chapter_data = json.load(f)

            # Validate the chapter
            if validate_chapter(chapter_data, file_path):
                print(f"  SUCCESS: Chapter validation passed for {file_path}")
            else:
                print(f"  ERROR: Chapter validation failed for {file_path}")
        except Exception as e:
            print(f"  ERROR: Exception while validating {file_path}: {e}")

if __name__ == "__main__":
    main()
