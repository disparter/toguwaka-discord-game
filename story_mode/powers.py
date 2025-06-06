from typing import Dict, List, Any, Optional, Union
import json
import logging
from datetime import datetime

logger = logging.getLogger('tokugawa_bot')

class PowerType:
    """
    Represents a type of power in the game.
    """
    def __init__(self, power_id: str, data: Dict[str, Any]):
        """
        Initialize a power type.

        Args:
            power_id: Unique identifier for the power type
            data: Dictionary containing power type data
        """
        self.power_id = power_id
        self.name = data.get("name", "Unknown Power")
        self.description = data.get("description", "No description available.")
        self.element = data.get("element", "neutral")
        self.skill_tree = data.get("skill_tree", {})
        self.awakening_rituals = data.get("awakening_rituals", {})
        self.challenges = data.get("challenges", {})

    def get_name(self) -> str:
        """Returns the power type name."""
        return self.name

    def get_description(self) -> str:
        """Returns the power type description."""
        return self.description

    def get_element(self) -> str:
        """Returns the power type element."""
        return self.element

    def get_skill_tree(self) -> Dict[str, Any]:
        """Returns the power type skill tree."""
        return self.skill_tree

    def get_awakening_rituals(self) -> Dict[str, Any]:
        """Returns the power type awakening rituals."""
        return self.awakening_rituals

    def get_challenges(self) -> Dict[str, Any]:
        """Returns the power type challenges."""
        return self.challenges


class SkillNode:
    """
    Represents a node in a power's skill tree.
    """
    def __init__(self, node_id: str, data: Dict[str, Any]):
        """
        Initialize a skill node.

        Args:
            node_id: Unique identifier for the skill node
            data: Dictionary containing skill node data
        """
        self.node_id = node_id
        self.name = data.get("name", "Unknown Skill")
        self.description = data.get("description", "No description available.")
        self.level = data.get("level", 1)
        self.prerequisites = data.get("prerequisites", [])
        self.effects = data.get("effects", {})
        self.cost = data.get("cost", {"power_points": 1})

    def get_name(self) -> str:
        """Returns the skill node name."""
        return self.name

    def get_description(self) -> str:
        """Returns the skill node description."""
        return self.description

    def get_level(self) -> int:
        """Returns the skill node level."""
        return self.level

    def get_prerequisites(self) -> List[str]:
        """Returns the skill node prerequisites."""
        return self.prerequisites

    def get_effects(self) -> Dict[str, Any]:
        """Returns the skill node effects."""
        return self.effects

    def get_cost(self) -> Dict[str, Any]:
        """Returns the skill node cost."""
        return self.cost

    def can_unlock(self, unlocked_nodes: List[str]) -> bool:
        """
        Checks if the skill node can be unlocked.

        Args:
            unlocked_nodes: List of already unlocked node IDs

        Returns:
            True if the node can be unlocked, False otherwise
        """
        # Check if all prerequisites are unlocked
        for prereq in self.prerequisites:
            if prereq not in unlocked_nodes:
                return False

        return True


class AwakeningRitual:
    """
    Represents a ritual to unlock advanced power abilities.
    """
    def __init__(self, ritual_id: str, data: Dict[str, Any]):
        """
        Initialize an awakening ritual.

        Args:
            ritual_id: Unique identifier for the ritual
            data: Dictionary containing ritual data
        """
        self.ritual_id = ritual_id
        self.name = data.get("name", "Unknown Ritual")
        self.description = data.get("description", "No description available.")
        self.requirements = data.get("requirements", {})
        self.effects = data.get("effects", {})
        self.unlocks = data.get("unlocks", [])

    def get_name(self) -> str:
        """Returns the ritual name."""
        return self.name

    def get_description(self) -> str:
        """Returns the ritual description."""
        return self.description

    def get_requirements(self) -> Dict[str, Any]:
        """Returns the ritual requirements."""
        return self.requirements

    def get_effects(self) -> Dict[str, Any]:
        """Returns the ritual effects."""
        return self.effects

    def get_unlocks(self) -> List[str]:
        """Returns the nodes unlocked by the ritual."""
        return self.unlocks

    def can_perform(self, player_data: Dict[str, Any], power_progress: Dict[str, Any]) -> bool:
        """
        Checks if the ritual can be performed.

        Args:
            player_data: Player data
            power_progress: Player's power progress

        Returns:
            True if the ritual can be performed, False otherwise
        """
        # Check level requirement
        if "level" in self.requirements and player_data.get("level", 1) < self.requirements["level"]:
            return False

        # Check power level requirement
        if "power_level" in self.requirements and power_progress.get("level", 1) < self.requirements["power_level"]:
            return False

        # Check unlocked skills requirement
        if "required_skills" in self.requirements:
            unlocked_nodes = power_progress.get("unlocked_nodes", [])
            for skill in self.requirements["required_skills"]:
                if skill not in unlocked_nodes:
                    return False

        # Check items requirement
        if "required_items" in self.requirements:
            special_items = player_data.get("story_progress", {}).get("special_items", [])
            for item in self.requirements["required_items"]:
                if item not in special_items:
                    return False

        # Check faction reputation requirement
        if "faction_reputation" in self.requirements:
            faction_reputation = player_data.get("story_progress", {}).get("faction_reputation", {})
            for faction, min_rep in self.requirements["faction_reputation"].items():
                if faction not in faction_reputation or faction_reputation[faction] < min_rep:
                    return False

        return True


