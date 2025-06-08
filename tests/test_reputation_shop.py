import unittest
import json
import os
import shutil
from pathlib import Path
from datetime import datetime, timedelta

from story_mode.reputation_manager import ReputationManager
from story_mode.shop_manager import ShopManager

class TestReputationShop(unittest.TestCase):
    """Test suite for reputation and shop systems."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_dir = Path("test_data")
        self.test_dir.mkdir(exist_ok=True)
        
        # Create test data
        self._create_test_data()
        
        # Initialize managers
        self.reputation_manager = ReputationManager(str(self.test_dir))
        self.shop_manager = ShopManager(str(self.test_dir), self.reputation_manager)
    
    def tearDown(self):
        """Clean up test environment."""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def _create_test_data(self):
        """Create test data files."""
        # Create reputation data
        reputation_dir = self.test_dir / "reputation"
        reputation_dir.mkdir(parents=True, exist_ok=True)
        
        # Club reputation
        with open(reputation_dir / "club_reputation.json", 'w') as f:
            json.dump({
                "clube_das_chamas": 50.0,
                "clube_elementalistas": 25.0
            }, f)
        
        # NPC reputation
        with open(reputation_dir / "npc_reputation.json", 'w') as f:
            json.dump({
                "professor_quantum": 75.0,
                "estudante_1": 0.0
            }, f)
        
        # Reputation items
        with open(reputation_dir / "reputation_items.json", 'w') as f:
            json.dump({
                "reputation_boost": {
                    "name": "Reputation Boost",
                    "effects": [
                        {
                            "target_type": "club",
                            "target_id": "clube_das_chamas",
                            "amount": 10.0,
                            "duration": 3600
                        }
                    ]
                }
            }, f)
        
        # Create shop data
        shop_dir = self.test_dir / "shops"
        shop_dir.mkdir(parents=True, exist_ok=True)
        
        # Items
        with open(shop_dir / "items.json", 'w') as f:
            json.dump({
                "item_1": {
                    "name": "Test Item 1",
                    "base_price": 100.0
                },
                "item_2": {
                    "name": "Test Item 2",
                    "base_price": 200.0
                }
            }, f)
        
        # Shops
        with open(shop_dir / "shops.json", 'w') as f:
            json.dump({
                "shop_1": {
                    "name": "Test Shop 1",
                    "inventory": ["item_1", "item_2"],
                    "reputation_target": "clube_das_chamas",
                    "reputation_target_type": "club"
                },
                "shop_2": {
                    "name": "Test Shop 2",
                    "inventory": ["item_1"],
                    "stock": {
                        "item_1": 5
                    }
                }
            }, f)
    
    def test_reputation_management(self):
        """Test reputation management functionality."""
        # Test getting reputation
        rep = self.reputation_manager.get_reputation("clube_das_chamas", "club")
        self.assertEqual(rep, 50.0)
        
        # Test modifying reputation
        new_rep = self.reputation_manager.modify_reputation("clube_das_chamas", 10.0, "club")
        self.assertEqual(new_rep, 60.0)
        
        # Test reputation level
        level = self.reputation_manager.get_reputation_level("clube_das_chamas", "club")
        self.assertEqual(level, "friendly")
        
        # Test reputation discount
        discount = self.reputation_manager.get_reputation_discount("clube_das_chamas", "club")
        self.assertEqual(discount, 0.15)  # 15% discount
    
    def test_reputation_items(self):
        """Test reputation item functionality."""
        player_data = {
            "status": {
                "reputation_boost": 1.5
            }
        }
        
        # Test applying reputation item
        changes = self.reputation_manager.apply_reputation_item("reputation_boost", player_data)
        self.assertIn("club:clube_das_chamas", changes)
        
        # Test active effects
        effects = self.reputation_manager.get_active_effects()
        self.assertIn("reputation_boost", effects)
    
    def test_shop_pricing(self):
        """Test shop pricing functionality."""
        player_data = {
            "currency": 1000,
            "active_events": [
                {
                    "type": "shop_discount",
                    "discount": 0.1
                }
            ],
            "status": {
                "shop_discount": 0.05
            }
        }
        
        # Test getting item price
        price, discounts = self.shop_manager.get_item_price("item_1", "shop_1", player_data)
        self.assertLess(price, 100.0)  # Price should be less than base price
        self.assertIn("reputation", discounts)
        self.assertIn("event", discounts)
        self.assertIn("status", discounts)
    
    def test_shop_purchase(self):
        """Test shop purchase functionality."""
        player_data = {
            "currency": 1000
        }
        
        # Test successful purchase
        success, message = self.shop_manager.purchase_item("item_1", "shop_1", player_data)
        self.assertTrue(success)
        self.assertEqual(message, "Purchase successful")
        self.assertIn("item_1", player_data["inventory"])
        
        # Test insufficient funds
        player_data["currency"] = 0
        success, message = self.shop_manager.purchase_item("item_1", "shop_1", player_data)
        self.assertFalse(success)
        self.assertEqual(message, "Insufficient funds")
    
    def test_shop_inventory(self):
        """Test shop inventory functionality."""
        player_data = {
            "currency": 1000
        }
        
        # Test getting inventory
        inventory = self.shop_manager.get_shop_inventory("shop_1", player_data)
        self.assertEqual(len(inventory), 2)
        
        # Test item data
        item = inventory[0]
        self.assertIn("price", item)
        self.assertIn("discounts", item)
    
    def test_temporary_discounts(self):
        """Test temporary discount functionality."""
        # Add temporary discount
        self.shop_manager.add_temporary_discount("shop_1", 0.2, 3600)
        
        # Test getting active discounts
        discounts = self.shop_manager.get_active_discounts()
        self.assertIn("shop_1", discounts)
        
        # Test discount in price calculation
        player_data = {"currency": 1000}
        price, discounts = self.shop_manager.get_item_price("item_1", "shop_1", player_data)
        self.assertIn("temporary", discounts)
    
    def test_stock_management(self):
        """Test shop stock management."""
        player_data = {"currency": 1000}
        
        # Test stock reduction
        for _ in range(5):
            success, _ = self.shop_manager.purchase_item("item_1", "shop_2", player_data)
            self.assertTrue(success)
        
        # Test out of stock
        success, message = self.shop_manager.purchase_item("item_1", "shop_2", player_data)
        self.assertFalse(success)
        self.assertEqual(message, "Item out of stock")

if __name__ == '__main__':
    unittest.main() 