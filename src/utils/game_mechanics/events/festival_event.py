"""
Implementation of festival events in the game mechanics.
This class is responsible for handling special events that occur during festivals.
"""
import random
from typing import Dict, Any, List
from src.utils.game_mechanics.events.event_base import EventBase

class FestivalEvent(EventBase):
    """Class for festival events."""
    
    def __init__(self, title: str, description: str, exp_gain: int, tusd_gain: int, duration: int = 1):
        """Initialize the festival event.
        
        Args:
            title (str): The title of the event
            description (str): The description of the event
            exp_gain (int): The amount of experience gained from the event
            tusd_gain (int): The amount of TUSD gained from the event
            duration (int, optional): The duration of the festival in days. Defaults to 1.
        """
        effect = {"exp": exp_gain, "tusd": tusd_gain, "duration": duration}
        
        super().__init__(title, description, "festival", effect)
    
    def trigger(self, player: Dict[str, Any]) -> Dict[str, Any]:
        """Trigger the festival event for a player and return the result.
        
        Args:
            player (Dict[str, Any]): The player data
            
        Returns:
            Dict[str, Any]: The result of the event, including experience and TUSD gains
        """
        result = {
            "title": self.get_title(),
            "description": self.get_description(),
            "type": self.get_type(),
            "exp_change": self.get_effect().get("exp", 0),
            "tusd_change": self.get_effect().get("tusd", 0),
            "duration": self.get_effect().get("duration", 1)
        }
        
        # Apply bonus based on player's charisma
        if "charisma" in player:
            charisma_bonus = player["charisma"] * 0.1  # 10% bonus per charisma point
            result["exp_change"] = int(result["exp_change"] * (1 + charisma_bonus))
            result["tusd_change"] = int(result["tusd_change"] * (1 + charisma_bonus))
            result["charisma_bonus"] = charisma_bonus
        
        return result
    
    @staticmethod
    def create_random_festival_event() -> 'FestivalEvent':
        """Create a random festival event.
        
        Returns:
            FestivalEvent: A randomly generated festival event
        """
        # Generate random festival name
        festival_names = [
            "Festival dos Poderes",
            "Celebração da Academia",
            "Festival das Estações",
            "Torneio Anual",
            "Festival Cultural",
            "Celebração da Fundação"
        ]
        
        # Generate random description
        descriptions = [
            "Um grande festival está acontecendo na Academia Tokugawa! Participe e ganhe recompensas especiais.",
            "A Academia está celebrando com um festival especial. Todos os estudantes estão convidados a participar.",
            "Um festival tradicional está acontecendo. Mostre suas habilidades e ganhe reconhecimento.",
            "A cidade está em festa! Participe das atividades e ganhe prêmios exclusivos.",
            "Um festival cultural está acontecendo na Academia. Aprenda sobre diferentes culturas e ganhe experiência."
        ]
        
        # Generate random rewards
        exp_gain = random.randint(50, 150)
        tusd_gain = random.randint(20, 100)
        duration = random.randint(1, 7)  # 1-7 days
        
        return FestivalEvent(
            random.choice(festival_names),
            random.choice(descriptions),
            exp_gain,
            tusd_gain,
            duration
        )