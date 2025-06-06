from typing import Dict, List, Any, Optional, Union, Tuple
import json
import logging
import random
from .npc import BaseNPC, NPCManager

logger = logging.getLogger('tokugawa_bot')

class RelationshipStatus:
    """
    Enum-like class for relationship statuses.
    """
    HOSTILE = "hostile"
    UNFRIENDLY = "unfriendly"
    NEUTRAL = "neutral"
    FRIENDLY = "friendly"
    CLOSE = "close"
    TRUSTED = "trusted"
    ROMANTIC_INTEREST = "romantic_interest"
    DATING = "dating"
    COMMITTED = "committed"

    @staticmethod
    def is_romantic(status: str) -> bool:
        """
        Checks if a relationship status is romantic.

        Args:
            status: Relationship status

        Returns:
            True if the status is romantic, False otherwise
        """
        return status in [
            RelationshipStatus.ROMANTIC_INTEREST,
            RelationshipStatus.DATING,
            RelationshipStatus.COMMITTED
        ]

    @staticmethod
    def get_next_romantic_level(current_status: str) -> Optional[str]:
        """
        Gets the next romantic level from the current status.

        Args:
            current_status: Current relationship status

        Returns:
            Next romantic level or None if already at highest level
        """
        romantic_progression = [
            RelationshipStatus.ROMANTIC_INTEREST,
            RelationshipStatus.DATING,
            RelationshipStatus.COMMITTED
        ]

        if current_status not in romantic_progression:
            return RelationshipStatus.ROMANTIC_INTEREST

        current_index = romantic_progression.index(current_status)
        if current_index < len(romantic_progression) - 1:
            return romantic_progression[current_index + 1]

        return None


