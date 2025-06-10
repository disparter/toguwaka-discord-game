from typing import Dict, List, Any, Optional, Union
import json
import logging
import random
from datetime import datetime, timedelta
from .consequences import DynamicConsequencesSystem

logger = logging.getLogger('tokugawa_bot')

class ClubSystem:
    """
    Enhanced club system that implements:
    1. Rivalries and alliances between clubs
    2. Club competitions
    3. Rank progression within clubs
    4. Club-specific missions
    """
    
    # Club IDs and names
    CLUBS = {
        1: "Clube das Chamas",
        2: "Ilusionistas Mentais",
        3: "Conselho Político",
        4: "Elementalistas",
        5: "Clube de Combate"
    }
    
    # Club leaders
    CLUB_LEADERS = {
        1: "Kai Flameheart",
        2: "Luna Mindweaver",
        3: "Alexander Strategos",
        4: "Gaia Naturae",
        5: "Ryuji Battleborn"
    }
    
    # Predefined rivalries between clubs
    DEFAULT_RIVALRIES = {
        1: [2],  # Flames vs Mental
        2: [1, 3],  # Mental vs Flames and Political
        3: [2, 5],  # Political vs Mental and Combat
        4: [1],  # Elemental vs Flames
        5: [3]   # Combat vs Political
    }
    
    # Predefined alliances between clubs
    DEFAULT_ALLIANCES = {
        1: [5],  # Flames and Combat
        2: [4],  # Mental and Elemental
        3: [4],  # Political and Elemental
        4: [2, 3],  # Elemental with Mental and Political
        5: [1]   # Combat and Flames
    }
    
    # Rank levels within clubs
    RANKS = {
        1: "Iniciante",
        2: "Aprendiz",
        3: "Membro",
        4: "Membro Avançado",
        5: "Elite",
        6: "Vice-Líder",
        7: "Líder"
    }
    
    def __init__(self, consequences_system: Optional[DynamicConsequencesSystem] = None):
        """
        Initialize the club system.
        
        Args:
            consequences_system: Optional reference to the consequences system for integration
        """
        self.consequences_system = consequences_system
        
    def initialize_player_club_data(self, player_data: Dict[str, Any]) -> None:
        """
        Initialize club-related data for a new player.
        
        Args:
            player_data: Player data dictionary
        """
        if "club" not in player_data:
            player_data["club"] = {
                "id": None,
                "rank": 1,
                "experience": 0,
                "joined_date": None,
                "missions_completed": 0,
                "competitions_won": 0,
                "rivalries": {},
                "alliances": {},
                "pending_missions": [],
                "completed_missions": [],
                "competition_history": []
            }
            
    def join_club(self, player_data: Dict[str, Any], club_id: int) -> bool:
        """
        Join a club.
        
        Args:
            player_data: Player data dictionary
            club_id: ID of the club to join
            
        Returns:
            True if successful, False otherwise
        """
        if club_id not in self.CLUBS:
            logger.error(f"Invalid club ID: {club_id}")
            return False
            
        self.initialize_player_club_data(player_data)
        
        # If player is already in a club, leave it first
        if player_data["club"]["id"] is not None:
            self.leave_club(player_data)
            
        # Join the new club
        player_data["club"]["id"] = club_id
        player_data["club"]["rank"] = 1
        player_data["club"]["experience"] = 0
        player_data["club"]["joined_date"] = datetime.now().isoformat()
        
        # Initialize rivalries and alliances based on defaults
        player_data["club"]["rivalries"] = {str(rival): 0 for rival in self.DEFAULT_RIVALRIES.get(club_id, [])}
        player_data["club"]["alliances"] = {str(ally): 0 for ally in self.DEFAULT_ALLIANCES.get(club_id, [])}
        
        # Add initial missions
        self._generate_initial_missions(player_data)
        
        # Update affinity with club leader
        leader_name = self.CLUB_LEADERS.get(club_id)
        if leader_name and self.consequences_system:
            self.consequences_system.update_faction_reputation(player_data, leader_name, 10)
            
        return True
        
    def leave_club(self, player_data: Dict[str, Any]) -> bool:
        """
        Leave the current club.
        
        Args:
            player_data: Player data dictionary
            
        Returns:
            True if successful, False otherwise
        """
        self.initialize_player_club_data(player_data)
        
        if player_data["club"]["id"] is None:
            logger.warning("Player is not in a club")
            return False
            
        # Store the old club ID for affinity updates
        old_club_id = player_data["club"]["id"]
        
        # Reset club data
        player_data["club"]["id"] = None
        player_data["club"]["rank"] = 1
        player_data["club"]["experience"] = 0
        player_data["club"]["joined_date"] = None
        player_data["club"]["missions_completed"] = 0
        player_data["club"]["competitions_won"] = 0
        player_data["club"]["rivalries"] = {}
        player_data["club"]["alliances"] = {}
        player_data["club"]["pending_missions"] = []
        player_data["club"]["completed_missions"] = []
        
        # Update affinity with old club leader (negative)
        leader_name = self.CLUB_LEADERS.get(old_club_id)
        if leader_name and self.consequences_system:
            self.consequences_system.update_faction_reputation(player_data, leader_name, -15)
            
        return True
        
    def get_club_info(self, player_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get information about the player's current club.
        
        Args:
            player_data: Player data dictionary
            
        Returns:
            Dictionary with club information
        """
        self.initialize_player_club_data(player_data)
        
        club_id = player_data["club"]["id"]
        if club_id is None:
            return {"error": "Player is not in a club"}
            
        return {
            "id": club_id,
            "name": self.CLUBS.get(club_id, "Unknown Club"),
            "leader": self.CLUB_LEADERS.get(club_id, "Unknown Leader"),
            "rank": player_data["club"]["rank"],
            "rank_name": self.RANKS.get(player_data["club"]["rank"], "Unknown Rank"),
            "experience": player_data["club"]["experience"],
            "experience_needed": self._get_experience_for_next_rank(player_data["club"]["rank"]),
            "joined_date": player_data["club"]["joined_date"],
            "missions_completed": player_data["club"]["missions_completed"],
            "competitions_won": player_data["club"]["competitions_won"],
            "rivalries": self._get_rivalries_info(player_data),
            "alliances": self._get_alliances_info(player_data),
            "pending_missions": player_data["club"]["pending_missions"],
            "completed_missions": player_data["club"]["completed_missions"][-5:],  # Last 5 completed missions
            "competition_history": player_data["club"]["competition_history"][-5:]  # Last 5 competitions
        }
        
    def _get_rivalries_info(self, player_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get information about club rivalries.
        
        Args:
            player_data: Player data dictionary
            
        Returns:
            List of rivalry information dictionaries
        """
        rivalries = []
        for rival_id_str, intensity in player_data["club"]["rivalries"].items():
            rival_id = int(rival_id_str)
            rivalries.append({
                "id": rival_id,
                "name": self.CLUBS.get(rival_id, "Unknown Club"),
                "leader": self.CLUB_LEADERS.get(rival_id, "Unknown Leader"),
                "intensity": intensity
            })
        return rivalries
        
    def _get_alliances_info(self, player_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get information about club alliances.
        
        Args:
            player_data: Player data dictionary
            
        Returns:
            List of alliance information dictionaries
        """
        alliances = []
        for ally_id_str, strength in player_data["club"]["alliances"].items():
            ally_id = int(ally_id_str)
            alliances.append({
                "id": ally_id,
                "name": self.CLUBS.get(ally_id, "Unknown Club"),
                "leader": self.CLUB_LEADERS.get(ally_id, "Unknown Leader"),
                "strength": strength
            })
        return alliances
        
    def add_club_experience(self, player_data: Dict[str, Any], experience: int) -> Dict[str, Any]:
        """
        Add experience to the player's club rank.
        
        Args:
            player_data: Player data dictionary
            experience: Amount of experience to add
            
        Returns:
            Dictionary with rank up information if applicable
        """
        self.initialize_player_club_data(player_data)
        
        if player_data["club"]["id"] is None:
            return {"error": "Player is not in a club"}
            
        old_rank = player_data["club"]["rank"]
        player_data["club"]["experience"] += experience
        
        # Check for rank up
        while (player_data["club"]["rank"] < 7 and 
               player_data["club"]["experience"] >= self._get_experience_for_next_rank(player_data["club"]["rank"])):
            player_data["club"]["rank"] += 1
            
        new_rank = player_data["club"]["rank"]
        
        result = {
            "experience_gained": experience,
            "total_experience": player_data["club"]["experience"],
            "rank": new_rank,
            "rank_name": self.RANKS.get(new_rank, "Unknown Rank")
        }
        
        if new_rank > old_rank:
            result["rank_up"] = True
            result["old_rank"] = old_rank
            result["old_rank_name"] = self.RANKS.get(old_rank, "Unknown Rank")
            
            # Update affinity with club leader on rank up
            leader_name = self.CLUB_LEADERS.get(player_data["club"]["id"])
            if leader_name and self.consequences_system:
                self.consequences_system.update_faction_reputation(player_data, leader_name, 5 * (new_rank - old_rank))
                
        return result
        
    def _get_experience_for_next_rank(self, current_rank: int) -> int:
        """
        Get the experience required for the next rank.
        
        Args:
            current_rank: Current rank level
            
        Returns:
            Experience required for the next rank
        """
        if current_rank >= 7:  # Max rank
            return float('inf')
            
        # Experience requirements increase exponentially
        return 100 * (2 ** (current_rank - 1))
        
    def _generate_initial_missions(self, player_data: Dict[str, Any]) -> None:
        """
        Generate initial missions for a new club member.
        
        Args:
            player_data: Player data dictionary
        """
        club_id = player_data["club"]["id"]
        if club_id is None:
            return
            
        # Generate 3 initial missions
        missions = []
        
        # Training mission
        missions.append({
            "id": f"training_{club_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "title": f"Treinamento Básico: {self.CLUBS.get(club_id)}",
            "description": f"Complete um treinamento básico com {self.CLUB_LEADERS.get(club_id)} para aprender as técnicas fundamentais do clube.",
            "difficulty": 1,
            "experience_reward": 50,
            "deadline": (datetime.now() + timedelta(days=7)).isoformat(),
            "type": "training",
            "status": "pending"
        })
        
        # Club history mission
        missions.append({
            "id": f"history_{club_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "title": f"História do {self.CLUBS.get(club_id)}",
            "description": f"Aprenda sobre a história e filosofia do {self.CLUBS.get(club_id)} através de pesquisa na biblioteca da academia.",
            "difficulty": 1,
            "experience_reward": 30,
            "deadline": (datetime.now() + timedelta(days=5)).isoformat(),
            "type": "research",
            "status": "pending"
        })
        
        # Meet members mission
        missions.append({
            "id": f"members_{club_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "title": f"Conheça os Membros do {self.CLUBS.get(club_id)}",
            "description": f"Apresente-se a pelo menos 3 membros do {self.CLUBS.get(club_id)} e aprenda sobre suas especialidades.",
            "difficulty": 1,
            "experience_reward": 20,
            "deadline": (datetime.now() + timedelta(days=3)).isoformat(),
            "type": "social",
            "status": "pending"
        })
        
        player_data["club"]["pending_missions"] = missions
        
    def generate_new_mission(self, player_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a new mission for the player based on their club and rank.
        
        Args:
            player_data: Player data dictionary
            
        Returns:
            The newly generated mission
        """
        self.initialize_player_club_data(player_data)
        
        club_id = player_data["club"]["id"]
        if club_id is None:
            return {"error": "Player is not in a club"}
            
        rank = player_data["club"]["rank"]
        
        # Mission types by club
        mission_types = {
            1: ["combat", "training", "challenge", "exploration"],  # Flames
            2: ["research", "puzzle", "social", "investigation"],   # Mental
            3: ["diplomacy", "debate", "strategy", "leadership"],   # Political
            4: ["nature", "harmony", "exploration", "research"],    # Elemental
            5: ["combat", "tournament", "training", "challenge"]    # Combat
        }
        
        # Select mission type based on club
        mission_type = random.choice(mission_types.get(club_id, ["general"]))
        
        # Difficulty based on rank
        difficulty = min(rank, 5)
        
        # Experience reward based on difficulty
        experience_reward = 30 * difficulty
        
        # Generate mission ID
        mission_id = f"{mission_type}_{club_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Generate mission title and description based on type and club
        title, description = self._generate_mission_content(mission_type, club_id, difficulty)
        
        # Create mission
        mission = {
            "id": mission_id,
            "title": title,
            "description": description,
            "difficulty": difficulty,
            "experience_reward": experience_reward,
            "deadline": (datetime.now() + timedelta(days=7)).isoformat(),
            "type": mission_type,
            "status": "pending"
        }
        
        # Add to pending missions
        player_data["club"]["pending_missions"].append(mission)
        
        return mission
        
    def _generate_mission_content(self, mission_type: str, club_id: int, difficulty: int) -> tuple:
        """
        Generate mission title and description based on type, club, and difficulty.
        
        Args:
            mission_type: Type of mission
            club_id: ID of the club
            difficulty: Difficulty level (1-5)
            
        Returns:
            Tuple of (title, description)
        """
        club_name = self.CLUBS.get(club_id, "Unknown Club")
        leader_name = self.CLUB_LEADERS.get(club_id, "Unknown Leader")
        
        # Mission templates by type
        templates = {
            "combat": (
                f"Desafio de Combate Nível {difficulty}",
                f"Complete um desafio de combate de nível {difficulty} para demonstrar suas habilidades. {leader_name} avaliará seu desempenho."
            ),
            "training": (
                f"Treinamento Avançado Nível {difficulty}",
                f"Participe de uma sessão de treinamento avançado nível {difficulty} com membros experientes do {club_name}."
            ),
            "research": (
                f"Pesquisa Arcana Nível {difficulty}",
                f"Conduza uma pesquisa de nível {difficulty} sobre um tópico relevante para o {club_name} e apresente seus resultados."
            ),
            "puzzle": (
                f"Enigma Mental Nível {difficulty}",
                f"Resolva um enigma mental de nível {difficulty} preparado por {leader_name} para testar sua agilidade mental."
            ),
            "social": (
                f"Missão Diplomática Nível {difficulty}",
                f"Represente o {club_name} em um evento social de nível {difficulty} e estabeleça conexões importantes para o clube."
            ),
            "diplomacy": (
                f"Negociação Estratégica Nível {difficulty}",
                f"Conduza uma negociação de nível {difficulty} com representantes de outro clube para beneficiar o {club_name}."
            ),
            "nature": (
                f"Comunhão com a Natureza Nível {difficulty}",
                f"Complete um ritual de comunhão com a natureza de nível {difficulty} para fortalecer sua conexão com os elementos."
            ),
            "tournament": (
                f"Torneio de Habilidades Nível {difficulty}",
                f"Participe de um torneio de nível {difficulty} e alcance pelo menos o top {6-difficulty} para trazer honra ao {club_name}."
            ),
            "challenge": (
                f"Desafio do {leader_name} Nível {difficulty}",
                f"Complete um desafio pessoal de nível {difficulty} designado por {leader_name} para provar seu valor."
            ),
            "exploration": (
                f"Exploração dos Territórios Nível {difficulty}",
                f"Explore uma área restrita de nível {difficulty} da academia e traga informações valiosas para o {club_name}."
            ),
            "investigation": (
                f"Investigação Secreta Nível {difficulty}",
                f"Conduza uma investigação de nível {difficulty} sobre um mistério relacionado à história da Academia Tokugawa."
            ),
            "debate": (
                f"Debate Filosófico Nível {difficulty}",
                f"Participe de um debate filosófico de nível {difficulty} sobre um tema controverso e defenda a posição do {club_name}."
            ),
            "strategy": (
                f"Planejamento Estratégico Nível {difficulty}",
                f"Desenvolva um plano estratégico de nível {difficulty} para melhorar a posição do {club_name} na hierarquia da academia."
            ),
            "leadership": (
                f"Projeto de Liderança Nível {difficulty}",
                f"Lidere um projeto de nível {difficulty} envolvendo membros juniores do {club_name} para demonstrar suas habilidades de liderança."
            ),
            "harmony": (
                f"Ritual de Harmonia Nível {difficulty}",
                f"Participe de um ritual de harmonia de nível {difficulty} para equilibrar as energias elementais dentro do {club_name}."
            ),
            "general": (
                f"Missão do {club_name} Nível {difficulty}",
                f"Complete uma tarefa de nível {difficulty} designada por {leader_name} para o benefício do {club_name}."
            )
        }
        
        return templates.get(mission_type, templates["general"])
        
    def complete_mission(self, player_data: Dict[str, Any], mission_id: str) -> Dict[str, Any]:
        """
        Complete a pending mission.
        
        Args:
            player_data: Player data dictionary
            mission_id: ID of the mission to complete
            
        Returns:
            Dictionary with completion results
        """
        self.initialize_player_club_data(player_data)
        
        if player_data["club"]["id"] is None:
            return {"error": "Player is not in a club"}
            
        # Find the mission in pending missions
        mission = None
        for i, m in enumerate(player_data["club"]["pending_missions"]):
            if m["id"] == mission_id:
                mission = m
                player_data["club"]["pending_missions"].pop(i)
                break
                
        if not mission:
            return {"error": f"Mission {mission_id} not found in pending missions"}
            
        # Mark as completed
        mission["status"] = "completed"
        mission["completed_date"] = datetime.now().isoformat()
        
        # Add to completed missions
        player_data["club"]["completed_missions"].append(mission)
        player_data["club"]["missions_completed"] += 1
        
        # Award experience
        rank_result = self.add_club_experience(player_data, mission["experience_reward"])
        
        # Generate a new mission to replace the completed one
        new_mission = self.generate_new_mission(player_data)
        
        return {
            "mission_completed": mission,
            "experience_gained": mission["experience_reward"],
            "rank_result": rank_result,
            "new_mission": new_mission
        }
        
    def create_club_competition(self, player_data: Dict[str, Any], opponent_club_id: int) -> Dict[str, Any]:
        """
        Create a competition between the player's club and another club.
        
        Args:
            player_data: Player data dictionary
            opponent_club_id: ID of the opponent club
            
        Returns:
            Dictionary with competition details
        """
        self.initialize_player_club_data(player_data)
        
        club_id = player_data["club"]["id"]
        if club_id is None:
            return {"error": "Player is not in a club"}
            
        if opponent_club_id not in self.CLUBS:
            return {"error": f"Invalid opponent club ID: {opponent_club_id}"}
            
        if club_id == opponent_club_id:
            return {"error": "Cannot compete against your own club"}
            
        # Check if player rank is high enough to organize competitions
        if player_data["club"]["rank"] < 3:
            return {"error": "You must be at least rank 3 (Membro) to organize club competitions"}
            
        # Generate competition ID
        competition_id = f"comp_{club_id}_{opponent_club_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Determine competition type based on clubs involved
        competition_type = self._determine_competition_type(club_id, opponent_club_id)
        
        # Create competition
        competition = {
            "id": competition_id,
            "type": competition_type["type"],
            "title": competition_type["title"],
            "description": competition_type["description"],
            "host_club_id": club_id,
            "opponent_club_id": opponent_club_id,
            "date": (datetime.now() + timedelta(days=3)).isoformat(),
            "status": "scheduled",
            "result": None
        }
        
        # Add to competition history
        if "competition_history" not in player_data["club"]:
            player_data["club"]["competition_history"] = []
            
        player_data["club"]["competition_history"].append(competition)
        
        # Update rivalry
        if str(opponent_club_id) not in player_data["club"]["rivalries"]:
            player_data["club"]["rivalries"][str(opponent_club_id)] = 0
            
        player_data["club"]["rivalries"][str(opponent_club_id)] += 5
        
        return competition
        
    def _determine_competition_type(self, host_club_id: int, opponent_club_id: int) -> Dict[str, str]:
        """
        Determine the type of competition based on the clubs involved.
        
        Args:
            host_club_id: ID of the host club
            opponent_club_id: ID of the opponent club
            
        Returns:
            Dictionary with competition type, title, and description
        """
        # Competition types by club pairs
        competition_types = {
            # Flames vs Mental
            (1, 2): {
                "type": "debate",
                "title": "Debate: Poder vs Controle",
                "description": "Um debate acalorado sobre a importância relativa do poder bruto versus controle mental."
            },
            # Flames vs Political
            (1, 3): {
                "type": "leadership",
                "title": "Desafio de Liderança",
                "description": "Uma competição para demonstrar diferentes estilos de liderança e sua eficácia."
            },
            # Flames vs Elemental
            (1, 4): {
                "type": "elemental_control",
                "title": "Controle Elemental: Fogo vs Todos",
                "description": "Uma demonstração de controle elemental, com foco no poder do fogo contra outros elementos."
            },
            # Flames vs Combat
            (1, 5): {
                "type": "tournament",
                "title": "Torneio de Combate Intenso",
                "description": "Um torneio de combate focado em poder e intensidade."
            },
            # Mental vs Political
            (2, 3): {
                "type": "strategy",
                "title": "Jogo de Estratégia Mental",
                "description": "Uma competição de estratégia e manipulação mental para influenciar resultados."
            },
            # Mental vs Elemental
            (2, 4): {
                "type": "harmony",
                "title": "Harmonia Mental-Elemental",
                "description": "Uma demonstração de como a mente pode harmonizar-se com os elementos."
            },
            # Mental vs Combat
            (2, 5): {
                "type": "controlled_combat",
                "title": "Combate Controlado",
                "description": "Uma competição de combate onde a estratégia e controle mental são tão importantes quanto a força."
            },
            # Political vs Elemental
            (3, 4): {
                "type": "negotiation",
                "title": "Negociação de Recursos",
                "description": "Uma simulação de negociação para controle de recursos elementais."
            },
            # Political vs Combat
            (3, 5): {
                "type": "war_games",
                "title": "Jogos de Guerra",
                "description": "Uma simulação de conflito em grande escala, testando estratégia e força."
            },
            # Elemental vs Combat
            (4, 5): {
                "type": "elemental_combat",
                "title": "Combate Elemental",
                "description": "Uma competição combinando técnicas de combate com controle elemental."
            }
        }
        
        # Check for direct match
        if (host_club_id, opponent_club_id) in competition_types:
            return competition_types[(host_club_id, opponent_club_id)]
            
        # Check for reverse match
        if (opponent_club_id, host_club_id) in competition_types:
            comp_type = competition_types[(opponent_club_id, host_club_id)].copy()
            # Adjust title to reflect reversed roles
            comp_type["title"] = comp_type["title"].replace("vs", "contra")
            return comp_type
            
        # Default competition type
        return {
            "type": "general",
            "title": f"Competição: {self.CLUBS.get(host_club_id)} vs {self.CLUBS.get(opponent_club_id)}",
            "description": f"Uma competição amistosa entre {self.CLUBS.get(host_club_id)} e {self.CLUBS.get(opponent_club_id)}."
        }
        
    def resolve_competition(self, player_data: Dict[str, Any], competition_id: str, win: bool = None) -> Dict[str, Any]:
        """
        Resolve a scheduled competition.
        
        Args:
            player_data: Player data dictionary
            competition_id: ID of the competition to resolve
            win: If True, player's club wins; if False, opponent wins; if None, random outcome
            
        Returns:
            Dictionary with resolution results
        """
        self.initialize_player_club_data(player_data)
        
        if player_data["club"]["id"] is None:
            return {"error": "Player is not in a club"}
            
        # Find the competition
        competition = None
        for i, c in enumerate(player_data["club"]["competition_history"]):
            if c["id"] == competition_id:
                competition = c
                break
                
        if not competition:
            return {"error": f"Competition {competition_id} not found"}
            
        if competition["status"] != "scheduled":
            return {"error": f"Competition {competition_id} is already {competition['status']}"}
            
        # Determine outcome if not specified
        if win is None:
            # Random outcome with slight advantage to higher-ranked players
            player_advantage = min(player_data["club"]["rank"] * 5, 30)  # 5-30% advantage based on rank
            win = random.randint(1, 100) <= (50 + player_advantage)
            
        # Update competition status
        competition["status"] = "completed"
        competition["completed_date"] = datetime.now().isoformat()
        
        host_club_id = competition["host_club_id"]
        opponent_club_id = competition["opponent_club_id"]
        
        # Set result
        if win:
            competition["result"] = "victory"
            player_data["club"]["competitions_won"] += 1
            
            # Award experience
            experience_reward = 100
            rank_result = self.add_club_experience(player_data, experience_reward)
            
            # Update rivalry/alliance
            if str(opponent_club_id) in player_data["club"]["rivalries"]:
                player_data["club"]["rivalries"][str(opponent_club_id)] += 10
            elif str(opponent_club_id) in player_data["club"]["alliances"]:
                player_data["club"]["alliances"][str(opponent_club_id)] += 5
                
            # Update leader affinity
            if self.consequences_system:
                self.consequences_system.update_faction_reputation(
                    player_data, 
                    self.CLUB_LEADERS.get(host_club_id), 
                    10
                )
                self.consequences_system.update_faction_reputation(
                    player_data, 
                    self.CLUB_LEADERS.get(opponent_club_id), 
                    -5
                )
                
            result = {
                "outcome": "victory",
                "experience_gained": experience_reward,
                "rank_result": rank_result,
                "message": f"Parabéns! {self.CLUBS.get(host_club_id)} venceu a competição contra {self.CLUBS.get(opponent_club_id)}!"
            }
        else:
            competition["result"] = "defeat"
            
            # Award consolation experience
            experience_reward = 30
            rank_result = self.add_club_experience(player_data, experience_reward)
            
            # Update rivalry/alliance
            if str(opponent_club_id) in player_data["club"]["rivalries"]:
                player_data["club"]["rivalries"][str(opponent_club_id)] += 15
            elif str(opponent_club_id) in player_data["club"]["alliances"]:
                player_data["club"]["alliances"][str(opponent_club_id)] -= 5
                
            # Update leader affinity
            if self.consequences_system:
                self.consequences_system.update_faction_reputation(
                    player_data, 
                    self.CLUB_LEADERS.get(host_club_id), 
                    -5
                )
                
            result = {
                "outcome": "defeat",
                "experience_gained": experience_reward,
                "rank_result": rank_result,
                "message": f"{self.CLUBS.get(host_club_id)} foi derrotado por {self.CLUBS.get(opponent_club_id)} na competição. Continue treinando!"
            }
            
        return result
        
    def form_alliance(self, player_data: Dict[str, Any], ally_club_id: int) -> Dict[str, Any]:
        """
        Form or strengthen an alliance with another club.
        
        Args:
            player_data: Player data dictionary
            ally_club_id: ID of the club to ally with
            
        Returns:
            Dictionary with alliance results
        """
        self.initialize_player_club_data(player_data)
        
        club_id = player_data["club"]["id"]
        if club_id is None:
            return {"error": "Player is not in a club"}
            
        if ally_club_id not in self.CLUBS:
            return {"error": f"Invalid ally club ID: {ally_club_id}"}
            
        if club_id == ally_club_id:
            return {"error": "Cannot form an alliance with your own club"}
            
        # Check if player rank is high enough
        if player_data["club"]["rank"] < 4:
            return {"error": "You must be at least rank 4 (Membro Avançado) to form alliances"}
            
        # Check if there's a strong rivalry
        if str(ally_club_id) in player_data["club"]["rivalries"] and player_data["club"]["rivalries"][str(ally_club_id)] > 20:
            return {"error": f"The rivalry with {self.CLUBS.get(ally_club_id)} is too strong to form an alliance"}
            
        # Remove from rivalries if present
        if str(ally_club_id) in player_data["club"]["rivalries"]:
            del player_data["club"]["rivalries"][str(ally_club_id)]
            
        # Add or strengthen alliance
        if str(ally_club_id) not in player_data["club"]["alliances"]:
            player_data["club"]["alliances"][str(ally_club_id)] = 10
            is_new = True
        else:
            player_data["club"]["alliances"][str(ally_club_id)] += 10
            is_new = False
            
        # Update leader affinity
        if self.consequences_system:
            self.consequences_system.update_faction_reputation(
                player_data, 
                self.CLUB_LEADERS.get(ally_club_id), 
                15
            )
            
        return {
            "club_id": ally_club_id,
            "club_name": self.CLUBS.get(ally_club_id),
            "alliance_strength": player_data["club"]["alliances"][str(ally_club_id)],
            "is_new": is_new,
            "message": f"{'Formada nova aliança' if is_new else 'Fortalecida a aliança'} com {self.CLUBS.get(ally_club_id)}!"
        }
        
    def declare_rivalry(self, player_data: Dict[str, Any], rival_club_id: int) -> Dict[str, Any]:
        """
        Declare or intensify a rivalry with another club.
        
        Args:
            player_data: Player data dictionary
            rival_club_id: ID of the club to rival with
            
        Returns:
            Dictionary with rivalry results
        """
        self.initialize_player_club_data(player_data)
        
        club_id = player_data["club"]["id"]
        if club_id is None:
            return {"error": "Player is not in a club"}
            
        if rival_club_id not in self.CLUBS:
            return {"error": f"Invalid rival club ID: {rival_club_id}"}
            
        if club_id == rival_club_id:
            return {"error": "Cannot declare rivalry with your own club"}
            
        # Check if player rank is high enough
        if player_data["club"]["rank"] < 4:
            return {"error": "You must be at least rank 4 (Membro Avançado) to declare rivalries"}
            
        # Remove from alliances if present
        if str(rival_club_id) in player_data["club"]["alliances"]:
            del player_data["club"]["alliances"][str(rival_club_id)]
            
        # Add or intensify rivalry
        if str(rival_club_id) not in player_data["club"]["rivalries"]:
            player_data["club"]["rivalries"][str(rival_club_id)] = 15
            is_new = True
        else:
            player_data["club"]["rivalries"][str(rival_club_id)] += 15
            is_new = False
            
        # Update leader affinity
        if self.consequences_system:
            self.consequences_system.update_faction_reputation(
                player_data, 
                self.CLUB_LEADERS.get(rival_club_id), 
                -20
            )
            
        return {
            "club_id": rival_club_id,
            "club_name": self.CLUBS.get(rival_club_id),
            "rivalry_intensity": player_data["club"]["rivalries"][str(rival_club_id)],
            "is_new": is_new,
            "message": f"{'Declarada nova rivalidade' if is_new else 'Intensificada a rivalidade'} com {self.CLUBS.get(rival_club_id)}!"
        }

# Singleton instance
_club_system = None

def get_club_system(consequences_system=None):
    """
    Get the singleton instance of the ClubSystem.
    
    Args:
        consequences_system: Optional reference to the consequences system
        
    Returns:
        ClubSystem instance
    """
    global _club_system
    if _club_system is None:
        _club_system = ClubSystem(consequences_system)
    return _club_system