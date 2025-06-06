from typing import Dict, List, Any, Optional, Union
import json
import logging
import random
from datetime import datetime
from .interfaces import NPC
from .npc import BaseNPC

logger = logging.getLogger('tokugawa_bot')

class Companion(BaseNPC):
    """
    Represents a companion NPC that can accompany the player on certain chapters.
    Extends the BaseNPC class with companion-specific functionality.
    """
    def __init__(self, npc_id: str, data: Dict[str, Any]):
        """
        Initialize a companion with its data.

        Args:
            npc_id: Unique identifier for the companion
            data: Dictionary containing companion data
        """
        super().__init__(npc_id, data)
        self.power_type = data.get("power_type", "unknown")
        self.specialization = data.get("specialization", "balanced")
        self.story_arc = data.get("story_arc", {})
        self.sync_abilities = data.get("sync_abilities", [])
        self.available_chapters = data.get("available_chapters", [])
        self.recruited = False
        self.active = False
        self.arc_progress = 0

    def get_power_type(self) -> str:
        """Returns the companion's power type."""
        return self.power_type

    def get_specialization(self) -> str:
        """Returns the companion's specialization."""
        return self.specialization

    def get_story_arc(self) -> Dict[str, Any]:
        """Returns the companion's story arc data."""
        return self.story_arc

    def get_sync_abilities(self) -> List[Dict[str, Any]]:
        """Returns the companion's synchronization abilities."""
        return self.sync_abilities

    def get_available_chapters(self) -> List[str]:
        """Returns the chapters where this companion is available."""
        return self.available_chapters

    def is_recruited(self, player_data: Dict[str, Any]) -> bool:
        """
        Checks if the companion has been recruited by the player.

        Args:
            player_data: Player data

        Returns:
            True if recruited, False otherwise
        """
        companions = player_data.get("story_progress", {}).get("companions", {})
        return self.npc_id in companions and companions[self.npc_id].get("recruited", False)

    def is_active(self, player_data: Dict[str, Any]) -> bool:
        """
        Checks if the companion is currently active with the player.

        Args:
            player_data: Player data

        Returns:
            True if active, False otherwise
        """
        companions = player_data.get("story_progress", {}).get("companions", {})
        return self.npc_id in companions and companions[self.npc_id].get("active", False)

    def get_arc_progress(self, player_data: Dict[str, Any]) -> int:
        """
        Gets the companion's story arc progress.

        Args:
            player_data: Player data

        Returns:
            Story arc progress (0-100)
        """
        companions = player_data.get("story_progress", {}).get("companions", {})
        if self.npc_id in companions:
            return companions[self.npc_id].get("arc_progress", 0)
        return 0

    def recruit(self, player_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recruits the companion.

        Args:
            player_data: Player data

        Returns:
            Updated player data
        """
        story_progress = player_data.get("story_progress", {})

        if "companions" not in story_progress:
            story_progress["companions"] = {}

        # Check if already recruited
        if self.npc_id in story_progress["companions"] and story_progress["companions"][self.npc_id].get("recruited", False):
            return player_data

        # Initialize companion data
        story_progress["companions"][self.npc_id] = {
            "recruited": True,
            "active": False,
            "arc_progress": 0,
            "completed_missions": [],
            "sync_level": 1,
            "recruited_date": datetime.now().isoformat()
        }

        # Update player data
        player_data["story_progress"] = story_progress

        logger.info(f"Player {player_data.get('user_id')} recruited companion {self.name} (ID: {self.npc_id})")

        return player_data

    def activate(self, player_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Activates the companion to accompany the player.

        Args:
            player_data: Player data

        Returns:
            Updated player data
        """
        story_progress = player_data.get("story_progress", {})

        if "companions" not in story_progress or self.npc_id not in story_progress["companions"]:
            # Cannot activate a companion that hasn't been recruited
            return player_data

        # Check if already active
        if story_progress["companions"][self.npc_id].get("active", False):
            return player_data

        # Deactivate any currently active companions
        for companion_id in story_progress["companions"]:
            if story_progress["companions"][companion_id].get("active", False):
                story_progress["companions"][companion_id]["active"] = False

        # Activate this companion
        story_progress["companions"][self.npc_id]["active"] = True

        # Update player data
        player_data["story_progress"] = story_progress

        logger.info(f"Player {player_data.get('user_id')} activated companion {self.name} (ID: {self.npc_id})")

        return player_data

    def deactivate(self, player_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deactivates the companion.

        Args:
            player_data: Player data

        Returns:
            Updated player data
        """
        story_progress = player_data.get("story_progress", {})

        if "companions" not in story_progress or self.npc_id not in story_progress["companions"]:
            return player_data

        # Check if already inactive
        if not story_progress["companions"][self.npc_id].get("active", False):
            return player_data

        # Deactivate this companion
        story_progress["companions"][self.npc_id]["active"] = False

        # Update player data
        player_data["story_progress"] = story_progress

        logger.info(f"Player {player_data.get('user_id')} deactivated companion {self.name} (ID: {self.npc_id})")

        return player_data

    def advance_arc(self, player_data: Dict[str, Any], progress_amount: int) -> Dict[str, Any]:
        """
        Advances the companion's story arc.

        Args:
            player_data: Player data
            progress_amount: Amount to advance the arc progress

        Returns:
            Updated player data and result information
        """
        story_progress = player_data.get("story_progress", {})

        if "companions" not in story_progress or self.npc_id not in story_progress["companions"]:
            return {
                "player_data": player_data,
                "error": f"Companion not recruited: {self.name}"
            }

        # Get current progress
        current_progress = story_progress["companions"][self.npc_id].get("arc_progress", 0)
        new_progress = min(100, current_progress + progress_amount)

        # Update progress
        story_progress["companions"][self.npc_id]["arc_progress"] = new_progress

        # Check for milestone rewards
        milestone_rewards = {}
        arc_milestones = self.story_arc.get("milestones", {})

        for milestone_str, rewards in arc_milestones.items():
            milestone = int(milestone_str)
            if current_progress < milestone <= new_progress:
                # Apply rewards
                if "exp" in rewards:
                    player_data["exp"] = player_data.get("exp", 0) + rewards["exp"]
                    milestone_rewards["exp"] = rewards["exp"]

                if "tusd" in rewards:
                    player_data["tusd"] = player_data.get("tusd", 0) + rewards["tusd"]
                    milestone_rewards["tusd"] = rewards["tusd"]

                if "special_item" in rewards:
                    special_items = story_progress.get("special_items", [])
                    if rewards["special_item"] not in special_items:
                        special_items.append(rewards["special_item"])
                    story_progress["special_items"] = special_items
                    milestone_rewards["special_item"] = rewards["special_item"]

                if "sync_level_increase" in rewards:
                    current_sync_level = story_progress["companions"][self.npc_id].get("sync_level", 1)
                    new_sync_level = current_sync_level + rewards["sync_level_increase"]
                    story_progress["companions"][self.npc_id]["sync_level"] = new_sync_level
                    milestone_rewards["sync_level_increase"] = rewards["sync_level_increase"]
                    milestone_rewards["new_sync_level"] = new_sync_level

                logger.info(f"Player {player_data.get('user_id')} reached milestone {milestone} with companion {self.name}")

        # Update player data
        player_data["story_progress"] = story_progress

        return {
            "player_data": player_data,
            "success": True,
            "previous_progress": current_progress,
            "new_progress": new_progress,
            "milestone_rewards": milestone_rewards
        }

    def complete_mission(self, player_data: Dict[str, Any], mission_id: str) -> Dict[str, Any]:
        """
        Completes a mission in the companion's story arc.

        Args:
            player_data: Player data
            mission_id: ID of the mission to complete

        Returns:
            Updated player data and result information
        """
        story_progress = player_data.get("story_progress", {})

        if "companions" not in story_progress or self.npc_id not in story_progress["companions"]:
            return {
                "player_data": player_data,
                "error": f"Companion not recruited: {self.name}"
            }

        # Check if mission already completed
        completed_missions = story_progress["companions"][self.npc_id].get("completed_missions", [])
        if mission_id in completed_missions:
            return {
                "player_data": player_data,
                "error": f"Mission already completed: {mission_id}"
            }

        # Find the mission
        mission = None
        for m in self.story_arc.get("missions", []):
            if m.get("id") == mission_id:
                mission = m
                break

        if not mission:
            return {
                "player_data": player_data,
                "error": f"Mission not found: {mission_id}"
            }

        # Add to completed missions
        if "completed_missions" not in story_progress["companions"][self.npc_id]:
            story_progress["companions"][self.npc_id]["completed_missions"] = []

        story_progress["companions"][self.npc_id]["completed_missions"].append(mission_id)

        # Apply rewards
        rewards = mission.get("rewards", {})

        if "exp" in rewards:
            player_data["exp"] = player_data.get("exp", 0) + rewards["exp"]

        if "tusd" in rewards:
            player_data["tusd"] = player_data.get("tusd", 0) + rewards["tusd"]

        if "special_item" in rewards:
            special_items = story_progress.get("special_items", [])
            if rewards["special_item"] not in special_items:
                special_items.append(rewards["special_item"])
            story_progress["special_items"] = special_items

        if "arc_progress" in rewards:
            current_progress = story_progress["companions"][self.npc_id].get("arc_progress", 0)
            new_progress = min(100, current_progress + rewards["arc_progress"])
            story_progress["companions"][self.npc_id]["arc_progress"] = new_progress

        # Update player data
        player_data["story_progress"] = story_progress

        logger.info(f"Player {player_data.get('user_id')} completed mission {mission_id} with companion {self.name}")

        return {
            "player_data": player_data,
            "success": True,
            "mission_name": mission.get("name", "Unknown Mission"),
            "mission_description": mission.get("description", "No description available."),
            "rewards": rewards
        }

    def perform_sync(self, player_data: Dict[str, Any], ability_id: str) -> Dict[str, Any]:
        """
        Performs a synchronization ability with the player.

        Args:
            player_data: Player data
            ability_id: ID of the synchronization ability to perform

        Returns:
            Updated player data and result information
        """
        story_progress = player_data.get("story_progress", {})

        if "companions" not in story_progress or self.npc_id not in story_progress["companions"]:
            return {
                "player_data": player_data,
                "error": f"Companion not recruited: {self.name}"
            }

        # Check if companion is active
        if not story_progress["companions"][self.npc_id].get("active", False):
            return {
                "player_data": player_data,
                "error": f"Companion not active: {self.name}"
            }

        # Find the ability
        ability = None
        for a in self.sync_abilities:
            if a.get("id") == ability_id:
                ability = a
                break

        if not ability:
            return {
                "player_data": player_data,
                "error": f"Ability not found: {ability_id}"
            }

        # Check sync level requirement
        required_sync_level = ability.get("required_sync_level", 1)
        current_sync_level = story_progress["companions"][self.npc_id].get("sync_level", 1)

        if current_sync_level < required_sync_level:
            return {
                "player_data": player_data,
                "error": f"Sync level too low. Required: {required_sync_level}, Current: {current_sync_level}"
            }

        # Check cooldown
        if "sync_cooldowns" not in story_progress["companions"][self.npc_id]:
            story_progress["companions"][self.npc_id]["sync_cooldowns"] = {}

        cooldowns = story_progress["companions"][self.npc_id]["sync_cooldowns"]

        if ability_id in cooldowns:
            last_used = datetime.fromisoformat(cooldowns[ability_id])
            cooldown_hours = ability.get("cooldown_hours", 24)
            elapsed = datetime.now() - last_used

            if elapsed.total_seconds() < cooldown_hours * 3600:
                hours_remaining = cooldown_hours - (elapsed.total_seconds() / 3600)
                return {
                    "player_data": player_data,
                    "error": f"Ability on cooldown. {hours_remaining:.1f} hours remaining."
                }

        # Apply ability effects
        effects = ability.get("effects", {})
        applied_effects = {}

        if "stat_boost" in effects:
            # In a real implementation, these would be applied to gameplay
            # For now, we'll just record them
            applied_effects["stat_boost"] = effects["stat_boost"]

        if "power_boost" in effects:
            # Check if player has the power
            powers = story_progress.get("powers", {})
            power_id = effects["power_boost"].get("power_id")

            if power_id in powers:
                boost_amount = effects["power_boost"].get("amount", 0)
                powers[power_id]["power_points"] = powers[power_id].get("power_points", 0) + boost_amount
                applied_effects["power_boost"] = {
                    "power_id": power_id,
                    "amount": boost_amount
                }

        if "special_action" in effects:
            # Record the special action
            applied_effects["special_action"] = effects["special_action"]

        # Record cooldown
        story_progress["companions"][self.npc_id]["sync_cooldowns"][ability_id] = datetime.now().isoformat()

        # Update player data
        player_data["story_progress"] = story_progress

        logger.info(f"Player {player_data.get('user_id')} performed sync ability {ability.get('name')} with companion {self.name}")

        return {
            "player_data": player_data,
            "success": True,
            "ability_name": ability.get("name", "Unknown Ability"),
            "ability_description": ability.get("description", "No description available."),
            "applied_effects": applied_effects
        }


class CompanionSystem:
    """
    Main class for the companion system.
    Manages companions, their story arcs, and synchronization abilities.
    """
    def __init__(self):
        """Initialize the companion system."""
        self.companions = {}

        # Define default companions
        self.default_companions = {
            "akira_tanaka": {
                "name": "Akira Tanaka",
                "type": "student",
                "background": {
                    "age": 17,
                    "origin": "Tóquio, Japão",
                    "personality": "Determinado, leal, às vezes impulsivo"
                },
                "power_type": "elemental",
                "specialization": "fogo",
                "available_chapters": ["1_3", "1_5", "1_7", "2_2", "2_4", "2_6"],
                "affinity_thresholds": {
                    "hostile": -50,
                    "unfriendly": -20,
                    "neutral": 0,
                    "friendly": 20,
                    "close": 50,
                    "trusted": 80
                },
                "story_arc": {
                    "title": "Chamas da Verdade",
                    "description": "Akira busca descobrir a verdade sobre o desaparecimento de seu irmão mais velho, que era um estudante prodígio na Academia Tokugawa.",
                    "milestones": {
                        "25": {
                            "exp": 300,
                            "tusd": 150,
                            "sync_level_increase": 1
                        },
                        "50": {
                            "exp": 600,
                            "tusd": 300,
                            "special_item": "Amuleto de Fogo de Akira",
                            "sync_level_increase": 1
                        },
                        "75": {
                            "exp": 900,
                            "tusd": 450,
                            "sync_level_increase": 1
                        },
                        "100": {
                            "exp": 1500,
                            "tusd": 750,
                            "special_item": "Espada de Chamas Eternas",
                            "sync_level_increase": 1
                        }
                    },
                    "missions": [
                        {
                            "id": "akira_m1",
                            "name": "Pistas no Arquivo",
                            "description": "Ajude Akira a encontrar registros sobre seu irmão nos arquivos da academia.",
                            "rewards": {
                                "exp": 200,
                                "tusd": 100,
                                "arc_progress": 15
                            }
                        },
                        {
                            "id": "akira_m2",
                            "name": "Confronto com o Passado",
                            "description": "Acompanhe Akira em um confronto com um antigo rival de seu irmão.",
                            "rewards": {
                                "exp": 300,
                                "tusd": 150,
                                "arc_progress": 20
                            }
                        },
                        {
                            "id": "akira_m3",
                            "name": "Treinamento Intensivo",
                            "description": "Treine com Akira para ajudá-lo a dominar uma técnica avançada de fogo.",
                            "rewards": {
                                "exp": 400,
                                "tusd": 200,
                                "arc_progress": 25,
                                "special_item": "Luvas de Treinamento de Fogo"
                            }
                        },
                        {
                            "id": "akira_m4",
                            "name": "A Verdade nas Sombras",
                            "description": "Descubra a verdade sobre o desaparecimento do irmão de Akira.",
                            "rewards": {
                                "exp": 800,
                                "tusd": 400,
                                "arc_progress": 40,
                                "special_item": "Diário do Irmão de Akira"
                            }
                        }
                    ]
                },
                "sync_abilities": [
                    {
                        "id": "akira_sync1",
                        "name": "Chamas Gêmeas",
                        "description": "Combina o poder de fogo de Akira com o seu, aumentando significativamente o dano de fogo.",
                        "required_sync_level": 1,
                        "cooldown_hours": 24,
                        "effects": {
                            "stat_boost": {
                                "fire_damage": 1.5,
                                "fire_resistance": 1.3
                            }
                        }
                    },
                    {
                        "id": "akira_sync2",
                        "name": "Escudo Flamejante",
                        "description": "Akira cria um escudo de fogo que protege vocês dois de ataques.",
                        "required_sync_level": 2,
                        "cooldown_hours": 48,
                        "effects": {
                            "stat_boost": {
                                "defense": 2.0,
                                "fire_resistance": 3.0
                            }
                        }
                    },
                    {
                        "id": "akira_sync3",
                        "name": "Inferno Concentrado",
                        "description": "Combina seus poderes para criar uma explosão de fogo concentrada de incrível poder.",
                        "required_sync_level": 3,
                        "cooldown_hours": 72,
                        "effects": {
                            "power_boost": {
                                "power_id": "elemental",
                                "amount": 5
                            },
                            "special_action": {
                                "type": "attack",
                                "damage_multiplier": 3.0,
                                "area_effect": True
                            }
                        }
                    },
                    {
                        "id": "akira_sync4",
                        "name": "Fênix Renascida",
                        "description": "Em situações críticas, Akira pode sacrificar sua própria energia para restaurar a sua.",
                        "required_sync_level": 4,
                        "cooldown_hours": 168,
                        "effects": {
                            "special_action": {
                                "type": "heal",
                                "heal_percentage": 100,
                                "revive": True
                            }
                        }
                    }
                ]
            },
            "mei_lin": {
                "name": "Mei Lin",
                "type": "student",
                "background": {
                    "age": 16,
                    "origin": "Hong Kong, China",
                    "personality": "Inteligente, estratégica, reservada"
                },
                "power_type": "psychic",
                "specialization": "telecinese",
                "available_chapters": ["1_4", "1_6", "1_8", "2_3", "2_5", "2_7"],
                "affinity_thresholds": {
                    "hostile": -50,
                    "unfriendly": -20,
                    "neutral": 0,
                    "friendly": 20,
                    "close": 50,
                    "trusted": 80
                },
                "story_arc": {
                    "title": "Mente Dividida",
                    "description": "Mei Lin luta para controlar seus poderes psíquicos cada vez mais fortes, enquanto descobre segredos sobre sua própria família.",
                    "milestones": {
                        "25": {
                            "exp": 300,
                            "tusd": 150,
                            "sync_level_increase": 1
                        },
                        "50": {
                            "exp": 600,
                            "tusd": 300,
                            "special_item": "Cristal Psíquico de Mei",
                            "sync_level_increase": 1
                        },
                        "75": {
                            "exp": 900,
                            "tusd": 450,
                            "sync_level_increase": 1
                        },
                        "100": {
                            "exp": 1500,
                            "tusd": 750,
                            "special_item": "Tiara da Clareza Mental",
                            "sync_level_increase": 1
                        }
                    },
                    "missions": [
                        {
                            "id": "mei_m1",
                            "name": "Controle Mental",
                            "description": "Ajude Mei a praticar técnicas de meditação para controlar seus poderes.",
                            "rewards": {
                                "exp": 200,
                                "tusd": 100,
                                "arc_progress": 15
                            }
                        },
                        {
                            "id": "mei_m2",
                            "name": "Carta Misteriosa",
                            "description": "Investigue uma carta enigmática que Mei recebeu de sua família.",
                            "rewards": {
                                "exp": 300,
                                "tusd": 150,
                                "arc_progress": 20
                            }
                        },
                        {
                            "id": "mei_m3",
                            "name": "Bloqueio Psíquico",
                            "description": "Ajude Mei a superar um bloqueio psíquico que está limitando seus poderes.",
                            "rewards": {
                                "exp": 400,
                                "tusd": 200,
                                "arc_progress": 25,
                                "special_item": "Incenso da Clareza Mental"
                            }
                        },
                        {
                            "id": "mei_m4",
                            "name": "Legado Familiar",
                            "description": "Descubra a verdade sobre o legado psíquico da família de Mei.",
                            "rewards": {
                                "exp": 800,
                                "tusd": 400,
                                "arc_progress": 40,
                                "special_item": "Grimório da Família Lin"
                            }
                        }
                    ]
                },
                "sync_abilities": [
                    {
                        "id": "mei_sync1",
                        "name": "Vínculo Mental",
                        "description": "Mei estabelece um vínculo mental com você, permitindo comunicação telepática e percepção aprimorada.",
                        "required_sync_level": 1,
                        "cooldown_hours": 24,
                        "effects": {
                            "stat_boost": {
                                "perception": 2.0,
                                "mental_resistance": 1.5
                            }
                        }
                    },
                    {
                        "id": "mei_sync2",
                        "name": "Barreira Psíquica",
                        "description": "Mei cria uma barreira psíquica que protege vocês dois de ataques mentais e físicos.",
                        "required_sync_level": 2,
                        "cooldown_hours": 48,
                        "effects": {
                            "stat_boost": {
                                "defense": 1.8,
                                "mental_resistance": 3.0
                            }
                        }
                    },
                    {
                        "id": "mei_sync3",
                        "name": "Impacto Psicocinético",
                        "description": "Combina seus poderes para criar uma onda de força telecinética devastadora.",
                        "required_sync_level": 3,
                        "cooldown_hours": 72,
                        "effects": {
                            "power_boost": {
                                "power_id": "psychic",
                                "amount": 5
                            },
                            "special_action": {
                                "type": "attack",
                                "damage_multiplier": 2.5,
                                "stun_chance": 0.7
                            }
                        }
                    },
                    {
                        "id": "mei_sync4",
                        "name": "Transcendência Mental",
                        "description": "Mei amplifica temporariamente suas habilidades mentais, permitindo façanhas psíquicas extraordinárias.",
                        "required_sync_level": 4,
                        "cooldown_hours": 168,
                        "effects": {
                            "stat_boost": {
                                "all_stats": 2.0
                            },
                            "special_action": {
                                "type": "utility",
                                "duration_minutes": 30,
                                "see_hidden": True,
                                "predict_future": True
                            }
                        }
                    }
                ]
            },
            "carlos_silva": {
                "name": "Carlos Silva",
                "type": "student",
                "background": {
                    "age": 18,
                    "origin": "Rio de Janeiro, Brasil",
                    "personality": "Extrovertido, corajoso, protetor"
                },
                "power_type": "physical",
                "specialization": "força",
                "available_chapters": ["1_2", "1_5", "1_9", "2_1", "2_4", "2_8"],
                "affinity_thresholds": {
                    "hostile": -50,
                    "unfriendly": -20,
                    "neutral": 0,
                    "friendly": 20,
                    "close": 50,
                    "trusted": 80
                },
                "story_arc": {
                    "title": "Coração de Campeão",
                    "description": "Carlos busca se tornar o campeão da academia enquanto lida com a responsabilidade de proteger sua família no Brasil.",
                    "milestones": {
                        "25": {
                            "exp": 300,
                            "tusd": 150,
                            "sync_level_increase": 1
                        },
                        "50": {
                            "exp": 600,
                            "tusd": 300,
                            "special_item": "Luvas de Treino de Carlos",
                            "sync_level_increase": 1
                        },
                        "75": {
                            "exp": 900,
                            "tusd": 450,
                            "sync_level_increase": 1
                        },
                        "100": {
                            "exp": 1500,
                            "tusd": 750,
                            "special_item": "Cinturão do Campeão",
                            "sync_level_increase": 1
                        }
                    },
                    "missions": [
                        {
                            "id": "carlos_m1",
                            "name": "Treinamento Matinal",
                            "description": "Participe da rotina de treinamento intensivo de Carlos.",
                            "rewards": {
                                "exp": 200,
                                "tusd": 100,
                                "arc_progress": 15
                            }
                        },
                        {
                            "id": "carlos_m2",
                            "name": "Notícias de Casa",
                            "description": "Ajude Carlos a lidar com notícias preocupantes de sua família no Brasil.",
                            "rewards": {
                                "exp": 300,
                                "tusd": 150,
                                "arc_progress": 20
                            }
                        },
                        {
                            "id": "carlos_m3",
                            "name": "Desafio do Campeão",
                            "description": "Apoie Carlos em seu desafio contra o atual campeão da academia.",
                            "rewards": {
                                "exp": 400,
                                "tusd": 200,
                                "arc_progress": 25,
                                "special_item": "Bandana da Determinação"
                            }
                        },
                        {
                            "id": "carlos_m4",
                            "name": "Família em Perigo",
                            "description": "Ajude Carlos a proteger sua família de uma ameaça misteriosa.",
                            "rewards": {
                                "exp": 800,
                                "tusd": 400,
                                "arc_progress": 40,
                                "special_item": "Amuleto Protetor da Família Silva"
                            }
                        }
                    ]
                },
                "sync_abilities": [
                    {
                        "id": "carlos_sync1",
                        "name": "Força Combinada",
                        "description": "Carlos amplifica sua força física, permitindo feitos de força extraordinários.",
                        "required_sync_level": 1,
                        "cooldown_hours": 24,
                        "effects": {
                            "stat_boost": {
                                "strength": 2.0,
                                "stamina": 1.5
                            }
                        }
                    },
                    {
                        "id": "carlos_sync2",
                        "name": "Defesa Impenetrável",
                        "description": "Carlos usa sua técnica defensiva para tornar vocês dois praticamente invulneráveis por um curto período.",
                        "required_sync_level": 2,
                        "cooldown_hours": 48,
                        "effects": {
                            "stat_boost": {
                                "defense": 3.0,
                                "damage_reduction": 0.7
                            }
                        }
                    },
                    {
                        "id": "carlos_sync3",
                        "name": "Impacto Devastador",
                        "description": "Combina seus poderes para um ataque físico de força incrível que pode derrubar obstáculos massivos.",
                        "required_sync_level": 3,
                        "cooldown_hours": 72,
                        "effects": {
                            "power_boost": {
                                "power_id": "physical",
                                "amount": 5
                            },
                            "special_action": {
                                "type": "attack",
                                "damage_multiplier": 3.5,
                                "knockback": True
                            }
                        }
                    },
                    {
                        "id": "carlos_sync4",
                        "name": "Espírito Inquebrável",
                        "description": "Carlos compartilha seu espírito indomável, tornando vocês dois imunes a efeitos de controle e aumentando drasticamente a recuperação.",
                        "required_sync_level": 4,
                        "cooldown_hours": 168,
                        "effects": {
                            "stat_boost": {
                                "stamina": 3.0,
                                "recovery_rate": 5.0
                            },
                            "special_action": {
                                "type": "utility",
                                "duration_minutes": 60,
                                "immune_to_control": True,
                                "health_regen": True
                            }
                        }
                    }
                ]
            }
        }

        # Load default companions
        self._load_default_companions()

    def _load_default_companions(self):
        """Loads the default companions."""
        for companion_id, companion_data in self.default_companions.items():
            self.register_companion(companion_id, companion_data)

        logger.info(f"Loaded {len(self.companions)} companions")

    def register_companion(self, companion_id: str, data: Dict[str, Any]) -> None:
        """
        Registers a companion.

        Args:
            companion_id: Unique identifier for the companion
            data: Dictionary containing companion data
        """
        self.companions[companion_id] = Companion(companion_id, data)
        logger.info(f"Registered companion: {data.get('name')} (ID: {companion_id})")

    def get_companion(self, companion_id: str) -> Optional[Companion]:
        """
        Gets a companion by ID.

        Args:
            companion_id: ID of the companion

        Returns:
            Companion object or None if not found
        """
        return self.companions.get(companion_id)

    def get_companion_by_name(self, name: str) -> Optional[Companion]:
        """
        Gets a companion by name.

        Args:
            name: Name of the companion

        Returns:
            Companion object or None if not found
        """
        for companion in self.companions.values():
            if companion.get_name() == name:
                return companion
        return None

    def get_all_companions(self) -> List[Companion]:
        """
        Gets all registered companions.

        Returns:
            List of all companions
        """
        return list(self.companions.values())

    def get_available_companions(self, player_data: Dict[str, Any], chapter_id: str) -> List[Dict[str, Any]]:
        """
        Gets companions available for recruitment in the current chapter.

        Args:
            player_data: Player data
            chapter_id: Current chapter ID

        Returns:
            List of available companions
        """
        available_companions = []

        for companion_id, companion in self.companions.items():
            # Check if companion is available in this chapter
            if chapter_id in companion.get_available_chapters():
                # Check if already recruited
                if not companion.is_recruited(player_data):
                    available_companions.append({
                        "id": companion_id,
                        "name": companion.get_name(),
                        "power_type": companion.get_power_type(),
                        "specialization": companion.get_specialization(),
                        "background": companion.get_background()
                    })

        return available_companions

    def get_recruited_companions(self, player_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Gets companions that have been recruited by the player.

        Args:
            player_data: Player data

        Returns:
            List of recruited companions
        """
        recruited_companions = []
        companions_data = player_data.get("story_progress", {}).get("companions", {})

        for companion_id, companion_data in companions_data.items():
            if companion_data.get("recruited", False):
                companion = self.get_companion(companion_id)
                if companion:
                    recruited_companions.append({
                        "id": companion_id,
                        "name": companion.get_name(),
                        "power_type": companion.get_power_type(),
                        "specialization": companion.get_specialization(),
                        "active": companion_data.get("active", False),
                        "arc_progress": companion_data.get("arc_progress", 0),
                        "sync_level": companion_data.get("sync_level", 1)
                    })

        return recruited_companions

    def get_active_companion(self, player_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Gets the currently active companion.

        Args:
            player_data: Player data

        Returns:
            Active companion data or None if no active companion
        """
        companions_data = player_data.get("story_progress", {}).get("companions", {})

        for companion_id, companion_data in companions_data.items():
            if companion_data.get("active", False):
                companion = self.get_companion(companion_id)
                if companion:
                    return {
                        "id": companion_id,
                        "name": companion.get_name(),
                        "power_type": companion.get_power_type(),
                        "specialization": companion.get_specialization(),
                        "arc_progress": companion_data.get("arc_progress", 0),
                        "sync_level": companion_data.get("sync_level", 1),
                        "available_sync_abilities": self.get_available_sync_abilities(player_data, companion_id)
                    }

        return None

    def recruit_companion(self, player_data: Dict[str, Any], companion_id: str) -> Dict[str, Any]:
        """
        Recruits a companion.

        Args:
            player_data: Player data
            companion_id: ID of the companion to recruit

        Returns:
            Updated player data and result information
        """
        companion = self.get_companion(companion_id)

        if not companion:
            return {
                "player_data": player_data,
                "error": f"Companion not found: {companion_id}"
            }

        # Check if already recruited
        if companion.is_recruited(player_data):
            return {
                "player_data": player_data,
                "error": f"Companion already recruited: {companion.get_name()}"
            }

        # Recruit the companion
        updated_player_data = companion.recruit(player_data)

        return {
            "player_data": updated_player_data,
            "success": True,
            "message": f"Você recrutou {companion.get_name()} como seu companheiro!",
            "companion_info": {
                "id": companion_id,
                "name": companion.get_name(),
                "power_type": companion.get_power_type(),
                "specialization": companion.get_specialization()
            }
        }

    def activate_companion(self, player_data: Dict[str, Any], companion_id: str) -> Dict[str, Any]:
        """
        Activates a companion.

        Args:
            player_data: Player data
            companion_id: ID of the companion to activate

        Returns:
            Updated player data and result information
        """
        companion = self.get_companion(companion_id)

        if not companion:
            return {
                "player_data": player_data,
                "error": f"Companion not found: {companion_id}"
            }

        # Check if recruited
        if not companion.is_recruited(player_data):
            return {
                "player_data": player_data,
                "error": f"Companion not recruited: {companion.get_name()}"
            }

        # Check if already active
        if companion.is_active(player_data):
            return {
                "player_data": player_data,
                "error": f"Companion already active: {companion.get_name()}"
            }

        # Activate the companion
        updated_player_data = companion.activate(player_data)

        return {
            "player_data": updated_player_data,
            "success": True,
            "message": f"{companion.get_name()} agora está ativo e acompanhando você!",
            "companion_info": {
                "id": companion_id,
                "name": companion.get_name(),
                "power_type": companion.get_power_type(),
                "specialization": companion.get_specialization(),
                "available_sync_abilities": self.get_available_sync_abilities(updated_player_data, companion_id)
            }
        }

    def deactivate_companion(self, player_data: Dict[str, Any], companion_id: str) -> Dict[str, Any]:
        """
        Deactivates a companion.

        Args:
            player_data: Player data
            companion_id: ID of the companion to deactivate

        Returns:
            Updated player data and result information
        """
        companion = self.get_companion(companion_id)

        if not companion:
            return {
                "player_data": player_data,
                "error": f"Companion not found: {companion_id}"
            }

        # Check if recruited
        if not companion.is_recruited(player_data):
            return {
                "player_data": player_data,
                "error": f"Companion not recruited: {companion.get_name()}"
            }

        # Check if active
        if not companion.is_active(player_data):
            return {
                "player_data": player_data,
                "error": f"Companion not active: {companion.get_name()}"
            }

        # Deactivate the companion
        updated_player_data = companion.deactivate(player_data)

        return {
            "player_data": updated_player_data,
            "success": True,
            "message": f"{companion.get_name()} não está mais acompanhando você."
        }

    def advance_companion_arc(self, player_data: Dict[str, Any], companion_id: str, progress_amount: int) -> Dict[str, Any]:
        """
        Advances a companion's story arc.

        Args:
            player_data: Player data
            companion_id: ID of the companion
            progress_amount: Amount to advance the arc progress

        Returns:
            Updated player data and result information
        """
        companion = self.get_companion(companion_id)

        if not companion:
            return {
                "player_data": player_data,
                "error": f"Companion not found: {companion_id}"
            }

        # Check if recruited
        if not companion.is_recruited(player_data):
            return {
                "player_data": player_data,
                "error": f"Companion not recruited: {companion.get_name()}"
            }

        # Advance the arc
        return companion.advance_arc(player_data, progress_amount)

    def complete_companion_mission(self, player_data: Dict[str, Any], companion_id: str, mission_id: str) -> Dict[str, Any]:
        """
        Completes a mission in a companion's story arc.

        Args:
            player_data: Player data
            companion_id: ID of the companion
            mission_id: ID of the mission to complete

        Returns:
            Updated player data and result information
        """
        companion = self.get_companion(companion_id)

        if not companion:
            return {
                "player_data": player_data,
                "error": f"Companion not found: {companion_id}"
            }

        # Check if recruited
        if not companion.is_recruited(player_data):
            return {
                "player_data": player_data,
                "error": f"Companion not recruited: {companion.get_name()}"
            }

        # Complete the mission
        return companion.complete_mission(player_data, mission_id)

    def get_available_sync_abilities(self, player_data: Dict[str, Any], companion_id: str) -> List[Dict[str, Any]]:
        """
        Gets synchronization abilities available for a companion.

        Args:
            player_data: Player data
            companion_id: ID of the companion

        Returns:
            List of available sync abilities
        """
        companion = self.get_companion(companion_id)

        if not companion or not companion.is_recruited(player_data):
            return []

        # Get companion data
        companions_data = player_data.get("story_progress", {}).get("companions", {})
        companion_data = companions_data.get(companion_id, {})
        sync_level = companion_data.get("sync_level", 1)

        # Get cooldowns
        cooldowns = companion_data.get("sync_cooldowns", {})

        # Filter abilities by sync level and cooldown
        available_abilities = []
        for ability in companion.get_sync_abilities():
            if ability.get("required_sync_level", 1) <= sync_level:
                ability_id = ability.get("id")
                on_cooldown = False

                if ability_id in cooldowns:
                    last_used = datetime.fromisoformat(cooldowns[ability_id])
                    cooldown_hours = ability.get("cooldown_hours", 24)
                    elapsed = datetime.now() - last_used

                    if elapsed.total_seconds() < cooldown_hours * 3600:
                        on_cooldown = True
                        hours_remaining = cooldown_hours - (elapsed.total_seconds() / 3600)

                available_abilities.append({
                    "id": ability_id,
                    "name": ability.get("name"),
                    "description": ability.get("description"),
                    "on_cooldown": on_cooldown,
                    "hours_remaining": hours_remaining if on_cooldown else 0
                })

        return available_abilities

    def perform_sync_ability(self, player_data: Dict[str, Any], companion_id: str, ability_id: str) -> Dict[str, Any]:
        """
        Performs a synchronization ability with a companion.

        Args:
            player_data: Player data
            companion_id: ID of the companion
            ability_id: ID of the sync ability to perform

        Returns:
            Updated player data and result information
        """
        companion = self.get_companion(companion_id)

        if not companion:
            return {
                "player_data": player_data,
                "error": f"Companion not found: {companion_id}"
            }

        # Check if recruited
        if not companion.is_recruited(player_data):
            return {
                "player_data": player_data,
                "error": f"Companion not recruited: {companion.get_name()}"
            }

        # Perform the sync
        return companion.perform_sync(player_data, ability_id)

    def get_companion_status(self, player_data: Dict[str, Any], companion_id: str) -> Dict[str, Any]:
        """
        Gets detailed status information for a companion.

        Args:
            player_data: Player data
            companion_id: ID of the companion

        Returns:
            Dictionary containing companion status information
        """
        companion = self.get_companion(companion_id)

        if not companion:
            return {
                "error": f"Companion not found: {companion_id}"
            }

        # Check if recruited
        if not companion.is_recruited(player_data):
            return {
                "error": f"Companion not recruited: {companion.get_name()}"
            }

        # Get companion data
        companions_data = player_data.get("story_progress", {}).get("companions", {})
        companion_data = companions_data.get(companion_id, {})

        # Get completed missions
        completed_missions = companion_data.get("completed_missions", [])

        # Format missions
        available_missions = []
        completed_mission_data = []

        for mission in companion.get_story_arc().get("missions", []):
            mission_id = mission.get("id")
            mission_info = {
                "id": mission_id,
                "name": mission.get("name"),
                "description": mission.get("description")
            }

            if mission_id in completed_missions:
                completed_mission_data.append(mission_info)
            else:
                available_missions.append(mission_info)

        # Get sync abilities
        sync_abilities = self.get_available_sync_abilities(player_data, companion_id)

        return {
            "id": companion_id,
            "name": companion.get_name(),
            "power_type": companion.get_power_type(),
            "specialization": companion.get_specialization(),
            "background": companion.get_background(),
            "active": companion_data.get("active", False),
            "arc_progress": companion_data.get("arc_progress", 0),
            "sync_level": companion_data.get("sync_level", 1),
            "story_arc": {
                "title": companion.get_story_arc().get("title"),
                "description": companion.get_story_arc().get("description")
            },
            "available_missions": available_missions,
            "completed_missions": completed_mission_data,
            "available_sync_abilities": sync_abilities
        }
