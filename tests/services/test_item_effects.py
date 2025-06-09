import json
import os
from datetime import datetime, timedelta

def load_items(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def test_item_effects():
    # Load all item files
    items_dir = 'data/economy/items'
    item_files = {
        'training': load_items(f'{items_dir}/training_items.json'),
        'combat': load_items(f'{items_dir}/combat_items.json'),
        'energy': load_items(f'{items_dir}/energy_items.json'),
        'attribute': load_items(f'{items_dir}/attribute_items.json'),
        'social': load_items(f'{items_dir}/social_items.json')
    }
    
    # Test Training Items
    training_potion = next(item for item in item_files['training'] if item['id'] == 1)
    assert training_potion['price'] == 150, "Training Potion price should be 150"
    assert training_potion['rarity'] == 'uncommon', "Training Potion should be uncommon"
    assert 'daily_usage_limit' in training_potion['effects'], "Training Potion should have daily usage limit"
    assert training_potion['effects']['daily_usage_limit'] == 3, "Training Potion should have 3 uses per day"
    
    # Test Combat Items
    for item in item_files['combat']:
        assert 'combat_only' in item['effects'], f"{item['name']} should be combat-only"
        assert item['effects']['combat_only'] == True, f"{item['name']} should be combat-only"
        assert 'attribute_boost' in item['effects'], f"{item['name']} should have attribute boost"
        for attr, value in item['effects']['attribute_boost'].items():
            assert value == 2, f"{item['name']} should boost attributes by 2"
    
    # Test Energy Items
    for item in item_files['energy']:
        assert 'daily_usage_limit' in item['effects'], f"{item['name']} should have daily usage limit"
        assert item['effects']['daily_usage_limit'] > 0, f"{item['name']} should have positive usage limit"
        
        if 'energy_restore' in item['effects']:
            assert isinstance(item['effects']['energy_restore'], dict), "Energy restore should be a dictionary"
            assert 'base' in item['effects']['energy_restore'], "Energy restore should have base value"
            assert 'level_multiplier' in item['effects']['energy_restore'], "Energy restore should have level multiplier"
    
    # Test Attribute Items
    for item in item_files['attribute']:
        if 'temp_attribute_boost' in item['effects']:
            for attr, value in item['effects']['temp_attribute_boost'].items():
                assert value >= 2, f"{item['name']} should boost attributes by at least 2"
        if 'permanent_attribute' in item['effects']:
            assert 'rare_attribute_chance' in item['effects'], "Permanent attribute items should have rare chance"
    
    # Test Social Items
    for item in item_files['social']:
        if 'club_reputation' in item['effects']:
            assert 'club_event_chance' in item['effects'], "Club items should have event chance"
        if 'rare_event_chance' in item['effects']:
            assert item['effects']['rare_event_chance'] >= 0.2, "Rare event chance should be at least 20%"
    
    print("All item effect tests passed!")

if __name__ == "__main__":
    test_item_effects() 