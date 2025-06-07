"""
Faction Reputation System

This module implements a system to track and manage player reputation with different factions,
affecting how these factions respond to the player throughout the game.
"""

import json
import os
from datetime import datetime
from collections import defaultdict

class FactionReputationManager:
    """
    Manages player reputation with different factions in the game.
    """
    
    def __init__(self, player_id):
        """
        Initialize the faction reputation manager for a specific player.
        
        Args:
            player_id (str): The unique identifier for the player
        """
        self.player_id = player_id
        self.reputation = defaultdict(int)
        self.reputation_history = defaultdict(list)
        self.faction_data = self._load_faction_data()
        self.load_data()
    
    def _load_faction_data(self):
        """
        Load faction data from the data file.
        
        Returns:
            dict: The faction data
        """
        try:
            file_path = "data/story_mode/factions/factions.json"
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # Create default faction data if file doesn't exist
                faction_data = self._create_default_faction_data()
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(faction_data, f, ensure_ascii=False, indent=2)
                return faction_data
        except Exception as e:
            print(f"Error loading faction data: {e}")
            return self._create_default_faction_data()
    
    def _create_default_faction_data(self):
        """
        Create default faction data.
        
        Returns:
            dict: The default faction data
        """
        return {
            "clube_das_chamas": {
                "name": "Clube das Chamas",
                "description": "Estudantes focados no domínio do fogo e técnicas de combate ofensivas.",
                "leader": "Kai Flameheart",
                "values": ["Poder", "Coragem", "Ação Direta"],
                "rivals": ["elementalistas"],
                "allies": ["clube_de_combate"],
                "reputation_thresholds": {
                    "hostile": -50,
                    "unfriendly": -20,
                    "neutral": 0,
                    "friendly": 20,
                    "close": 50,
                    "trusted": 80
                },
                "reputation_benefits": {
                    "friendly": ["Acesso a treinamentos básicos de fogo"],
                    "close": ["Desconto em itens do clube", "Acesso a áreas restritas de treinamento"],
                    "trusted": ["Técnicas secretas de fogo", "Apoio em duelos"]
                }
            },
            "ilusionistas_mentais": {
                "name": "Ilusionistas Mentais",
                "description": "Estudantes especializados em poderes mentais, telepatia e manipulação psíquica.",
                "leader": "Luna Mindweaver",
                "values": ["Conhecimento", "Sutileza", "Controle Mental"],
                "rivals": ["clube_de_combate"],
                "allies": ["conselho_politico"],
                "reputation_thresholds": {
                    "hostile": -50,
                    "unfriendly": -20,
                    "neutral": 0,
                    "friendly": 20,
                    "close": 50,
                    "trusted": 80
                },
                "reputation_benefits": {
                    "friendly": ["Acesso a livros básicos de telepatia"],
                    "close": ["Proteção mental contra invasões", "Acesso à biblioteca restrita"],
                    "trusted": ["Técnicas avançadas de telepatia", "Segredos da academia"]
                }
            },
            "conselho_politico": {
                "name": "Conselho Político",
                "description": "Estudantes focados em diplomacia, estratégia e liderança política.",
                "leader": "Alexander Strategos",
                "values": ["Influência", "Estratégia", "Ordem"],
                "rivals": ["rebeldes_independentes"],
                "allies": ["ilusionistas_mentais"],
                "reputation_thresholds": {
                    "hostile": -50,
                    "unfriendly": -20,
                    "neutral": 0,
                    "friendly": 20,
                    "close": 50,
                    "trusted": 80
                },
                "reputation_benefits": {
                    "friendly": ["Acesso a eventos políticos"],
                    "close": ["Influência em decisões menores", "Informações privilegiadas"],
                    "trusted": ["Poder de voto no conselho", "Rede de contatos influentes"]
                }
            },
            "elementalistas": {
                "name": "Elementalistas",
                "description": "Estudantes dedicados ao equilíbrio e harmonia entre os elementos naturais.",
                "leader": "Gaia Naturae",
                "values": ["Equilíbrio", "Natureza", "Harmonia"],
                "rivals": ["clube_das_chamas"],
                "allies": ["guardioes_do_conhecimento"],
                "reputation_thresholds": {
                    "hostile": -50,
                    "unfriendly": -20,
                    "neutral": 0,
                    "friendly": 20,
                    "close": 50,
                    "trusted": 80
                },
                "reputation_benefits": {
                    "friendly": ["Acesso a jardins elementais"],
                    "close": ["Rituais de purificação elemental", "Materiais raros da natureza"],
                    "trusted": ["Comunhão com espíritos elementais", "Técnicas de fusão elemental"]
                }
            },
            "clube_de_combate": {
                "name": "Clube de Combate",
                "description": "Estudantes focados em técnicas de combate físico e desenvolvimento de força.",
                "leader": "Ryuji Battleborn",
                "values": ["Força", "Disciplina", "Honra"],
                "rivals": ["ilusionistas_mentais"],
                "allies": ["clube_das_chamas"],
                "reputation_thresholds": {
                    "hostile": -50,
                    "unfriendly": -20,
                    "neutral": 0,
                    "friendly": 20,
                    "close": 50,
                    "trusted": 80
                },
                "reputation_benefits": {
                    "friendly": ["Acesso a equipamentos de treino básicos"],
                    "close": ["Treinamento personalizado", "Participação em torneios internos"],
                    "trusted": ["Técnicas secretas de combate", "Parceria com lutadores de elite"]
                }
            },
            "guardioes_do_conhecimento": {
                "name": "Guardiões do Conhecimento",
                "description": "Estudantes dedicados à preservação e descoberta de conhecimentos antigos.",
                "leader": "Professora Chronos",
                "values": ["Sabedoria", "Preservação", "Descoberta"],
                "rivals": ["inovadores_tecnologicos"],
                "allies": ["elementalistas"],
                "reputation_thresholds": {
                    "hostile": -50,
                    "unfriendly": -20,
                    "neutral": 0,
                    "friendly": 20,
                    "close": 50,
                    "trusted": 80
                },
                "reputation_benefits": {
                    "friendly": ["Acesso a textos históricos básicos"],
                    "close": ["Acesso a arquivos restritos", "Orientação de mestres antigos"],
                    "trusted": ["Segredos ancestrais", "Rituais de conhecimento proibido"]
                }
            },
            "inovadores_tecnologicos": {
                "name": "Inovadores Tecnológicos",
                "description": "Estudantes focados em combinar tecnologia com poderes para criar novas possibilidades.",
                "leader": "Diretor",
                "values": ["Inovação", "Progresso", "Ciência"],
                "rivals": ["guardioes_do_conhecimento"],
                "allies": ["conselho_politico"],
                "reputation_thresholds": {
                    "hostile": -50,
                    "unfriendly": -20,
                    "neutral": 0,
                    "friendly": 20,
                    "close": 50,
                    "trusted": 80
                },
                "reputation_benefits": {
                    "friendly": ["Acesso a laboratórios básicos"],
                    "close": ["Equipamentos tecnológicos experimentais", "Participação em projetos"],
                    "trusted": ["Protótipos avançados", "Acesso ao laboratório secreto do Diretor"]
                }
            },
            "rebeldes_independentes": {
                "name": "Rebeldes Independentes",
                "description": "Estudantes que questionam a estrutura da academia e buscam mais liberdade.",
                "leader": "Desconhecido",
                "values": ["Liberdade", "Individualidade", "Questionamento"],
                "rivals": ["conselho_politico"],
                "allies": [],
                "reputation_thresholds": {
                    "hostile": -50,
                    "unfriendly": -20,
                    "neutral": 0,
                    "friendly": 20,
                    "close": 50,
                    "trusted": 80
                },
                "reputation_benefits": {
                    "friendly": ["Informações sobre falhas de segurança"],
                    "close": ["Acesso a áreas proibidas", "Rede de contatos fora da academia"],
                    "trusted": ["Segredos sobre a verdadeira história da academia", "Técnicas não-autorizadas"]
                }
            }
        }
    
    def load_data(self):
        """Load player faction reputation data from storage if it exists."""
        try:
            file_path = f"data/player_data/{self.player_id}/faction_reputation.json"
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.reputation = defaultdict(int, data.get('reputation', {}))
                    self.reputation_history = defaultdict(list, {
                        faction: [tuple(entry) for entry in entries]
                        for faction, entries in data.get('reputation_history', {}).items()
                    })
        except Exception as e:
            print(f"Error loading faction reputation data: {e}")
    
    def save_data(self):
        """Save player faction reputation data to storage."""
        try:
            file_path = f"data/player_data/{self.player_id}/faction_reputation.json"
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Convert tuples in history to lists for JSON serialization
            history_dict = {
                faction: [list(entry) for entry in entries]
                for faction, entries in self.reputation_history.items()
            }
            
            data = {
                'reputation': dict(self.reputation),
                'reputation_history': history_dict
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving faction reputation data: {e}")
    
    def change_reputation(self, faction_id, amount, reason=None):
        """
        Change the player's reputation with a faction.
        
        Args:
            faction_id (str): The ID of the faction
            amount (int): The amount to change the reputation by (positive or negative)
            reason (str, optional): The reason for the reputation change
            
        Returns:
            int: The new reputation value
        """
        # Check if faction exists
        if faction_id not in self.faction_data:
            print(f"Warning: Faction '{faction_id}' not found in faction data")
        
        # Update reputation
        self.reputation[faction_id] += amount
        
        # Record in history
        timestamp = datetime.now().isoformat()
        self.reputation_history[faction_id].append((timestamp, amount, reason or "No reason provided"))
        
        # Update rival and ally factions
        if faction_id in self.faction_data:
            faction = self.faction_data[faction_id]
            
            # Rivals lose reputation when this faction gains it (and vice versa)
            for rival_id in faction.get('rivals', []):
                rival_change = -amount // 2  # Half the effect, in the opposite direction
                if rival_change != 0:
                    self.reputation[rival_id] += rival_change
                    self.reputation_history[rival_id].append(
                        (timestamp, rival_change, f"Rival effect from {faction_id} reputation change")
                    )
            
            # Allies gain some reputation when this faction gains it (and vice versa)
            for ally_id in faction.get('allies', []):
                ally_change = amount // 3  # One-third the effect, in the same direction
                if ally_change != 0:
                    self.reputation[ally_id] += ally_change
                    self.reputation_history[ally_id].append(
                        (timestamp, ally_change, f"Ally effect from {faction_id} reputation change")
                    )
        
        self.save_data()
        return self.reputation[faction_id]
    
    def get_reputation(self, faction_id=None):
        """
        Get the player's reputation with a faction or all factions.
        
        Args:
            faction_id (str, optional): The ID of the faction
            
        Returns:
            int or dict: The reputation value for a specific faction or all factions
        """
        if faction_id:
            return self.reputation.get(faction_id, 0)
        return dict(self.reputation)
    
    def get_reputation_level(self, faction_id):
        """
        Get the player's reputation level with a faction.
        
        Args:
            faction_id (str): The ID of the faction
            
        Returns:
            str: The reputation level (hostile, unfriendly, neutral, friendly, close, trusted)
        """
        if faction_id not in self.faction_data:
            return "neutral"
        
        rep_value = self.reputation.get(faction_id, 0)
        thresholds = self.faction_data[faction_id].get('reputation_thresholds', {
            "hostile": -50,
            "unfriendly": -20,
            "neutral": 0,
            "friendly": 20,
            "close": 50,
            "trusted": 80
        })
        
        # Determine level based on thresholds
        if rep_value >= thresholds.get("trusted", 80):
            return "trusted"
        elif rep_value >= thresholds.get("close", 50):
            return "close"
        elif rep_value >= thresholds.get("friendly", 20):
            return "friendly"
        elif rep_value >= thresholds.get("neutral", 0):
            return "neutral"
        elif rep_value >= thresholds.get("unfriendly", -20):
            return "unfriendly"
        else:
            return "hostile"
    
    def get_reputation_benefits(self, faction_id):
        """
        Get the benefits the player receives from their reputation with a faction.
        
        Args:
            faction_id (str): The ID of the faction
            
        Returns:
            list: The benefits the player receives
        """
        if faction_id not in self.faction_data:
            return []
        
        level = self.get_reputation_level(faction_id)
        benefits = []
        
        # Add benefits based on current and lower levels
        reputation_benefits = self.faction_data[faction_id].get('reputation_benefits', {})
        levels_order = ["friendly", "close", "trusted"]
        
        for i, check_level in enumerate(levels_order):
            if level == check_level or i < levels_order.index(level) if level in levels_order else False:
                benefits.extend(reputation_benefits.get(check_level, []))
        
        return benefits
    
    def get_faction_response(self, faction_id, context=None):
        """
        Get how a faction responds to the player based on reputation.
        
        Args:
            faction_id (str): The ID of the faction
            context (str, optional): The context of the interaction
            
        Returns:
            dict: The faction's response data
        """
        if faction_id not in self.faction_data:
            return {"attitude": "neutral", "message": "Sem resposta específica."}
        
        level = self.get_reputation_level(faction_id)
        faction = self.faction_data[faction_id]
        
        responses = {
            "hostile": {
                "attitude": "hostile",
                "message": f"Os membros do {faction['name']} te tratam com hostilidade aberta.",
                "gameplay_effects": ["Preços aumentados", "Missões negadas", "Possíveis ataques"]
            },
            "unfriendly": {
                "attitude": "unfriendly",
                "message": f"Os membros do {faction['name']} são frios e desconfiados com você.",
                "gameplay_effects": ["Informações limitadas", "Preços elevados"]
            },
            "neutral": {
                "attitude": "neutral",
                "message": f"Os membros do {faction['name']} te tratam com neutralidade profissional.",
                "gameplay_effects": ["Interações padrão"]
            },
            "friendly": {
                "attitude": "friendly",
                "message": f"Os membros do {faction['name']} são amigáveis e prestativos.",
                "gameplay_effects": ["Pequenos descontos", "Informações extras"]
            },
            "close": {
                "attitude": "close",
                "message": f"Os membros do {faction['name']} te consideram um aliado valioso.",
                "gameplay_effects": ["Descontos significativos", "Missões especiais", "Áreas restritas"]
            },
            "trusted": {
                "attitude": "trusted",
                "message": f"Os membros do {faction['name']} confiam plenamente em você como um dos seus.",
                "gameplay_effects": ["Acesso total", "Segredos da facção", "Itens exclusivos"]
            }
        }
        
        response = responses.get(level, responses["neutral"]).copy()
        
        # Add benefits to the response
        response["benefits"] = self.get_reputation_benefits(faction_id)
        
        # Add faction-specific context if available
        if context and "context_responses" in faction:
            context_responses = faction["context_responses"].get(context, {})
            if level in context_responses:
                response["context_message"] = context_responses[level]
        
        return response
    
    def get_dominant_faction(self):
        """
        Get the faction the player has the highest reputation with.
        
        Returns:
            str: The ID of the dominant faction
        """
        if not self.reputation:
            return None
        
        return max(self.reputation.items(), key=lambda x: x[1])[0]
    
    def get_reputation_history(self, faction_id=None, limit=10):
        """
        Get the history of reputation changes for a faction or all factions.
        
        Args:
            faction_id (str, optional): The ID of the faction
            limit (int, optional): Maximum number of entries to return
            
        Returns:
            list or dict: The reputation history
        """
        if faction_id:
            history = self.reputation_history.get(faction_id, [])
            return sorted(history, key=lambda x: x[0], reverse=True)[:limit]
        
        # For all factions, return a dictionary with limited history for each
        return {
            faction: sorted(history, key=lambda x: x[0], reverse=True)[:limit]
            for faction, history in self.reputation_history.items()
        }