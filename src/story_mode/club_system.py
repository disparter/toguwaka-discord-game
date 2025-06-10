"""
Club system for Academia Tokugawa.

This module provides functionality for managing clubs, alliances, and rivalries.
"""

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger('tokugawa_bot')

class ClubSystem:
    """
    Manages club relationships, alliances, and rivalries.
    """
    def __init__(self):
        """Initialize the club system with predefined clubs."""
        # Map of club_id to club name
        self.CLUBS = {
            "club_1": "Clube de Artes Marciais",
            "club_2": "Clube de Magia Elemental",
            "club_3": "Clube de Ciências Arcanas",
            "club_4": "Clube de Esportes Sobrenaturais",
            "club_5": "Clube de Estratégia e Táticas"
        }
        
        # Track alliances and rivalries
        self.alliances = {}  # club_id -> list of allied club_ids
        self.rivalries = {}  # club_id -> list of rival club_ids
        
        logger.info("ClubSystem initialized")
    
    def get_club_name(self, club_id: str) -> Optional[str]:
        """Get the name of a club by its ID."""
        return self.CLUBS.get(club_id)
    
    def get_club_id(self, club_name: str) -> Optional[str]:
        """Get the ID of a club by its name."""
        for club_id, name in self.CLUBS.items():
            if name.lower() == club_name.lower():
                return club_id
        return None
    
    def form_alliance(self, player: Dict[str, Any], target_club_id: str) -> Dict[str, Any]:
        """
        Form an alliance between the player's club and the target club.
        
        Args:
            player: Player data dictionary
            target_club_id: ID of the club to form an alliance with
            
        Returns:
            Dictionary with result information
        """
        player_club_id = player.get('club_id')
        
        if not player_club_id:
            return {"error": "Você não está em nenhum clube."}
        
        if player_club_id == target_club_id:
            return {"error": "Você não pode formar uma aliança com seu próprio clube."}
        
        # Check if the target club exists
        if target_club_id not in self.CLUBS:
            return {"error": f"Clube com ID {target_club_id} não encontrado."}
        
        # Initialize alliance lists if they don't exist
        if player_club_id not in self.alliances:
            self.alliances[player_club_id] = []
        
        if target_club_id not in self.alliances:
            self.alliances[target_club_id] = []
        
        # Check if already allied
        if target_club_id in self.alliances[player_club_id]:
            return {"error": f"Seu clube já tem uma aliança com {self.CLUBS[target_club_id]}."}
        
        # Check if they are rivals
        if player_club_id in self.rivalries and target_club_id in self.rivalries[player_club_id]:
            return {"error": f"Seu clube tem uma rivalidade com {self.CLUBS[target_club_id]}. Você precisa encerrar a rivalidade antes de formar uma aliança."}
        
        # Form alliance (both ways)
        self.alliances[player_club_id].append(target_club_id)
        self.alliances[target_club_id].append(player_club_id)
        
        logger.info(f"Alliance formed between {player_club_id} and {target_club_id}")
        
        return {
            "success": True,
            "message": f"Seu clube ({self.CLUBS[player_club_id]}) formou uma aliança com {self.CLUBS[target_club_id]}. Esta aliança trará benefícios mútuos para ambos os clubes."
        }
    
    def declare_rivalry(self, player: Dict[str, Any], target_club_id: str) -> Dict[str, Any]:
        """
        Declare a rivalry between the player's club and the target club.
        
        Args:
            player: Player data dictionary
            target_club_id: ID of the club to declare rivalry with
            
        Returns:
            Dictionary with result information
        """
        player_club_id = player.get('club_id')
        
        if not player_club_id:
            return {"error": "Você não está em nenhum clube."}
        
        if player_club_id == target_club_id:
            return {"error": "Você não pode declarar rivalidade com seu próprio clube."}
        
        # Check if the target club exists
        if target_club_id not in self.CLUBS:
            return {"error": f"Clube com ID {target_club_id} não encontrado."}
        
        # Initialize rivalry lists if they don't exist
        if player_club_id not in self.rivalries:
            self.rivalries[player_club_id] = []
        
        if target_club_id not in self.rivalries:
            self.rivalries[target_club_id] = []
        
        # Check if already rivals
        if target_club_id in self.rivalries[player_club_id]:
            return {"error": f"Seu clube já tem uma rivalidade com {self.CLUBS[target_club_id]}."}
        
        # Check if they are allies
        if player_club_id in self.alliances and target_club_id in self.alliances[player_club_id]:
            return {"error": f"Seu clube tem uma aliança com {self.CLUBS[target_club_id]}. Você precisa encerrar a aliança antes de declarar rivalidade."}
        
        # Declare rivalry (both ways)
        self.rivalries[player_club_id].append(target_club_id)
        self.rivalries[target_club_id].append(player_club_id)
        
        logger.info(f"Rivalry declared between {player_club_id} and {target_club_id}")
        
        return {
            "success": True,
            "message": f"Seu clube ({self.CLUBS[player_club_id]}) declarou rivalidade com {self.CLUBS[target_club_id]}. Esta rivalidade aumentará a competição entre os clubes e poderá trazer recompensas para o vencedor."
        }
    
    def get_club_alliances(self, club_id: str) -> List[str]:
        """Get all alliances for a club."""
        if club_id not in self.alliances:
            return []
        return self.alliances[club_id]
    
    def get_club_rivalries(self, club_id: str) -> List[str]:
        """Get all rivalries for a club."""
        if club_id not in self.rivalries:
            return []
        return self.rivalries[club_id]