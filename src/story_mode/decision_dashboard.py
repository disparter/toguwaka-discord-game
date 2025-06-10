from typing import Dict, List, Any, Optional, Union
import json
import logging
import os
import random
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger('tokugawa_bot')

class DecisionTracker:
    """
    Tracks player decisions and provides community comparison functionality.
    
    This system:
    1. Records player choices
    2. Aggregates community choice statistics
    3. Provides comparison between player and community choices
    4. Offers ethical reflections on choices
    """
    
    def __init__(self, data_dir: str):
        """
        Initialize the decision tracker.
        
        Args:
            data_dir: Directory to store community choice data
        """
        self.data_dir = data_dir
        self.community_choices_file = os.path.join(data_dir, "community_choices.json")
        self.ethical_reflections_file = os.path.join(data_dir, "ethical_reflections.json")
        self.community_choices = self._load_community_choices()
        self.ethical_reflections = self._load_ethical_reflections()
        
    def _load_community_choices(self) -> Dict[str, Dict[str, Dict[str, int]]]:
        """
        Load community choice data from file.
        
        Returns:
            Dictionary of community choices
        """
        if not os.path.exists(self.community_choices_file):
            # Initialize with empty structure
            community_choices = {}
            self._save_community_choices(community_choices)
            return community_choices
            
        try:
            with open(self.community_choices_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading community choices: {e}")
            return {}
            
    def _save_community_choices(self, community_choices: Dict[str, Dict[str, Dict[str, int]]]) -> bool:
        """
        Save community choice data to file.
        
        Args:
            community_choices: Dictionary of community choices
            
        Returns:
            True if successful, False otherwise
        """
        try:
            os.makedirs(os.path.dirname(self.community_choices_file), exist_ok=True)
            with open(self.community_choices_file, 'w', encoding='utf-8') as f:
                json.dump(community_choices, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving community choices: {e}")
            return False
            
    def _load_ethical_reflections(self) -> Dict[str, Dict[str, List[str]]]:
        """
        Load ethical reflection data from file.
        
        Returns:
            Dictionary of ethical reflections
        """
        if not os.path.exists(self.ethical_reflections_file):
            # Initialize with default reflections
            ethical_reflections = self._generate_default_reflections()
            self._save_ethical_reflections(ethical_reflections)
            return ethical_reflections
            
        try:
            with open(self.ethical_reflections_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading ethical reflections: {e}")
            return self._generate_default_reflections()
            
    def _save_ethical_reflections(self, ethical_reflections: Dict[str, Dict[str, List[str]]]) -> bool:
        """
        Save ethical reflection data to file.
        
        Args:
            ethical_reflections: Dictionary of ethical reflections
            
        Returns:
            True if successful, False otherwise
        """
        try:
            os.makedirs(os.path.dirname(self.ethical_reflections_file), exist_ok=True)
            with open(self.ethical_reflections_file, 'w', encoding='utf-8') as f:
                json.dump(ethical_reflections, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving ethical reflections: {e}")
            return False
            
    def _generate_default_reflections(self) -> Dict[str, Dict[str, List[str]]]:
        """
        Generate default ethical reflections.
        
        Returns:
            Dictionary of default ethical reflections
        """
        return {
            "general": {
                "power": [
                    "Como você equilibra poder e responsabilidade em suas escolhas?",
                    "Você considera as consequências de longo prazo ao buscar mais poder?",
                    "O poder deve ser um meio para um fim ou um fim em si mesmo?"
                ],
                "loyalty": [
                    "Até que ponto a lealdade deve ser mantida quando confrontada com dilemas éticos?",
                    "Você prioriza lealdade a indivíduos ou a princípios?",
                    "Como você equilibra lealdade com pensamento crítico?"
                ],
                "justice": [
                    "O que significa justiça para você em um mundo de poderes desiguais?",
                    "Você prioriza justiça individual ou bem-estar coletivo?",
                    "Como você lida com situações onde justiça e misericórdia parecem conflitantes?"
                ],
                "truth": [
                    "Existem momentos em que ocultar a verdade é eticamente justificável?",
                    "Como você equilibra honestidade com compaixão?",
                    "Qual é o valor da verdade em um mundo de percepções subjetivas?"
                ],
                "freedom": [
                    "Quais são os limites apropriados para a liberdade individual?",
                    "Como você equilibra liberdade pessoal com responsabilidade social?",
                    "A liberdade sem restrições leva a melhores resultados para todos?"
                ]
            },
            "clubs": {
                "1": [  # Flames
                    "Como você equilibra poder destrutivo com propósito construtivo?",
                    "A intensidade e paixão justificam meios mais agressivos para atingir objetivos?",
                    "Qual é a responsabilidade de quem possui poder capaz de causar grande destruição?"
                ],
                "2": [  # Mental
                    "Quais são os limites éticos da influência mental sobre outros?",
                    "Como você equilibra manipulação estratégica com respeito pela autonomia?",
                    "O conhecimento deve ser compartilhado livremente ou controlado cuidadosamente?"
                ],
                "3": [  # Political
                    "O poder político deve servir a quem: ao indivíduo, ao grupo ou a todos?",
                    "Quais compromissos são aceitáveis na busca por influência e estabilidade?",
                    "Como você equilibra pragmatismo político com princípios morais?"
                ],
                "4": [  # Elemental
                    "Como sua conexão com os elementos influencia sua visão sobre equilíbrio e harmonia?",
                    "Qual é nossa responsabilidade com o mundo natural ao usar seus poderes?",
                    "O equilíbrio deve ser mantido a todo custo ou existem momentos para desequilíbrio intencional?"
                ],
                "5": [  # Combat
                    "Quando o uso da força é justificável?",
                    "Como você equilibra competição e cooperação em sua filosofia de combate?",
                    "Qual é o propósito final do poder marcial: proteção, dominação ou crescimento pessoal?"
                ]
            },
            "chapters": {
                # Chapter-specific reflections can be added here
            }
        }
        
    def record_player_choice(self, player_data: Dict[str, Any], chapter_id: str, choice_key: str, choice_text: str) -> bool:
        """
        Record a player's choice and update community statistics.
        
        Args:
            player_data: Player data dictionary
            chapter_id: ID of the chapter
            choice_key: Key or index of the choice
            choice_text: Text of the choice
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Initialize player's choice history if not present
            if "choice_history" not in player_data:
                player_data["choice_history"] = {}
                
            # Record choice in player data
            if chapter_id not in player_data["choice_history"]:
                player_data["choice_history"][chapter_id] = {}
                
            player_data["choice_history"][chapter_id][choice_key] = {
                "text": choice_text,
                "timestamp": datetime.now().isoformat()
            }
            
            # Update community statistics
            community_choices = self._load_community_choices()
            
            if chapter_id not in community_choices:
                community_choices[chapter_id] = {}
                
            if choice_key not in community_choices[chapter_id]:
                community_choices[chapter_id][choice_key] = {}
                
            if choice_text not in community_choices[chapter_id][choice_key]:
                community_choices[chapter_id][choice_key][choice_text] = 0
                
            community_choices[chapter_id][choice_key][choice_text] += 1
            
            # Save updated community choices
            self._save_community_choices(community_choices)
            
            return True
        except Exception as e:
            logger.error(f"Error recording player choice: {e}")
            return False
            
    def get_community_comparison(self, player_data: Dict[str, Any], chapter_id: str, choice_key: str) -> Dict[str, Any]:
        """
        Get comparison between player's choice and community choices.
        
        Args:
            player_data: Player data dictionary
            chapter_id: ID of the chapter
            choice_key: Key or index of the choice
            
        Returns:
            Dictionary with comparison data
        """
        try:
            # Check if player has made this choice
            if ("choice_history" not in player_data or 
                chapter_id not in player_data["choice_history"] or 
                choice_key not in player_data["choice_history"][chapter_id]):
                return {"error": "Player has not made this choice"}
                
            player_choice = player_data["choice_history"][chapter_id][choice_key]["text"]
            
            # Get community choices
            community_choices = self._load_community_choices()
            
            if (chapter_id not in community_choices or 
                choice_key not in community_choices[chapter_id]):
                return {
                    "player_choice": player_choice,
                    "community_choices": {},
                    "total_choices": 0,
                    "percentage": 0,
                    "message": "Não há dados suficientes da comunidade para comparação."
                }
                
            # Calculate statistics
            choice_stats = community_choices[chapter_id][choice_key]
            total_choices = sum(choice_stats.values())
            
            # Calculate percentages
            percentages = {}
            for choice_text, count in choice_stats.items():
                percentages[choice_text] = (count / total_choices) * 100
                
            # Get player's percentage
            player_percentage = percentages.get(player_choice, 0)
            
            # Generate message
            if player_percentage < 10:
                message = "Sua escolha é rara! Menos de 10% dos jogadores fizeram a mesma escolha."
            elif player_percentage < 30:
                message = "Sua escolha é incomum. Cerca de {:.1f}% dos jogadores fizeram a mesma escolha.".format(player_percentage)
            elif player_percentage < 50:
                message = "Sua escolha é relativamente comum. {:.1f}% dos jogadores fizeram a mesma escolha.".format(player_percentage)
            elif player_percentage < 70:
                message = "Sua escolha é popular. {:.1f}% dos jogadores fizeram a mesma escolha.".format(player_percentage)
            else:
                message = "Sua escolha é muito popular! {:.1f}% dos jogadores fizeram a mesma escolha.".format(player_percentage)
                
            return {
                "player_choice": player_choice,
                "community_choices": percentages,
                "total_choices": total_choices,
                "player_percentage": player_percentage,
                "message": message
            }
        except Exception as e:
            logger.error(f"Error getting community comparison: {e}")
            return {"error": f"Error getting community comparison: {e}"}
            
    def get_ethical_reflection(self, player_data: Dict[str, Any], category: str = None, specific_id: str = None) -> Dict[str, Any]:
        """
        Get ethical reflection prompts based on player's choices or specified category.
        
        Args:
            player_data: Player data dictionary
            category: Optional category for reflection (power, loyalty, etc.)
            specific_id: Optional specific ID (chapter_id, club_id, etc.)
            
        Returns:
            Dictionary with reflection prompts
        """
        try:
            reflections = self._load_ethical_reflections()
            
            # If specific chapter reflection is requested
            if category == "chapter" and specific_id:
                if "chapters" in reflections and specific_id in reflections["chapters"]:
                    chapter_reflections = reflections["chapters"][specific_id]
                    return {
                        "category": "chapter",
                        "id": specific_id,
                        "reflections": chapter_reflections,
                        "message": f"Reflexões sobre o Capítulo {specific_id}"
                    }
                    
            # If club reflection is requested
            if category == "club" and specific_id:
                if "clubs" in reflections and specific_id in reflections["clubs"]:
                    club_reflections = reflections["clubs"][specific_id]
                    return {
                        "category": "club",
                        "id": specific_id,
                        "reflections": club_reflections,
                        "message": f"Reflexões sobre seu Clube"
                    }
                    
            # If general category reflection is requested
            if category and "general" in reflections and category in reflections["general"]:
                general_reflections = reflections["general"][category]
                return {
                    "category": category,
                    "reflections": general_reflections,
                    "message": f"Reflexões sobre {category.capitalize()}"
                }
                
            # If no specific reflection is requested, choose random category
            if "general" in reflections:
                categories = list(reflections["general"].keys())
                random_category = random.choice(categories)
                general_reflections = reflections["general"][random_category]
                return {
                    "category": random_category,
                    "reflections": general_reflections,
                    "message": f"Reflexões sobre {random_category.capitalize()}"
                }
                
            # Fallback
            return {
                "category": "general",
                "reflections": [
                    "Como suas escolhas refletem seus valores pessoais?",
                    "Você considera as consequências de longo prazo de suas decisões?",
                    "Que tipo de mundo suas escolhas estão ajudando a criar?"
                ],
                "message": "Reflexões Gerais"
            }
        except Exception as e:
            logger.error(f"Error getting ethical reflection: {e}")
            return {"error": f"Error getting ethical reflection: {e}"}
            
    def get_alternative_paths(self, player_data: Dict[str, Any], chapter_id: str) -> Dict[str, Any]:
        """
        Get information about alternative paths not taken by the player.
        
        Args:
            player_data: Player data dictionary
            chapter_id: ID of the chapter
            
        Returns:
            Dictionary with alternative path information
        """
        try:
            # Check if player has made choices in this chapter
            if ("choice_history" not in player_data or 
                chapter_id not in player_data["choice_history"]):
                return {"error": "Player has not made choices in this chapter"}
                
            player_choices = player_data["choice_history"][chapter_id]
            
            # Get community choices
            community_choices = self._load_community_choices()
            
            if chapter_id not in community_choices:
                return {
                    "chapter_id": chapter_id,
                    "alternative_paths": [],
                    "message": "Não há dados suficientes sobre caminhos alternativos."
                }
                
            # Find choices in this chapter that the player didn't make
            alternative_paths = []
            
            for choice_key, choices in community_choices[chapter_id].items():
                # Skip if player didn't make a choice here (shouldn't happen normally)
                if choice_key not in player_choices:
                    continue
                    
                player_choice_text = player_choices[choice_key]["text"]
                
                # Find alternative choices for this decision point
                alternatives = []
                for choice_text, count in choices.items():
                    if choice_text != player_choice_text:
                        # Only include alternatives chosen by at least 5% of players
                        total_choices = sum(choices.values())
                        percentage = (count / total_choices) * 100
                        
                        if percentage >= 5:
                            alternatives.append({
                                "text": choice_text,
                                "percentage": percentage
                            })
                            
                # Sort alternatives by popularity
                alternatives.sort(key=lambda x: x["percentage"], reverse=True)
                
                if alternatives:
                    alternative_paths.append({
                        "choice_key": choice_key,
                        "player_choice": player_choice_text,
                        "alternatives": alternatives[:3]  # Top 3 alternatives
                    })
                    
            # Generate message
            if not alternative_paths:
                message = "Você seguiu os caminhos mais comuns neste capítulo."
            elif len(alternative_paths) == 1:
                message = "Há um ponto de decisão importante onde você poderia ter feito uma escolha diferente."
            else:
                message = f"Há {len(alternative_paths)} pontos de decisão importantes onde você poderia ter feito escolhas diferentes."
                
            return {
                "chapter_id": chapter_id,
                "alternative_paths": alternative_paths,
                "message": message
            }
        except Exception as e:
            logger.error(f"Error getting alternative paths: {e}")
            return {"error": f"Error getting alternative paths: {e}"}
            
    def get_player_choice_patterns(self, player_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze player's choice patterns across all chapters.
        
        Args:
            player_data: Player data dictionary
            
        Returns:
            Dictionary with pattern analysis
        """
        try:
            # Check if player has made any choices
            if "choice_history" not in player_data or not player_data["choice_history"]:
                return {"error": "Player has not made any choices"}
                
            # Initialize pattern counters
            patterns = {
                "power": 0,
                "diplomacy": 0,
                "knowledge": 0,
                "compassion": 0,
                "independence": 0
            }
            
            # Get player's club for context
            club_id = player_data.get("club", {}).get("id")
            
            # Analyze choices
            total_choices = 0
            
            for chapter_id, choices in player_data["choice_history"].items():
                for choice_key, choice_data in choices.items():
                    choice_text = choice_data["text"].lower()
                    total_choices += 1
                    
                    # Simple keyword analysis
                    if any(word in choice_text for word in ["poder", "força", "controle", "dominar", "liderar"]):
                        patterns["power"] += 1
                        
                    if any(word in choice_text for word in ["conversar", "negociar", "acordo", "aliança", "diplomacia"]):
                        patterns["diplomacy"] += 1
                        
                    if any(word in choice_text for word in ["aprender", "estudar", "conhecimento", "informação", "descobrir"]):
                        patterns["knowledge"] += 1
                        
                    if any(word in choice_text for word in ["ajudar", "proteger", "salvar", "cuidar", "compaixão"]):
                        patterns["compassion"] += 1
                        
                    if any(word in choice_text for word in ["sozinho", "independente", "próprio", "caminho", "liberdade"]):
                        patterns["independence"] += 1
                        
            # Calculate percentages
            if total_choices > 0:
                for key in patterns:
                    patterns[key] = (patterns[key] / total_choices) * 100
                    
            # Determine dominant traits (top 2)
            sorted_patterns = sorted(patterns.items(), key=lambda x: x[1], reverse=True)
            dominant_traits = [trait for trait, _ in sorted_patterns[:2] if _ > 0]
            
            # Generate personality description
            personality = self._generate_personality_description(dominant_traits, club_id)
            
            return {
                "patterns": patterns,
                "dominant_traits": dominant_traits,
                "total_choices": total_choices,
                "personality": personality
            }
        except Exception as e:
            logger.error(f"Error analyzing choice patterns: {e}")
            return {"error": f"Error analyzing choice patterns: {e}"}
            
    def _generate_personality_description(self, dominant_traits: List[str], club_id: Optional[int] = None) -> str:
        """
        Generate a personality description based on dominant traits and club.
        
        Args:
            dominant_traits: List of dominant traits
            club_id: Optional club ID for context
            
        Returns:
            Personality description
        """
        # Trait descriptions
        trait_descriptions = {
            "power": "você valoriza poder e controle, buscando posições de liderança e influência",
            "diplomacy": "você prefere resolver conflitos através de negociação e construção de alianças",
            "knowledge": "você prioriza a busca por conhecimento e compreensão do mundo",
            "compassion": "você demonstra grande empatia e desejo de ajudar os outros",
            "independence": "você valoriza sua liberdade e autonomia acima de tudo"
        }
        
        # Club-specific context
        club_context = {
            1: {  # Flames
                "power": "o que se alinha perfeitamente com a filosofia do Clube das Chamas",
                "diplomacy": "o que pode parecer contraditório para um membro do Clube das Chamas, mas demonstra versatilidade",
                "knowledge": "o que pode complementar bem o foco em poder do Clube das Chamas",
                "compassion": "o que traz um equilíbrio interessante ao seu treinamento no Clube das Chamas",
                "independence": "o que ressoa com o espírito individualista do Clube das Chamas"
            },
            2: {  # Mental
                "power": "o que pode parecer contraditório para um Ilusionista Mental, mas demonstra ambição",
                "diplomacy": "o que complementa perfeitamente as habilidades de um Ilusionista Mental",
                "knowledge": "o que se alinha perfeitamente com a filosofia dos Ilusionistas Mentais",
                "compassion": "o que traz uma dimensão ética importante ao seu treinamento como Ilusionista Mental",
                "independence": "o que reflete a natureza introspectiva dos Ilusionistas Mentais"
            },
            3: {  # Political
                "power": "o que se alinha com as ambições esperadas de um membro do Conselho Político",
                "diplomacy": "o que demonstra sua aptidão natural para o Conselho Político",
                "knowledge": "o que fornece uma base sólida para suas estratégias no Conselho Político",
                "compassion": "o que traz uma perspectiva humanitária rara ao Conselho Político",
                "independence": "o que pode criar tensões interessantes com a natureza coletiva do Conselho Político"
            },
            4: {  # Elemental
                "power": "o que pode desequilibrar sua harmonia como Elementalista se não for bem administrado",
                "diplomacy": "o que reflete o equilíbrio e harmonia valorizados pelos Elementalistas",
                "knowledge": "o que aprofunda sua conexão com os elementos como Elementalista",
                "compassion": "o que ressoa com a filosofia de equilíbrio dos Elementalistas",
                "independence": "o que reflete sua jornada pessoal de conexão com os elementos"
            },
            5: {  # Combat
                "power": "o que intensifica sua eficácia no Clube de Combate",
                "diplomacy": "o que traz uma dimensão estratégica interessante ao seu treinamento no Clube de Combate",
                "knowledge": "o que transforma você em um lutador mais técnico e tático no Clube de Combate",
                "compassion": "o que pode parecer contraditório para um membro do Clube de Combate, mas demonstra profundidade",
                "independence": "o que faz de você um competidor imprevisível no Clube de Combate"
            }
        }
        
        # Generate description
        if not dominant_traits:
            return "Seu padrão de escolhas ainda não revela traços dominantes claros em sua personalidade."
            
        if len(dominant_traits) == 1:
            trait = dominant_traits[0]
            description = f"Suas escolhas revelam que {trait_descriptions[trait]}"
            
            if club_id in club_context:
                description += f", {club_context[club_id][trait]}."
            else:
                description += "."
                
            return description
            
        # Two dominant traits
        trait1, trait2 = dominant_traits[:2]
        description = f"Suas escolhas revelam uma personalidade que combina {trait_descriptions[trait1]} com {trait_descriptions[trait2]}"
        
        if club_id in club_context:
            description += f". Como membro do clube, {club_context[club_id][trait1][:-1]} e {club_context[club_id][trait2]}."
        else:
            description += "."
            
        return description
        
    def generate_dashboard(self, player_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a comprehensive dashboard of player's choices and comparisons.
        
        Args:
            player_data: Player data dictionary
            
        Returns:
            Dictionary with dashboard data
        """
        try:
            # Check if player has made any choices
            if "choice_history" not in player_data or not player_data["choice_history"]:
                return {"error": "Player has not made any choices"}
                
            # Get personality analysis
            personality = self.get_player_choice_patterns(player_data)
            
            # Get ethical reflection
            if "club" in player_data and player_data["club"].get("id"):
                reflection = self.get_ethical_reflection(player_data, "club", str(player_data["club"]["id"]))
            else:
                reflection = self.get_ethical_reflection(player_data)
                
            # Get recent chapters with choices
            recent_chapters = list(player_data["choice_history"].keys())[-5:]
            
            # Get community comparisons for recent chapters
            comparisons = []
            for chapter_id in recent_chapters:
                # Get the last choice in each chapter
                choice_keys = list(player_data["choice_history"][chapter_id].keys())
                if choice_keys:
                    last_choice = choice_keys[-1]
                    comparison = self.get_community_comparison(player_data, chapter_id, last_choice)
                    if "error" not in comparison:
                        comparisons.append({
                            "chapter_id": chapter_id,
                            "choice_key": last_choice,
                            "comparison": comparison
                        })
                        
            # Get alternative paths for most recent chapter
            alternatives = {}
            if recent_chapters:
                most_recent = recent_chapters[-1]
                alternatives = self.get_alternative_paths(player_data, most_recent)
                
            return {
                "personality": personality,
                "ethical_reflection": reflection,
                "recent_comparisons": comparisons,
                "alternative_paths": alternatives,
                "total_choices_made": sum(len(choices) for choices in player_data["choice_history"].values()),
                "chapters_completed": len(player_data["choice_history"])
            }
        except Exception as e:
            logger.error(f"Error generating dashboard: {e}")
            return {"error": f"Error generating dashboard: {e}"}

# Singleton instance
_decision_tracker = None

def get_decision_tracker(data_dir=None):
    """
    Get the singleton instance of the DecisionTracker.
    
    Args:
        data_dir: Optional directory to store data
        
    Returns:
        DecisionTracker instance
    """
    global _decision_tracker
    if _decision_tracker is None:
        if data_dir is None:
            data_dir = os.path.join("data", "story_mode", "community")
        _decision_tracker = DecisionTracker(data_dir)
    return _decision_tracker