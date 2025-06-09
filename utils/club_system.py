"""
Club system implementation for Academia Tokugawa.

This module provides the ClubSystem class that manages club operations
and provides club information for the game.
"""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger('tokugawa_bot')

class ClubSystem:
    """System for managing clubs in Academia Tokugawa."""

    # Club definitions
    CLUBS = {
        '1': 'Clube das Chamas',
        '2': 'Ilusionistas Mentais',
        '3': 'Conselho Político',
        '4': 'Elementalistas',
        '5': 'Clube de Combate'
    }

    def __init__(self):
        """Initialize the club system."""
        self.logger = logging.getLogger('tokugawa_bot')
        self.logger.info("Initializing ClubSystem")

    def get_club_name(self, club_id: str) -> Optional[str]:
        """
        Get the name of a club by its ID.
        
        Args:
            club_id (str): The ID of the club
            
        Returns:
            Optional[str]: The name of the club, or None if not found
        """
        return self.CLUBS.get(club_id)

    def get_club_id(self, club_name: str) -> Optional[str]:
        """
        Get the ID of a club by its name.
        
        Args:
            club_name (str): The name of the club
            
        Returns:
            Optional[str]: The ID of the club, or None if not found
        """
        for club_id, name in self.CLUBS.items():
            if name.lower() == club_name.lower():
                return club_id
        return None

    def get_all_clubs(self) -> List[Dict[str, str]]:
        """
        Get a list of all clubs with their IDs and names.
        
        Returns:
            List[Dict[str, str]]: List of dictionaries containing club IDs and names
        """
        return [{'id': club_id, 'name': name} for club_id, name in self.CLUBS.items()]

    def is_valid_club(self, club_id: str) -> bool:
        """
        Check if a club ID is valid.
        
        Args:
            club_id (str): The ID to check
            
        Returns:
            bool: True if the club ID is valid, False otherwise
        """
        return club_id in self.CLUBS

    def get_club_description(self, club_id: str) -> str:
        """
        Get the description of a club.
        
        Args:
            club_id (str): The ID of the club
            
        Returns:
            str: The description of the club
        """
        club_name = self.get_club_name(club_id)
        if not club_name:
            return "Clube não encontrado"
            
        descriptions = {
            '1': "O Clube das Chamas é especializado em combate físico e treinamento de força.",
            '2': "Os Ilusionistas Mentais focam em habilidades mentais e controle de energia.",
            '3': "O Conselho Político é dedicado à diplomacia e estratégia política.",
            '4': "Os Elementalistas dominam o controle dos elementos naturais.",
            '5': "O Clube de Combate é focado em técnicas de luta e defesa pessoal."
        }
        
        return descriptions.get(club_id, f"O {club_name} é um dos clubes mais prestigiados da Academia Tokugawa.") 