class NPCRelationship:
    """
    Enhanced NPC relationship system that extends the existing NPC system.
    This class adds support for romantic relationships, relationship events,
    and more complex interactions.

    Following the Single Responsibility Principle, this class only handles
    relationship-related aspects of NPCs.
    """
    def __init__(self, npc_manager: NPCManager):
        """
        Initialize the NPC relationship system.

        Args:
            npc_manager: The NPC manager to use for NPC lookups
        """
        self.npc_manager = npc_manager
        self.relationship_events = {}
        self.romantic_dialogues = {}

        # Try to load relationship data from files
        self._load_relationship_data()

        logger.info("NPCRelationship initialized")

    def _load_relationship_data(self):
        """
        Loads relationship data from files.
        """
        try:
            # Load relationship events
            events_path = "data/story_mode/relationship_events.json"
            try:
                with open(events_path, 'r') as f:
                    self.relationship_events = json.load(f)
                logger.info(f"Loaded {len(self.relationship_events)} relationship events")
            except FileNotFoundError:
                logger.warning(f"Relationship events file not found: {events_path}")
                self._initialize_default_relationship_events()
                self._save_relationship_data()

            # Load romantic dialogues
            dialogues_path = "data/story_mode/romantic_dialogues.json"
            try:
                with open(dialogues_path, 'r') as f:
                    self.romantic_dialogues = json.load(f)
                logger.info(f"Loaded romantic dialogues for {len(self.romantic_dialogues)} NPCs")
            except FileNotFoundError:
                logger.warning(f"Romantic dialogues file not found: {dialogues_path}")
                self._initialize_default_romantic_dialogues()
                self._save_relationship_data()
        except Exception as e:
            logger.error(f"Error loading relationship data: {e}")
            self._initialize_default_relationship_events()
            self._initialize_default_romantic_dialogues()

    def _save_relationship_data(self):
        """
        Saves relationship data to files.
        """
        try:
            # Save relationship events
            events_path = "data/story_mode/relationship_events.json"
            with open(events_path, 'w') as f:
                json.dump(self.relationship_events, f, indent=2)
            logger.info(f"Saved {len(self.relationship_events)} relationship events")

            # Save romantic dialogues
            dialogues_path = "data/story_mode/romantic_dialogues.json"
            with open(dialogues_path, 'w') as f:
                json.dump(self.romantic_dialogues, f, indent=2)
            logger.info(f"Saved romantic dialogues for {len(self.romantic_dialogues)} NPCs")
        except Exception as e:
            logger.error(f"Error saving relationship data: {e}")

    def _initialize_default_relationship_events(self):
        """
        Initializes default relationship events.
        """
        self.relationship_events = {
            "friendly": [
                {
                    "name": "Estudo em Grupo",
                    "description": "Você e {npc_name} estudam juntos para uma prova difícil.",
                    "affinity_change": 5,
                    "attribute_bonus": {"intellect": 1}
                },
                {
                    "name": "Almoço Casual",
                    "description": "Você encontra {npc_name} no refeitório e vocês almoçam juntos.",
                    "affinity_change": 3,
                    "attribute_bonus": {"charisma": 1}
                },
                {
                    "name": "Treino Conjunto",
                    "description": "Você e {npc_name} treinam juntos no campo de prática.",
                    "affinity_change": 4,
                    "attribute_bonus": {"power_stat": 1}
                }
            ],
            "close": [
                {
                    "name": "Segredo Compartilhado",
                    "description": "{npc_name} compartilha um segredo pessoal com você, fortalecendo a confiança entre vocês.",
                    "affinity_change": 8,
                    "attribute_bonus": {"charisma": 2}
                },
                {
                    "name": "Exploração do Campus",
                    "description": "Você e {npc_name} exploram partes pouco conhecidas do campus juntos.",
                    "affinity_change": 7,
                    "attribute_bonus": {"intellect": 1, "dexterity": 1}
                },
                {
                    "name": "Ajuda em Momento Difícil",
                    "description": "Você ajuda {npc_name} durante um momento pessoal difícil.",
                    "affinity_change": 10,
                    "attribute_bonus": {"charisma": 2}
                }
            ],
            "romantic_interest": [
                {
                    "name": "Momento de Conexão",
                    "description": "Você e {npc_name} compartilham um momento especial que sugere algo além da amizade.",
                    "affinity_change": 10,
                    "attribute_bonus": {"charisma": 2}
                },
                {
                    "name": "Passeio ao Pôr do Sol",
                    "description": "Você convida {npc_name} para um passeio ao pôr do sol nos jardins da academia.",
                    "affinity_change": 12,
                    "attribute_bonus": {"charisma": 3}
                },
                {
                    "name": "Presente Especial",
                    "description": "Você dá um presente especial para {npc_name}, que fica visivelmente tocado(a).",
                    "affinity_change": 15,
                    "attribute_bonus": {"charisma": 2}
                }
            ],
            "dating": [
                {
                    "name": "Encontro Romântico",
                    "description": "Você e {npc_name} têm um encontro romântico na cidade próxima à academia.",
                    "affinity_change": 15,
                    "attribute_bonus": {"charisma": 3}
                },
                {
                    "name": "Treino Especial",
                    "description": "{npc_name} te ensina uma técnica especial que poucos conhecem.",
                    "affinity_change": 12,
                    "attribute_bonus": {"power_stat": 3}
                },
                {
                    "name": "Segredos da Academia",
                    "description": "Você e {npc_name} descobrem juntos um segredo antigo da academia.",
                    "affinity_change": 18,
                    "attribute_bonus": {"intellect": 2, "power_stat": 1}
                }
            ],
            "committed": [
                {
                    "name": "Promessa de Futuro",
                    "description": "Você e {npc_name} fazem planos para o futuro após a graduação.",
                    "affinity_change": 20,
                    "attribute_bonus": {"charisma": 3, "power_stat": 2}
                },
                {
                    "name": "Técnica Combinada",
                    "description": "Você e {npc_name} desenvolvem uma técnica que combina seus poderes de forma única.",
                    "affinity_change": 18,
                    "attribute_bonus": {"power_stat": 4}
                },
                {
                    "name": "Revelação Profunda",
                    "description": "{npc_name} revela seu segredo mais profundo, algo que nunca contou a ninguém.",
                    "affinity_change": 25,
                    "attribute_bonus": {"intellect": 3, "charisma": 2}
                }
            ]
        }

        logger.info("Initialized default relationship events")

    def _initialize_default_romantic_dialogues(self):
        """
        Initializes default romantic dialogues.
        """
        self.romantic_dialogues = {
            "kai_flameheart": {
                "romantic_interest": [
                    {"text": "Sabe, você é diferente dos outros estudantes. Há algo em você que... acende uma chama em mim."},
                    {"text": "Quando estou com você, sinto que posso baixar minha guarda. É raro eu me sentir assim com alguém."}
                ],
                "dating": [
                    {"text": "Ainda me surpreendo com o quanto você se tornou importante para mim. É como se você fosse o combustível para minha chama."},
                    {"text": "Nunca pensei que encontraria alguém que entendesse tanto minha paixão e intensidade."}
                ],
                "committed": [
                    {"text": "Você é a única pessoa que viu através das minhas chamas e encontrou quem eu realmente sou. Isso significa tudo para mim."},
                    {"text": "Juntos, nossa chama nunca se apagará. Não importa o que o futuro reserve, enfrentaremos juntos."}
                ]
            },
            "luna_mindweaver": {
                "romantic_interest": [
                    {"text": "É estranho... geralmente leio os pensamentos das pessoas com facilidade, mas com você, quero descobrir naturalmente."},
                    {"text": "Sua mente tem um padrão único, sabia? É como uma bela constelação que não consigo parar de admirar."}
                ],
                "dating": [
                    {"text": "Pela primeira vez, não me sinto sozinha em meus pensamentos. É como se você criasse um espaço seguro na minha mente."},
                    {"text": "Nunca pensei que permitiria alguém tão perto dos meus pensamentos mais íntimos. Você mudou isso."}
                ],
                "committed": [
                    {"text": "Nossas mentes estão conectadas de uma forma que transcende a telepatia. É como se fôssemos parte de uma consciência maior quando estamos juntos."},
                    {"text": "Você é o único que vê além das ilusões, direto para minha verdadeira essência. E ainda assim, escolhe ficar."}
                ]
            },
            "alexander_strategos": {
                "romantic_interest": [
                    {"text": "Você sabe que não tomo decisões sem calcular todas as variáveis, certo? E ainda assim, com você, me pego agindo por impulso às vezes."},
                    {"text": "Em meu tabuleiro mental, você se tornou uma peça que não consigo prever. É... intrigante."}
                ],
                "dating": [
                    {"text": "Nunca incluí 'relacionamento' em meus planos estratégicos para a academia. Você é a variável que mudou toda a equação."},
                    {"text": "Meu pai diria que sentimentos são uma fraqueza. Mas com você, descobri que podem ser uma força extraordinária."}
                ],
                "committed": [
                    {"text": "Analisei todas as possibilidades, e em cada cenário futuro que visualizo, você está lá. É a única constante que desejo manter."},
                    {"text": "Juntos, não há jogo político que não possamos vencer, não há desafio que não possamos superar. Somos a aliança perfeita."}
                ]
            },
            "gaia_naturae": {
                "romantic_interest": [
                    {"text": "Os espíritos elementais sussurram quando você está por perto. Eles sentem a mesma conexão que eu sinto."},
                    {"text": "Sua energia tem um equilíbrio raro. É como um ecossistema perfeitamente harmonizado."}
                ],
                "dating": [
                    {"text": "Na minha comunidade, acreditamos que algumas almas são entrelaçadas como raízes de árvores antigas. Talvez as nossas sejam assim."},
                    {"text": "Você me ajuda a encontrar equilíbrio entre minhas tradições e este novo mundo. É como se fosse a ponte que eu precisava."}
                ],
                "committed": [
                    {"text": "Os antigos dizem que quando dois espíritos verdadeiramente se conectam, os próprios elementos celebram. Agora entendo o que isso significa."},
                    {"text": "Com você, encontrei um lar longe de casa. Um lugar onde posso ser completamente eu mesma, conectada a todas as minhas raízes."}
                ]
            },
            "ryuji_battleborn": {
                "romantic_interest": [
                    {"text": "Um guerreiro deve manter o foco na batalha, mas você... você tem sido uma distração que não consigo ignorar."},
                    {"text": "Sua força não está apenas em seus poderes, mas em seu espírito. É algo que admiro profundamente."}
                ],
                "dating": [
                    {"text": "Em minha família, nos ensinam que mostrar emoção é fraqueza. Com você, estou aprendendo que é preciso força para ser vulnerável."},
                    {"text": "Lutamos lado a lado, mas também lutamos um pelo outro. Isso nos torna mais fortes do que qualquer guerreiro solitário."}
                ],
                "committed": [
                    {"text": "Meus ancestrais falavam de guerreiros que encontravam sua outra metade em batalha. Agora entendo que não era apenas uma lenda."},
                    {"text": "Jurei lealdade apenas à minha família e ao código do guerreiro. Agora, minha lealdade também pertence a você, para sempre."}
                ]
            }
        }

        logger.info("Initialized default romantic dialogues")

    def get_relationship_status(self, player_data: Dict[str, Any], npc_name: str) -> str:
        """
        Gets the relationship status between the player and an NPC.

        Args:
            player_data: Player data
            npc_name: Name of the NPC

        Returns:
            Relationship status
        """
        # Get the NPC
        npc = self.npc_manager.get_npc_by_name(npc_name)
        if not npc:
            logger.warning(f"NPC not found: {npc_name}")
            return RelationshipStatus.NEUTRAL

        # Get the affinity level
        affinity_level = npc.get_affinity_level(player_data)

        # Check if there's a romantic relationship
        story_progress = player_data.get("story_progress", {})
        romantic_relationships = story_progress.get("romantic_relationships", {})

        if npc_name in romantic_relationships:
            return romantic_relationships[npc_name]

        return affinity_level

    def update_relationship_status(self, player_data: Dict[str, Any], npc_name: str, new_status: str) -> Dict[str, Any]:
        """
        Updates the relationship status between the player and an NPC.

        Args:
            player_data: Player data
            npc_name: Name of the NPC
            new_status: New relationship status

        Returns:
            Updated player data
        """
        # Get the NPC
        npc = self.npc_manager.get_npc_by_name(npc_name)
        if not npc:
            logger.warning(f"NPC not found: {npc_name}")
            return player_data

        # Update the relationship status
        story_progress = player_data.get("story_progress", {})
        romantic_relationships = story_progress.get("romantic_relationships", {})

        # Log the change
        old_status = romantic_relationships.get(npc_name, npc.get_affinity_level(player_data))
        logger.info(f"Updating relationship status with {npc_name}: {old_status} -> {new_status}")

        # Update the status
        romantic_relationships[npc_name] = new_status
        story_progress["romantic_relationships"] = romantic_relationships
        player_data["story_progress"] = story_progress

        return player_data

    def can_romance(self, player_data: Dict[str, Any], npc_name: str) -> bool:
        """
        Checks if an NPC can be romanced by the player.

        Args:
            player_data: Player data
            npc_name: Name of the NPC

        Returns:
            True if the NPC can be romanced, False otherwise
        """
        # Get the NPC
        npc = self.npc_manager.get_npc_by_name(npc_name)
        if not npc:
            logger.warning(f"NPC not found: {npc_name}")
            return False

        # Check if the NPC has romantic dialogues
        npc_id = getattr(npc, "npc_id", "")
        if npc_id not in self.romantic_dialogues:
            return False

        # Check if the affinity is high enough
        affinity_level = npc.get_affinity_level(player_data)
        return affinity_level in [RelationshipStatus.CLOSE, RelationshipStatus.TRUSTED]

    def get_romantic_dialogue(self, player_data: Dict[str, Any], npc_name: str) -> Optional[str]:
        """
        Gets a romantic dialogue for an NPC based on the current relationship status.

        Args:
            player_data: Player data
            npc_name: Name of the NPC

        Returns:
            Romantic dialogue or None if not available
        """
        # Get the NPC
        npc = self.npc_manager.get_npc_by_name(npc_name)
        if not npc:
            logger.warning(f"NPC not found: {npc_name}")
            return None

        # Get the relationship status
        status = self.get_relationship_status(player_data, npc_name)

        # Check if the status is romantic
        if not RelationshipStatus.is_romantic(status):
            return None

        # Get the romantic dialogues for this NPC
        npc_id = getattr(npc, "npc_id", "")
        if npc_id not in self.romantic_dialogues:
            return None

        # Get the dialogues for this status
        dialogues = self.romantic_dialogues[npc_id].get(status, [])
        if not dialogues:
            return None

        # Return a random dialogue
        return random.choice(dialogues)["text"]

    def get_available_relationship_events(self, player_data: Dict[str, Any], npc_name: str) -> List[Dict[str, Any]]:
        """
        Gets available relationship events for an NPC based on the current relationship status.

        Args:
            player_data: Player data
            npc_name: Name of the NPC

        Returns:
            List of available relationship events
        """
        # Get the relationship status
        status = self.get_relationship_status(player_data, npc_name)

        # Get events for this status
        events = self.relationship_events.get(status, [])

        # Format the events with the NPC name
        formatted_events = []
        for event in events:
            formatted_event = event.copy()
            formatted_event["description"] = formatted_event["description"].format(npc_name=npc_name)
            formatted_events.append(formatted_event)

        return formatted_events

    def trigger_relationship_event(self, player_data: Dict[str, Any], npc_name: str, event_name: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Triggers a relationship event between the player and an NPC.

        Args:
            player_data: Player data
            npc_name: Name of the NPC
            event_name: Name of the event

        Returns:
            Tuple of (updated player data, event result)
        """
        # Get the relationship status
        status = self.get_relationship_status(player_data, npc_name)

        # Get events for this status
        events = self.relationship_events.get(status, [])

        # Find the event
        event = None
        for e in events:
            if e["name"] == event_name:
                event = e
                break

        if not event:
            logger.warning(f"Event not found: {event_name} for status {status}")
            return player_data, {"error": f"Event not found: {event_name}"}

        # Format the event description
        event_result = event.copy()
        event_result["description"] = event_result["description"].format(npc_name=npc_name)

        # Update affinity
        affinity_change = event.get("affinity_change", 0)
        if affinity_change != 0:
            # Get the NPC
            npc = self.npc_manager.get_npc_by_name(npc_name)
            if npc:
                player_data = npc.update_affinity(player_data, affinity_change)
            else:
                logger.warning(f"NPC not found: {npc_name}, using NPCManager.update_affinity")
                player_data = self.npc_manager.update_affinity(player_data, npc_name, affinity_change)

        # Check if the relationship should progress to the next level
        new_affinity = 0
        npc = self.npc_manager.get_npc_by_name(npc_name)
        if npc:
            new_affinity = npc.get_affinity(player_data)

        # Check for relationship progression
        current_status = self.get_relationship_status(player_data, npc_name)

        # If at trusted level and not already in a romantic relationship, check for romance
        if current_status == RelationshipStatus.TRUSTED and not RelationshipStatus.is_romantic(current_status):
            if self.can_romance(player_data, npc_name) and random.random() < 0.3:  # 30% chance
                player_data = self.update_relationship_status(player_data, npc_name, RelationshipStatus.ROMANTIC_INTEREST)
                event_result["relationship_change"] = f"Seu relacionamento com {npc_name} evoluiu para interesse romântico!"

        # If already in a romantic relationship, check for progression
        elif RelationshipStatus.is_romantic(current_status):
            # Higher affinity increases chance of progression
            progression_chance = 0.1 + (new_affinity / 1000)  # Max 20% chance at 100 affinity
            if random.random() < progression_chance:
                next_level = RelationshipStatus.get_next_romantic_level(current_status)
                if next_level:
                    player_data = self.update_relationship_status(player_data, npc_name, next_level)
                    event_result["relationship_change"] = f"Seu relacionamento com {npc_name} evoluiu para {next_level}!"

        # Add the event to the player's history
        story_progress = player_data.get("story_progress", {})
        relationship_events = story_progress.get("relationship_events", [])
        relationship_events.append({
            "npc": npc_name,
            "event": event_name,
            "date": "current_date"  # This would be replaced with the actual date in a real implementation
        })
        story_progress["relationship_events"] = relationship_events
        player_data["story_progress"] = story_progress

        return player_data, event_result

    def get_relationship_benefits(self, player_data: Dict[str, Any], npc_name: str) -> Dict[str, Any]:
        """
        Gets the benefits of a relationship with an NPC.

        Args:
            player_data: Player data
            npc_name: Name of the NPC

        Returns:
            Dict of relationship benefits
        """
        # Get the relationship status
        status = self.get_relationship_status(player_data, npc_name)

        # Initialize default benefits
        benefits = {
            "attribute_bonus": {},
            "special_abilities": [],
            "description": ""
        }

        # Get the NPC
        npc = self.npc_manager.get_npc_by_name(npc_name)
        if not npc:
            logger.warning(f"NPC not found: {npc_name}")
            return benefits

        # Get NPC attributes
        npc_power = getattr(npc, "power", "Unknown")
        npc_club_id = getattr(npc, "club_id", None)

        # Load relationship benefits from JSON file
        try:
            benefits_path = "data/story_mode/relationship_benefits.json"
            with open(benefits_path, 'r') as f:
                all_benefits = json.load(f)

            # Get benefits for the current status
            if status in all_benefits:
                status_benefits = all_benefits[status]

                # Format the description with the NPC name
                benefits["description"] = status_benefits["description"].format(npc_name=npc_name)

                # Copy attribute bonuses
                benefits["attribute_bonus"] = status_benefits["attribute_bonus"]

                # Format special abilities with NPC attributes
                for ability in status_benefits["special_abilities"]:
                    formatted_ability = ability.format(npc_name=npc_name, npc_power=npc_power)
                    benefits["special_abilities"].append(formatted_ability)

                logger.debug(f"Loaded relationship benefits for {npc_name} with status {status}")
            else:
                logger.warning(f"No benefits found for status: {status}")
        except Exception as e:
            logger.error(f"Error loading relationship benefits from JSON file: {e}")
            # Fallback to hardcoded benefits
            if status == RelationshipStatus.FRIENDLY:
                benefits["description"] = f"Como amigo de {npc_name}, você recebe dicas ocasionais e pequenos bônus."
                benefits["attribute_bonus"] = {"charisma": 1}

            elif status == RelationshipStatus.CLOSE:
                benefits["description"] = f"{npc_name} compartilha conhecimentos especiais com você, melhorando suas habilidades."
                benefits["attribute_bonus"] = {"charisma": 1, "intellect": 1}
                benefits["special_abilities"].append(f"Acesso a áreas exclusivas do clube de {npc_name}")

            elif status == RelationshipStatus.TRUSTED:
                benefits["description"] = f"A confiança profunda entre você e {npc_name} traz benefícios significativos."
                benefits["attribute_bonus"] = {"charisma": 2, "intellect": 1}
                benefits["special_abilities"].append(f"Treinamento especial com {npc_name}")
                benefits["special_abilities"].append(f"Informações privilegiadas sobre eventos da academia")

            elif status == RelationshipStatus.ROMANTIC_INTEREST:
                benefits["description"] = f"Seu interesse romântico em {npc_name} te motiva a se esforçar mais."
                benefits["attribute_bonus"] = {"charisma": 2, "power_stat": 1}
                benefits["special_abilities"].append(f"Inspiração: +10% de XP em atividades relacionadas a {npc_power}")

            elif status == RelationshipStatus.DATING:
                benefits["description"] = f"Seu relacionamento com {npc_name} traz força e motivação extras."
                benefits["attribute_bonus"] = {"charisma": 2, "power_stat": 2}
                benefits["special_abilities"].append(f"Técnica Compartilhada: Acesso a uma habilidade especial de {npc_name}")
                benefits["special_abilities"].append(f"Apoio Emocional: Recuperação mais rápida de energia")

            elif status == RelationshipStatus.COMMITTED:
                benefits["description"] = f"Seu compromisso com {npc_name} cria uma sinergia poderosa entre vocês."
                benefits["attribute_bonus"] = {"charisma": 3, "power_stat": 2, "intellect": 1}
                benefits["special_abilities"].append(f"Técnica Combinada: Habilidade especial que combina seus poderes")
                benefits["special_abilities"].append(f"Vínculo Profundo: Bônus em todas as atividades quando {npc_name} está presente")
                benefits["special_abilities"].append(f"Segredos Compartilhados: Acesso a conhecimentos exclusivos de {npc_name}")

            logger.warning("Using hardcoded relationship benefits")

        return benefits
