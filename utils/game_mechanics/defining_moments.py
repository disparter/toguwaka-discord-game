"""
Defining Moments System

This module implements the "Defining Moments" system, where player choices converge
to create significant consequences that shape the player's story.
"""

import json
import os
from datetime import datetime
import random

class DefiningMomentManager:
    """
    Manages the creation and triggering of defining moments based on player choices.
    """

    def __init__(self, player_id):
        """
        Initialize the defining moment manager for a specific player.

        Args:
            player_id (str): The unique identifier for the player
        """
        self.player_id = player_id
        self.defining_moment_templates = self._load_templates()

    def _load_templates(self):
        """
        Load defining moment templates from the data file.

        Returns:
            dict: The defining moment templates
        """
        try:
            file_path = "data/story_mode/defining_moments/templates.json"
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # Create default templates if file doesn't exist
                templates = self._create_default_templates()
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(templates, f, ensure_ascii=False, indent=2)
                return templates
        except Exception as e:
            print(f"Error loading defining moment templates: {e}")
            return self._create_default_templates()

    def _create_default_templates(self):
        """
        Create default defining moment templates.

        Returns:
            dict: The default templates
        """
        return {
            "moral_crossroads": {
                "name": "Encruzilhada Moral",
                "description": "Suas escolhas passadas de {choice_pattern} levaram a um momento crucial onde você deve decidir entre {option_a} ou {option_b}.",
                "requirements": {
                    "min_choices": 5,
                    "choice_pattern": ["moral", "ethical"],
                    "min_pattern_frequency": 0.6
                },
                "options": {
                    "option_a": {
                        "description": "Manter seus princípios, mesmo com um custo pessoal",
                        "consequences": {
                            "reputation": 10,
                            "faction_reputation": {"Conselho de Ética": 15, "Conselho Político": -5},
                            "unlock_path": "moral_paragon"
                        }
                    },
                    "option_b": {
                        "description": "Fazer uma exceção por necessidade prática",
                        "consequences": {
                            "tusd": 200,
                            "faction_reputation": {"Conselho de Ética": -10, "Conselho Político": 10},
                            "unlock_path": "pragmatic_leader"
                        }
                    }
                }
            },
            "power_manifestation": {
                "name": "Manifestação de Poder",
                "description": "Seu treinamento consistente em {power_type} culmina em um momento de crise onde seu verdadeiro potencial se manifesta.",
                "requirements": {
                    "min_level": 10,
                    "power_usage_frequency": 0.7,
                    "power_type": ["Fogo", "Água", "Terra", "Ar", "Mental", "Físico"]
                },
                "outcomes": {
                    "success": {
                        "description": "Você domina o surto de poder, revelando uma nova habilidade!",
                        "consequences": {
                            "power_boost": 5,
                            "unlock_ability": "advanced_{power_type}",
                            "reputation": 15
                        }
                    },
                    "failure": {
                        "description": "O poder é demais para controlar, causando danos colaterais.",
                        "consequences": {
                            "power_boost": 2,
                            "reputation": -10,
                            "faction_reputation": {"Conselho de Segurança": -15}
                        }
                    }
                }
            },
            "faction_allegiance": {
                "name": "Aliança Faccional",
                "description": "Suas interações consistentes com {faction} levam a um convite formal para se juntar a eles, mas {rival_faction} vê isso como traição.",
                "requirements": {
                    "min_faction_reputation": 50,
                    "rival_faction_reputation": -20
                },
                "options": {
                    "accept": {
                        "description": "Aceitar a aliança com {faction}",
                        "consequences": {
                            "faction_reputation": {"{faction}": 25, "{rival_faction}": -30},
                            "unlock_path": "{faction}_path",
                            "special_item": "{faction}_emblem"
                        }
                    },
                    "reject": {
                        "description": "Rejeitar a aliança e manter neutralidade",
                        "consequences": {
                            "faction_reputation": {"{faction}": -15, "{rival_faction}": 10},
                            "unlock_path": "independent_path",
                            "charisma": 2
                        }
                    },
                    "negotiate": {
                        "description": "Tentar negociar uma posição que agrade ambas as facções",
                        "consequences": {
                            "faction_reputation": {"{faction}": 10, "{rival_faction}": 5},
                            "unlock_path": "diplomat_path",
                            "intellect": 2,
                            "charisma": 1
                        },
                        "success_chance": 0.4
                    }
                }
            },
            "mentor_challenge": {
                "name": "Desafio do Mentor",
                "description": "Seu mentor {mentor_name} o desafia a provar seu crescimento em um teste que reflete suas escolhas passadas.",
                "requirements": {
                    "min_level": 15,
                    "mentor_relationship": True
                },
                "challenge": {
                    "difficulty": "adaptive",
                    "focus_attribute": "dominant_choice_type",
                    "success_threshold": 0.7
                },
                "outcomes": {
                    "success": {
                        "description": "Você supera o desafio, impressionando seu mentor!",
                        "consequences": {
                            "exp": 500,
                            "unlock_ability": "mentor_technique",
                            "reputation": 20
                        }
                    },
                    "failure": {
                        "description": "Você falha no desafio, mas aprende lições valiosas.",
                        "consequences": {
                            "exp": 200,
                            "intellect": 1,
                            "unlock_path": "redemption_arc"
                        }
                    }
                }
            },
            "past_returns": {
                "name": "O Passado Retorna",
                "description": "Uma figura do seu passado, afetada por uma decisão que você tomou em {past_event}, retorna com consequências inesperadas.",
                "requirements": {
                    "specific_past_choice": True,
                    "min_time_passed": "30d"
                },
                "variations": {
                    "positive": {
                        "description": "Sua boa ação passada retorna como uma aliança inesperada.",
                        "consequences": {
                            "new_ally": True,
                            "reputation": 15,
                            "special_item": "token_of_gratitude"
                        }
                    },
                    "negative": {
                        "description": "Sua decisão controversa retorna como um novo adversário.",
                        "consequences": {
                            "new_adversary": True,
                            "reputation": -10,
                            "challenge_event": "confront_past"
                        }
                    },
                    "complex": {
                        "description": "Sua decisão passada tem ramificações complexas que exigem uma nova escolha.",
                        "consequences": {
                            "new_defining_moment": True,
                            "intellect": 1,
                            "wisdom": 1
                        }
                    }
                }
            }
        }

    def check_for_defining_moment(self, player_choice_tracker):
        """
        Check if the player's choices have triggered a defining moment.

        Args:
            player_choice_tracker: The player's choice tracker object

        Returns:
            dict or None: The defining moment data if triggered, None otherwise
        """
        # Get player data
        choice_patterns = player_choice_tracker.get_choice_pattern()
        faction_reputation = player_choice_tracker.get_faction_reputation()
        choice_history = player_choice_tracker.get_choice_history(limit=100)
        dominant_choice_type = player_choice_tracker.get_dominant_choice_type()

        # Check each template to see if requirements are met
        potential_moments = []

        for moment_id, template in self.defining_moment_templates.items():
            if self._check_requirements(template, choice_patterns, faction_reputation, 
                                       choice_history, dominant_choice_type):
                potential_moments.append((moment_id, template))

        # If no moments are triggered, return None
        if not potential_moments:
            return None

        # Select a random defining moment from the potential ones
        moment_id, template = random.choice(potential_moments)

        # Prepare the defining moment data
        moment_data = self._prepare_moment_data(moment_id, template, choice_patterns, 
                                              faction_reputation, dominant_choice_type)

        return moment_data

    def _check_requirements(self, template, choice_patterns, faction_reputation, 
                           choice_history, dominant_choice_type):
        """
        Check if the requirements for a defining moment are met.

        Args:
            template (dict): The defining moment template
            choice_patterns (dict): The player's choice patterns
            faction_reputation (dict): The player's faction reputation
            choice_history (list): The player's choice history
            dominant_choice_type (str): The player's dominant choice type

        Returns:
            bool: True if requirements are met, False otherwise
        """
        requirements = template.get('requirements', {})

        # Check minimum choices
        min_choices = requirements.get('min_choices', 0)
        if len(choice_history) < min_choices:
            return False

        # Check choice pattern frequency
        pattern_types = requirements.get('choice_pattern', [])
        if pattern_types:
            pattern_count = sum(choice_patterns.get(pattern, 0) for pattern in pattern_types)
            total_choices = sum(choice_patterns.values())
            min_frequency = requirements.get('min_pattern_frequency', 0)

            if total_choices == 0 or pattern_count / total_choices < min_frequency:
                return False

        # Check faction reputation
        min_faction_rep = requirements.get('min_faction_reputation', 0)
        if min_faction_rep > 0:
            faction = requirements.get('faction', '')
            if faction and faction_reputation.get(faction, 0) < min_faction_rep:
                return False

        # Check rival faction reputation
        rival_faction_rep = requirements.get('rival_faction_reputation', 0)
        if rival_faction_rep < 0:
            rival_faction = requirements.get('rival_faction', '')
            if rival_faction and faction_reputation.get(rival_faction, 0) > rival_faction_rep:
                return False

        # Check power type requirements
        power_types = requirements.get('power_type', [])
        if power_types and dominant_choice_type not in power_types:
            return False

        # All requirements met
        return True

    def _prepare_moment_data(self, moment_id, template, choice_patterns, 
                            faction_reputation, dominant_choice_type):
        """
        Prepare the defining moment data with dynamic elements.

        Args:
            moment_id (str): The ID of the defining moment
            template (dict): The defining moment template
            choice_patterns (dict): The player's choice patterns
            faction_reputation (dict): The player's faction reputation
            dominant_choice_type (str): The player's dominant choice type

        Returns:
            dict: The prepared defining moment data
        """
        # Create a copy of the template to modify
        moment_data = {
            'id': moment_id,
            'name': template['name'],
            'description': template['description'],
            'timestamp': datetime.now().isoformat()
        }

        # Fill in dynamic elements in the description
        description = moment_data['description']

        # Replace {choice_pattern} with dominant choice type
        if '{choice_pattern}' in description:
            description = description.replace('{choice_pattern}', dominant_choice_type or 'varied')

        # Replace {power_type} with dominant choice type if it's a power type
        power_types = ['Fogo', 'Água', 'Terra', 'Ar', 'Mental', 'Físico']
        if '{power_type}' in description and dominant_choice_type in power_types:
            description = description.replace('{power_type}', dominant_choice_type)

        # Replace {faction} with the faction the player has highest reputation with
        if '{faction}' in description:
            top_faction = max(faction_reputation.items(), key=lambda x: x[1])[0] if faction_reputation else 'neutral'
            description = description.replace('{faction}', top_faction)

        # Replace {rival_faction} with the faction the player has lowest reputation with
        if '{rival_faction}' in description:
            rival_faction = min(faction_reputation.items(), key=lambda x: x[1])[0] if faction_reputation else 'neutral'
            description = description.replace('{rival_faction}', rival_faction)

        moment_data['description'] = description

        # Add options or outcomes
        if 'options' in template:
            moment_data['options'] = template['options']
        elif 'outcomes' in template:
            moment_data['outcomes'] = template['outcomes']
        elif 'variations' in template:
            # Select the most appropriate variation based on player history
            variations = template['variations']
            if 'positive' in variations and 'negative' in variations:
                # Determine if player tends toward positive or negative choices
                positive_choices = sum(choice_patterns.get(choice, 0) for choice in 
                                     ['diplomacy', 'assist', 'collaborate', 'alliance'])
                negative_choices = sum(choice_patterns.get(choice, 0) for choice in 
                                     ['intimidate', 'aggressive', 'power'])

                if positive_choices > negative_choices:
                    moment_data['variation'] = variations['positive']
                elif negative_choices > positive_choices:
                    moment_data['variation'] = variations['negative']
                else:
                    moment_data['variation'] = variations.get('complex', variations['positive'])
            else:
                # Just pick a random variation
                moment_data['variation'] = random.choice(list(variations.values()))

        return moment_data

    def process_defining_moment_choice(self, moment_id, choice_id, player_choice_tracker):
        """
        Process a player's choice in a defining moment.

        Args:
            moment_id (str): The ID of the defining moment
            choice_id (str): The ID of the choice made
            player_choice_tracker: The player's choice tracker object

        Returns:
            dict: The consequences of the choice
        """
        # Get the defining moment template
        template = self.defining_moment_templates.get(moment_id)
        if not template:
            return {'error': 'Defining moment not found'}

        # Get the choice data
        options = template.get('options', {})
        choice_data = options.get(choice_id)

        if not choice_data:
            return {'error': 'Choice not found'}

        # Get the consequences
        consequences = choice_data.get('consequences', {})

        # Record the choice as a defining moment
        consequences['is_defining_moment'] = True
        consequences['defining_moment_description'] = template['name']
        consequences['defining_moment_impact'] = consequences.copy()

        player_choice_tracker.record_choice(
            event_id=f"defining_moment_{moment_id}",
            choice_id=choice_id,
            choice_type='defining_moment',
            consequences=consequences,
            context={'moment_name': template['name']}
        )

        return consequences