class PowerChallenge:
    """
    Represents a challenge to test mastery of a power.
    """
    def __init__(self, challenge_id: str, data: Dict[str, Any]):
        """
        Initialize a power challenge.

        Args:
            challenge_id: Unique identifier for the challenge
            data: Dictionary containing challenge data
        """
        self.challenge_id = challenge_id
        self.name = data.get("name", "Unknown Challenge")
        self.description = data.get("description", "No description available.")
        self.requirements = data.get("requirements", {})
        self.rewards = data.get("rewards", {})
        self.difficulty = data.get("difficulty", "normal")

    def get_name(self) -> str:
        """Returns the challenge name."""
        return self.name

    def get_description(self) -> str:
        """Returns the challenge description."""
        return self.description

    def get_requirements(self) -> Dict[str, Any]:
        """Returns the challenge requirements."""
        return self.requirements

    def get_rewards(self) -> Dict[str, Any]:
        """Returns the challenge rewards."""
        return self.rewards

    def get_difficulty(self) -> str:
        """Returns the challenge difficulty."""
        return self.difficulty

    def can_attempt(self, player_data: Dict[str, Any], power_progress: Dict[str, Any]) -> bool:
        """
        Checks if the challenge can be attempted.

        Args:
            player_data: Player data
            power_progress: Player's power progress

        Returns:
            True if the challenge can be attempted, False otherwise
        """
        # Check level requirement
        if "level" in self.requirements and player_data.get("level", 1) < self.requirements["level"]:
            return False

        # Check power level requirement
        if "power_level" in self.requirements and power_progress.get("level", 1) < self.requirements["power_level"]:
            return False

        # Check unlocked skills requirement
        if "required_skills" in self.requirements:
            unlocked_nodes = power_progress.get("unlocked_nodes", [])
            for skill in self.requirements["required_skills"]:
                if skill not in unlocked_nodes:
                    return False

        # Check completed rituals requirement
        if "completed_rituals" in self.requirements:
            completed_rituals = power_progress.get("completed_rituals", [])
            for ritual in self.requirements["completed_rituals"]:
                if ritual not in completed_rituals:
                    return False

        return True


