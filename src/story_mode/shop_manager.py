import json
import logging
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from datetime import datetime, timedelta

from .reputation_manager import ReputationManager

logger = logging.getLogger('tokugawa_bot')

class ShopManager:
    """
    Manages shop functionality, including pricing and discounts.
    """
    
    def __init__(self, data_dir: str = "data/story_mode", reputation_manager: Optional[ReputationManager] = None):
        """
        Initialize the shop manager.
        
        Args:
            data_dir: Path to the directory containing shop data
            reputation_manager: Optional ReputationManager instance
        """
        self.data_dir = Path(data_dir)
        self.shop_dir = self.data_dir / "shops"
        self.shop_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize reputation manager
        self.reputation_manager = reputation_manager or ReputationManager(data_dir)
        
        # Load shop data
        self.shop_data = self._load_shop_data()
        
        # Active discounts cache
        self.active_discounts: Dict[str, Dict] = {}
    
    def _load_shop_data(self) -> Dict:
        """Load shop data from files."""
        shop_data = {
            "items": {},
            "shops": {}
        }
        
        # Load items from category-based structure
        items_dir = Path("data/economy/items")
        if items_dir.exists():
            for item_file in items_dir.glob("*.json"):
                with open(item_file, 'r') as f:
                    items = json.load(f)
                    for item in items:
                        shop_data["items"][str(item["id"])] = item
        
        # Load shops
        shops_file = self.shop_dir / "shops.json"
        if shops_file.exists():
            with open(shops_file, 'r') as f:
                shop_data["shops"] = json.load(f)
        
        return shop_data
    
    def _save_shop_data(self) -> None:
        """Save shop data to files."""
        # Save items
        with open(self.shop_dir / "items.json", 'w') as f:
            json.dump(self.shop_data["items"], f, indent=2)
        
        # Save shops
        with open(self.shop_dir / "shops.json", 'w') as f:
            json.dump(self.shop_data["shops"], f, indent=2)
    
    def get_item_price(self, item_id: str, shop_id: str, player_data: Dict) -> Tuple[float, Dict[str, float]]:
        """
        Get the price of an item with all applicable discounts.
        
        Args:
            item_id: ID of the item
            shop_id: ID of the shop
            player_data: Player data dictionary
            
        Returns:
            Tuple of (final_price, discount_breakdown)
        """
        # Get base price
        base_price = self.shop_data["items"][item_id]["base_price"]
        
        # Initialize discount breakdown
        discounts = {
            "reputation": 0.0,
            "event": 0.0,
            "status": 0.0,
            "temporary": 0.0
        }
        
        # Calculate reputation discount
        shop_data = self.shop_data["shops"][shop_id]
        if "reputation_target" in shop_data:
            target_type = shop_data["reputation_target_type"]
            target_id = shop_data["reputation_target"]
            rep_discount = self.reputation_manager.get_reputation_discount(target_id, target_type)
            discounts["reputation"] = base_price * rep_discount
        
        # Calculate event discount
        if "active_events" in player_data:
            for event in player_data["active_events"]:
                if event.get("type") == "shop_discount":
                    event_discount = base_price * event["discount"]
                    discounts["event"] += event_discount
        
        # Calculate status discount
        if "status" in player_data and "shop_discount" in player_data["status"]:
            status_discount = base_price * player_data["status"]["shop_discount"]
            discounts["status"] = status_discount
        
        # Calculate temporary discount
        if shop_id in self.active_discounts:
            temp_discount = base_price * self.active_discounts[shop_id]["discount"]
            discounts["temporary"] = temp_discount
        
        # Calculate final price
        total_discount = sum(discounts.values())
        final_price = max(0, base_price - total_discount)
        
        return final_price, discounts
    
    def add_temporary_discount(self, shop_id: str, discount: float, duration: int) -> None:
        """
        Add a temporary discount to a shop.
        
        Args:
            shop_id: ID of the shop
            discount: Discount percentage (0.0 to 1.0)
            duration: Duration in seconds
        """
        self.active_discounts[shop_id] = {
            "discount": discount,
            "expires_at": datetime.now() + timedelta(seconds=duration)
        }
    
    def get_shop_inventory(self, shop_id: str, player_data: Dict) -> List[Dict]:
        """
        Get the inventory of a shop with prices.
        
        Args:
            shop_id: ID of the shop
            player_data: Player data dictionary
            
        Returns:
            List of items with prices
        """
        shop_data = self.shop_data["shops"][shop_id]
        inventory = []
        
        for item_id in shop_data["inventory"]:
            if item_id not in self.shop_data["items"]:
                logger.warning(f"Item {item_id} not found in shop {shop_id}")
                continue
            
            item_data = self.shop_data["items"][item_id].copy()
            price, discounts = self.get_item_price(item_id, shop_id, player_data)
            
            item_data["price"] = price
            item_data["discounts"] = discounts
            inventory.append(item_data)
        
        return inventory
    
    def purchase_item(self, item_id: str, shop_id: str, player_data: Dict) -> Tuple[bool, str]:
        """
        Purchase an item from a shop.
        
        Args:
            item_id: ID of the item
            shop_id: ID of the shop
            player_data: Player data dictionary
            
        Returns:
            Tuple of (success, message)
        """
        # Get price
        price, _ = self.get_item_price(item_id, shop_id, player_data)
        
        # Check if player has enough currency
        if player_data.get("currency", 0) < price:
            return False, "Insufficient funds"
        
        # Check if item is in stock
        if not self._is_item_available(item_id, shop_id):
            return False, "Item out of stock"
        
        # Deduct currency
        player_data["currency"] -= price
        
        # Add item to inventory
        if "inventory" not in player_data:
            player_data["inventory"] = []
        player_data["inventory"].append(item_id)
        
        # Update stock if applicable
        if "stock" in self.shop_data["shops"][shop_id]:
            self.shop_data["shops"][shop_id]["stock"][item_id] -= 1
            self._save_shop_data()
        
        return True, "Purchase successful"
    
    def _is_item_available(self, item_id: str, shop_id: str) -> bool:
        """Check if an item is available in a shop."""
        shop_data = self.shop_data["shops"][shop_id]
        
        # Check if item is in inventory
        if item_id not in shop_data["inventory"]:
            return False
        
        # Check stock if applicable
        if "stock" in shop_data:
            return shop_data["stock"].get(item_id, 0) > 0
        
        return True
    
    def get_active_discounts(self) -> Dict[str, Dict]:
        """Get all active temporary discounts."""
        # Clean expired discounts
        for shop_id, discount_data in list(self.active_discounts.items()):
            if discount_data["expires_at"] <= datetime.now():
                del self.active_discounts[shop_id]
        
        return self.active_discounts 