"""
Dynamic narrative events module for the Academia Tokugawa Discord bot.
This module provides functions to generate dynamic narrative events based on player attributes and choices.
"""

import random
import logging
import json
import os
from typing import Dict, Any, List, Tuple

logger = logging.getLogger('tokugawa_bot')

# Load event templates from JSON file
def load_event_templates():
    try:
        file_path = os.path.join("data", "story_mode", "events", "event_templates.json")
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get("event_templates", [])
    except Exception as e:
        logger.error(f"Error loading event templates: {e}")
        return []

# Load event templates
EVENT_TEMPLATES = load_event_templates()

def generate_dynamic_event(player: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a dynamic narrative event based on player attributes.

    Args:
        player (Dict[str, Any]): The player data

    Returns:
        Dict[str, Any]: The generated event
    """
    # Select an event template based on player attributes
    # Prioritize events that match the player's strongest attribute
    attributes = {
        "intellect": player.get("intellect", 5),
        "charisma": player.get("charisma", 5),
        "dexterity": player.get("dexterity", 5),
        "power_stat": player.get("power_stat", 5)
    }
    strongest_attribute = max(attributes, key=attributes.get)

    # Filter templates that check the player's strongest attribute
    matching_templates = [t for t in EVENT_TEMPLATES if t["attribute_check"] == strongest_attribute]

    # If no matching templates, use any template
    if not matching_templates:
        matching_templates = EVENT_TEMPLATES

    # Select a random template
    template = random.choice(matching_templates)

    # Fill in dynamic elements
    dynamic_elements = {}
    for key, values in template["dynamic_elements"].items():
        if key == "outcome":
            # Outcome will be determined later
            continue
        elif isinstance(values, list):
            dynamic_elements[key] = random.choice(values)

    # Determine outcome based on attribute check
    attribute_value = attributes[template["attribute_check"]]
    difficulty = template["difficulty"]

    # Add some randomness to the check
    check_result = attribute_value + random.randint(-2, 2)
    success = check_result >= difficulty

    # Get outcome text
    outcome = template["dynamic_elements"]["outcome"]["success" if success else "failure"]

    # Fill in description
    description_template = template["description_template"]
    description = description_template.format(outcome=outcome, **dynamic_elements)

    # Determine rewards
    rewards = template["rewards"]["success" if success else "failure"]

    # Create event
    event = {
        "title": template["title"],
        "description": description,
        "type": template["type"],
        "success": success,
        "attribute_checked": template["attribute_check"],
        "difficulty": difficulty,
        "check_result": check_result,
        "rewards": rewards,
        "dynamic_elements": {
            **dynamic_elements,
            "outcome": template["dynamic_elements"]["outcome"]
        }
    }

    logger.info(f"Generated dynamic event: {event['title']} (Success: {success})")
    return event

def apply_event_rewards(player: Dict[str, Any], event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply the rewards from an event to a player.

    Args:
        player (Dict[str, Any]): The player data
        event (Dict[str, Any]): The event data

    Returns:
        Dict[str, Any]: The updated player data
    """
    rewards = event["rewards"]
    updates = {}

    # Apply experience
    if "exp" in rewards:
        updates["exp"] = player["exp"] + rewards["exp"]

    # Apply TUSD
    if "tusd" in rewards:
        updates["tusd"] = max(0, player["tusd"] + rewards["tusd"])  # Ensure TUSD doesn't go below 0

    # Apply attribute changes
    for attr in ["intellect", "charisma", "dexterity", "power_stat"]:
        if attr in rewards:
            updates[attr] = player[attr] + rewards[attr]

    # Apply reputation changes
    if "reputation" in rewards:
        updates["reputation"] = player.get("reputation", 0) + rewards["reputation"]

    # Apply HP loss
    if "hp_loss" in rewards and "hp" in player:
        updates["hp"] = max(1, player["hp"] - rewards["hp_loss"])  # Ensure HP doesn't go below 1

    logger.info(f"Applied event rewards to player {player['name']}: {rewards}")
    return updates

# Load event choices from JSON file
def load_event_choices():
    try:
        file_path = os.path.join("data", "story_mode", "events", "event_choices.json")
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get("event_choices", {})
    except Exception as e:
        logger.error(f"Error loading event choices: {e}")
        return {}

# Load event choices
EVENT_CHOICES = load_event_choices()

def generate_event_choices(event_type: str) -> List[Tuple[str, str, Dict[str, Any]]]:
    """
    Generate choices for an event based on its type.

    Args:
        event_type (str): The type of event

    Returns:
        List[Tuple[str, str, Dict[str, Any]]]: A list of choices with (choice_id, description, consequences)
    """
    # Get choices for this event type from the loaded data
    choices_data = EVENT_CHOICES.get(event_type, EVENT_CHOICES.get("default", []))

    # If no choices found, return default choices
    if not choices_data:
        logger.warning(f"No choices found for event type: {event_type}, using default")
        choices_data = EVENT_CHOICES.get("default", [])

    # Convert the JSON structure to the expected format
    choices = []
    for choice in choices_data:
        choices.append((choice["id"], choice["description"], choice["consequences"]))

    return choices

def apply_choice_consequences(event: Dict[str, Any], choice_id: str, player: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply the consequences of a player's choice to an event.

    Args:
        event (Dict[str, Any]): The event data
        choice_id (str): The ID of the choice made
        player (Dict[str, Any]): The player data

    Returns:
        Dict[str, Any]: The updated event data
    """
    # Get choices for this event type
    choices = generate_event_choices(event["type"])

    # Find the chosen choice
    chosen_choice = None
    for c_id, desc, consequences in choices:
        if c_id == choice_id:
            chosen_choice = (c_id, desc, consequences)
            break

    if not chosen_choice:
        logger.warning(f"Invalid choice ID: {choice_id}")
        return event

    # Unpack the choice
    _, _, consequences = chosen_choice

    # Apply attribute bonuses
    attribute_checks = {
        "intellect_bonus": "intellect",
        "charisma_bonus": "charisma",
        "dexterity_bonus": "dexterity",
        "power_bonus": "power_stat"
    }

    # Create a copy of the event to modify
    updated_event = event.copy()

    # Apply attribute bonuses to check result
    for bonus_key, attr_name in attribute_checks.items():
        if bonus_key in consequences:
            bonus = consequences[bonus_key]
            if event["attribute_checked"] == attr_name:
                updated_event["check_result"] = event["check_result"] + bonus
                logger.info(f"Applied {bonus_key} of {bonus} to check result")

    # Recalculate success based on new check result or success_chance
    if "success_chance" in consequences:
        success_roll = random.random()
        updated_event["success"] = success_roll <= consequences["success_chance"]
        logger.info(f"Recalculated success based on success_chance: {consequences['success_chance']}, roll: {success_roll}, result: {updated_event['success']}")
    else:
        updated_event["success"] = updated_event["check_result"] >= event["difficulty"]
        logger.info(f"Recalculated success based on check result: {updated_event['check_result']} vs difficulty: {event['difficulty']}, result: {updated_event['success']}")

    # Apply reward multiplier if present
    if "reward_multiplier" in consequences and updated_event["success"]:
        multiplier = consequences["reward_multiplier"]
        for reward_key in ["exp", "tusd"]:
            if reward_key in updated_event["rewards"]:
                updated_event["rewards"][reward_key] = int(updated_event["rewards"][reward_key] * multiplier)
        logger.info(f"Applied reward multiplier: {multiplier}")

    # Apply direct rewards/penalties
    for reward_key in ["exp", "tusd", "reputation"]:
        if reward_key in consequences:
            if reward_key not in updated_event["rewards"]:
                updated_event["rewards"][reward_key] = 0
            updated_event["rewards"][reward_key] += consequences[reward_key]
            logger.info(f"Applied direct {reward_key} change: {consequences[reward_key]}")

    # Apply HP bonus if present
    if "hp_bonus" in consequences:
        if "hp_loss" in updated_event["rewards"]:
            updated_event["rewards"]["hp_loss"] = max(0, updated_event["rewards"]["hp_loss"] - consequences["hp_bonus"])
        else:
            # Add HP recovery instead of loss
            updated_event["rewards"]["hp_recovery"] = consequences["hp_bonus"]
        logger.info(f"Applied HP bonus: {consequences['hp_bonus']}")

    # Apply risk factor if present
    if "risk" in consequences:
        risk_level = consequences["risk"]
        if risk_level == "high":
            # High risk: 40% chance to fail regardless of check result
            if random.random() < 0.4:
                updated_event["success"] = False
                logger.info("High risk choice failed due to risk factor")
        elif risk_level == "medium":
            # Medium risk: 20% chance to fail regardless of check result
            if random.random() < 0.2:
                updated_event["success"] = False
                logger.info("Medium risk choice failed due to risk factor")

    # Update outcome text based on new success value
    outcome_key = "success" if updated_event["success"] else "failure"
    outcome_text = event["dynamic_elements"]["outcome"][outcome_key]

    # Update description with new outcome
    description_template = EVENT_TEMPLATES[0]["description_template"]  # This is a placeholder, we need to find the actual template
    for template in EVENT_TEMPLATES:
        if template["title"] == event["title"]:
            description_template = template["description_template"]
            break

    # Update dynamic elements with new outcome
    dynamic_elements = event["dynamic_elements"].copy()
    dynamic_elements["outcome"] = outcome_text

    # Update description
    updated_event["description"] = description_template.format(**dynamic_elements)

    # Update rewards based on new success value
    for template in EVENT_TEMPLATES:
        if template["title"] == event["title"]:
            updated_event["rewards"] = template["rewards"][outcome_key].copy()
            break

    # Apply any direct reward modifications from the choice
    for key in ["exp", "tusd", "reputation"]:
        if key in consequences:
            if key not in updated_event["rewards"]:
                updated_event["rewards"][key] = 0
            updated_event["rewards"][key] += consequences[key]

    logger.info(f"Applied choice consequences for {choice_id}, new success: {updated_event['success']}")
    return updated_event
