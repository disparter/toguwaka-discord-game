"""
Companion System

This module implements a system for companions, including recruitable NPCs,
character arcs, and a "Synchronization" power-combining system.
"""

import json
import os
import random
from datetime import datetime
from collections import defaultdict

class CompanionManager:
    """
    Manages companions, their development arcs, and power synchronization.
    """
    
    def __init__(self, player_id):
        """
        Initialize the companion manager for a specific player.
        
        Args:
            player_id (str): The unique identifier for the player
        """
        self.player_id = player_id
        self.companion_data = self._load_companion_data()
        self.active_companions = []
        self.companion_relationships = {}
        self.completed_arcs = set()
        self.synchronization_data = {}
        self.load_data()
    
    def _load_companion_data(self):
        """
        Load companion data from the data file.
        
        Returns:
            dict: The companion data
        """
        try:
            file_path = "data/story_mode/npcs/companions.json"
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # Create default companion data if file doesn't exist
                companion_data = self._create_default_companion_data()
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(companion_data, f, ensure_ascii=False, indent=2)
                return companion_data
        except Exception as e:
            print(f"Error loading companion data: {e}")
            return self._create_default_companion_data()
    
    def _create_default_companion_data(self):
        """
        Create default companion data.
        
        Returns:
            dict: The default companion data
        """
        return {
            "kai_flameheart": {
                "name": "Kai Flameheart",
                "description": "Um prodígio na manipulação do fogo, com um passado trágico e uma determinação inabalável.",
                "power_type": "Fogo",
                "recruitment": {
                    "chapter": "2_3",
                    "requirements": {
                        "min_affinity": 50,
                        "completed_quest": "ajudando_kai"
                    }
                },
                "character_arc": {
                    "stages": [
                        {
                            "id": "confianca_inicial",
                            "name": "Confiança Inicial",
                            "description": "Kai começa a confiar em você o suficiente para compartilhar algumas de suas preocupações.",
                            "requirements": {
                                "affinity": 60,
                                "completed_events": ["treinamento_com_kai"]
                            },
                            "rewards": {
                                "exp": 200,
                                "special_dialogue": "kai_confianca_1",
                                "skill_unlock": "chama_compartilhada"
                            }
                        },
                        {
                            "id": "enfrentando_o_passado",
                            "name": "Enfrentando o Passado",
                            "description": "Ajude Kai a enfrentar os traumas de seu passado relacionados à perda de seus pais.",
                            "requirements": {
                                "affinity": 75,
                                "completed_events": ["pesadelo_de_kai", "visita_ao_memorial"]
                            },
                            "rewards": {
                                "exp": 500,
                                "special_dialogue": "kai_confianca_2",
                                "skill_unlock": "chamas_da_superacao"
                            }
                        },
                        {
                            "id": "controle_total",
                            "name": "Controle Total",
                            "description": "Ajude Kai a dominar completamente seus poderes, incluindo o controle durante emoções intensas.",
                            "requirements": {
                                "affinity": 90,
                                "completed_events": ["treinamento_avancado", "teste_emocional"]
                            },
                            "rewards": {
                                "exp": 1000,
                                "special_dialogue": "kai_confianca_3",
                                "skill_unlock": "sincronizacao_flamejante"
                            }
                        }
                    ]
                },
                "synchronization": {
                    "name": "Sincronização Flamejante",
                    "description": "Uma poderosa combinação que funde seus poderes com as chamas de Kai, criando um fogo controlado com precisão e intensidade sem precedentes.",
                    "requirements": {
                        "player_level": 15,
                        "companion_arc_stage": "controle_total",
                        "affinity": 95
                    },
                    "effects": {
                        "damage_boost": 50,
                        "fire_resistance": 75,
                        "special_attack": "inferno_duplo",
                        "duration": 5
                    },
                    "cooldown": 24  # hours
                }
            },
            "luna_mindweaver": {
                "name": "Luna Mindweaver",
                "description": "Uma telepata poderosa e misteriosa, com segredos sobre a academia e uma busca por controle mental.",
                "power_type": "Mental",
                "recruitment": {
                    "chapter": "2_5",
                    "requirements": {
                        "min_affinity": 50,
                        "completed_quest": "segredos_da_biblioteca"
                    }
                },
                "character_arc": {
                    "stages": [
                        {
                            "id": "conexao_mental",
                            "name": "Conexão Mental",
                            "description": "Luna estabelece uma conexão mental básica com você, permitindo comunicação telepática limitada.",
                            "requirements": {
                                "affinity": 60,
                                "completed_events": ["meditacao_conjunta"]
                            },
                            "rewards": {
                                "exp": 200,
                                "special_dialogue": "luna_conexao_1",
                                "skill_unlock": "comunicacao_telepatica"
                            }
                        },
                        {
                            "id": "descobertas_proibidas",
                            "name": "Descobertas Proibidas",
                            "description": "Ajude Luna a investigar os experimentos secretos da academia sem serem descobertos.",
                            "requirements": {
                                "affinity": 75,
                                "completed_events": ["infiltracao_laboratorio", "decifrando_documentos"]
                            },
                            "rewards": {
                                "exp": 500,
                                "special_dialogue": "luna_conexao_2",
                                "skill_unlock": "escudo_mental"
                            }
                        },
                        {
                            "id": "mentes_unidas",
                            "name": "Mentes Unidas",
                            "description": "Estabeleça uma conexão mental profunda com Luna, permitindo compartilhar pensamentos e memórias.",
                            "requirements": {
                                "affinity": 90,
                                "completed_events": ["ritual_mental", "sincronizacao_de_memorias"]
                            },
                            "rewards": {
                                "exp": 1000,
                                "special_dialogue": "luna_conexao_3",
                                "skill_unlock": "sincronizacao_mental"
                            }
                        }
                    ]
                },
                "synchronization": {
                    "name": "Sincronização Mental",
                    "description": "Uma fusão de mentes que amplifica drasticamente os poderes telepáticos e permite ataques psíquicos coordenados.",
                    "requirements": {
                        "player_level": 15,
                        "companion_arc_stage": "mentes_unidas",
                        "affinity": 95
                    },
                    "effects": {
                        "mental_power_boost": 75,
                        "mind_reading_range": 100,
                        "special_attack": "onda_psionica_dupla",
                        "duration": 3
                    },
                    "cooldown": 48  # hours
                }
            },
            "gaia_naturae": {
                "name": "Gaia Naturae",
                "description": "Uma elementalista conectada profundamente com a natureza, buscando equilíbrio entre tradição e modernidade.",
                "power_type": "Terra",
                "recruitment": {
                    "chapter": "3_2",
                    "requirements": {
                        "min_affinity": 50,
                        "completed_quest": "equilibrio_natural"
                    }
                },
                "character_arc": {
                    "stages": [
                        {
                            "id": "harmonia_elemental",
                            "name": "Harmonia Elemental",
                            "description": "Gaia ensina os princípios básicos da harmonia com os elementos naturais.",
                            "requirements": {
                                "affinity": 60,
                                "completed_events": ["meditacao_no_bosque"]
                            },
                            "rewards": {
                                "exp": 200,
                                "special_dialogue": "gaia_harmonia_1",
                                "skill_unlock": "toque_da_natureza"
                            }
                        },
                        {
                            "id": "comunhao_espiritual",
                            "name": "Comunhão Espiritual",
                            "description": "Ajude Gaia a se comunicar com os espíritos elementais e aprenda a perceber sua presença.",
                            "requirements": {
                                "affinity": 75,
                                "completed_events": ["ritual_dos_elementos", "chamado_dos_espiritos"]
                            },
                            "rewards": {
                                "exp": 500,
                                "special_dialogue": "gaia_harmonia_2",
                                "skill_unlock": "visao_elemental"
                            }
                        },
                        {
                            "id": "unidade_com_a_natureza",
                            "name": "Unidade com a Natureza",
                            "description": "Alcance um estado de completa harmonia com a natureza, permitindo manipulação elemental avançada.",
                            "requirements": {
                                "affinity": 90,
                                "completed_events": ["peregrinacao_sagrada", "teste_dos_elementos"]
                            },
                            "rewards": {
                                "exp": 1000,
                                "special_dialogue": "gaia_harmonia_3",
                                "skill_unlock": "sincronizacao_elemental"
                            }
                        }
                    ]
                },
                "synchronization": {
                    "name": "Sincronização Elemental",
                    "description": "Uma fusão harmoniosa com os poderes elementais de Gaia, permitindo controlar múltiplos elementos simultaneamente com precisão perfeita.",
                    "requirements": {
                        "player_level": 15,
                        "companion_arc_stage": "unidade_com_a_natureza",
                        "affinity": 95
                    },
                    "effects": {
                        "elemental_control": 100,
                        "multi_element_casting": True,
                        "special_attack": "tempestade_elemental",
                        "duration": 4
                    },
                    "cooldown": 36  # hours
                }
            },
            "alexander_strategos": {
                "name": "Alexander Strategos",
                "description": "Um estrategista brilhante e manipulador, com conexões políticas e ambições de poder.",
                "power_type": "Persuasão",
                "recruitment": {
                    "chapter": "4_1",
                    "requirements": {
                        "min_affinity": 50,
                        "completed_quest": "alianca_estrategica"
                    }
                },
                "character_arc": {
                    "stages": [
                        {
                            "id": "alianca_tatica",
                            "name": "Aliança Tática",
                            "description": "Alexander propõe uma aliança mutuamente benéfica, compartilhando informações básicas.",
                            "requirements": {
                                "affinity": 60,
                                "completed_events": ["negociacao_inicial"]
                            },
                            "rewards": {
                                "exp": 200,
                                "special_dialogue": "alexander_alianca_1",
                                "skill_unlock": "persuasao_basica"
                            }
                        },
                        {
                            "id": "manipulacao_politica",
                            "name": "Manipulação Política",
                            "description": "Trabalhe com Alexander para influenciar o Conselho Estudantil e ganhar poder político na academia.",
                            "requirements": {
                                "affinity": 75,
                                "completed_events": ["eleicao_do_conselho", "manipulacao_de_votos"]
                            },
                            "rewards": {
                                "exp": 500,
                                "special_dialogue": "alexander_alianca_2",
                                "skill_unlock": "rede_de_informantes"
                            }
                        },
                        {
                            "id": "mestre_estrategista",
                            "name": "Mestre Estrategista",
                            "description": "Desenvolva habilidades avançadas de estratégia e manipulação política com Alexander.",
                            "requirements": {
                                "affinity": 90,
                                "completed_events": ["golpe_politico", "dominacao_do_conselho"]
                            },
                            "rewards": {
                                "exp": 1000,
                                "special_dialogue": "alexander_alianca_3",
                                "skill_unlock": "sincronizacao_estrategica"
                            }
                        }
                    ]
                },
                "synchronization": {
                    "name": "Sincronização Estratégica",
                    "description": "Uma combinação de habilidades persuasivas que permite manipular grupos inteiros e prever movimentos políticos com precisão assustadora.",
                    "requirements": {
                        "player_level": 15,
                        "companion_arc_stage": "mestre_estrategista",
                        "affinity": 95
                    },
                    "effects": {
                        "persuasion_power": 100,
                        "strategic_foresight": 75,
                        "special_ability": "manipulacao_em_massa",
                        "duration": 6
                    },
                    "cooldown": 72  # hours
                }
            }
        }
    
    def load_data(self):
        """Load player companion data from storage if it exists."""
        try:
            file_path = f"data/player_data/{self.player_id}/companions.json"
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.active_companions = data.get('active_companions', [])
                    self.companion_relationships = data.get('companion_relationships', {})
                    self.completed_arcs = set(data.get('completed_arcs', []))
                    self.synchronization_data = data.get('synchronization_data', {})
        except Exception as e:
            print(f"Error loading companion data: {e}")
    
    def save_data(self):
        """Save player companion data to storage."""
        try:
            file_path = f"data/player_data/{self.player_id}/companions.json"
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            data = {
                'active_companions': self.active_companions,
                'companion_relationships': self.companion_relationships,
                'completed_arcs': list(self.completed_arcs),
                'synchronization_data': self.synchronization_data
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving companion data: {e}")
    
    def get_available_companions(self, current_chapter, player_affinities):
        """
        Get companions that are available for recruitment but not yet recruited.
        
        Args:
            current_chapter (str): The current chapter the player is on
            player_affinities (dict): The player's affinities with NPCs
            
        Returns:
            list: Available companions and their data
        """
        available_companions = []
        
        for companion_id, companion_data in self.companion_data.items():
            # Skip already recruited companions
            if companion_id in self.active_companions:
                continue
            
            # Check recruitment requirements
            recruitment = companion_data.get('recruitment', {})
            required_chapter = recruitment.get('chapter', '')
            
            # Check if the player has reached the required chapter
            if self._compare_chapters(current_chapter, required_chapter) < 0:
                continue
            
            # Check affinity requirement
            min_affinity = recruitment.get('requirements', {}).get('min_affinity', 0)
            current_affinity = player_affinities.get(companion_id, 0)
            
            if current_affinity < min_affinity:
                continue
            
            # Check quest requirement
            required_quest = recruitment.get('requirements', {}).get('completed_quest', '')
            # In a real implementation, you would check if the player has completed the quest
            # For now, we'll assume the quest is completed if the affinity is high enough
            
            # Companion is available
            available_companions.append({
                'id': companion_id,
                'name': companion_data.get('name', ''),
                'description': companion_data.get('description', ''),
                'power_type': companion_data.get('power_type', ''),
                'requirements_met': True  # In a real implementation, this would be based on all requirements
            })
        
        return available_companions
    
    def _compare_chapters(self, chapter1, chapter2):
        """
        Compare two chapter IDs to determine which comes first.
        
        Args:
            chapter1 (str): The first chapter ID
            chapter2 (str): The second chapter ID
            
        Returns:
            int: -1 if chapter1 comes before chapter2, 0 if equal, 1 if chapter1 comes after chapter2
        """
        try:
            # Parse chapter IDs like "2_3" into [2, 3]
            ch1_parts = [int(part) for part in chapter1.split('_')]
            ch2_parts = [int(part) for part in chapter2.split('_')]
            
            # Compare major chapter first
            if ch1_parts[0] < ch2_parts[0]:
                return -1
            elif ch1_parts[0] > ch2_parts[0]:
                return 1
            
            # If major chapters are equal, compare minor chapter
            if len(ch1_parts) > 1 and len(ch2_parts) > 1:
                if ch1_parts[1] < ch2_parts[1]:
                    return -1
                elif ch1_parts[1] > ch2_parts[1]:
                    return 1
            
            # If we get here, the chapters are equal or one is a subset of the other
            return 0
        except:
            # If there's any error in parsing, just do string comparison
            if chapter1 < chapter2:
                return -1
            elif chapter1 > chapter2:
                return 1
            return 0
    
    def recruit_companion(self, companion_id):
        """
        Recruit a companion.
        
        Args:
            companion_id (str): The ID of the companion to recruit
            
        Returns:
            dict: The result of recruiting the companion
        """
        if companion_id not in self.companion_data:
            return {"success": False, "message": "Companion not found"}
        
        if companion_id in self.active_companions:
            return {"success": False, "message": "Companion already recruited"}
        
        # In a real implementation, you would check all recruitment requirements here
        
        # Add companion to active companions
        self.active_companions.append(companion_id)
        
        # Initialize relationship data
        self.companion_relationships[companion_id] = {
            'affinity': 50,  # Start with neutral affinity
            'current_arc_stage': None,
            'completed_events': [],
            'last_interaction': datetime.now().isoformat()
        }
        
        self.save_data()
        return {
            "success": True, 
            "message": f"Successfully recruited {self.companion_data[companion_id]['name']}!"
        }
    
    def get_active_companions(self):
        """
        Get all active companions.
        
        Returns:
            list: The active companions with their data
        """
        companions = []
        
        for companion_id in self.active_companions:
            if companion_id in self.companion_data:
                companion = self.companion_data[companion_id].copy()
                companion['id'] = companion_id
                companion['relationship'] = self.companion_relationships.get(companion_id, {})
                companions.append(companion)
        
        return companions
    
    def get_companion_data(self, companion_id):
        """
        Get data for a specific companion.
        
        Args:
            companion_id (str): The ID of the companion
            
        Returns:
            dict: The companion data
        """
        if companion_id not in self.companion_data:
            return None
        
        companion = self.companion_data[companion_id].copy()
        companion['id'] = companion_id
        
        if companion_id in self.companion_relationships:
            companion['relationship'] = self.companion_relationships[companion_id]
        
        return companion
    
    def change_affinity(self, companion_id, amount, reason=None):
        """
        Change the affinity with a companion.
        
        Args:
            companion_id (str): The ID of the companion
            amount (int): The amount to change the affinity by (positive or negative)
            reason (str, optional): The reason for the affinity change
            
        Returns:
            int: The new affinity value
        """
        if companion_id not in self.active_companions or companion_id not in self.companion_relationships:
            return 0
        
        # Update affinity
        self.companion_relationships[companion_id]['affinity'] += amount
        
        # Clamp affinity between 0 and 100
        self.companion_relationships[companion_id]['affinity'] = max(0, min(100, self.companion_relationships[companion_id]['affinity']))
        
        # Update last interaction
        self.companion_relationships[companion_id]['last_interaction'] = datetime.now().isoformat()
        
        # Check for arc progression
        self._check_arc_progression(companion_id)
        
        self.save_data()
        return self.companion_relationships[companion_id]['affinity']
    
    def complete_companion_event(self, companion_id, event_id):
        """
        Mark a companion event as completed.
        
        Args:
            companion_id (str): The ID of the companion
            event_id (str): The ID of the event
            
        Returns:
            dict: The result of completing the event
        """
        if companion_id not in self.active_companions or companion_id not in self.companion_relationships:
            return {"success": False, "message": "Companion not active"}
        
        # Add event to completed events
        if event_id not in self.companion_relationships[companion_id]['completed_events']:
            self.companion_relationships[companion_id]['completed_events'].append(event_id)
        
        # Update last interaction
        self.companion_relationships[companion_id]['last_interaction'] = datetime.now().isoformat()
        
        # Check for arc progression
        result = self._check_arc_progression(companion_id)
        
        self.save_data()
        
        if result:
            return {
                "success": True, 
                "message": f"Event completed and advanced to arc stage: {result['stage_name']}"
            }
        else:
            return {"success": True, "message": "Event completed"}
    
    def _check_arc_progression(self, companion_id):
        """
        Check if the companion can progress to the next arc stage.
        
        Args:
            companion_id (str): The ID of the companion
            
        Returns:
            dict or None: The new arc stage data if progressed, None otherwise
        """
        if companion_id not in self.companion_data:
            return None
        
        relationship = self.companion_relationships.get(companion_id, {})
        current_stage = relationship.get('current_arc_stage')
        completed_events = relationship.get('completed_events', [])
        affinity = relationship.get('affinity', 0)
        
        # Get character arc data
        arc_data = self.companion_data[companion_id].get('character_arc', {})
        stages = arc_data.get('stages', [])
        
        # Find the next stage
        next_stage = None
        
        if current_stage is None:
            # If no current stage, check the first stage
            if stages:
                next_stage = stages[0]
        else:
            # Find the current stage index
            current_index = -1
            for i, stage in enumerate(stages):
                if stage.get('id') == current_stage:
                    current_index = i
                    break
            
            # Check if there's a next stage
            if current_index >= 0 and current_index < len(stages) - 1:
                next_stage = stages[current_index + 1]
        
        # Check if the next stage requirements are met
        if next_stage:
            requirements = next_stage.get('requirements', {})
            required_affinity = requirements.get('affinity', 0)
            required_events = requirements.get('completed_events', [])
            
            if affinity >= required_affinity and all(event in completed_events for event in required_events):
                # Requirements met, progress to next stage
                stage_id = next_stage.get('id')
                self.companion_relationships[companion_id]['current_arc_stage'] = stage_id
                
                # Add to completed arcs if this is the final stage
                if stages.index(next_stage) == len(stages) - 1:
                    self.completed_arcs.add(f"{companion_id}:character_arc")
                
                return {
                    "stage_id": stage_id,
                    "stage_name": next_stage.get('name'),
                    "rewards": next_stage.get('rewards', {})
                }
        
        return None
    
    def get_character_arc_progress(self, companion_id):
        """
        Get the progress of a companion's character arc.
        
        Args:
            companion_id (str): The ID of the companion
            
        Returns:
            dict: The character arc progress
        """
        if companion_id not in self.companion_data:
            return {"error": "Companion not found"}
        
        relationship = self.companion_relationships.get(companion_id, {})
        current_stage = relationship.get('current_arc_stage')
        completed_events = relationship.get('completed_events', [])
        affinity = relationship.get('affinity', 0)
        
        # Get character arc data
        arc_data = self.companion_data[companion_id].get('character_arc', {})
        stages = arc_data.get('stages', [])
        
        # Calculate progress for each stage
        stage_progress = []
        
        for stage in stages:
            stage_id = stage.get('id')
            requirements = stage.get('requirements', {})
            required_affinity = requirements.get('affinity', 0)
            required_events = requirements.get('completed_events', [])
            
            # Calculate completion percentage
            affinity_met = affinity >= required_affinity
            events_completed = sum(1 for event in required_events if event in completed_events)
            events_total = len(required_events)
            
            if events_total == 0:
                events_percentage = 100 if affinity_met else 0
            else:
                events_percentage = (events_completed / events_total) * 100
            
            affinity_percentage = (min(affinity, required_affinity) / required_affinity) * 100 if required_affinity > 0 else 100
            
            # Overall percentage is the average of affinity and events percentages
            overall_percentage = (affinity_percentage + events_percentage) / 2
            
            # Check if this stage is completed
            completed = current_stage == stage_id or stages.index(stage) < [s.get('id') for s in stages].index(current_stage) if current_stage else -1
            
            stage_progress.append({
                "id": stage_id,
                "name": stage.get('name'),
                "description": stage.get('description'),
                "affinity_required": required_affinity,
                "affinity_current": affinity,
                "events_required": required_events,
                "events_completed": [event for event in required_events if event in completed_events],
                "percentage": overall_percentage,
                "completed": completed,
                "is_current": current_stage == stage_id
            })
        
        return {
            "companion_id": companion_id,
            "companion_name": self.companion_data[companion_id].get('name'),
            "current_stage": current_stage,
            "stages": stage_progress,
            "completed": f"{companion_id}:character_arc" in self.completed_arcs
        }
    
    def can_synchronize(self, companion_id, player_level):
        """
        Check if the player can synchronize with a companion.
        
        Args:
            companion_id (str): The ID of the companion
            player_level (int): The player's level
            
        Returns:
            dict: The result of the check
        """
        if companion_id not in self.active_companions:
            return {"can_synchronize": False, "reason": "Companion not active"}
        
        if companion_id not in self.companion_data:
            return {"can_synchronize": False, "reason": "Companion data not found"}
        
        # Get synchronization data
        sync_data = self.companion_data[companion_id].get('synchronization', {})
        requirements = sync_data.get('requirements', {})
        
        # Check player level
        required_level = requirements.get('player_level', 0)
        if player_level < required_level:
            return {
                "can_synchronize": False, 
                "reason": f"Player level too low (need {required_level})"
            }
        
        # Check companion arc stage
        required_stage = requirements.get('companion_arc_stage', '')
        current_stage = self.companion_relationships.get(companion_id, {}).get('current_arc_stage')
        
        if required_stage != current_stage:
            return {
                "can_synchronize": False, 
                "reason": f"Character arc not advanced enough (need {required_stage})"
            }
        
        # Check affinity
        required_affinity = requirements.get('affinity', 0)
        current_affinity = self.companion_relationships.get(companion_id, {}).get('affinity', 0)
        
        if current_affinity < required_affinity:
            return {
                "can_synchronize": False, 
                "reason": f"Affinity too low (need {required_affinity})"
            }
        
        # Check cooldown
        last_sync = self.synchronization_data.get(companion_id, {}).get('last_sync')
        if last_sync:
            last_sync_time = datetime.fromisoformat(last_sync)
            cooldown_hours = sync_data.get('cooldown', 24)
            cooldown_delta = timedelta(hours=cooldown_hours)
            
            if datetime.now() - last_sync_time < cooldown_delta:
                time_left = cooldown_delta - (datetime.now() - last_sync_time)
                hours, remainder = divmod(time_left.seconds, 3600)
                minutes, _ = divmod(remainder, 60)
                
                return {
                    "can_synchronize": False, 
                    "reason": f"On cooldown ({hours}h {minutes}m remaining)"
                }
        
        return {"can_synchronize": True}
    
    def synchronize(self, companion_id, player_level):
        """
        Synchronize with a companion to combine powers.
        
        Args:
            companion_id (str): The ID of the companion
            player_level (int): The player's level
            
        Returns:
            dict: The result of the synchronization
        """
        # Check if synchronization is possible
        check_result = self.can_synchronize(companion_id, player_level)
        if not check_result.get('can_synchronize', False):
            return {
                "success": False, 
                "message": check_result.get('reason', "Cannot synchronize")
            }
        
        # Get synchronization data
        sync_data = self.companion_data[companion_id].get('synchronization', {})
        effects = sync_data.get('effects', {})
        
        # Record synchronization
        if companion_id not in self.synchronization_data:
            self.synchronization_data[companion_id] = {}
        
        self.synchronization_data[companion_id]['last_sync'] = datetime.now().isoformat()
        self.synchronization_data[companion_id]['active_until'] = (datetime.now() + timedelta(minutes=effects.get('duration', 5))).isoformat()
        
        self.save_data()
        
        return {
            "success": True,
            "message": f"Successfully synchronized with {self.companion_data[companion_id]['name']}!",
            "effects": effects,
            "duration": effects.get('duration', 5)
        }
    
    def get_active_synchronizations(self):
        """
        Get all active synchronizations.
        
        Returns:
            list: The active synchronizations
        """
        active_syncs = []
        current_time = datetime.now()
        
        for companion_id, sync_data in self.synchronization_data.items():
            if 'active_until' in sync_data:
                end_time = datetime.fromisoformat(sync_data['active_until'])
                
                if current_time < end_time:
                    # Synchronization is still active
                    companion_name = self.companion_data.get(companion_id, {}).get('name', companion_id)
                    effects = self.companion_data.get(companion_id, {}).get('synchronization', {}).get('effects', {})
                    
                    time_left = end_time - current_time
                    minutes, seconds = divmod(time_left.seconds, 60)
                    
                    active_syncs.append({
                        "companion_id": companion_id,
                        "companion_name": companion_name,
                        "effects": effects,
                        "time_left": f"{minutes}m {seconds}s"
                    })
        
        return active_syncs
    
    def get_synchronization_effects(self, player_power_type=None):
        """
        Get the combined effects of all active synchronizations.
        
        Args:
            player_power_type (str, optional): The player's power type
            
        Returns:
            dict: The combined effects
        """
        combined_effects = {}
        current_time = datetime.now()
        
        for companion_id, sync_data in self.synchronization_data.items():
            if 'active_until' in sync_data:
                end_time = datetime.fromisoformat(sync_data['active_until'])
                
                if current_time < end_time:
                    # Synchronization is still active
                    effects = self.companion_data.get(companion_id, {}).get('synchronization', {}).get('effects', {})
                    companion_power = self.companion_data.get(companion_id, {}).get('power_type')
                    
                    # Apply effects based on power compatibility
                    for effect, value in effects.items():
                        if effect in combined_effects:
                            # For numerical effects, take the highest value
                            if isinstance(value, (int, float)) and isinstance(combined_effects[effect], (int, float)):
                                combined_effects[effect] = max(combined_effects[effect], value)
                            # For boolean effects, OR them together
                            elif isinstance(value, bool) and isinstance(combined_effects[effect], bool):
                                combined_effects[effect] = combined_effects[effect] or value
                            # For other effects, just overwrite
                            else:
                                combined_effects[effect] = value
                        else:
                            combined_effects[effect] = value
                    
                    # Add special attack if compatible with player's power
                    if player_power_type and player_power_type == companion_power:
                        special_attack = effects.get('special_attack')
                        if special_attack:
                            combined_effects['special_attacks'] = combined_effects.get('special_attacks', []) + [special_attack]
        
        return combined_effects