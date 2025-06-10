from typing import Dict, List, Any, Optional, Union
import json
import logging
import random
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger('tokugawa_bot')

class Season(Enum):
    """
    Represents the four seasons of the year.
    """
    SPRING = "spring"
    SUMMER = "summer"
    AUTUMN = "autumn"
    WINTER = "winter"
    
    @classmethod
    def get_current_season(cls) -> 'Season':
        """
        Determines the current season based on the current date.
        
        Returns:
            Current season
        """
        now = datetime.now()
        month = now.month
        
        if 3 <= month <= 5:
            return cls.SPRING
        elif 6 <= month <= 8:
            return cls.SUMMER
        elif 9 <= month <= 11:
            return cls.AUTUMN
        else:  # month == 12 or month <= 2
            return cls.WINTER
            
    @classmethod
    def get_next_season(cls, season: 'Season') -> 'Season':
        """
        Gets the next season in the cycle.
        
        Args:
            season: Current season
            
        Returns:
            Next season
        """
        if season == cls.SPRING:
            return cls.SUMMER
        elif season == cls.SUMMER:
            return cls.AUTUMN
        elif season == cls.AUTUMN:
            return cls.WINTER
        else:  # season == cls.WINTER
            return cls.SPRING


class SeasonalEvent:
    """
    Represents a seasonal event that occurs during a specific season.
    """
    def __init__(self, event_id: str, data: Dict[str, Any]):
        """
        Initialize a seasonal event.
        
        Args:
            event_id: Unique identifier for the event
            data: Dictionary containing event data
        """
        self.event_id = event_id
        self.name = data.get("name", "Unknown Event")
        self.description = data.get("description", "No description available.")
        self.season = data.get("season", "any")
        self.duration_days = data.get("duration_days", 7)
        self.requirements = data.get("requirements", {})
        self.rewards = data.get("rewards", {})
        self.story_integration = data.get("story_integration", {})
        self.activities = data.get("activities", [])
        
    def get_name(self) -> str:
        """Returns the event name."""
        return self.name
        
    def get_description(self) -> str:
        """Returns the event description."""
        return self.description
        
    def get_season(self) -> str:
        """Returns the event season."""
        return self.season
        
    def get_duration_days(self) -> int:
        """Returns the event duration in days."""
        return self.duration_days
        
    def get_requirements(self) -> Dict[str, Any]:
        """Returns the event requirements."""
        return self.requirements
        
    def get_rewards(self) -> Dict[str, Any]:
        """Returns the event rewards."""
        return self.rewards
        
    def get_story_integration(self) -> Dict[str, Any]:
        """Returns the event story integration details."""
        return self.story_integration
        
    def get_activities(self) -> List[Dict[str, Any]]:
        """Returns the event activities."""
        return self.activities
        
    def is_available(self, player_data: Dict[str, Any], current_season: Season) -> bool:
        """
        Checks if the event is available for the player.
        
        Args:
            player_data: Player data
            current_season: Current season
            
        Returns:
            True if the event is available, False otherwise
        """
        # Check season
        if self.season != "any" and self.season != current_season.value:
            return False
            
        # Check level requirement
        if "level" in self.requirements and player_data.get("level", 1) < self.requirements["level"]:
            return False
            
        # Check completed chapters requirement
        if "completed_chapters" in self.requirements:
            story_progress = player_data.get("story_progress", {})
            completed_chapters = story_progress.get("completed_chapters", [])
            for chapter in self.requirements["completed_chapters"]:
                if chapter not in completed_chapters:
                    return False
                    
        # Check faction reputation requirement
        if "faction_reputation" in self.requirements:
            faction_reputation = player_data.get("story_progress", {}).get("faction_reputation", {})
            for faction, min_rep in self.requirements["faction_reputation"].items():
                if faction not in faction_reputation or faction_reputation[faction] < min_rep:
                    return False
                    
        # Check power requirement
        if "power" in self.requirements:
            powers = player_data.get("story_progress", {}).get("powers", {})
            power_id = self.requirements["power"].get("id")
            power_level = self.requirements["power"].get("level", 1)
            
            if power_id not in powers or powers[power_id].get("level", 1) < power_level:
                return False
                
        return True
        
    def participate(self, player_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Allows a player to participate in the event.
        
        Args:
            player_data: Player data
            
        Returns:
            Updated player data and result information
        """
        story_progress = player_data.get("story_progress", {})
        
        # Record participation
        if "seasonal_events" not in story_progress:
            story_progress["seasonal_events"] = {}
            
        if "participated_events" not in story_progress["seasonal_events"]:
            story_progress["seasonal_events"]["participated_events"] = []
            
        # Check if already participated
        if self.event_id in story_progress["seasonal_events"].get("participated_events", []):
            return {
                "player_data": player_data,
                "error": f"Already participated in event: {self.name}"
            }
            
        # Add to participated events
        story_progress["seasonal_events"]["participated_events"].append(self.event_id)
        
        # Apply rewards
        rewards = self.get_rewards()
        
        if "exp" in rewards:
            player_data["exp"] = player_data.get("exp", 0) + rewards["exp"]
            
        if "tusd" in rewards:
            player_data["tusd"] = player_data.get("tusd", 0) + rewards["tusd"]
            
        if "hierarchy_points" in rewards:
            story_progress["hierarchy_points"] = story_progress.get("hierarchy_points", 0) + rewards["hierarchy_points"]
            
        if "special_item" in rewards:
            special_items = story_progress.get("special_items", [])
            if rewards["special_item"] not in special_items:
                special_items.append(rewards["special_item"])
            story_progress["special_items"] = special_items
            
        if "faction_reputation" in rewards:
            faction_reputation = story_progress.get("faction_reputation", {})
            for faction, change in rewards["faction_reputation"].items():
                faction_reputation[faction] = faction_reputation.get(faction, 0) + change
            story_progress["faction_reputation"] = faction_reputation
            
        # Update player data
        player_data["story_progress"] = story_progress
        
        logger.info(f"Player {player_data.get('user_id')} participated in seasonal event: {self.name}")
        
        return {
            "player_data": player_data,
            "success": True,
            "message": f"Você participou do evento: {self.name}!",
            "event_info": {
                "id": self.event_id,
                "name": self.name,
                "description": self.description,
                "rewards": rewards
            }
        }


class AcademyFestival(SeasonalEvent):
    """
    Represents a festival event at the academy with mini-games and challenges.
    """
    def __init__(self, event_id: str, data: Dict[str, Any]):
        super().__init__(event_id, data)
        self.mini_games = data.get("mini_games", [])
        self.exclusive_challenges = data.get("exclusive_challenges", [])
        
    def get_mini_games(self) -> List[Dict[str, Any]]:
        """Returns the festival mini-games."""
        return self.mini_games
        
    def get_exclusive_challenges(self) -> List[Dict[str, Any]]:
        """Returns the festival exclusive challenges."""
        return self.exclusive_challenges
        
    def participate_in_mini_game(self, player_data: Dict[str, Any], mini_game_id: str) -> Dict[str, Any]:
        """
        Allows a player to participate in a mini-game.
        
        Args:
            player_data: Player data
            mini_game_id: ID of the mini-game
            
        Returns:
            Updated player data and result information
        """
        # Find the mini-game
        mini_game = None
        for game in self.mini_games:
            if game.get("id") == mini_game_id:
                mini_game = game
                break
                
        if not mini_game:
            return {
                "player_data": player_data,
                "error": f"Mini-game not found: {mini_game_id}"
            }
            
        story_progress = player_data.get("story_progress", {})
        
        # Record participation
        if "seasonal_events" not in story_progress:
            story_progress["seasonal_events"] = {}
            
        if "mini_games" not in story_progress["seasonal_events"]:
            story_progress["seasonal_events"]["mini_games"] = {}
            
        # Check if already participated
        if mini_game_id in story_progress["seasonal_events"].get("mini_games", {}):
            return {
                "player_data": player_data,
                "error": f"Already participated in mini-game: {mini_game.get('name')}"
            }
            
        # Determine result (win/lose)
        # For simplicity, we'll use a random chance of winning
        # In a real implementation, this would be based on player skill or choices
        win_chance = mini_game.get("win_chance", 0.5)
        win = random.random() < win_chance
        
        # Record result
        story_progress["seasonal_events"]["mini_games"][mini_game_id] = {
            "participated": True,
            "won": win,
            "timestamp": datetime.now().isoformat()
        }
        
        # Apply rewards if won
        rewards = {}
        if win:
            rewards = mini_game.get("rewards", {})
            
            if "exp" in rewards:
                player_data["exp"] = player_data.get("exp", 0) + rewards["exp"]
                
            if "tusd" in rewards:
                player_data["tusd"] = player_data.get("tusd", 0) + rewards["tusd"]
                
            if "special_item" in rewards:
                special_items = story_progress.get("special_items", [])
                if rewards["special_item"] not in special_items:
                    special_items.append(rewards["special_item"])
                story_progress["special_items"] = special_items
                
        # Update player data
        player_data["story_progress"] = story_progress
        
        logger.info(f"Player {player_data.get('user_id')} participated in mini-game {mini_game.get('name')}, result: {'won' if win else 'lost'}")
        
        return {
            "player_data": player_data,
            "success": True,
            "message": f"Você {'venceu' if win else 'perdeu'} no mini-jogo: {mini_game.get('name')}!",
            "mini_game_info": {
                "id": mini_game_id,
                "name": mini_game.get("name"),
                "description": mini_game.get("description"),
                "won": win,
                "rewards": rewards if win else {}
            }
        }
        
    def attempt_challenge(self, player_data: Dict[str, Any], challenge_id: str) -> Dict[str, Any]:
        """
        Allows a player to attempt an exclusive challenge.
        
        Args:
            player_data: Player data
            challenge_id: ID of the challenge
            
        Returns:
            Updated player data and result information
        """
        # Find the challenge
        challenge = None
        for ch in self.exclusive_challenges:
            if ch.get("id") == challenge_id:
                challenge = ch
                break
                
        if not challenge:
            return {
                "player_data": player_data,
                "error": f"Challenge not found: {challenge_id}"
            }
            
        story_progress = player_data.get("story_progress", {})
        
        # Record attempt
        if "seasonal_events" not in story_progress:
            story_progress["seasonal_events"] = {}
            
        if "challenges" not in story_progress["seasonal_events"]:
            story_progress["seasonal_events"]["challenges"] = {}
            
        # Check if already completed
        if challenge_id in story_progress["seasonal_events"].get("challenges", {}) and story_progress["seasonal_events"]["challenges"][challenge_id].get("completed", False):
            return {
                "player_data": player_data,
                "error": f"Challenge already completed: {challenge.get('name')}"
            }
            
        # Check requirements
        requirements = challenge.get("requirements", {})
        
        if "level" in requirements and player_data.get("level", 1) < requirements["level"]:
            return {
                "player_data": player_data,
                "error": f"Level requirement not met for challenge: {challenge.get('name')}"
            }
            
        if "power" in requirements:
            powers = player_data.get("story_progress", {}).get("powers", {})
            power_id = requirements["power"].get("id")
            power_level = requirements["power"].get("level", 1)
            
            if power_id not in powers or powers[power_id].get("level", 1) < power_level:
                return {
                    "player_data": player_data,
                    "error": f"Power requirement not met for challenge: {challenge.get('name')}"
                }
                
        # Determine result (success/failure)
        # For simplicity, we'll use a random chance of success
        # In a real implementation, this would be based on player skill or choices
        success_chance = challenge.get("success_chance", 0.3)  # Challenges are harder than mini-games
        success = random.random() < success_chance
        
        # Record result
        story_progress["seasonal_events"]["challenges"][challenge_id] = {
            "attempted": True,
            "completed": success,
            "timestamp": datetime.now().isoformat()
        }
        
        # Apply rewards if successful
        rewards = {}
        if success:
            rewards = challenge.get("rewards", {})
            
            if "exp" in rewards:
                player_data["exp"] = player_data.get("exp", 0) + rewards["exp"]
                
            if "tusd" in rewards:
                player_data["tusd"] = player_data.get("tusd", 0) + rewards["tusd"]
                
            if "special_item" in rewards:
                special_items = story_progress.get("special_items", [])
                if rewards["special_item"] not in special_items:
                    special_items.append(rewards["special_item"])
                story_progress["special_items"] = special_items
                
            if "power_points" in rewards:
                power_id = requirements.get("power", {}).get("id")
                if power_id and power_id in story_progress.get("powers", {}):
                    power = story_progress["powers"][power_id]
                    power["power_points"] = power.get("power_points", 0) + rewards["power_points"]
                    
        # Update player data
        player_data["story_progress"] = story_progress
        
        logger.info(f"Player {player_data.get('user_id')} attempted challenge {challenge.get('name')}, result: {'completed' if success else 'failed'}")
        
        return {
            "player_data": player_data,
            "success": True,
            "message": f"Você {'completou' if success else 'falhou'} no desafio: {challenge.get('name')}!",
            "challenge_info": {
                "id": challenge_id,
                "name": challenge.get("name"),
                "description": challenge.get("description"),
                "completed": success,
                "rewards": rewards if success else {}
            }
        }


class WeatherEvent(SeasonalEvent):
    """
    Represents a weather event that affects gameplay and unlocks exclusive content.
    """
    def __init__(self, event_id: str, data: Dict[str, Any]):
        super().__init__(event_id, data)
        self.weather_type = data.get("weather_type", "normal")
        self.gameplay_effects = data.get("gameplay_effects", {})
        self.exclusive_content = data.get("exclusive_content", {})
        
    def get_weather_type(self) -> str:
        """Returns the weather type."""
        return self.weather_type
        
    def get_gameplay_effects(self) -> Dict[str, Any]:
        """Returns the gameplay effects."""
        return self.gameplay_effects
        
    def get_exclusive_content(self) -> Dict[str, Any]:
        """Returns the exclusive content."""
        return self.exclusive_content
        
    def apply_weather_effects(self, player_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Applies weather effects to the player.
        
        Args:
            player_data: Player data
            
        Returns:
            Updated player data and effect information
        """
        story_progress = player_data.get("story_progress", {})
        
        # Record weather event
        if "seasonal_events" not in story_progress:
            story_progress["seasonal_events"] = {}
            
        if "weather_events" not in story_progress["seasonal_events"]:
            story_progress["seasonal_events"]["weather_events"] = {}
            
        # Check if already experienced
        if self.event_id in story_progress["seasonal_events"].get("weather_events", {}):
            return {
                "player_data": player_data,
                "error": f"Already experienced weather event: {self.name}"
            }
            
        # Record experience
        story_progress["seasonal_events"]["weather_events"][self.event_id] = {
            "experienced": True,
            "timestamp": datetime.now().isoformat()
        }
        
        # Apply gameplay effects
        effects = self.gameplay_effects
        applied_effects = {}
        
        if "stat_modifiers" in effects:
            # In a real implementation, these would be applied to gameplay
            # For now, we'll just record them
            applied_effects["stat_modifiers"] = effects["stat_modifiers"]
            
        if "unlock_locations" in effects:
            if "unlocked_locations" not in story_progress:
                story_progress["unlocked_locations"] = []
                
            for location in effects["unlock_locations"]:
                if location not in story_progress["unlocked_locations"]:
                    story_progress["unlocked_locations"].append(location)
                    
            applied_effects["unlocked_locations"] = effects["unlock_locations"]
            
        # Unlock exclusive content
        exclusive_content = self.exclusive_content
        unlocked_content = {}
        
        if "special_items" in exclusive_content:
            special_items = story_progress.get("special_items", [])
            for item in exclusive_content["special_items"]:
                if item not in special_items:
                    special_items.append(item)
                    
            story_progress["special_items"] = special_items
            unlocked_content["special_items"] = exclusive_content["special_items"]
            
        if "quests" in exclusive_content:
            if "available_quests" not in story_progress:
                story_progress["available_quests"] = []
                
            for quest in exclusive_content["quests"]:
                if quest not in story_progress["available_quests"]:
                    story_progress["available_quests"].append(quest)
                    
            unlocked_content["quests"] = exclusive_content["quests"]
            
        # Update player data
        player_data["story_progress"] = story_progress
        
        logger.info(f"Player {player_data.get('user_id')} experienced weather event: {self.name}")
        
        return {
            "player_data": player_data,
            "success": True,
            "message": f"Você experimentou o evento climático: {self.name}!",
            "weather_info": {
                "id": self.event_id,
                "name": self.name,
                "description": self.description,
                "weather_type": self.weather_type,
                "applied_effects": applied_effects,
                "unlocked_content": unlocked_content
            }
        }


class SeasonalEventSystem:
    """
    Main class for the seasonal event system.
    Manages seasonal events, academy festivals, and weather events.
    """
    def __init__(self):
        """Initialize the seasonal event system."""
        self.seasonal_events = {}
        self.academy_festivals = {}
        self.weather_events = {}
        
        # Define default seasonal events
        self.default_seasonal_events = {
            "spring_awakening": {
                "name": "Despertar da Primavera",
                "description": "Um evento que celebra o renascimento e novos começos na Academia Tokugawa.",
                "season": "spring",
                "duration_days": 7,
                "requirements": {
                    "level": 5
                },
                "rewards": {
                    "exp": 500,
                    "tusd": 200,
                    "special_item": "Flor de Cerejeira Encantada"
                },
                "story_integration": {
                    "theme": "renascimento",
                    "related_chapters": ["1_3", "2_2"]
                },
                "activities": [
                    {
                        "name": "Cerimônia de Plantio",
                        "description": "Plante uma árvore nos jardins da academia para simbolizar seu crescimento."
                    },
                    {
                        "name": "Meditação ao Amanhecer",
                        "description": "Participe de uma sessão de meditação ao nascer do sol para fortalecer seu poder."
                    }
                ]
            },
            "summer_solstice": {
                "name": "Solstício de Verão",
                "description": "Um evento que celebra o auge do poder e da energia na Academia Tokugawa.",
                "season": "summer",
                "duration_days": 7,
                "requirements": {
                    "level": 10
                },
                "rewards": {
                    "exp": 800,
                    "tusd": 300,
                    "special_item": "Amuleto Solar"
                },
                "story_integration": {
                    "theme": "poder",
                    "related_chapters": ["1_5", "2_4"]
                },
                "activities": [
                    {
                        "name": "Ritual do Sol",
                        "description": "Participe de um ritual para canalizar a energia do sol e fortalecer seu poder."
                    },
                    {
                        "name": "Torneio de Duelos",
                        "description": "Compita em um torneio de duelos para testar suas habilidades."
                    }
                ]
            },
            "autumn_harvest": {
                "name": "Colheita de Outono",
                "description": "Um evento que celebra a colheita e a preparação para o inverno na Academia Tokugawa.",
                "season": "autumn",
                "duration_days": 7,
                "requirements": {
                    "level": 15
                },
                "rewards": {
                    "exp": 1000,
                    "tusd": 400,
                    "special_item": "Fruto da Sabedoria"
                },
                "story_integration": {
                    "theme": "sabedoria",
                    "related_chapters": ["1_7", "2_6"]
                },
                "activities": [
                    {
                        "name": "Banquete da Colheita",
                        "description": "Participe de um banquete para celebrar a colheita e compartilhar histórias."
                    },
                    {
                        "name": "Estudo dos Antigos",
                        "description": "Estude textos antigos para desbloquear conhecimentos perdidos."
                    }
                ]
            },
            "winter_solstice": {
                "name": "Solstício de Inverno",
                "description": "Um evento que celebra a introspecção e a renovação na Academia Tokugawa.",
                "season": "winter",
                "duration_days": 7,
                "requirements": {
                    "level": 20
                },
                "rewards": {
                    "exp": 1200,
                    "tusd": 500,
                    "special_item": "Cristal de Gelo Eterno"
                },
                "story_integration": {
                    "theme": "renovação",
                    "related_chapters": ["1_9", "2_8"]
                },
                "activities": [
                    {
                        "name": "Vigília das Luzes",
                        "description": "Participe de uma vigília para manter a luz durante a noite mais longa do ano."
                    },
                    {
                        "name": "Ritual de Purificação",
                        "description": "Purifique seu espírito e prepare-se para o novo ano."
                    }
                ]
            }
        }
        
        # Define default academy festivals
        self.default_academy_festivals = {
            "spring_festival": {
                "name": "Festival da Primavera",
                "description": "O maior festival da Academia Tokugawa, celebrando o início do ano acadêmico.",
                "season": "spring",
                "duration_days": 3,
                "requirements": {
                    "level": 5
                },
                "rewards": {
                    "exp": 1000,
                    "tusd": 500,
                    "faction_reputation": {
                        "academy_administration": 10,
                        "student_council": 15
                    }
                },
                "story_integration": {
                    "theme": "comunidade",
                    "related_chapters": ["1_2", "2_1"]
                },
                "activities": [
                    {
                        "name": "Desfile dos Clubes",
                        "description": "Assista ao desfile dos clubes da academia e descubra novas atividades."
                    },
                    {
                        "name": "Feira de Comidas",
                        "description": "Experimente pratos de diferentes regiões preparados pelos alunos."
                    }
                ],
                "mini_games": [
                    {
                        "id": "spring_archery",
                        "name": "Tiro com Arco da Primavera",
                        "description": "Teste sua precisão neste jogo de tiro com arco.",
                        "win_chance": 0.6,
                        "rewards": {
                            "exp": 200,
                            "tusd": 100
                        }
                    },
                    {
                        "id": "flower_arrangement",
                        "name": "Arranjo de Flores",
                        "description": "Crie o mais belo arranjo de flores para impressionar os juízes.",
                        "win_chance": 0.5,
                        "rewards": {
                            "exp": 150,
                            "tusd": 75,
                            "special_item": "Vaso de Flores Encantado"
                        }
                    }
                ],
                "exclusive_challenges": [
                    {
                        "id": "spring_duel",
                        "name": "Duelo da Primavera",
                        "description": "Enfrente um oponente poderoso em um duelo cerimonial.",
                        "requirements": {
                            "level": 10,
                            "power": {
                                "id": "elemental",
                                "level": 2
                            }
                        },
                        "success_chance": 0.4,
                        "rewards": {
                            "exp": 500,
                            "tusd": 250,
                            "power_points": 3,
                            "special_item": "Medalha do Duelo da Primavera"
                        }
                    }
                ]
            },
            "summer_games": {
                "name": "Jogos de Verão",
                "description": "Uma competição esportiva que testa as habilidades físicas e poderes dos estudantes.",
                "season": "summer",
                "duration_days": 5,
                "requirements": {
                    "level": 12
                },
                "rewards": {
                    "exp": 1500,
                    "tusd": 700,
                    "faction_reputation": {
                        "student_council": 20,
                        "faculty_council": 10
                    }
                },
                "story_integration": {
                    "theme": "competição",
                    "related_chapters": ["1_6", "2_5"]
                },
                "activities": [
                    {
                        "name": "Cerimônia de Abertura",
                        "description": "Assista à cerimônia de abertura com demonstrações de poderes impressionantes."
                    },
                    {
                        "name": "Competições por Equipe",
                        "description": "Forme uma equipe e compita em diversos eventos esportivos."
                    }
                ],
                "mini_games": [
                    {
                        "id": "power_sprint",
                        "name": "Corrida de Poderes",
                        "description": "Use seu poder para correr o mais rápido possível até a linha de chegada.",
                        "win_chance": 0.5,
                        "rewards": {
                            "exp": 300,
                            "tusd": 150
                        }
                    },
                    {
                        "id": "elemental_swimming",
                        "name": "Natação Elemental",
                        "description": "Nade através de um percurso enquanto supera obstáculos elementais.",
                        "win_chance": 0.4,
                        "rewards": {
                            "exp": 250,
                            "tusd": 125,
                            "special_item": "Medalha de Natação Elemental"
                        }
                    }
                ],
                "exclusive_challenges": [
                    {
                        "id": "power_triathlon",
                        "name": "Triatlo de Poderes",
                        "description": "Complete três provas consecutivas usando diferentes aspectos do seu poder.",
                        "requirements": {
                            "level": 15,
                            "power": {
                                "id": "physical",
                                "level": 3
                            }
                        },
                        "success_chance": 0.3,
                        "rewards": {
                            "exp": 800,
                            "tusd": 400,
                            "power_points": 5,
                            "special_item": "Troféu do Triatlo de Poderes"
                        }
                    }
                ]
            },
            "autumn_masquerade": {
                "name": "Baile de Máscaras de Outono",
                "description": "Um elegante baile de máscaras onde segredos são revelados e alianças são formadas.",
                "season": "autumn",
                "duration_days": 2,
                "requirements": {
                    "level": 18
                },
                "rewards": {
                    "exp": 1200,
                    "tusd": 600,
                    "faction_reputation": {
                        "academy_administration": 15,
                        "shadow_society": 10
                    }
                },
                "story_integration": {
                    "theme": "mistério",
                    "related_chapters": ["1_8", "2_7"]
                },
                "activities": [
                    {
                        "name": "Confecção de Máscaras",
                        "description": "Crie sua própria máscara mágica para usar no baile."
                    },
                    {
                        "name": "Dança Cerimonial",
                        "description": "Participe da dança cerimonial que abre o baile."
                    }
                ],
                "mini_games": [
                    {
                        "id": "mask_matching",
                        "name": "Combinação de Máscaras",
                        "description": "Encontre a pessoa com a máscara complementar à sua.",
                        "win_chance": 0.5,
                        "rewards": {
                            "exp": 200,
                            "tusd": 100
                        }
                    },
                    {
                        "id": "secret_exchange",
                        "name": "Troca de Segredos",
                        "description": "Troque segredos com outros participantes para desvendar um mistério.",
                        "win_chance": 0.4,
                        "rewards": {
                            "exp": 250,
                            "tusd": 125,
                            "special_item": "Pergaminho de Segredos"
                        }
                    }
                ],
                "exclusive_challenges": [
                    {
                        "id": "shadow_dance",
                        "name": "Dança das Sombras",
                        "description": "Participe de uma dança misteriosa que testa sua percepção e agilidade.",
                        "requirements": {
                            "level": 20,
                            "power": {
                                "id": "psychic",
                                "level": 3
                            }
                        },
                        "success_chance": 0.3,
                        "rewards": {
                            "exp": 700,
                            "tusd": 350,
                            "power_points": 4,
                            "special_item": "Máscara das Sombras"
                        }
                    }
                ]
            },
            "winter_gala": {
                "name": "Gala de Inverno",
                "description": "Uma celebração elegante que marca o fim do ano acadêmico com apresentações e premiações.",
                "season": "winter",
                "duration_days": 3,
                "requirements": {
                    "level": 25
                },
                "rewards": {
                    "exp": 2000,
                    "tusd": 1000,
                    "faction_reputation": {
                        "academy_administration": 25,
                        "faculty_council": 20,
                        "student_council": 15
                    }
                },
                "story_integration": {
                    "theme": "reconhecimento",
                    "related_chapters": ["1_10", "2_9"]
                },
                "activities": [
                    {
                        "name": "Cerimônia de Premiação",
                        "description": "Assista à cerimônia onde os melhores alunos são reconhecidos."
                    },
                    {
                        "name": "Apresentações de Poderes",
                        "description": "Veja apresentações impressionantes dos poderes mais avançados."
                    }
                ],
                "mini_games": [
                    {
                        "id": "ice_sculpture",
                        "name": "Escultura de Gelo",
                        "description": "Crie uma bela escultura de gelo usando seu poder.",
                        "win_chance": 0.5,
                        "rewards": {
                            "exp": 400,
                            "tusd": 200
                        }
                    },
                    {
                        "id": "formal_dance",
                        "name": "Dança Formal",
                        "description": "Demonstre sua elegância e graça na pista de dança.",
                        "win_chance": 0.6,
                        "rewards": {
                            "exp": 300,
                            "tusd": 150,
                            "special_item": "Broche da Gala de Inverno"
                        }
                    }
                ],
                "exclusive_challenges": [
                    {
                        "id": "power_showcase",
                        "name": "Demonstração de Poder",
                        "description": "Apresente seu poder para toda a academia em uma demonstração impressionante.",
                        "requirements": {
                            "level": 30,
                            "power": {
                                "id": "elemental",
                                "level": 4
                            }
                        },
                        "success_chance": 0.3,
                        "rewards": {
                            "exp": 1000,
                            "tusd": 500,
                            "power_points": 7,
                            "special_item": "Medalha de Excelência em Poder"
                        }
                    }
                ]
            }
        }
        
        # Define default weather events
        self.default_weather_events = {
            "spring_rain": {
                "name": "Chuva da Renovação",
                "description": "Uma chuva mágica que revitaliza poderes e revela segredos antigos.",
                "season": "spring",
                "duration_days": 2,
                "requirements": {
                    "level": 8
                },
                "rewards": {
                    "exp": 300,
                    "tusd": 150
                },
                "story_integration": {
                    "theme": "purificação",
                    "related_chapters": ["1_4", "2_3"]
                },
                "activities": [
                    {
                        "name": "Meditação na Chuva",
                        "description": "Medite sob a chuva para purificar seu espírito e fortalecer seu poder."
                    }
                ],
                "weather_type": "rain",
                "gameplay_effects": {
                    "stat_modifiers": {
                        "elemental_power": 1.2,
                        "physical_power": 0.9
                    },
                    "unlock_locations": ["Jardim da Chuva", "Caverna das Lágrimas"]
                },
                "exclusive_content": {
                    "special_items": ["Gota de Chuva Encantada", "Guarda-Chuva Dimensional"],
                    "quests": ["quest_rain_collection", "quest_water_elemental"]
                }
            },
            "summer_heatwave": {
                "name": "Onda de Calor Arcana",
                "description": "Uma onda de calor sobrenatural que intensifica poderes de fogo e enfraquece poderes de gelo.",
                "season": "summer",
                "duration_days": 3,
                "requirements": {
                    "level": 12
                },
                "rewards": {
                    "exp": 400,
                    "tusd": 200
                },
                "story_integration": {
                    "theme": "intensificação",
                    "related_chapters": ["1_6", "2_5"]
                },
                "activities": [
                    {
                        "name": "Treinamento no Calor",
                        "description": "Treine sob o calor intenso para fortalecer sua resistência."
                    }
                ],
                "weather_type": "heatwave",
                "gameplay_effects": {
                    "stat_modifiers": {
                        "fire_power": 1.5,
                        "ice_power": 0.7,
                        "stamina": 0.8
                    },
                    "unlock_locations": ["Deserto Arcano", "Forja Elemental"]
                },
                "exclusive_content": {
                    "special_items": ["Essência de Fogo Puro", "Amuleto de Resistência ao Calor"],
                    "quests": ["quest_fire_mastery", "quest_desert_survival"]
                }
            },
            "autumn_winds": {
                "name": "Ventos do Conhecimento",
                "description": "Ventos místicos que carregam fragmentos de conhecimento antigo e aumentam a percepção.",
                "season": "autumn",
                "duration_days": 2,
                "requirements": {
                    "level": 15
                },
                "rewards": {
                    "exp": 500,
                    "tusd": 250
                },
                "story_integration": {
                    "theme": "conhecimento",
                    "related_chapters": ["1_7", "2_6"]
                },
                "activities": [
                    {
                        "name": "Escuta dos Ventos",
                        "description": "Escute os segredos carregados pelos ventos para obter conhecimento."
                    }
                ],
                "weather_type": "windy",
                "gameplay_effects": {
                    "stat_modifiers": {
                        "perception": 1.3,
                        "air_power": 1.4,
                        "earth_power": 0.8
                    },
                    "unlock_locations": ["Torre dos Ventos", "Biblioteca Suspensa"]
                },
                "exclusive_content": {
                    "special_items": ["Pena do Vento Sábio", "Pergaminho Voador"],
                    "quests": ["quest_wind_whispers", "quest_ancient_knowledge"]
                }
            },
            "winter_blizzard": {
                "name": "Nevasca Temporal",
                "description": "Uma nevasca mágica que altera a percepção do tempo e revela caminhos ocultos.",
                "season": "winter",
                "duration_days": 4,
                "requirements": {
                    "level": 20
                },
                "rewards": {
                    "exp": 700,
                    "tusd": 350
                },
                "story_integration": {
                    "theme": "preservação",
                    "related_chapters": ["1_9", "2_8"]
                },
                "activities": [
                    {
                        "name": "Caminhada na Neve",
                        "description": "Caminhe através da nevasca para encontrar locais normalmente inacessíveis."
                    }
                ],
                "weather_type": "blizzard",
                "gameplay_effects": {
                    "stat_modifiers": {
                        "ice_power": 1.6,
                        "fire_power": 0.6,
                        "time_perception": 1.2
                    },
                    "unlock_locations": ["Caverna de Gelo Eterno", "Santuário Congelado"]
                },
                "exclusive_content": {
                    "special_items": ["Cristal de Tempo Congelado", "Capa da Nevasca"],
                    "quests": ["quest_frozen_memories", "quest_time_fragment"]
                }
            }
        }
        
        # Load default events
        self._load_default_events()
        
    def _load_default_events(self):
        """Loads the default seasonal events, academy festivals, and weather events."""
        # Load seasonal events
        for event_id, event_data in self.default_seasonal_events.items():
            self.register_seasonal_event(event_id, event_data)
            
        # Load academy festivals
        for festival_id, festival_data in self.default_academy_festivals.items():
            self.register_academy_festival(festival_id, festival_data)
            
        # Load weather events
        for weather_id, weather_data in self.default_weather_events.items():
            self.register_weather_event(weather_id, weather_data)
            
        logger.info(f"Loaded {len(self.seasonal_events)} seasonal events, {len(self.academy_festivals)} academy festivals, and {len(self.weather_events)} weather events")
        
    def register_seasonal_event(self, event_id: str, data: Dict[str, Any]) -> None:
        """
        Registers a seasonal event.
        
        Args:
            event_id: Unique identifier for the event
            data: Dictionary containing event data
        """
        self.seasonal_events[event_id] = SeasonalEvent(event_id, data)
        logger.info(f"Registered seasonal event: {data.get('name')} (ID: {event_id})")
        
    def register_academy_festival(self, festival_id: str, data: Dict[str, Any]) -> None:
        """
        Registers an academy festival.
        
        Args:
            festival_id: Unique identifier for the festival
            data: Dictionary containing festival data
        """
        self.academy_festivals[festival_id] = AcademyFestival(festival_id, data)
        logger.info(f"Registered academy festival: {data.get('name')} (ID: {festival_id})")
        
    def register_weather_event(self, weather_id: str, data: Dict[str, Any]) -> None:
        """
        Registers a weather event.
        
        Args:
            weather_id: Unique identifier for the weather event
            data: Dictionary containing weather event data
        """
        self.weather_events[weather_id] = WeatherEvent(weather_id, data)
        logger.info(f"Registered weather event: {data.get('name')} (ID: {weather_id})")
        
    def get_current_season_events(self, player_data: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Gets events available in the current season for a player.
        
        Args:
            player_data: Player data
            
        Returns:
            Dictionary mapping event types to lists of available events
        """
        current_season = Season.get_current_season()
        
        # Get available seasonal events
        available_seasonal_events = []
        for event_id, event in self.seasonal_events.items():
            if event.is_available(player_data, current_season):
                available_seasonal_events.append({
                    "id": event_id,
                    "name": event.get_name(),
                    "description": event.get_description(),
                    "season": event.get_season(),
                    "duration_days": event.get_duration_days(),
                    "activities": event.get_activities()
                })
                
        # Get available academy festivals
        available_festivals = []
        for festival_id, festival in self.academy_festivals.items():
            if festival.is_available(player_data, current_season):
                available_festivals.append({
                    "id": festival_id,
                    "name": festival.get_name(),
                    "description": festival.get_description(),
                    "season": festival.get_season(),
                    "duration_days": festival.get_duration_days(),
                    "activities": festival.get_activities(),
                    "mini_games": festival.get_mini_games(),
                    "exclusive_challenges": festival.get_exclusive_challenges()
                })
                
        # Get available weather events
        available_weather_events = []
        for weather_id, weather in self.weather_events.items():
            if weather.is_available(player_data, current_season):
                available_weather_events.append({
                    "id": weather_id,
                    "name": weather.get_name(),
                    "description": weather.get_description(),
                    "season": weather.get_season(),
                    "duration_days": weather.get_duration_days(),
                    "weather_type": weather.get_weather_type(),
                    "gameplay_effects": weather.get_gameplay_effects()
                })
                
        return {
            "seasonal_events": available_seasonal_events,
            "academy_festivals": available_festivals,
            "weather_events": available_weather_events
        }
        
    def participate_in_seasonal_event(self, player_data: Dict[str, Any], event_id: str) -> Dict[str, Any]:
        """
        Allows a player to participate in a seasonal event.
        
        Args:
            player_data: Player data
            event_id: ID of the seasonal event
            
        Returns:
            Updated player data and result information
        """
        if event_id in self.seasonal_events:
            event = self.seasonal_events[event_id]
            return event.participate(player_data)
        elif event_id in self.academy_festivals:
            festival = self.academy_festivals[event_id]
            return festival.participate(player_data)
        elif event_id in self.weather_events:
            weather = self.weather_events[event_id]
            return weather.apply_weather_effects(player_data)
        else:
            return {
                "player_data": player_data,
                "error": f"Event not found: {event_id}"
            }
            
    def participate_in_mini_game(self, player_data: Dict[str, Any], festival_id: str, mini_game_id: str) -> Dict[str, Any]:
        """
        Allows a player to participate in a mini-game at an academy festival.
        
        Args:
            player_data: Player data
            festival_id: ID of the academy festival
            mini_game_id: ID of the mini-game
            
        Returns:
            Updated player data and result information
        """
        if festival_id not in self.academy_festivals:
            return {
                "player_data": player_data,
                "error": f"Festival not found: {festival_id}"
            }
            
        festival = self.academy_festivals[festival_id]
        return festival.participate_in_mini_game(player_data, mini_game_id)
        
    def attempt_festival_challenge(self, player_data: Dict[str, Any], festival_id: str, challenge_id: str) -> Dict[str, Any]:
        """
        Allows a player to attempt an exclusive challenge at an academy festival.
        
        Args:
            player_data: Player data
            festival_id: ID of the academy festival
            challenge_id: ID of the challenge
            
        Returns:
            Updated player data and result information
        """
        if festival_id not in self.academy_festivals:
            return {
                "player_data": player_data,
                "error": f"Festival not found: {festival_id}"
            }
            
        festival = self.academy_festivals[festival_id]
        return festival.attempt_challenge(player_data, challenge_id)
        
    def get_seasonal_event_status(self, player_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Gets the status of a player's participation in seasonal events.
        
        Args:
            player_data: Player data
            
        Returns:
            Dictionary containing seasonal event status information
        """
        story_progress = player_data.get("story_progress", {})
        seasonal_events = story_progress.get("seasonal_events", {})
        
        participated_events = seasonal_events.get("participated_events", [])
        mini_games = seasonal_events.get("mini_games", {})
        challenges = seasonal_events.get("challenges", {})
        weather_events = seasonal_events.get("weather_events", {})
        
        # Format participated events
        formatted_events = []
        for event_id in participated_events:
            event = None
            if event_id in self.seasonal_events:
                event = self.seasonal_events[event_id]
            elif event_id in self.academy_festivals:
                event = self.academy_festivals[event_id]
                
            if event:
                formatted_events.append({
                    "id": event_id,
                    "name": event.get_name(),
                    "description": event.get_description(),
                    "season": event.get_season()
                })
                
        # Format mini-games
        formatted_mini_games = []
        for mini_game_id, mini_game_data in mini_games.items():
            # Find the festival that contains this mini-game
            for festival_id, festival in self.academy_festivals.items():
                for mini_game in festival.get_mini_games():
                    if mini_game.get("id") == mini_game_id:
                        formatted_mini_games.append({
                            "id": mini_game_id,
                            "name": mini_game.get("name"),
                            "description": mini_game.get("description"),
                            "festival": festival.get_name(),
                            "won": mini_game_data.get("won", False),
                            "timestamp": mini_game_data.get("timestamp")
                        })
                        break
                        
        # Format challenges
        formatted_challenges = []
        for challenge_id, challenge_data in challenges.items():
            # Find the festival that contains this challenge
            for festival_id, festival in self.academy_festivals.items():
                for challenge in festival.get_exclusive_challenges():
                    if challenge.get("id") == challenge_id:
                        formatted_challenges.append({
                            "id": challenge_id,
                            "name": challenge.get("name"),
                            "description": challenge.get("description"),
                            "festival": festival.get_name(),
                            "completed": challenge_data.get("completed", False),
                            "timestamp": challenge_data.get("timestamp")
                        })
                        break
                        
        # Format weather events
        formatted_weather_events = []
        for weather_id, weather_data in weather_events.items():
            weather = self.weather_events.get(weather_id)
            if weather:
                formatted_weather_events.append({
                    "id": weather_id,
                    "name": weather.get_name(),
                    "description": weather.get_description(),
                    "weather_type": weather.get_weather_type(),
                    "timestamp": weather_data.get("timestamp")
                })
                
        return {
            "current_season": Season.get_current_season().value,
            "participated_events": formatted_events,
            "mini_games": formatted_mini_games,
            "challenges": formatted_challenges,
            "weather_events": formatted_weather_events,
            "available_events": self.get_current_season_events(player_data)
        }