class PowerEvolutionSystem:
    """
    Main class for the power evolution system.
    Manages power types, skill trees, awakening rituals, and challenges.
    """
    def __init__(self):
        """Initialize the power evolution system."""
        self.power_types = {}
        self.skill_nodes = {}
        self.awakening_rituals = {}
        self.power_challenges = {}

        # Define default power types
        self.default_power_types = {
            "elemental": {
                "name": "Poder Elemental",
                "description": "Controle sobre os elementos da natureza.",
                "element": "varies",
                "skill_tree": {
                    "basic_control": {
                        "name": "Controle Básico",
                        "description": "Manipulação básica do elemento.",
                        "level": 1,
                        "prerequisites": [],
                        "effects": {"damage": 10, "control": 5}
                    },
                    "advanced_control": {
                        "name": "Controle Avançado",
                        "description": "Manipulação avançada do elemento.",
                        "level": 2,
                        "prerequisites": ["basic_control"],
                        "effects": {"damage": 20, "control": 15}
                    },
                    "elemental_shield": {
                        "name": "Escudo Elemental",
                        "description": "Cria um escudo protetor do seu elemento.",
                        "level": 2,
                        "prerequisites": ["basic_control"],
                        "effects": {"defense": 15}
                    },
                    "elemental_burst": {
                        "name": "Explosão Elemental",
                        "description": "Libera uma explosão poderosa do seu elemento.",
                        "level": 3,
                        "prerequisites": ["advanced_control"],
                        "effects": {"damage": 35, "area_effect": True}
                    },
                    "elemental_mastery": {
                        "name": "Maestria Elemental",
                        "description": "Domínio completo sobre o elemento.",
                        "level": 4,
                        "prerequisites": ["elemental_burst", "elemental_shield"],
                        "effects": {"damage": 50, "control": 40, "defense": 30}
                    }
                },
                "awakening_rituals": {
                    "elemental_communion": {
                        "name": "Comunhão Elemental",
                        "description": "Um ritual para se conectar profundamente com seu elemento.",
                        "requirements": {
                            "level": 15,
                            "power_level": 3,
                            "required_skills": ["advanced_control"]
                        },
                        "effects": {
                            "power_level_increase": 1,
                            "element_affinity_increase": 20
                        },
                        "unlocks": ["elemental_burst"]
                    },
                    "elemental_transcendence": {
                        "name": "Transcendência Elemental",
                        "description": "Um ritual avançado para transcender os limites do seu poder elemental.",
                        "requirements": {
                            "level": 25,
                            "power_level": 4,
                            "required_skills": ["elemental_burst", "elemental_shield"],
                            "required_items": ["Cristal Elemental Puro"]
                        },
                        "effects": {
                            "power_level_increase": 2,
                            "element_affinity_increase": 40,
                            "new_ability": "elemental_form"
                        },
                        "unlocks": ["elemental_mastery"]
                    }
                },
                "challenges": {
                    "elemental_trial": {
                        "name": "Provação Elemental",
                        "description": "Um desafio para testar seu controle elemental básico.",
                        "requirements": {
                            "level": 10,
                            "power_level": 2,
                            "required_skills": ["basic_control"]
                        },
                        "rewards": {
                            "exp": 500,
                            "power_points": 2,
                            "special_item": "Amuleto Elemental"
                        },
                        "difficulty": "easy"
                    },
                    "elemental_mastery_challenge": {
                        "name": "Desafio de Maestria Elemental",
                        "description": "Um desafio avançado para testar sua maestria sobre o elemento.",
                        "requirements": {
                            "level": 20,
                            "power_level": 3,
                            "required_skills": ["advanced_control", "elemental_shield"]
                        },
                        "rewards": {
                            "exp": 1500,
                            "power_points": 5,
                            "special_item": "Cristal Elemental Puro"
                        },
                        "difficulty": "hard"
                    }
                }
            },
            "psychic": {
                "name": "Poder Psíquico",
                "description": "Habilidades mentais e telecinéticas.",
                "element": "mental",
                "skill_tree": {
                    "mind_reading": {
                        "name": "Leitura Mental",
                        "description": "Capacidade de ler pensamentos superficiais.",
                        "level": 1,
                        "prerequisites": [],
                        "effects": {"perception": 15}
                    },
                    "telekinesis": {
                        "name": "Telecinese",
                        "description": "Mover objetos com a mente.",
                        "level": 1,
                        "prerequisites": [],
                        "effects": {"control": 10, "utility": 15}
                    },
                    "mental_shield": {
                        "name": "Escudo Mental",
                        "description": "Proteção contra ataques psíquicos.",
                        "level": 2,
                        "prerequisites": ["mind_reading"],
                        "effects": {"mental_defense": 25}
                    },
                    "psychic_blast": {
                        "name": "Explosão Psíquica",
                        "description": "Um ataque poderoso de energia mental.",
                        "level": 3,
                        "prerequisites": ["telekinesis"],
                        "effects": {"damage": 30, "stun_chance": 20}
                    },
                    "mind_control": {
                        "name": "Controle Mental",
                        "description": "Influenciar ou controlar as ações de outros.",
                        "level": 4,
                        "prerequisites": ["mental_shield", "psychic_blast"],
                        "effects": {"control": 40, "influence": 35}
                    }
                },
                "awakening_rituals": {
                    "mental_awakening": {
                        "name": "Despertar Mental",
                        "description": "Um ritual para expandir sua consciência e poder mental.",
                        "requirements": {
                            "level": 15,
                            "power_level": 2,
                            "required_skills": ["mind_reading", "telekinesis"]
                        },
                        "effects": {
                            "power_level_increase": 1,
                            "mental_capacity_increase": 25
                        },
                        "unlocks": ["mental_shield", "psychic_blast"]
                    },
                    "psychic_ascension": {
                        "name": "Ascensão Psíquica",
                        "description": "Um ritual avançado para ascender a um novo nível de poder psíquico.",
                        "requirements": {
                            "level": 25,
                            "power_level": 4,
                            "required_skills": ["mental_shield", "psychic_blast"],
                            "required_items": ["Cristal de Foco Mental"]
                        },
                        "effects": {
                            "power_level_increase": 2,
                            "mental_capacity_increase": 50,
                            "new_ability": "astral_projection"
                        },
                        "unlocks": ["mind_control"]
                    }
                },
                "challenges": {
                    "mental_discipline": {
                        "name": "Disciplina Mental",
                        "description": "Um desafio para testar seu controle mental básico.",
                        "requirements": {
                            "level": 10,
                            "power_level": 2,
                            "required_skills": ["mind_reading"]
                        },
                        "rewards": {
                            "exp": 500,
                            "power_points": 2,
                            "special_item": "Amuleto de Foco"
                        },
                        "difficulty": "easy"
                    },
                    "psychic_dominance": {
                        "name": "Dominância Psíquica",
                        "description": "Um desafio avançado para testar sua força mental.",
                        "requirements": {
                            "level": 20,
                            "power_level": 3,
                            "required_skills": ["mental_shield", "psychic_blast"]
                        },
                        "rewards": {
                            "exp": 1500,
                            "power_points": 5,
                            "special_item": "Cristal de Foco Mental"
                        },
                        "difficulty": "hard"
                    }
                }
            },
            "physical": {
                "name": "Poder Físico",
                "description": "Habilidades físicas sobre-humanas.",
                "element": "body",
                "skill_tree": {
                    "enhanced_strength": {
                        "name": "Força Aprimorada",
                        "description": "Força física acima do normal.",
                        "level": 1,
                        "prerequisites": [],
                        "effects": {"strength": 15, "damage": 10}
                    },
                    "enhanced_speed": {
                        "name": "Velocidade Aprimorada",
                        "description": "Velocidade acima do normal.",
                        "level": 1,
                        "prerequisites": [],
                        "effects": {"speed": 15, "evasion": 10}
                    },
                    "iron_body": {
                        "name": "Corpo de Ferro",
                        "description": "Resistência física aprimorada.",
                        "level": 2,
                        "prerequisites": ["enhanced_strength"],
                        "effects": {"defense": 20, "health": 15}
                    },
                    "combat_mastery": {
                        "name": "Maestria em Combate",
                        "description": "Técnicas avançadas de combate corpo a corpo.",
                        "level": 3,
                        "prerequisites": ["enhanced_strength", "enhanced_speed"],
                        "effects": {"damage": 25, "critical_chance": 15}
                    },
                    "physical_perfection": {
                        "name": "Perfeição Física",
                        "description": "O auge do desenvolvimento físico humano.",
                        "level": 4,
                        "prerequisites": ["iron_body", "combat_mastery"],
                        "effects": {"strength": 40, "speed": 35, "defense": 30, "health": 25}
                    }
                },
                "awakening_rituals": {
                    "body_tempering": {
                        "name": "Têmpera Corporal",
                        "description": "Um ritual para fortalecer seu corpo além dos limites normais.",
                        "requirements": {
                            "level": 15,
                            "power_level": 2,
                            "required_skills": ["enhanced_strength", "enhanced_speed"]
                        },
                        "effects": {
                            "power_level_increase": 1,
                            "physical_capacity_increase": 25
                        },
                        "unlocks": ["iron_body", "combat_mastery"]
                    },
                    "physical_transcendence": {
                        "name": "Transcendência Física",
                        "description": "Um ritual avançado para transcender os limites do corpo humano.",
                        "requirements": {
                            "level": 25,
                            "power_level": 4,
                            "required_skills": ["iron_body", "combat_mastery"],
                            "required_items": ["Elixir de Aprimoramento Físico"]
                        },
                        "effects": {
                            "power_level_increase": 2,
                            "physical_capacity_increase": 50,
                            "new_ability": "adrenaline_surge"
                        },
                        "unlocks": ["physical_perfection"]
                    }
                },
                "challenges": {
                    "physical_trial": {
                        "name": "Provação Física",
                        "description": "Um desafio para testar sua força e resistência básicas.",
                        "requirements": {
                            "level": 10,
                            "power_level": 2,
                            "required_skills": ["enhanced_strength"]
                        },
                        "rewards": {
                            "exp": 500,
                            "power_points": 2,
                            "special_item": "Bracelete de Força"
                        },
                        "difficulty": "easy"
                    },
                    "combat_challenge": {
                        "name": "Desafio de Combate",
                        "description": "Um desafio avançado para testar suas habilidades de combate.",
                        "requirements": {
                            "level": 20,
                            "power_level": 3,
                            "required_skills": ["iron_body", "combat_mastery"]
                        },
                        "rewards": {
                            "exp": 1500,
                            "power_points": 5,
                            "special_item": "Elixir de Aprimoramento Físico"
                        },
                        "difficulty": "hard"
                    }
                }
            }
        }

        # Load default power types
        self._load_default_power_types()

    def _load_default_power_types(self):
        """Loads the default power types."""
        for power_id, power_data in self.default_power_types.items():
            self.register_power_type(power_id, power_data)

            # Register skill nodes
            for node_id, node_data in power_data.get("skill_tree", {}).items():
                full_node_id = f"{power_id}_{node_id}"
                self.skill_nodes[full_node_id] = SkillNode(full_node_id, node_data)

            # Register awakening rituals
            for ritual_id, ritual_data in power_data.get("awakening_rituals", {}).items():
                full_ritual_id = f"{power_id}_{ritual_id}"
                self.awakening_rituals[full_ritual_id] = AwakeningRitual(full_ritual_id, ritual_data)

            # Register power challenges
            for challenge_id, challenge_data in power_data.get("challenges", {}).items():
                full_challenge_id = f"{power_id}_{challenge_id}"
                self.power_challenges[full_challenge_id] = PowerChallenge(full_challenge_id, challenge_data)

        logger.info(f"Loaded {len(self.power_types)} default power types")

    def register_power_type(self, power_id: str, data: Dict[str, Any]) -> None:
        """
        Registers a power type.

        Args:
            power_id: Unique identifier for the power type
            data: Dictionary containing power type data
        """
        self.power_types[power_id] = PowerType(power_id, data)
        logger.info(f"Registered power type: {data.get('name')} (ID: {power_id})")

    def get_power_type(self, power_id: str) -> Optional[PowerType]:
        """
        Gets a power type by ID.

        Args:
            power_id: ID of the power type

        Returns:
            PowerType instance or None if not found
        """
        return self.power_types.get(power_id)

    def get_all_power_types(self) -> Dict[str, PowerType]:
        """
        Gets all registered power types.

        Returns:
            Dictionary mapping power type IDs to PowerType instances
        """
        return self.power_types

    def initialize_player_power(self, player_data: Dict[str, Any], power_id: str) -> Dict[str, Any]:
        """
        Initializes a player's power.

        Args:
            player_data: Player data
            power_id: ID of the power type

        Returns:
            Updated player data
        """
        if power_id not in self.power_types:
            logger.warning(f"Power type not found: {power_id}")
            return player_data

        story_progress = player_data.get("story_progress", {})

        if "powers" not in story_progress:
            story_progress["powers"] = {}

        if power_id not in story_progress["powers"]:
            story_progress["powers"][power_id] = {
                "level": 1,
                "experience": 0,
                "power_points": 3,  # Initial points to spend
                "unlocked_nodes": [],
                "completed_rituals": [],
                "completed_challenges": []
            }

        player_data["story_progress"] = story_progress
        logger.info(f"Initialized power {power_id} for player {player_data.get('user_id')}")

        return player_data

    def get_player_power(self, player_data: Dict[str, Any], power_id: str) -> Optional[Dict[str, Any]]:
        """
        Gets a player's power progress.

        Args:
            player_data: Player data
            power_id: ID of the power type

        Returns:
            Power progress data or None if not found
        """
        story_progress = player_data.get("story_progress", {})
        powers = story_progress.get("powers", {})

        return powers.get(power_id)

    def unlock_skill_node(self, player_data: Dict[str, Any], power_id: str, node_id: str) -> Dict[str, Any]:
        """
        Unlocks a skill node for a player.

        Args:
            player_data: Player data
            power_id: ID of the power type
            node_id: ID of the skill node

        Returns:
            Updated player data and result information
        """
        full_node_id = f"{power_id}_{node_id}"

        if full_node_id not in self.skill_nodes:
            return {"player_data": player_data, "error": f"Skill node not found: {node_id}"}

        power_progress = self.get_player_power(player_data, power_id)
        if not power_progress:
            return {"player_data": player_data, "error": f"Power not initialized: {power_id}"}

        # Check if already unlocked
        if node_id in power_progress["unlocked_nodes"]:
            return {"player_data": player_data, "error": f"Skill node already unlocked: {node_id}"}

        # Check prerequisites
        node = self.skill_nodes[full_node_id]
        unlocked_nodes = power_progress["unlocked_nodes"]

        if not node.can_unlock(unlocked_nodes):
            return {"player_data": player_data, "error": f"Prerequisites not met for skill node: {node_id}"}

        # Check power points
        cost = node.get_cost()
        power_points = power_progress.get("power_points", 0)

        if power_points < cost.get("power_points", 1):
            return {"player_data": player_data, "error": f"Not enough power points to unlock skill node: {node_id}"}

        # Unlock the node
        power_progress["unlocked_nodes"].append(node_id)
        power_progress["power_points"] -= cost.get("power_points", 1)

        # Update player data
        story_progress = player_data.get("story_progress", {})
        powers = story_progress.get("powers", {})
        powers[power_id] = power_progress
        story_progress["powers"] = powers
        player_data["story_progress"] = story_progress

        logger.info(f"Unlocked skill node {node_id} for power {power_id} for player {player_data.get('user_id')}")

        return {
            "player_data": player_data,
            "success": True,
            "message": f"Desbloqueou {node.get_name()}!",
            "node_info": {
                "id": node_id,
                "name": node.get_name(),
                "description": node.get_description(),
                "effects": node.get_effects()
            }
        }

    def perform_awakening_ritual(self, player_data: Dict[str, Any], power_id: str, ritual_id: str) -> Dict[str, Any]:
        """
        Performs an awakening ritual for a player.

        Args:
            player_data: Player data
            power_id: ID of the power type
            ritual_id: ID of the awakening ritual

        Returns:
            Updated player data and result information
        """
        full_ritual_id = f"{power_id}_{ritual_id}"

        if full_ritual_id not in self.awakening_rituals:
            return {"player_data": player_data, "error": f"Awakening ritual not found: {ritual_id}"}

        power_progress = self.get_player_power(player_data, power_id)
        if not power_progress:
            return {"player_data": player_data, "error": f"Power not initialized: {power_id}"}

        # Check if already completed
        if ritual_id in power_progress.get("completed_rituals", []):
            return {"player_data": player_data, "error": f"Awakening ritual already completed: {ritual_id}"}

        # Check if can perform
        ritual = self.awakening_rituals[full_ritual_id]
        if not ritual.can_perform(player_data, power_progress):
            return {"player_data": player_data, "error": f"Requirements not met for awakening ritual: {ritual_id}"}

        # Perform the ritual
        # Mark as completed
        if "completed_rituals" not in power_progress:
            power_progress["completed_rituals"] = []
        power_progress["completed_rituals"].append(ritual_id)

        # Apply effects
        effects = ritual.get_effects()

        if "power_level_increase" in effects:
            power_progress["level"] += effects["power_level_increase"]

        if "power_points" in effects:
            power_progress["power_points"] += effects["power_points"]

        # Unlock nodes
        for node_id in ritual.get_unlocks():
            if node_id not in power_progress["unlocked_nodes"]:
                power_progress["unlocked_nodes"].append(node_id)

        # Update player data
        story_progress = player_data.get("story_progress", {})
        powers = story_progress.get("powers", {})
        powers[power_id] = power_progress
        story_progress["powers"] = powers
        player_data["story_progress"] = story_progress

        logger.info(f"Completed awakening ritual {ritual_id} for power {power_id} for player {player_data.get('user_id')}")

        return {
            "player_data": player_data,
            "success": True,
            "message": f"Completou o ritual: {ritual.get_name()}!",
            "ritual_info": {
                "id": ritual_id,
                "name": ritual.get_name(),
                "description": ritual.get_description(),
                "effects": effects
            }
        }

    def complete_power_challenge(self, player_data: Dict[str, Any], power_id: str, challenge_id: str) -> Dict[str, Any]:
        """
        Completes a power challenge for a player.

        Args:
            player_data: Player data
            power_id: ID of the power type
            challenge_id: ID of the power challenge

        Returns:
            Updated player data and result information
        """
        full_challenge_id = f"{power_id}_{challenge_id}"

        if full_challenge_id not in self.power_challenges:
            return {"player_data": player_data, "error": f"Power challenge not found: {challenge_id}"}

        power_progress = self.get_player_power(player_data, power_id)
        if not power_progress:
            return {"player_data": player_data, "error": f"Power not initialized: {power_id}"}

        # Check if already completed
        if challenge_id in power_progress.get("completed_challenges", []):
            return {"player_data": player_data, "error": f"Power challenge already completed: {challenge_id}"}

        # Check if can attempt
        challenge = self.power_challenges[full_challenge_id]
        if not challenge.can_attempt(player_data, power_progress):
            return {"player_data": player_data, "error": f"Requirements not met for power challenge: {challenge_id}"}

        # Complete the challenge
        # Mark as completed
        if "completed_challenges" not in power_progress:
            power_progress["completed_challenges"] = []
        power_progress["completed_challenges"].append(challenge_id)

        # Apply rewards
        rewards = challenge.get_rewards()

        if "exp" in rewards:
            player_data["exp"] = player_data.get("exp", 0) + rewards["exp"]

        if "power_points" in rewards:
            power_progress["power_points"] += rewards["power_points"]

        if "special_item" in rewards:
            story_progress = player_data.get("story_progress", {})
            special_items = story_progress.get("special_items", [])
            if rewards["special_item"] not in special_items:
                special_items.append(rewards["special_item"])
            story_progress["special_items"] = special_items
            player_data["story_progress"] = story_progress

        # Update player data
        story_progress = player_data.get("story_progress", {})
        powers = story_progress.get("powers", {})
        powers[power_id] = power_progress
        story_progress["powers"] = powers
        player_data["story_progress"] = story_progress

        logger.info(f"Completed power challenge {challenge_id} for power {power_id} for player {player_data.get('user_id')}")

        return {
            "player_data": player_data,
            "success": True,
            "message": f"Completou o desafio: {challenge.get_name()}!",
            "challenge_info": {
                "id": challenge_id,
                "name": challenge.get_name(),
                "description": challenge.get_description(),
                "rewards": rewards
            }
        }

    def get_available_skill_nodes(self, player_data: Dict[str, Any], power_id: str) -> List[Dict[str, Any]]:
        """
        Gets skill nodes available for unlocking.

        Args:
            player_data: Player data
            power_id: ID of the power type

        Returns:
            List of available skill nodes
        """
        power_progress = self.get_player_power(player_data, power_id)
        if not power_progress:
            return []

        unlocked_nodes = power_progress.get("unlocked_nodes", [])
        power_points = power_progress.get("power_points", 0)

        available_nodes = []

        for full_node_id, node in self.skill_nodes.items():
            if not full_node_id.startswith(f"{power_id}_"):
                continue

            node_id = full_node_id.split("_", 1)[1]

            if node_id in unlocked_nodes:
                continue

            if node.can_unlock(unlocked_nodes) and power_points >= node.get_cost().get("power_points", 1):
                available_nodes.append({
                    "id": node_id,
                    "name": node.get_name(),
                    "description": node.get_description(),
                    "level": node.get_level(),
                    "cost": node.get_cost(),
                    "effects": node.get_effects()
                })

        return available_nodes

    def get_available_awakening_rituals(self, player_data: Dict[str, Any], power_id: str) -> List[Dict[str, Any]]:
        """
        Gets awakening rituals available for performing.

        Args:
            player_data: Player data
            power_id: ID of the power type

        Returns:
            List of available awakening rituals
        """
        power_progress = self.get_player_power(player_data, power_id)
        if not power_progress:
            return []

        completed_rituals = power_progress.get("completed_rituals", [])

        available_rituals = []

        for full_ritual_id, ritual in self.awakening_rituals.items():
            if not full_ritual_id.startswith(f"{power_id}_"):
                continue

            ritual_id = full_ritual_id.split("_", 1)[1]

            if ritual_id in completed_rituals:
                continue

            if ritual.can_perform(player_data, power_progress):
                available_rituals.append({
                    "id": ritual_id,
                    "name": ritual.get_name(),
                    "description": ritual.get_description(),
                    "requirements": ritual.get_requirements(),
                    "effects": ritual.get_effects()
                })

        return available_rituals

    def get_available_power_challenges(self, player_data: Dict[str, Any], power_id: str) -> List[Dict[str, Any]]:
        """
        Gets power challenges available for attempting.

        Args:
            player_data: Player data
            power_id: ID of the power type

        Returns:
            List of available power challenges
        """
        power_progress = self.get_player_power(player_data, power_id)
        if not power_progress:
            return []

        completed_challenges = power_progress.get("completed_challenges", [])

        available_challenges = []

        for full_challenge_id, challenge in self.power_challenges.items():
            if not full_challenge_id.startswith(f"{power_id}_"):
                continue

            challenge_id = full_challenge_id.split("_", 1)[1]

            if challenge_id in completed_challenges:
                continue

            if challenge.can_attempt(player_data, power_progress):
                available_challenges.append({
                    "id": challenge_id,
                    "name": challenge.get_name(),
                    "description": challenge.get_description(),
                    "difficulty": challenge.get_difficulty(),
                    "requirements": challenge.get_requirements(),
                    "rewards": challenge.get_rewards()
                })

        return available_challenges

    def get_power_status(self, player_data: Dict[str, Any], power_id: str) -> Dict[str, Any]:
        """
        Gets the status of a player's power.

        Args:
            player_data: Player data
            power_id: ID of the power type

        Returns:
            Dictionary containing power status information
        """
        power_type = self.get_power_type(power_id)
        if not power_type:
            return {"error": f"Power type not found: {power_id}"}

        power_progress = self.get_player_power(player_data, power_id)
        if not power_progress:
            return {"error": f"Power not initialized: {power_id}"}

        # Get unlocked nodes with details
        unlocked_nodes = []
        for node_id in power_progress.get("unlocked_nodes", []):
            full_node_id = f"{power_id}_{node_id}"
            if full_node_id in self.skill_nodes:
                node = self.skill_nodes[full_node_id]
                unlocked_nodes.append({
                    "id": node_id,
                    "name": node.get_name(),
                    "description": node.get_description(),
                    "level": node.get_level(),
                    "effects": node.get_effects()
                })

        # Get completed rituals with details
        completed_rituals = []
        for ritual_id in power_progress.get("completed_rituals", []):
            full_ritual_id = f"{power_id}_{ritual_id}"
            if full_ritual_id in self.awakening_rituals:
                ritual = self.awakening_rituals[full_ritual_id]
                completed_rituals.append({
                    "id": ritual_id,
                    "name": ritual.get_name(),
                    "description": ritual.get_description(),
                    "effects": ritual.get_effects()
                })

        # Get completed challenges with details
        completed_challenges = []
        for challenge_id in power_progress.get("completed_challenges", []):
            full_challenge_id = f"{power_id}_{challenge_id}"
            if full_challenge_id in self.power_challenges:
                challenge = self.power_challenges[full_challenge_id]
                completed_challenges.append({
                    "id": challenge_id,
                    "name": challenge.get_name(),
                    "description": challenge.get_description(),
                    "difficulty": challenge.get_difficulty(),
                    "rewards": challenge.get_rewards()
                })

        return {
            "power_id": power_id,
            "name": power_type.get_name(),
            "description": power_type.get_description(),
            "element": power_type.get_element(),
            "level": power_progress.get("level", 1),
            "experience": power_progress.get("experience", 0),
            "power_points": power_progress.get("power_points", 0),
            "unlocked_nodes": unlocked_nodes,
            "completed_rituals": completed_rituals,
            "completed_challenges": completed_challenges,
            "available_nodes": self.get_available_skill_nodes(player_data, power_id),
            "available_rituals": self.get_available_awakening_rituals(player_data, power_id),
            "available_challenges": self.get_available_power_challenges(player_data, power_id)
        }
