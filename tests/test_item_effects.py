import json
import os
from datetime import datetime, timedelta

def load_items(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def test_item_effects():
    # Load all item files
    fixed_items = load_items('data/economy/fixed_items.json')
    daily_items = load_items('data/economy/daily_items.json')
    weekly_items = load_items('data/economy/weekly_items.json')
    
    # Test Training Potion
    training_potion = next(item for item in fixed_items if item['id'] == 1)
    assert training_potion['price'] == 150, "Training Potion price should be 150"
    assert training_potion['rarity'] == 'uncommon', "Training Potion should be uncommon"
    assert 'daily_usage_limit' in training_potion['effects'], "Training Potion should have daily usage limit"
    assert training_potion['effects']['daily_usage_limit'] == 3, "Training Potion should have 3 uses per day"
    
    # Test Daily Items
    for item in daily_items:
        assert 'daily_usage_limit' in item['effects'], f"{item['name']} should have daily usage limit"
        assert item['effects']['daily_usage_limit'] > 0, f"{item['name']} should have positive usage limit"
        
        # Test energy items
        if 'energy_restore' in item['effects']:
            assert isinstance(item['effects']['energy_restore'], dict), "Energy restore should be a dictionary"
            assert 'base' in item['effects']['energy_restore'], "Energy restore should have base value"
            assert 'level_multiplier' in item['effects']['energy_restore'], "Energy restore should have level multiplier"
        
        # Test attribute boosts
        if 'temp_attribute_boost' in item['effects']:
            for attr, value in item['effects']['temp_attribute_boost'].items():
                assert value >= 2, f"{item['name']} should boost attributes by at least 2"
    
    # Test Weekly Items
    for item in weekly_items:
        assert 'weekly_usage_limit' in item['effects'], f"{item['name']} should have weekly usage limit"
        assert item['effects']['weekly_usage_limit'] == 1, f"{item['name']} should have 1 use per week"
        
        # Test damage modifiers
        if 'damage_reduction' in item['effects']:
            assert item['effects']['damage_reduction'] == 0.15, "Damage reduction should be 15%"
        if 'damage_boost' in item['effects']:
            assert item['effects']['damage_boost'] == 0.15, "Damage boost should be 15%"
        
        # Test technique boosts
        if 'technique_level_boost' in item['effects']:
            assert item['effects']['technique_level_boost'] == 2, "Technique level boost should be +2"
    
    print("All item effect tests passed!")

if __name__ == "__main__":
    test_item_effects() 