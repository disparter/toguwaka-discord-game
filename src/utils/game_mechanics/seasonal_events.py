"""
Seasonal Narrative Events System

This module implements a system for seasonal events, including special events for each season,
academy festivals with mini-games, and seasonal weather events that affect gameplay.
"""

import json
import os
import random
from datetime import datetime, timedelta
from collections import defaultdict

class SeasonalEventManager:
    """
    Manages seasonal events, festivals, and weather events in the game.
    """
    
    def __init__(self, player_id):
        """
        Initialize the seasonal event manager for a specific player.
        
        Args:
            player_id (str): The unique identifier for the player
        """
        self.player_id = player_id
        self.seasonal_data = self._load_seasonal_data()
        self.current_season = self._determine_current_season()
        self.active_events = []
        self.completed_events = set()
        self.festival_progress = {}
        self.weather_effects = {}
        self.load_data()
    
    def _load_seasonal_data(self):
        """
        Load seasonal event data from the data file.
        
        Returns:
            dict: The seasonal event data
        """
        try:
            file_path = "data/story_mode/events/seasonal_events.json"
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # Create default seasonal data if file doesn't exist
                seasonal_data = self._create_default_seasonal_data()
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(seasonal_data, f, ensure_ascii=False, indent=2)
                return seasonal_data
        except Exception as e:
            print(f"Error loading seasonal event data: {e}")
            return self._create_default_seasonal_data()
    
    def _create_default_seasonal_data(self):
        """
        Create default seasonal event data.
        
        Returns:
            dict: The default seasonal event data
        """
        return {
            "seasons": {
                "spring": {
                    "name": "Primavera",
                    "description": "A estação do renascimento e novos começos.",
                    "months": [3, 4, 5],  # March, April, May
                    "weather_events": ["gentle_rain", "flower_bloom", "spring_breeze"],
                    "narrative_events": ["spring_awakening", "cherry_blossom_festival", "elemental_rebirth"],
                    "gameplay_effects": {
                        "nature_power_boost": 15,
                        "water_power_boost": 10,
                        "healing_efficiency": 20
                    }
                },
                "summer": {
                    "name": "Verão",
                    "description": "A estação do calor, energia e atividade intensa.",
                    "months": [6, 7, 8],  # June, July, August
                    "weather_events": ["heat_wave", "summer_storm", "clear_skies"],
                    "narrative_events": ["summer_solstice", "beach_tournament", "fire_ritual"],
                    "gameplay_effects": {
                        "fire_power_boost": 20,
                        "lightning_power_boost": 15,
                        "stamina_regeneration": 10
                    }
                },
                "autumn": {
                    "name": "Outono",
                    "description": "A estação da colheita, reflexão e transformação.",
                    "months": [9, 10, 11],  # September, October, November
                    "weather_events": ["falling_leaves", "autumn_mist", "harvest_moon"],
                    "narrative_events": ["harvest_festival", "spirit_communion", "knowledge_quest"],
                    "gameplay_effects": {
                        "earth_power_boost": 15,
                        "mental_power_boost": 20,
                        "crafting_efficiency": 25
                    }
                },
                "winter": {
                    "name": "Inverno",
                    "description": "A estação do descanso, introspecção e desafios.",
                    "months": [12, 1, 2],  # December, January, February
                    "weather_events": ["blizzard", "frost", "northern_lights"],
                    "narrative_events": ["winter_solstice", "ice_trial", "new_year_ceremony"],
                    "gameplay_effects": {
                        "ice_power_boost": 25,
                        "defense_boost": 15,
                        "meditation_efficiency": 20
                    }
                }
            },
            "festivals": {
                "cherry_blossom_festival": {
                    "name": "Festival das Cerejeiras",
                    "description": "Um festival celebrando a beleza efêmera das flores de cerejeira e o início da primavera.",
                    "season": "spring",
                    "duration_days": 7,
                    "start_month": 3,
                    "start_day": 21,
                    "main_story_integration": "Os estudantes participam de rituais de renovação que fortalecem suas conexões com seus poderes elementais.",
                    "mini_games": [
                        {
                            "id": "petal_dance",
                            "name": "Dança das Pétalas",
                            "description": "Use seus poderes para criar padrões com pétalas de cerejeira no ar.",
                            "rewards": {
                                "exp": 200,
                                "tusd": 150,
                                "special_item": "essência_de_cerejeira"
                            }
                        },
                        {
                            "id": "harmony_ritual",
                            "name": "Ritual de Harmonia",
                            "description": "Trabalhe com outros estudantes para criar um círculo de energia harmônica.",
                            "rewards": {
                                "exp": 300,
                                "tusd": 200,
                                "power_boost": 5
                            }
                        }
                    ],
                    "exclusive_content": {
                        "quest": "renascimento_primaveril",
                        "npc": "espírito_da_primavera",
                        "item": "broto_de_poder"
                    }
                },
                "summer_solstice": {
                    "name": "Solstício de Verão",
                    "description": "Uma celebração do dia mais longo do ano, focada no poder do sol e do fogo.",
                    "season": "summer",
                    "duration_days": 3,
                    "start_month": 6,
                    "start_day": 21,
                    "main_story_integration": "Os usuários de fogo realizam demonstrações impressionantes, revelando segredos ancestrais de sua arte.",
                    "mini_games": [
                        {
                            "id": "fire_dancing",
                            "name": "Dança do Fogo",
                            "description": "Crie e controle chamas em uma performance artística.",
                            "rewards": {
                                "exp": 250,
                                "tusd": 200,
                                "special_item": "chama_eterna"
                            }
                        },
                        {
                            "id": "solar_challenge",
                            "name": "Desafio Solar",
                            "description": "Capture e concentre a energia solar para criar o cristal mais brilhante.",
                            "rewards": {
                                "exp": 350,
                                "tusd": 250,
                                "power_boost": 8
                            }
                        }
                    ],
                    "exclusive_content": {
                        "quest": "segredo_da_chama_ancestral",
                        "npc": "guardião_do_fogo",
                        "item": "núcleo_solar"
                    }
                },
                "harvest_festival": {
                    "name": "Festival da Colheita",
                    "description": "Uma celebração da abundância e dos frutos do trabalho duro.",
                    "season": "autumn",
                    "duration_days": 5,
                    "start_month": 9,
                    "start_day": 22,
                    "main_story_integration": "Antigos conhecimentos são compartilhados, e os estudantes aprendem sobre a conexão entre seus poderes e o ciclo natural da vida.",
                    "mini_games": [
                        {
                            "id": "bounty_gathering",
                            "name": "Coleta da Abundância",
                            "description": "Colete ingredientes raros para o grande banquete do festival.",
                            "rewards": {
                                "exp": 200,
                                "tusd": 180,
                                "special_item": "fruto_dourado"
                            }
                        },
                        {
                            "id": "knowledge_sharing",
                            "name": "Compartilhamento de Conhecimento",
                            "description": "Participe de um círculo de troca de conhecimentos ancestrais.",
                            "rewards": {
                                "exp": 300,
                                "tusd": 150,
                                "skill_point": 1
                            }
                        }
                    ],
                    "exclusive_content": {
                        "quest": "sabedoria_dos_ancestrais",
                        "npc": "ancião_da_colheita",
                        "item": "pergaminho_da_sabedoria"
                    }
                },
                "winter_solstice": {
                    "name": "Solstício de Inverno",
                    "description": "Uma celebração da noite mais longa do ano e do retorno gradual da luz.",
                    "season": "winter",
                    "duration_days": 3,
                    "start_month": 12,
                    "start_day": 21,
                    "main_story_integration": "Os estudantes enfrentam seus medos internos e descobrem forças ocultas durante a longa noite.",
                    "mini_games": [
                        {
                            "id": "ice_sculpting",
                            "name": "Escultura de Gelo",
                            "description": "Use seus poderes para criar esculturas de gelo impressionantes.",
                            "rewards": {
                                "exp": 250,
                                "tusd": 200,
                                "special_item": "cristal_de_gelo_eterno"
                            }
                        },
                        {
                            "id": "light_ritual",
                            "name": "Ritual da Luz",
                            "description": "Participe de um ritual para trazer de volta a luz durante a noite mais escura.",
                            "rewards": {
                                "exp": 400,
                                "tusd": 300,
                                "power_boost": 10
                            }
                        }
                    ],
                    "exclusive_content": {
                        "quest": "luz_na_escuridão",
                        "npc": "guardião_do_inverno",
                        "item": "essência_da_luz_interior"
                    }
                }
            },
            "weather_events": {
                "gentle_rain": {
                    "name": "Chuva Gentil",
                    "description": "Uma chuva leve e revigorante que nutre a terra.",
                    "season": "spring",
                    "duration_hours": [1, 6],  # Random between 1 and 6 hours
                    "chance_per_day": 0.4,  # 40% chance each day in spring
                    "gameplay_effects": {
                        "water_power_boost": 15,
                        "fire_power_penalty": 10,
                        "healing_efficiency": 10
                    },
                    "exclusive_content": {
                        "quest": "dança_da_chuva",
                        "collectible": "flor_da_chuva"
                    }
                },
                "heat_wave": {
                    "name": "Onda de Calor",
                    "description": "Um período de calor intenso que testa a resistência de todos.",
                    "season": "summer",
                    "duration_hours": [4, 12],
                    "chance_per_day": 0.3,
                    "gameplay_effects": {
                        "fire_power_boost": 25,
                        "ice_power_penalty": 20,
                        "stamina_drain": 15
                    },
                    "exclusive_content": {
                        "quest": "teste_do_calor",
                        "collectible": "cristal_de_fogo"
                    }
                },
                "autumn_mist": {
                    "name": "Névoa de Outono",
                    "description": "Uma névoa misteriosa que encobre a academia, criando uma atmosfera mística.",
                    "season": "autumn",
                    "duration_hours": [2, 8],
                    "chance_per_day": 0.35,
                    "gameplay_effects": {
                        "mental_power_boost": 20,
                        "perception_penalty": 15,
                        "stealth_boost": 25
                    },
                    "exclusive_content": {
                        "quest": "segredos_na_névoa",
                        "collectible": "essência_nebulosa"
                    }
                },
                "blizzard": {
                    "name": "Nevasca",
                    "description": "Uma tempestade de neve intensa que isola a academia do mundo exterior.",
                    "season": "winter",
                    "duration_hours": [6, 24],
                    "chance_per_day": 0.25,
                    "gameplay_effects": {
                        "ice_power_boost": 30,
                        "fire_power_penalty": 25,
                        "movement_penalty": 20
                    },
                    "exclusive_content": {
                        "quest": "sobrevivência_na_nevasca",
                        "collectible": "cristal_de_gelo_primordial"
                    }
                }
            }
        }
    
    def _determine_current_season(self):
        """
        Determine the current season based on the current date.
        
        Returns:
            str: The current season
        """
        current_month = datetime.now().month
        
        for season, data in self.seasonal_data.get('seasons', {}).items():
            if current_month in data.get('months', []):
                return season
        
        return "spring"  # Default to spring if something goes wrong
    
    def load_data(self):
        """Load player seasonal event data from storage if it exists."""
        try:
            file_path = f"data/player_data/{self.player_id}/seasonal_events.json"
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.active_events = data.get('active_events', [])
                    self.completed_events = set(data.get('completed_events', []))
                    self.festival_progress = data.get('festival_progress', {})
                    self.weather_effects = data.get('weather_effects', {})
        except Exception as e:
            print(f"Error loading seasonal event data: {e}")
    
    def save_data(self):
        """Save player seasonal event data to storage."""
        try:
            file_path = f"data/player_data/{self.player_id}/seasonal_events.json"
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            data = {
                'active_events': self.active_events,
                'completed_events': list(self.completed_events),
                'festival_progress': self.festival_progress,
                'weather_effects': self.weather_effects
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving seasonal event data: {e}")
    
    def get_current_season_data(self):
        """
        Get data for the current season.
        
        Returns:
            dict: The current season data
        """
        return self.seasonal_data.get('seasons', {}).get(self.current_season, {})
    
    def update_season(self):
        """
        Update the current season based on the current date.
        
        Returns:
            bool: True if the season changed, False otherwise
        """
        old_season = self.current_season
        self.current_season = self._determine_current_season()
        
        if old_season != self.current_season:
            # Season changed, trigger season change events
            self._handle_season_change(old_season, self.current_season)
            return True
        
        return False
    
    def _handle_season_change(self, old_season, new_season):
        """
        Handle season change events.
        
        Args:
            old_season (str): The previous season
            new_season (str): The new season
        """
        # Clear weather effects from the old season
        self.weather_effects = {}
        
        # Add season change event to active events
        self.active_events.append({
            'type': 'season_change',
            'old_season': old_season,
            'new_season': new_season,
            'timestamp': datetime.now().isoformat()
        })
        
        # Check for seasonal narrative events that should start
        season_data = self.seasonal_data.get('seasons', {}).get(new_season, {})
        for event_id in season_data.get('narrative_events', []):
            if event_id not in self.completed_events:
                self._activate_narrative_event(event_id)
        
        self.save_data()
    
    def _activate_narrative_event(self, event_id):
        """
        Activate a narrative event.
        
        Args:
            event_id (str): The ID of the event to activate
        """
        # Add event to active events
        self.active_events.append({
            'type': 'narrative_event',
            'event_id': event_id,
            'status': 'active',
            'progress': 0,
            'timestamp': datetime.now().isoformat()
        })
    
    def get_active_events(self):
        """
        Get all active events.
        
        Returns:
            list: The active events
        """
        return self.active_events
    
    def get_active_narrative_events(self):
        """
        Get active narrative events.
        
        Returns:
            list: The active narrative events
        """
        return [event for event in self.active_events if event.get('type') == 'narrative_event']
    
    def get_active_festivals(self):
        """
        Get active festivals.
        
        Returns:
            list: The active festivals
        """
        return [event for event in self.active_events if event.get('type') == 'festival']
    
    def get_active_weather_events(self):
        """
        Get active weather events.
        
        Returns:
            list: The active weather events
        """
        return [event for event in self.active_events if event.get('type') == 'weather_event']
    
    def check_for_festivals(self):
        """
        Check if any festivals should start or end based on the current date.
        
        Returns:
            list: Newly started festivals
        """
        current_date = datetime.now()
        current_month = current_date.month
        current_day = current_date.day
        
        started_festivals = []
        
        # Check for festivals that should start
        for festival_id, festival_data in self.seasonal_data.get('festivals', {}).items():
            if festival_data.get('season') == self.current_season:
                start_month = festival_data.get('start_month')
                start_day = festival_data.get('start_day')
                duration_days = festival_data.get('duration_days', 1)
                
                # Calculate end date
                start_date = datetime(current_date.year, start_month, start_day)
                end_date = start_date + timedelta(days=duration_days)
                
                # Check if today is within the festival period
                if start_date <= current_date <= end_date:
                    # Check if festival is already active
                    if not any(event.get('event_id') == festival_id and event.get('type') == 'festival' 
                              for event in self.active_events):
                        # Start festival
                        self.active_events.append({
                            'type': 'festival',
                            'event_id': festival_id,
                            'status': 'active',
                            'start_date': start_date.isoformat(),
                            'end_date': end_date.isoformat(),
                            'timestamp': datetime.now().isoformat()
                        })
                        started_festivals.append(festival_id)
                        
                        # Initialize festival progress
                        self.festival_progress[festival_id] = {
                            'mini_games_completed': [],
                            'quests_completed': []
                        }
        
        # Check for festivals that should end
        for event in list(self.active_events):
            if event.get('type') == 'festival':
                end_date = datetime.fromisoformat(event.get('end_date'))
                if current_date > end_date:
                    # End festival
                    event['status'] = 'completed'
                    self.completed_events.add(event.get('event_id'))
        
        self.save_data()
        return started_festivals
    
    def generate_weather_event(self):
        """
        Generate a random weather event based on the current season.
        
        Returns:
            str or None: The ID of the generated weather event, or None if no event was generated
        """
        season_data = self.seasonal_data.get('seasons', {}).get(self.current_season, {})
        possible_events = season_data.get('weather_events', [])
        
        if not possible_events:
            return None
        
        # Check if we should generate a weather event
        for event_id in possible_events:
            event_data = self.seasonal_data.get('weather_events', {}).get(event_id, {})
            chance = event_data.get('chance_per_day', 0)
            
            if random.random() < chance:
                # Generate event
                min_duration, max_duration = event_data.get('duration_hours', [1, 3])
                duration = random.randint(min_duration, max_duration)
                
                end_time = datetime.now() + timedelta(hours=duration)
                
                # Add event to active events
                self.active_events.append({
                    'type': 'weather_event',
                    'event_id': event_id,
                    'status': 'active',
                    'end_time': end_time.isoformat(),
                    'timestamp': datetime.now().isoformat()
                })
                
                # Apply weather effects
                self.weather_effects = event_data.get('gameplay_effects', {})
                
                self.save_data()
                return event_id
        
        return None
    
    def update_weather_events(self):
        """
        Update weather events, ending those that have expired.
        
        Returns:
            list: Weather events that ended
        """
        current_time = datetime.now()
        ended_events = []
        
        for event in list(self.active_events):
            if event.get('type') == 'weather_event' and event.get('status') == 'active':
                end_time = datetime.fromisoformat(event.get('end_time'))
                if current_time > end_time:
                    # End weather event
                    event['status'] = 'completed'
                    ended_events.append(event.get('event_id'))
                    
                    # Clear weather effects
                    self.weather_effects = {}
        
        self.save_data()
        return ended_events
    
    def get_weather_effects(self):
        """
        Get the current weather effects.
        
        Returns:
            dict: The current weather effects
        """
        return self.weather_effects
    
    def get_festival_data(self, festival_id):
        """
        Get data for a specific festival.
        
        Args:
            festival_id (str): The ID of the festival
            
        Returns:
            dict: The festival data
        """
        return self.seasonal_data.get('festivals', {}).get(festival_id, {})
    
    def get_festival_progress(self, festival_id):
        """
        Get the player's progress in a festival.
        
        Args:
            festival_id (str): The ID of the festival
            
        Returns:
            dict: The festival progress
        """
        return self.festival_progress.get(festival_id, {})
    
    def complete_festival_mini_game(self, festival_id, mini_game_id):
        """
        Mark a festival mini-game as completed and award rewards.
        
        Args:
            festival_id (str): The ID of the festival
            mini_game_id (str): The ID of the mini-game
            
        Returns:
            dict: The rewards for completing the mini-game
        """
        # Check if festival is active
        if not any(event.get('event_id') == festival_id and event.get('type') == 'festival' 
                  and event.get('status') == 'active' for event in self.active_events):
            return {"success": False, "message": "Festival is not active"}
        
        # Check if mini-game exists
        festival_data = self.get_festival_data(festival_id)
        mini_game = None
        for game in festival_data.get('mini_games', []):
            if game.get('id') == mini_game_id:
                mini_game = game
                break
        
        if not mini_game:
            return {"success": False, "message": "Mini-game not found"}
        
        # Check if mini-game is already completed
        if mini_game_id in self.festival_progress.get(festival_id, {}).get('mini_games_completed', []):
            return {"success": False, "message": "Mini-game already completed"}
        
        # Mark mini-game as completed
        if festival_id not in self.festival_progress:
            self.festival_progress[festival_id] = {'mini_games_completed': [], 'quests_completed': []}
        
        self.festival_progress[festival_id]['mini_games_completed'].append(mini_game_id)
        
        # Get rewards
        rewards = mini_game.get('rewards', {})
        
        self.save_data()
        return {"success": True, "rewards": rewards}
    
    def complete_festival_quest(self, festival_id, quest_id):
        """
        Mark a festival quest as completed.
        
        Args:
            festival_id (str): The ID of the festival
            quest_id (str): The ID of the quest
            
        Returns:
            dict: The result of completing the quest
        """
        # Check if festival is active
        if not any(event.get('event_id') == festival_id and event.get('type') == 'festival' 
                  and event.get('status') == 'active' for event in self.active_events):
            return {"success": False, "message": "Festival is not active"}
        
        # Check if quest exists
        festival_data = self.get_festival_data(festival_id)
        if quest_id != festival_data.get('exclusive_content', {}).get('quest'):
            return {"success": False, "message": "Quest not found"}
        
        # Check if quest is already completed
        if quest_id in self.festival_progress.get(festival_id, {}).get('quests_completed', []):
            return {"success": False, "message": "Quest already completed"}
        
        # Mark quest as completed
        if festival_id not in self.festival_progress:
            self.festival_progress[festival_id] = {'mini_games_completed': [], 'quests_completed': []}
        
        self.festival_progress[festival_id]['quests_completed'].append(quest_id)
        
        self.save_data()
        return {"success": True, "message": "Quest completed successfully"}
    
    def progress_narrative_event(self, event_id, progress_amount):
        """
        Progress a narrative event.
        
        Args:
            event_id (str): The ID of the event
            progress_amount (int): The amount of progress to add
            
        Returns:
            dict: The result of progressing the event
        """
        # Find the event
        event = None
        for e in self.active_events:
            if e.get('type') == 'narrative_event' and e.get('event_id') == event_id:
                event = e
                break
        
        if not event:
            return {"success": False, "message": "Event not found or not active"}
        
        # Update progress
        event['progress'] += progress_amount
        
        # Check if event is completed
        if event['progress'] >= 100:
            event['status'] = 'completed'
            self.completed_events.add(event_id)
        
        self.save_data()
        return {"success": True, "progress": event['progress'], "completed": event['status'] == 'completed'}
    
    def get_seasonal_power_boosts(self):
        """
        Get power boosts based on the current season.
        
        Returns:
            dict: The seasonal power boosts
        """
        season_data = self.get_current_season_data()
        return season_data.get('gameplay_effects', {})
    
    def get_weather_event_data(self, event_id):
        """
        Get data for a specific weather event.
        
        Args:
            event_id (str): The ID of the weather event
            
        Returns:
            dict: The weather event data
        """
        return self.seasonal_data.get('weather_events', {}).get(event_id, {})
    
    def get_narrative_event_data(self, event_id):
        """
        Get data for a specific narrative event.
        
        Args:
            event_id (str): The ID of the narrative event
            
        Returns:
            dict: The narrative event data
        """
        # This would need to be implemented with actual narrative event data
        # For now, we'll return a placeholder
        return {
            "id": event_id,
            "name": f"Evento Narrativo: {event_id}",
            "description": "Um evento narrativo sazonal.",
            "season": self.current_season
        }
    
    def get_all_seasonal_content(self):
        """
        Get all seasonal content for the current season.
        
        Returns:
            dict: All seasonal content
        """
        season_data = self.get_current_season_data()
        
        # Get festivals for this season
        festivals = {}
        for festival_id, festival_data in self.seasonal_data.get('festivals', {}).items():
            if festival_data.get('season') == self.current_season:
                festivals[festival_id] = festival_data
        
        # Get weather events for this season
        weather_events = {}
        for event_id in season_data.get('weather_events', []):
            weather_events[event_id] = self.seasonal_data.get('weather_events', {}).get(event_id, {})
        
        # Get narrative events for this season
        narrative_events = {}
        for event_id in season_data.get('narrative_events', []):
            narrative_events[event_id] = self.get_narrative_event_data(event_id)
        
        return {
            "season": self.current_season,
            "season_data": season_data,
            "festivals": festivals,
            "weather_events": weather_events,
            "narrative_events": narrative_events,
            "active_events": self.active_events,
            "weather_effects": self.weather_effects
        }