"""
Power Evolution System

This module implements a system for power evolution, including skill trees,
awakening rituals, and power-specific challenges.
"""

import json
import os
import random
from datetime import datetime
from collections import defaultdict

class PowerEvolutionManager:
    """
    Manages the evolution of player powers through skill trees, rituals, and challenges.
    """

    def __init__(self, player_id):
        """
        Initialize the power evolution manager for a specific player.

        Args:
            player_id (str): The unique identifier for the player
        """
        self.player_id = player_id
        self.power_data = self._load_power_data()
        self.player_powers = {}
        self.unlocked_skills = set()
        self.completed_rituals = set()
        self.completed_challenges = set()
        self.load_data()

    def _load_power_data(self):
        """
        Load power data from the data file.

        Returns:
            dict: The power data
        """
        try:
            file_path = "data/story_mode/powers/power_trees.json"
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # Create default power data if file doesn't exist
                power_data = self._create_default_power_data()
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(power_data, f, ensure_ascii=False, indent=2)
                return power_data
        except Exception as e:
            print(f"Error loading power data: {e}")
            return self._create_default_power_data()

    def _create_default_power_data(self):
        """
        Create default power data.

        Returns:
            dict: The default power data
        """
        return {
            "Fogo": {
                "description": "Poderes relacionados à manipulação e criação de fogo.",
                "skill_tree": {
                    "basic": {
                        "chama_controlada": {
                            "name": "Chama Controlada",
                            "description": "Capacidade de criar e controlar pequenas chamas.",
                            "requirements": {"level": 1},
                            "effects": {"damage": 5, "control": 3}
                        },
                        "resistencia_termica": {
                            "name": "Resistência Térmica",
                            "description": "Resistência a altas temperaturas e danos por fogo.",
                            "requirements": {"level": 2},
                            "effects": {"fire_resistance": 50}
                        },
                        "rajada_flamejante": {
                            "name": "Rajada Flamejante",
                            "description": "Disparo de uma rajada concentrada de fogo.",
                            "requirements": {"level": 3, "skills": ["chama_controlada"]},
                            "effects": {"damage": 15, "cooldown": 3}
                        }
                    },
                    "intermediate": {
                        "escudo_de_fogo": {
                            "name": "Escudo de Fogo",
                            "description": "Cria uma barreira protetora de chamas ao redor do usuário.",
                            "requirements": {"level": 5, "skills": ["resistencia_termica"]},
                            "effects": {"defense": 20, "reflect_damage": 5, "duration": 3}
                        },
                        "explosao_infernal": {
                            "name": "Explosão Infernal",
                            "description": "Cria uma explosão de fogo que atinge múltiplos alvos.",
                            "requirements": {"level": 7, "skills": ["rajada_flamejante"]},
                            "effects": {"damage": 25, "area_effect": True, "cooldown": 5}
                        },
                        "forma_flamejante": {
                            "name": "Forma Flamejante",
                            "description": "Transforma o corpo do usuário em fogo vivo temporariamente.",
                            "requirements": {"level": 10, "skills": ["escudo_de_fogo", "explosao_infernal"]},
                            "effects": {"damage_aura": 10, "movement_speed": 50, "duration": 4}
                        }
                    },
                    "advanced": {
                        "furia_do_fenix": {
                            "name": "Fúria da Fênix",
                            "description": "Invoca o poder mítico da fênix para um ataque devastador.",
                            "requirements": {
                                "level": 15, 
                                "skills": ["forma_flamejante"], 
                                "ritual": "ritual_da_fenix"
                            },
                            "effects": {"damage": 100, "area_effect": True, "cooldown": 10}
                        },
                        "inferno_eterno": {
                            "name": "Inferno Eterno",
                            "description": "Cria chamas que continuam queimando enquanto o usuário mantiver concentração.",
                            "requirements": {
                                "level": 18, 
                                "skills": ["explosao_infernal"], 
                                "ritual": "ritual_da_chama_eterna"
                            },
                            "effects": {"damage_over_time": 15, "duration": "concentration", "area_denial": True}
                        },
                        "avatar_do_fogo": {
                            "name": "Avatar do Fogo",
                            "description": "Transformação completa em uma entidade de fogo puro, com poder imenso.",
                            "requirements": {
                                "level": 20, 
                                "skills": ["furia_do_fenix", "inferno_eterno"], 
                                "ritual": "ritual_da_transcendencia_flamejante"
                            },
                            "effects": {
                                "damage": 50, 
                                "defense": 50, 
                                "fire_immunity": True, 
                                "flight": True, 
                                "duration": 5
                            }
                        }
                    }
                },
                "rituals": {
                    "ritual_da_fenix": {
                        "name": "Ritual da Fênix",
                        "description": "Um ritual que conecta o usuário à essência mítica da fênix.",
                        "requirements": {"level": 15, "items": ["pena_de_fenix", "cristal_de_fogo"]},
                        "challenge": "sobreviver_pira_flamejante",
                        "effects": {"unlock_skill": "furia_do_fenix", "power_boost": 20}
                    },
                    "ritual_da_chama_eterna": {
                        "name": "Ritual da Chama Eterna",
                        "description": "Um ritual que permite ao usuário criar chamas que nunca se extinguem.",
                        "requirements": {"level": 18, "items": ["carvao_eterno", "essencia_de_lava"]},
                        "challenge": "manter_chama_por_24h",
                        "effects": {"unlock_skill": "inferno_eterno", "fire_duration": 100}
                    },
                    "ritual_da_transcendencia_flamejante": {
                        "name": "Ritual da Transcendência Flamejante",
                        "description": "O ritual final que permite ao usuário transcender a forma humana e se tornar um com o fogo.",
                        "requirements": {
                            "level": 20, 
                            "rituals": ["ritual_da_fenix", "ritual_da_chama_eterna"],
                            "items": ["nucleo_de_estrela", "lagrima_de_dragao", "essencia_de_vulcao"]
                        },
                        "challenge": "desafio_do_vulcao",
                        "effects": {"unlock_skill": "avatar_do_fogo", "power_mastery": True}
                    }
                },
                "challenges": {
                    "sobreviver_pira_flamejante": {
                        "name": "Sobreviver à Pira Flamejante",
                        "description": "Permanecer no centro de uma pira flamejante mágica por uma hora.",
                        "difficulty": "hard",
                        "requirements": {"fire_resistance": 30, "willpower": 15},
                        "rewards": {"exp": 500, "unlock_ritual": "ritual_da_fenix"}
                    },
                    "manter_chama_por_24h": {
                        "name": "Manter a Chama por 24 Horas",
                        "description": "Manter uma chama acesa usando apenas seu poder por 24 horas.",
                        "difficulty": "medium",
                        "requirements": {"concentration": 20, "power_control": 15},
                        "rewards": {"exp": 700, "unlock_ritual": "ritual_da_chama_eterna"}
                    },
                    "desafio_do_vulcao": {
                        "name": "Desafio do Vulcão",
                        "description": "Entrar no coração de um vulcão ativo e absorver seu poder.",
                        "difficulty": "extreme",
                        "requirements": {
                            "fire_resistance": 50, 
                            "power_control": 25, 
                            "completed_rituals": ["ritual_da_fenix", "ritual_da_chama_eterna"]
                        },
                        "rewards": {
                            "exp": 1500, 
                            "unlock_ritual": "ritual_da_transcendencia_flamejante",
                            "special_item": "essencia_de_vulcao"
                        }
                    }
                }
            },
            "Água": {
                "description": "Poderes relacionados à manipulação da água em todas as suas formas.",
                "skill_tree": {
                    "basic": {
                        "manipulacao_basica": {
                            "name": "Manipulação Básica",
                            "description": "Capacidade de mover pequenas quantidades de água.",
                            "requirements": {"level": 1},
                            "effects": {"water_control": 5}
                        },
                        "respiracao_aquatica": {
                            "name": "Respiração Aquática",
                            "description": "Capacidade de respirar debaixo d'água.",
                            "requirements": {"level": 2},
                            "effects": {"water_breathing": True}
                        },
                        "jato_de_agua": {
                            "name": "Jato de Água",
                            "description": "Disparo de um jato de água pressurizada.",
                            "requirements": {"level": 3, "skills": ["manipulacao_basica"]},
                            "effects": {"damage": 10, "knockback": 5}
                        }
                    },
                    "intermediate": {
                        "escudo_aquatico": {
                            "name": "Escudo Aquático",
                            "description": "Cria uma barreira de água que absorve impactos.",
                            "requirements": {"level": 5, "skills": ["manipulacao_basica"]},
                            "effects": {"defense": 15, "duration": 4}
                        },
                        "prisao_de_agua": {
                            "name": "Prisão de Água",
                            "description": "Cria uma esfera de água que prende o alvo.",
                            "requirements": {"level": 7, "skills": ["jato_de_agua"]},
                            "effects": {"immobilize": True, "duration": 3, "cooldown": 6}
                        },
                        "forma_liquida": {
                            "name": "Forma Líquida",
                            "description": "Transforma o corpo do usuário em água temporariamente.",
                            "requirements": {"level": 10, "skills": ["escudo_aquatico", "respiracao_aquatica"]},
                            "effects": {"physical_immunity": True, "duration": 3, "cooldown": 8}
                        }
                    },
                    "advanced": {
                        "tsunami": {
                            "name": "Tsunami",
                            "description": "Invoca uma onda gigante que causa dano massivo.",
                            "requirements": {
                                "level": 15, 
                                "skills": ["prisao_de_agua"], 
                                "ritual": "ritual_do_oceano"
                            },
                            "effects": {"damage": 80, "area_effect": True, "knockback": 20, "cooldown": 12}
                        },
                        "cura_aquatica": {
                            "name": "Cura Aquática",
                            "description": "Usa a água para curar ferimentos.",
                            "requirements": {
                                "level": 18, 
                                "skills": ["forma_liquida"], 
                                "ritual": "ritual_da_purificacao"
                            },
                            "effects": {"healing": 30, "cleanse_status": True, "cooldown": 8}
                        },
                        "avatar_da_agua": {
                            "name": "Avatar da Água",
                            "description": "Transformação completa em uma entidade de água pura, com poder imenso.",
                            "requirements": {
                                "level": 20, 
                                "skills": ["tsunami", "cura_aquatica"], 
                                "ritual": "ritual_da_transcendencia_aquatica"
                            },
                            "effects": {
                                "damage": 40, 
                                "defense": 60, 
                                "water_immunity": True, 
                                "healing_aura": 10, 
                                "duration": 5
                            }
                        }
                    }
                },
                "rituals": {
                    "ritual_do_oceano": {
                        "name": "Ritual do Oceano",
                        "description": "Um ritual que conecta o usuário às profundezas do oceano.",
                        "requirements": {"level": 15, "items": ["perola_abissal", "agua_primordial"]},
                        "challenge": "comunhao_com_o_abismo",
                        "effects": {"unlock_skill": "tsunami", "water_control": 30}
                    },
                    "ritual_da_purificacao": {
                        "name": "Ritual da Purificação",
                        "description": "Um ritual que permite ao usuário purificar e curar através da água.",
                        "requirements": {"level": 18, "items": ["cristal_de_agua_pura", "lagrima_de_sereia"]},
                        "challenge": "purificar_fonte_contaminada",
                        "effects": {"unlock_skill": "cura_aquatica", "healing_power": 30}
                    },
                    "ritual_da_transcendencia_aquatica": {
                        "name": "Ritual da Transcendência Aquática",
                        "description": "O ritual final que permite ao usuário transcender a forma humana e se tornar um com a água.",
                        "requirements": {
                            "level": 20, 
                            "rituals": ["ritual_do_oceano", "ritual_da_purificacao"],
                            "items": ["essencia_de_cachoeira_celestial", "coracao_do_mar", "gota_do_diluvio"]
                        },
                        "challenge": "desafio_da_tempestade",
                        "effects": {"unlock_skill": "avatar_da_agua", "power_mastery": True}
                    }
                },
                "challenges": {
                    "comunhao_com_o_abismo": {
                        "name": "Comunhão com o Abismo",
                        "description": "Meditar no fundo do oceano por três horas.",
                        "difficulty": "hard",
                        "requirements": {"water_breathing": True, "meditation": 15},
                        "rewards": {"exp": 500, "unlock_ritual": "ritual_do_oceano"}
                    },
                    "purificar_fonte_contaminada": {
                        "name": "Purificar Fonte Contaminada",
                        "description": "Usar seus poderes para purificar uma fonte de água contaminada.",
                        "difficulty": "medium",
                        "requirements": {"water_control": 20, "power_control": 15},
                        "rewards": {"exp": 700, "unlock_ritual": "ritual_da_purificacao"}
                    },
                    "desafio_da_tempestade": {
                        "name": "Desafio da Tempestade",
                        "description": "Permanecer no centro de uma tempestade mágica e controlar suas águas.",
                        "difficulty": "extreme",
                        "requirements": {
                            "water_control": 30, 
                            "power_control": 25, 
                            "completed_rituals": ["ritual_do_oceano", "ritual_da_purificacao"]
                        },
                        "rewards": {
                            "exp": 1500, 
                            "unlock_ritual": "ritual_da_transcendencia_aquatica",
                            "special_item": "gota_do_diluvio"
                        }
                    }
                }
            },
            "Terra": {
                "description": "Poderes relacionados à manipulação da terra, rochas e metais.",
                "skill_tree": {
                    "basic": {
                        "manipulacao_de_terra": {
                            "name": "Manipulação de Terra",
                            "description": "Capacidade de mover pequenas quantidades de terra e pedra.",
                            "requirements": {"level": 1},
                            "effects": {"earth_control": 5}
                        },
                        "pele_de_pedra": {
                            "name": "Pele de Pedra",
                            "description": "Endurece a pele, tornando-a resistente como pedra.",
                            "requirements": {"level": 2},
                            "effects": {"defense": 10, "duration": 3}
                        },
                        "projetil_de_rocha": {
                            "name": "Projétil de Rocha",
                            "description": "Lança pedras em alta velocidade contra o alvo.",
                            "requirements": {"level": 3, "skills": ["manipulacao_de_terra"]},
                            "effects": {"damage": 15, "cooldown": 2}
                        }
                    },
                    "intermediate": {
                        "muralha_de_pedra": {
                            "name": "Muralha de Pedra",
                            "description": "Cria uma barreira de pedra para proteção.",
                            "requirements": {"level": 5, "skills": ["manipulacao_de_terra"]},
                            "effects": {"defense": 25, "duration": 5}
                        },
                        "punhos_de_pedra": {
                            "name": "Punhos de Pedra",
                            "description": "Envolve os punhos com pedra para aumentar o dano de ataques físicos.",
                            "requirements": {"level": 7, "skills": ["pele_de_pedra"]},
                            "effects": {"damage": 20, "defense": 10, "duration": 4}
                        },
                        "controle_de_metal": {
                            "name": "Controle de Metal",
                            "description": "Estende o controle para incluir metais.",
                            "requirements": {"level": 10, "skills": ["manipulacao_de_terra", "projetil_de_rocha"]},
                            "effects": {"metal_control": 15, "damage": 25}
                        }
                    },
                    "advanced": {
                        "terremoto": {
                            "name": "Terremoto",
                            "description": "Causa um terremoto localizado que desequilibra e danifica os inimigos.",
                            "requirements": {
                                "level": 15, 
                                "skills": ["muralha_de_pedra"], 
                                "ritual": "ritual_do_nucleo_terrestre"
                            },
                            "effects": {"damage": 60, "area_effect": True, "knockdown": True, "cooldown": 15}
                        },
                        "armadura_de_cristal": {
                            "name": "Armadura de Cristal",
                            "description": "Cria uma armadura de cristais inquebrável.",
                            "requirements": {
                                "level": 18, 
                                "skills": ["controle_de_metal"], 
                                "ritual": "ritual_da_forja_elemental"
                            },
                            "effects": {"defense": 50, "reflect_damage": 15, "duration": 5}
                        },
                        "avatar_da_terra": {
                            "name": "Avatar da Terra",
                            "description": "Transformação completa em uma entidade de pedra e cristal, com poder imenso.",
                            "requirements": {
                                "level": 20, 
                                "skills": ["terremoto", "armadura_de_cristal"], 
                                "ritual": "ritual_da_transcendencia_terrestre"
                            },
                            "effects": {
                                "damage": 60, 
                                "defense": 80, 
                                "earth_immunity": True, 
                                "terrain_manipulation": True, 
                                "duration": 5
                            }
                        }
                    }
                },
                "rituals": {
                    "ritual_do_nucleo_terrestre": {
                        "name": "Ritual do Núcleo Terrestre",
                        "description": "Um ritual que conecta o usuário ao núcleo da Terra.",
                        "requirements": {"level": 15, "items": ["fragmento_do_nucleo", "cristal_de_terra"]},
                        "challenge": "meditacao_na_caverna_profunda",
                        "effects": {"unlock_skill": "terremoto", "earth_control": 30}
                    },
                    "ritual_da_forja_elemental": {
                        "name": "Ritual da Forja Elemental",
                        "description": "Um ritual que permite ao usuário forjar cristais e metais com seu poder.",
                        "requirements": {"level": 18, "items": ["metal_primordial", "cristal_perfeito"]},
                        "challenge": "forjar_arma_elemental",
                        "effects": {"unlock_skill": "armadura_de_cristal", "crafting_power": 30}
                    },
                    "ritual_da_transcendencia_terrestre": {
                        "name": "Ritual da Transcendência Terrestre",
                        "description": "O ritual final que permite ao usuário transcender a forma humana e se tornar um com a terra.",
                        "requirements": {
                            "level": 20, 
                            "rituals": ["ritual_do_nucleo_terrestre", "ritual_da_forja_elemental"],
                            "items": ["coração_da_montanha", "essência_de_diamante", "pó_de_meteoro"]
                        },
                        "challenge": "desafio_da_montanha",
                        "effects": {"unlock_skill": "avatar_da_terra", "power_mastery": True}
                    }
                },
                "challenges": {
                    "meditacao_na_caverna_profunda": {
                        "name": "Meditação na Caverna Profunda",
                        "description": "Meditar em uma caverna profunda por 24 horas, conectando-se com a terra.",
                        "difficulty": "hard",
                        "requirements": {"meditation": 20, "earth_affinity": 15},
                        "rewards": {"exp": 500, "unlock_ritual": "ritual_do_nucleo_terrestre"}
                    },
                    "forjar_arma_elemental": {
                        "name": "Forjar Arma Elemental",
                        "description": "Usar seus poderes para forjar uma arma a partir de metais e cristais elementais.",
                        "difficulty": "medium",
                        "requirements": {"earth_control": 20, "metal_control": 15},
                        "rewards": {"exp": 700, "unlock_ritual": "ritual_da_forja_elemental"}
                    },
                    "desafio_da_montanha": {
                        "name": "Desafio da Montanha",
                        "description": "Escalar a montanha mais alta sem equipamentos, usando apenas seus poderes.",
                        "difficulty": "extreme",
                        "requirements": {
                            "earth_control": 30, 
                            "physical_strength": 25, 
                            "completed_rituals": ["ritual_do_nucleo_terrestre", "ritual_da_forja_elemental"]
                        },
                        "rewards": {
                            "exp": 1500, 
                            "unlock_ritual": "ritual_da_transcendencia_terrestre",
                            "special_item": "coração_da_montanha"
                        }
                    }
                }
            }
        }

    def load_data(self):
        """Load player power evolution data from storage if it exists."""
        try:
            file_path = f"data/player_data/{self.player_id}/power_evolution.json"
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.player_powers = data.get('player_powers', {})
                    self.unlocked_skills = set(data.get('unlocked_skills', []))
                    self.completed_rituals = set(data.get('completed_rituals', []))
                    self.completed_challenges = set(data.get('completed_challenges', []))
        except Exception as e:
            print(f"Error loading power evolution data: {e}")

    def save_data(self):
        """Save player power evolution data to storage."""
        try:
            file_path = f"data/player_data/{self.player_id}/power_evolution.json"
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            data = {
                'player_powers': self.player_powers,
                'unlocked_skills': list(self.unlocked_skills),
                'completed_rituals': list(self.completed_rituals),
                'completed_challenges': list(self.completed_challenges)
            }

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving power evolution data: {e}")

    def set_player_power(self, power_type, level=1):
        """
        Set or update a player's power type and level.

        Args:
            power_type (str): The type of power (e.g., 'Fogo', 'Água', 'Terra')
            level (int, optional): The power level

        Returns:
            bool: True if successful, False otherwise
        """
        if power_type not in self.power_data:
            print(f"Warning: Power type '{power_type}' not found in power data")
            return False

        self.player_powers[power_type] = {
            'level': level,
            'experience': 0,
            'mastery': 0
        }

        # Unlock basic skills automatically
        if power_type in self.power_data and 'skill_tree' in self.power_data[power_type]:
            basic_skills = self.power_data[power_type]['skill_tree'].get('basic', {})
            for skill_id, skill_data in basic_skills.items():
                if skill_data.get('requirements', {}).get('level', 99) <= level:
                    self.unlocked_skills.add(f"{power_type}:{skill_id}")

        self.save_data()
        return True

    def get_player_powers(self):
        """
        Get all player powers.

        Returns:
            dict: The player's powers
        """
        return self.player_powers

    def get_power_level(self, power_type):
        """
        Get the level of a specific power.

        Args:
            power_type (str): The type of power

        Returns:
            int: The power level, or 0 if the player doesn't have this power
        """
        return self.player_powers.get(power_type, {}).get('level', 0)

    def increase_power_experience(self, power_type, amount):
        """
        Increase the experience of a power, potentially leveling it up.

        Args:
            power_type (str): The type of power
            amount (int): The amount of experience to add

        Returns:
            dict: Information about the power update, including level ups
        """
        if power_type not in self.player_powers:
            return {"success": False, "message": f"Player does not have {power_type} power"}

        power_data = self.player_powers[power_type]
        old_level = power_data['level']
        power_data['experience'] += amount

        # Check for level up
        exp_needed = old_level * 100  # Simple formula: level * 100 exp needed for next level
        if power_data['experience'] >= exp_needed:
            power_data['level'] += 1
            power_data['experience'] -= exp_needed

            # Check for newly unlockable skills
            newly_unlocked = self._check_unlockable_skills(power_type, power_data['level'])

            self.save_data()
            return {
                "success": True, 
                "level_up": True, 
                "old_level": old_level, 
                "new_level": power_data['level'],
                "newly_unlocked_skills": newly_unlocked
            }

        self.save_data()
        return {"success": True, "level_up": False}

    def _check_unlockable_skills(self, power_type, level):
        """
        Check for skills that can be unlocked at the current level.

        Args:
            power_type (str): The type of power
            level (int): The current power level

        Returns:
            list: Newly unlockable skills
        """
        newly_unlocked = []

        if power_type in self.power_data and 'skill_tree' in self.power_data[power_type]:
            skill_tree = self.power_data[power_type]['skill_tree']

            # Check all tiers of skills
            for tier in ['basic', 'intermediate', 'advanced']:
                if tier in skill_tree:
                    for skill_id, skill_data in skill_tree[tier].items():
                        skill_key = f"{power_type}:{skill_id}"

                        # Skip already unlocked skills
                        if skill_key in self.unlocked_skills:
                            continue

                        # Check if requirements are met
                        requirements = skill_data.get('requirements', {})
                        if requirements.get('level', 99) <= level:
                            # Check if required skills are unlocked
                            required_skills = requirements.get('skills', [])
                            all_skills_unlocked = all(
                                f"{power_type}:{req_skill}" in self.unlocked_skills 
                                for req_skill in required_skills
                            )

                            # Check if required ritual is completed
                            required_ritual = requirements.get('ritual')
                            ritual_completed = not required_ritual or required_ritual in self.completed_rituals

                            if all_skills_unlocked and ritual_completed:
                                newly_unlocked.append(skill_key)

        return newly_unlocked

    def unlock_skill(self, power_type, skill_id):
        """
        Unlock a specific skill.

        Args:
            power_type (str): The type of power
            skill_id (str): The ID of the skill

        Returns:
            bool: True if successful, False otherwise
        """
        skill_key = f"{power_type}:{skill_id}"

        # Check if skill exists
        if power_type not in self.power_data:
            return False

        skill_found = False
        skill_data = None

        for tier in ['basic', 'intermediate', 'advanced']:
            tier_skills = self.power_data[power_type]['skill_tree'].get(tier, {})
            if skill_id in tier_skills:
                skill_found = True
                skill_data = tier_skills[skill_id]
                break

        if not skill_found:
            return False

        # Check requirements
        requirements = skill_data.get('requirements', {})

        # Check level requirement
        if self.get_power_level(power_type) < requirements.get('level', 0):
            return False

        # Check required skills
        for req_skill in requirements.get('skills', []):
            if f"{power_type}:{req_skill}" not in self.unlocked_skills:
                return False

        # Check required ritual
        required_ritual = requirements.get('ritual')
        if required_ritual and required_ritual not in self.completed_rituals:
            return False

        # All requirements met, unlock the skill
        self.unlocked_skills.add(skill_key)
        self.save_data()
        return True

    def get_unlocked_skills(self, power_type=None):
        """
        Get all unlocked skills, optionally filtered by power type.

        Args:
            power_type (str, optional): The type of power

        Returns:
            list: The unlocked skills
        """
        if power_type:
            return [skill.split(':', 1)[1] for skill in self.unlocked_skills 
                   if skill.startswith(f"{power_type}:")]
        return list(self.unlocked_skills)

    def get_skill_data(self, power_type, skill_id):
        """
        Get data for a specific skill.

        Args:
            power_type (str): The type of power
            skill_id (str): The ID of the skill

        Returns:
            dict: The skill data, or None if not found
        """
        if power_type not in self.power_data:
            return None

        for tier in ['basic', 'intermediate', 'advanced']:
            tier_skills = self.power_data[power_type]['skill_tree'].get(tier, {})
            if skill_id in tier_skills:
                return tier_skills[skill_id]

        return None

    def get_available_rituals(self, power_type):
        """
        Get rituals that are available but not yet completed.

        Args:
            power_type (str): The type of power

        Returns:
            dict: Available rituals and their data
        """
        if power_type not in self.power_data or 'rituals' not in self.power_data[power_type]:
            return {}

        available_rituals = {}
        power_level = self.get_power_level(power_type)

        for ritual_id, ritual_data in self.power_data[power_type]['rituals'].items():
            # Skip completed rituals
            if ritual_id in self.completed_rituals:
                continue

            # Check level requirement
            if power_level < ritual_data.get('requirements', {}).get('level', 99):
                continue

            # Check required rituals
            required_rituals = ritual_data.get('requirements', {}).get('rituals', [])
            if not all(req_ritual in self.completed_rituals for req_ritual in required_rituals):
                continue

            # Ritual is available
            available_rituals[ritual_id] = ritual_data

        return available_rituals

    def complete_ritual(self, power_type, ritual_id):
        """
        Mark a ritual as completed and apply its effects.

        Args:
            power_type (str): The type of power
            ritual_id (str): The ID of the ritual

        Returns:
            dict: The results of completing the ritual
        """
        if power_type not in self.power_data or 'rituals' not in self.power_data[power_type]:
            return {"success": False, "message": "Power type or rituals not found"}

        if ritual_id not in self.power_data[power_type]['rituals']:
            return {"success": False, "message": "Ritual not found"}

        if ritual_id in self.completed_rituals:
            return {"success": False, "message": "Ritual already completed"}

        ritual_data = self.power_data[power_type]['rituals'][ritual_id]

        # Check requirements
        requirements = ritual_data.get('requirements', {})

        # Check level requirement
        if self.get_power_level(power_type) < requirements.get('level', 0):
            return {"success": False, "message": "Level requirement not met"}

        # Check required rituals
        for req_ritual in requirements.get('rituals', []):
            if req_ritual not in self.completed_rituals:
                return {"success": False, "message": f"Required ritual {req_ritual} not completed"}

        # Check required items (this would need to be integrated with an inventory system)
        # For now, we'll assume the items are available

        # Mark ritual as completed
        self.completed_rituals.add(ritual_id)

        # Apply effects
        effects = ritual_data.get('effects', {})
        results = {"success": True, "effects_applied": []}

        # Unlock skill if specified
        if 'unlock_skill' in effects:
            skill_id = effects['unlock_skill']
            if self.unlock_skill(power_type, skill_id):
                results["effects_applied"].append(f"Unlocked skill: {skill_id}")

        # Apply power boost if specified
        if 'power_boost' in effects:
            boost = effects['power_boost']
            if power_type in self.player_powers:
                self.player_powers[power_type]['mastery'] += boost
                results["effects_applied"].append(f"Power mastery increased by {boost}")

        # Apply other effects as needed

        self.save_data()
        return results

    def get_available_challenges(self, power_type):
        """
        Get challenges that are available but not yet completed.

        Args:
            power_type (str): The type of power

        Returns:
            dict: Available challenges and their data
        """
        if power_type not in self.power_data or 'challenges' not in self.power_data[power_type]:
            return {}

        available_challenges = {}
        power_level = self.get_power_level(power_type)

        for challenge_id, challenge_data in self.power_data[power_type]['challenges'].items():
            # Skip completed challenges
            if challenge_id in self.completed_challenges:
                continue

            # Check requirements (simplified for now)
            requirements = challenge_data.get('requirements', {})

            # For now, we'll just check if the player has the required power level
            # In a real implementation, you'd check all requirements
            if power_level < requirements.get('power_level', 0):
                continue

            # Challenge is available
            available_challenges[challenge_id] = challenge_data

        return available_challenges

    def complete_challenge(self, power_type, challenge_id):
        """
        Mark a challenge as completed and apply its rewards.

        Args:
            power_type (str): The type of power
            challenge_id (str): The ID of the challenge

        Returns:
            dict: The results of completing the challenge
        """
        if power_type not in self.power_data or 'challenges' not in self.power_data[power_type]:
            return {"success": False, "message": "Power type or challenges not found"}

        if challenge_id not in self.power_data[power_type]['challenges']:
            return {"success": False, "message": "Challenge not found"}

        if challenge_id in self.completed_challenges:
            return {"success": False, "message": "Challenge already completed"}

        challenge_data = self.power_data[power_type]['challenges'][challenge_id]

        # Mark challenge as completed
        self.completed_challenges.add(challenge_id)

        # Apply rewards
        rewards = challenge_data.get('rewards', {})
        results = {"success": True, "rewards_applied": []}

        # Apply experience reward
        if 'exp' in rewards:
            exp = rewards['exp']
            self.increase_power_experience(power_type, exp)
            results["rewards_applied"].append(f"Gained {exp} experience")

        # Unlock ritual if specified
        if 'unlock_ritual' in rewards:
            ritual_id = rewards['unlock_ritual']
            results["rewards_applied"].append(f"Unlocked ritual: {ritual_id}")

        # Add special item if specified (would need inventory integration)
        if 'special_item' in rewards:
            item = rewards['special_item']
            results["rewards_applied"].append(f"Received special item: {item}")

        self.save_data()
        return results

    def get_skill_tree(self, power_type):
        """
        Get the full skill tree for a power type, with unlocked status.

        Args:
            power_type (str): The type of power

        Returns:
            dict: The skill tree with unlocked status
        """
        if power_type not in self.power_data or 'skill_tree' not in self.power_data[power_type]:
            return {}

        skill_tree = self.power_data[power_type]['skill_tree']
        result = {}

        for tier, skills in skill_tree.items():
            result[tier] = {}
            for skill_id, skill_data in skills.items():
                # Copy skill data and add unlocked status
                skill_copy = skill_data.copy()
                skill_copy['unlocked'] = f"{power_type}:{skill_id}" in self.unlocked_skills
                result[tier][skill_id] = skill_copy

        return result

    def get_power_summary(self, power_type):
        """
        Get a summary of a player's power, including level, skills, rituals, and challenges.

        Args:
            power_type (str): The type of power

        Returns:
            dict: The power summary
        """
        if power_type not in self.player_powers:
            return {"error": "Player does not have this power"}

        power_data = self.player_powers[power_type]

        return {
            "power_type": power_type,
            "level": power_data['level'],
            "experience": power_data['experience'],
            "mastery": power_data['mastery'],
            "unlocked_skills": self.get_unlocked_skills(power_type),
            "completed_rituals": [ritual for ritual in self.completed_rituals 
                                if ritual in self.power_data.get(power_type, {}).get('rituals', {})],
            "completed_challenges": [challenge for challenge in self.completed_challenges 
                                   if challenge in self.power_data.get(power_type, {}).get('challenges', {})]
        }
