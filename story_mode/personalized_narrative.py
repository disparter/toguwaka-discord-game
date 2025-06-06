from typing import Dict, List, Any, Optional, Union
import json
import logging
import os
import random
from .interfaces import Chapter, Event, NPC

logger = logging.getLogger('tokugawa_bot')

class PersonalizedNarrative:
    """
    Generates personalized narrative content based on player attributes.
    This class is responsible for creating choices, dialogues, and outcomes
    that are tailored to the player's origin, power, club, and other attributes.
    
    Following the Single Responsibility Principle, this class only handles
    the personalization of narrative content.
    """
    def __init__(self):
        """
        Initialize the personalized narrative generator.
        """
        # Load narrative templates
        self.choice_templates = {}
        self.dialogue_templates = {}
        self.outcome_templates = {}
        
        # Try to load templates from files
        self._load_templates()
        
        logger.info("PersonalizedNarrative initialized")
    
    def _load_templates(self):
        """
        Loads narrative templates from files.
        """
        templates_dir = os.path.join("data", "story_mode", "narrative_templates")
        
        # Create directory if it doesn't exist
        os.makedirs(templates_dir, exist_ok=True)
        
        # Try to load choice templates
        choices_path = os.path.join(templates_dir, "choices.json")
        if os.path.exists(choices_path):
            try:
                with open(choices_path, 'r') as f:
                    self.choice_templates = json.load(f)
                logger.info(f"Loaded {len(self.choice_templates)} choice templates")
            except Exception as e:
                logger.error(f"Error loading choice templates: {e}")
                # Initialize with default templates
                self._initialize_default_choice_templates()
        else:
            # Initialize with default templates
            self._initialize_default_choice_templates()
            # Save default templates to file
            self._save_templates()
        
        # Try to load dialogue templates
        dialogues_path = os.path.join(templates_dir, "dialogues.json")
        if os.path.exists(dialogues_path):
            try:
                with open(dialogues_path, 'r') as f:
                    self.dialogue_templates = json.load(f)
                logger.info(f"Loaded {len(self.dialogue_templates)} dialogue templates")
            except Exception as e:
                logger.error(f"Error loading dialogue templates: {e}")
                # Initialize with default templates
                self._initialize_default_dialogue_templates()
        else:
            # Initialize with default templates
            self._initialize_default_dialogue_templates()
            # Save default templates to file
            self._save_templates()
        
        # Try to load outcome templates
        outcomes_path = os.path.join(templates_dir, "outcomes.json")
        if os.path.exists(outcomes_path):
            try:
                with open(outcomes_path, 'r') as f:
                    self.outcome_templates = json.load(f)
                logger.info(f"Loaded {len(self.outcome_templates)} outcome templates")
            except Exception as e:
                logger.error(f"Error loading outcome templates: {e}")
                # Initialize with default templates
                self._initialize_default_outcome_templates()
        else:
            # Initialize with default templates
            self._initialize_default_outcome_templates()
            # Save default templates to file
            self._save_templates()
    
    def _save_templates(self):
        """
        Saves narrative templates to files.
        """
        templates_dir = os.path.join("data", "story_mode", "narrative_templates")
        
        # Create directory if it doesn't exist
        os.makedirs(templates_dir, exist_ok=True)
        
        # Save choice templates
        choices_path = os.path.join(templates_dir, "choices.json")
        try:
            with open(choices_path, 'w') as f:
                json.dump(self.choice_templates, f, indent=2)
            logger.info(f"Saved {len(self.choice_templates)} choice templates")
        except Exception as e:
            logger.error(f"Error saving choice templates: {e}")
        
        # Save dialogue templates
        dialogues_path = os.path.join(templates_dir, "dialogues.json")
        try:
            with open(dialogues_path, 'w') as f:
                json.dump(self.dialogue_templates, f, indent=2)
            logger.info(f"Saved {len(self.dialogue_templates)} dialogue templates")
        except Exception as e:
            logger.error(f"Error saving dialogue templates: {e}")
        
        # Save outcome templates
        outcomes_path = os.path.join(templates_dir, "outcomes.json")
        try:
            with open(outcomes_path, 'w') as f:
                json.dump(self.outcome_templates, f, indent=2)
            logger.info(f"Saved {len(self.outcome_templates)} outcome templates")
        except Exception as e:
            logger.error(f"Error saving outcome templates: {e}")
    
    def _initialize_default_choice_templates(self):
        """
        Initializes default choice templates.
        """
        self.choice_templates = {
            "origin": {
                "Bairro Popular": [
                    {"text": "Usar sua experiência de rua para encontrar uma solução alternativa.", "attribute_bonus": {"charisma": 1}},
                    {"text": "Defender um colega excluído pela elite escolar.", "attribute_bonus": {"charisma": 2}},
                    {"text": "Mostrar que sua origem humilde não define suas capacidades.", "attribute_bonus": {"power_stat": 1}}
                ],
                "Família de Elite": [
                    {"text": "Usar seus contatos para obter informações privilegiadas.", "attribute_bonus": {"intellect": 1}},
                    {"text": "Mostrar que nem todos da elite são arrogantes e distantes.", "attribute_bonus": {"charisma": 1}},
                    {"text": "Aproveitar sua educação privilegiada para resolver o problema.", "attribute_bonus": {"intellect": 2}}
                ],
                "Órfão": [
                    {"text": "Usar sua independência e resiliência para superar o desafio.", "attribute_bonus": {"power_stat": 2}},
                    {"text": "Mostrar que você não precisa de família para ser forte.", "attribute_bonus": {"power_stat": 1, "charisma": 1}},
                    {"text": "Formar laços com outros que entendem sua situação.", "attribute_bonus": {"charisma": 2}}
                ],
                "Transferido": [
                    {"text": "Usar sua perspectiva externa para ver o que os outros não veem.", "attribute_bonus": {"intellect": 2}},
                    {"text": "Compartilhar experiências de sua escola anterior.", "attribute_bonus": {"charisma": 1}},
                    {"text": "Mostrar que novatos também podem fazer a diferença.", "attribute_bonus": {"power_stat": 1, "charisma": 1}}
                ],
                "Comunidade Isolada": [
                    {"text": "Usar conhecimentos tradicionais que outros não possuem.", "attribute_bonus": {"intellect": 2}},
                    {"text": "Mostrar o valor de uma perspectiva diferente e única.", "attribute_bonus": {"charisma": 1, "intellect": 1}},
                    {"text": "Adaptar-se rapidamente para superar as diferenças culturais.", "attribute_bonus": {"charisma": 2}}
                ]
            },
            "power": {
                "Fogo": [
                    {"text": "Usar seu poder de fogo para intimidar.", "attribute_bonus": {"power_stat": 2}},
                    {"text": "Demonstrar controle preciso sobre as chamas.", "attribute_bonus": {"power_stat": 1, "intellect": 1}},
                    {"text": "Aquecer o ambiente para criar uma atmosfera acolhedora.", "attribute_bonus": {"charisma": 2}}
                ],
                "Água": [
                    {"text": "Adaptar-se como a água para encontrar uma solução.", "attribute_bonus": {"intellect": 2}},
                    {"text": "Usar a água para acalmar os ânimos exaltados.", "attribute_bonus": {"charisma": 2}},
                    {"text": "Demonstrar a força persistente da água.", "attribute_bonus": {"power_stat": 2}}
                ],
                "Terra": [
                    {"text": "Manter-se firme como a rocha diante da adversidade.", "attribute_bonus": {"power_stat": 2}},
                    {"text": "Usar sua conexão com a terra para sentir vibrações e movimentos.", "attribute_bonus": {"intellect": 2}},
                    {"text": "Mostrar a importância da estabilidade e paciência.", "attribute_bonus": {"charisma": 1, "intellect": 1}}
                ],
                "Ar": [
                    {"text": "Usar sua agilidade e leveza para evitar o confronto.", "attribute_bonus": {"dexterity": 2}},
                    {"text": "Sussurrar mensagens através do vento.", "attribute_bonus": {"charisma": 2}},
                    {"text": "Demonstrar a liberdade e adaptabilidade do ar.", "attribute_bonus": {"intellect": 1, "dexterity": 1}}
                ],
                "Telepatia": [
                    {"text": "Ler os pensamentos para entender as verdadeiras intenções.", "attribute_bonus": {"intellect": 2}},
                    {"text": "Usar comunicação telepática para coordenar ações.", "attribute_bonus": {"charisma": 1, "intellect": 1}},
                    {"text": "Projetar pensamentos tranquilizadores.", "attribute_bonus": {"charisma": 2}}
                ],
                "Força": [
                    {"text": "Demonstrar força bruta para impressionar.", "attribute_bonus": {"power_stat": 2}},
                    {"text": "Usar força controlada para ajudar em uma tarefa difícil.", "attribute_bonus": {"power_stat": 1, "charisma": 1}},
                    {"text": "Mostrar que força vem com responsabilidade.", "attribute_bonus": {"charisma": 2}}
                ],
                "Manipulação do Tempo": [
                    {"text": "Desacelerar o tempo para analisar a situação com calma.", "attribute_bonus": {"intellect": 2}},
                    {"text": "Usar pequenos saltos temporais para prever reações.", "attribute_bonus": {"charisma": 2}},
                    {"text": "Demonstrar o valor da precisão temporal.", "attribute_bonus": {"power_stat": 1, "intellect": 1}}
                ]
            },
            "club": {
                "1": [  # Clube das Chamas
                    {"text": "Usar a intensidade e paixão característica do Clube das Chamas.", "attribute_bonus": {"power_stat": 2}},
                    {"text": "Mostrar que o fogo pode iluminar, não apenas destruir.", "attribute_bonus": {"charisma": 1, "power_stat": 1}},
                    {"text": "Desafiar alguém para um duelo amistoso para resolver o impasse.", "attribute_bonus": {"power_stat": 1, "charisma": 1}}
                ],
                "2": [  # Ilusionistas Mentais
                    {"text": "Usar sutileza e manipulação psicológica para alcançar seus objetivos.", "attribute_bonus": {"intellect": 2}},
                    {"text": "Revelar que você percebe mais do que os outros imaginam.", "attribute_bonus": {"intellect": 1, "charisma": 1}},
                    {"text": "Criar uma ilusão para distrair ou impressionar.", "attribute_bonus": {"power_stat": 1, "intellect": 1}}
                ],
                "3": [  # Conselho Político
                    {"text": "Negociar um acordo que beneficie todas as partes.", "attribute_bonus": {"charisma": 2}},
                    {"text": "Usar informações estratégicas para ganhar vantagem.", "attribute_bonus": {"intellect": 2}},
                    {"text": "Demonstrar liderança ao tomar a iniciativa.", "attribute_bonus": {"charisma": 1, "power_stat": 1}}
                ],
                "4": [  # Elementalistas
                    {"text": "Buscar o equilíbrio e a harmonia na situação.", "attribute_bonus": {"intellect": 1, "charisma": 1}},
                    {"text": "Demonstrar a versatilidade do controle elemental.", "attribute_bonus": {"power_stat": 2}},
                    {"text": "Conectar-se com o ambiente natural para encontrar uma solução.", "attribute_bonus": {"intellect": 2}}
                ],
                "5": [  # Clube de Combate
                    {"text": "Enfrentar o desafio diretamente, sem hesitação.", "attribute_bonus": {"power_stat": 2}},
                    {"text": "Mostrar disciplina e autocontrole mesmo sob pressão.", "attribute_bonus": {"power_stat": 1, "charisma": 1}},
                    {"text": "Usar técnicas de combate para uma demonstração impressionante.", "attribute_bonus": {"power_stat": 1, "dexterity": 1}}
                ]
            }
        }
        
        logger.info("Initialized default choice templates")
    
    def _initialize_default_dialogue_templates(self):
        """
        Initializes default dialogue templates.
        """
        self.dialogue_templates = {
            "origin": {
                "Bairro Popular": {
                    "professor": [
                        {"npc": "Professor", "text": "Sua perspectiva única traz uma visão refrescante para a discussão. Nem tudo se aprende nos livros."},
                        {"npc": "Professor", "text": "Interessante como você aborda os problemas de forma prática. Isso vem da sua experiência no bairro?"}
                    ],
                    "elite_student": [
                        {"npc": "Estudante de Elite", "text": "Não esperava que alguém do seu... background... tivesse ideias tão interessantes."},
                        {"npc": "Estudante de Elite", "text": "Você até que se adaptou bem à academia, considerando de onde veio."}
                    ],
                    "friendly_student": [
                        {"npc": "Colega", "text": "Adoro suas histórias do bairro! Deve ter sido uma infância cheia de aventuras."},
                        {"npc": "Colega", "text": "Você tem uma força que muitos aqui, criados em berço de ouro, não têm."}
                    ]
                },
                "Família de Elite": {
                    "professor": [
                        {"npc": "Professor", "text": "Sua educação privilegiada é evidente, mas é bom ver que você não se apoia apenas nisso."},
                        {"npc": "Professor", "text": "Seus pais devem ter investido muito em sua formação. Use esse privilégio com sabedoria."}
                    ],
                    "working_class_student": [
                        {"npc": "Estudante Comum", "text": "Nem todos aqui nasceram com uma colher de prata na boca, sabia?"},
                        {"npc": "Estudante Comum", "text": "Surpreendente ver alguém da sua classe social se misturando com o resto de nós."}
                    ],
                    "friendly_student": [
                        {"npc": "Colega", "text": "Seus contatos da alta sociedade podem ser úteis para todos nós algum dia."},
                        {"npc": "Colega", "text": "É legal ver que você não é esnobe como outros da elite."}
                    ]
                },
                "Órfão": {
                    "professor": [
                        {"npc": "Professor", "text": "Sua independência é admirável. Muitos estudantes com famílias completas não têm metade da sua determinação."},
                        {"npc": "Professor", "text": "A academia pode se tornar sua família agora, se você permitir."}
                    ],
                    "family_student": [
                        {"npc": "Estudante com Família", "text": "Não consigo imaginar como deve ser não ter pais. Você é muito forte."},
                        {"npc": "Estudante com Família", "text": "Meus pais estão sempre me pressionando. Às vezes invejo sua liberdade."}
                    ],
                    "friendly_student": [
                        {"npc": "Colega", "text": "Ei, alguns de nós vamos fazer um almoço no fim de semana. Você deveria vir."},
                        {"npc": "Colega", "text": "Você construiu sua própria força. Isso é mais impressionante do que qualquer linhagem."}
                    ]
                },
                "Transferido": {
                    "professor": [
                        {"npc": "Professor", "text": "Sua experiência em outra instituição traz uma perspectiva valiosa para nossas discussões."},
                        {"npc": "Professor", "text": "Como nossa academia se compara à sua escola anterior?"}
                    ],
                    "local_student": [
                        {"npc": "Estudante Local", "text": "Ainda se adaptando? A Academia Tokugawa tem tradições que levam tempo para entender."},
                        {"npc": "Estudante Local", "text": "O que te fez vir para cá? Ouvi dizer que sua antiga escola também era boa."}
                    ],
                    "friendly_student": [
                        {"npc": "Colega", "text": "Suas histórias da outra escola são fascinantes! Como era o sistema de hierarquia lá?"},
                        {"npc": "Colega", "text": "É bom ter sangue novo por aqui. Traz novas ideias."}
                    ]
                },
                "Comunidade Isolada": {
                    "professor": [
                        {"npc": "Professor", "text": "Seus conhecimentos tradicionais oferecem uma perspectiva única que enriquece nossa aula."},
                        {"npc": "Professor", "text": "A sabedoria antiga às vezes supera a ciência moderna. Sua comunidade preservou conhecimentos valiosos."}
                    ],
                    "modern_student": [
                        {"npc": "Estudante Moderno", "text": "Sério que você cresceu sem internet? Como sobreviveu?"},
                        {"npc": "Estudante Moderno", "text": "Suas tradições parecem interessantes, mesmo que um pouco... antiquadas."}
                    ],
                    "friendly_student": [
                        {"npc": "Colega", "text": "Poderia me ensinar mais sobre as técnicas de meditação da sua comunidade?"},
                        {"npc": "Colega", "text": "Sua conexão com a natureza é incrível. Nunca vi ninguém com tanta sensibilidade aos elementos."}
                    ]
                }
            },
            "power": {
                "Fogo": {
                    "mentor": [
                        {"npc": "Mentor", "text": "O fogo reflete seu espírito - intenso, apaixonado, às vezes difícil de controlar."},
                        {"npc": "Mentor", "text": "Lembre-se: o fogo pode aquecer ou destruir. A escolha é sua."}
                    ],
                    "water_user": [
                        {"npc": "Usuário de Água", "text": "Nossos poderes são opostos, mas isso não significa que devemos ser inimigos."},
                        {"npc": "Usuário de Água", "text": "Sua intensidade é impressionante, mas às vezes é preciso fluidez, não apenas força."}
                    ],
                    "impressed_peer": [
                        {"npc": "Colega", "text": "Uau! Nunca vi ninguém manipular o fogo com tanta precisão!"},
                        {"npc": "Colega", "text": "O calor que você gera poderia ser útil na próxima excursão de inverno."}
                    ]
                },
                "Água": {
                    "mentor": [
                        {"npc": "Mentor", "text": "Como a água, você se adapta às circunstâncias. Essa é sua maior força."},
                        {"npc": "Mentor", "text": "A água pode ser gentil como um riacho ou poderosa como um tsunami. Aprenda a ser ambos."}
                    ],
                    "fire_user": [
                        {"npc": "Usuário de Fogo", "text": "Sua calma me irrita às vezes, sabia? Nem tudo se resolve com paciência."},
                        {"npc": "Usuário de Fogo", "text": "Tenho que admitir, sua adaptabilidade é uma vantagem que o fogo não tem."}
                    ],
                    "impressed_peer": [
                        {"npc": "Colega", "text": "A forma como você manipula a água é quase hipnótica."},
                        {"npc": "Colega", "text": "Poderia nos ajudar com o sistema de irrigação do jardim da academia?"}
                    ]
                },
                "Terra": {
                    "mentor": [
                        {"npc": "Mentor", "text": "Sua conexão com a terra lhe dá estabilidade. Use isso como fundação para crescer."},
                        {"npc": "Mentor", "text": "A terra é paciente e duradoura. Cultive essas qualidades em si mesmo."}
                    ],
                    "air_user": [
                        {"npc": "Usuário de Ar", "text": "Como você consegue ficar tão... parado? Não sente vontade de se mover, explorar?"},
                        {"npc": "Usuário de Ar", "text": "Sua solidez compensa minha tendência a me dispersar. Formamos uma boa equipe."}
                    ],
                    "impressed_peer": [
                        {"npc": "Colega", "text": "A forma como você moldou aquela escultura de pedra foi incrível!"},
                        {"npc": "Colega", "text": "Poderia nos ajudar a reforçar as fundações do novo prédio do clube?"}
                    ]
                },
                "Ar": {
                    "mentor": [
                        {"npc": "Mentor", "text": "O ar é o elemento da liberdade e do intelecto. Seu poder reflete sua mente ágil."},
                        {"npc": "Mentor", "text": "Não deixe sua natureza dispersa impedir seu progresso. O ar precisa de direção."}
                    ],
                    "earth_user": [
                        {"npc": "Usuário de Terra", "text": "Como você consegue pensar tão rápido? Às vezes mal consigo acompanhar."},
                        {"npc": "Usuário de Terra", "text": "Sua agilidade compensa minha lentidão. Poderíamos aprender um com o outro."}
                    ],
                    "impressed_peer": [
                        {"npc": "Colega", "text": "Incrível como você pode praticamente voar! Deve ser a melhor sensação do mundo."},
                        {"npc": "Colega", "text": "Poderia criar uma brisa refrescante? Este verão está insuportável."}
                    ]
                },
                "Telepatia": {
                    "mentor": [
                        {"npc": "Mentor", "text": "Seu dom é raro e poderoso. Lembre-se sempre da responsabilidade que vem com ele."},
                        {"npc": "Mentor", "text": "A mente dos outros é um território sagrado. Entre com respeito ou não entre."}
                    ],
                    "suspicious_peer": [
                        {"npc": "Colega Desconfiado", "text": "Você está lendo minha mente agora? Porque isso seria uma invasão de privacidade."},
                        {"npc": "Colega Desconfiado", "text": "Deve ser conveniente sempre saber o que os outros estão pensando..."}
                    ],
                    "impressed_peer": [
                        {"npc": "Colega", "text": "Sua telepatia poderia nos ajudar muito no próximo projeto em grupo!"},
                        {"npc": "Colega", "text": "Como é? Ouvir tantas vozes na sua cabeça?"}
                    ]
                },
                "Força": {
                    "mentor": [
                        {"npc": "Mentor", "text": "Força sem controle é apenas destruição. Aprenda a dosar seu poder."},
                        {"npc": "Mentor", "text": "Sua força física é impressionante, mas não negligencie o desenvolvimento da sua mente."}
                    ],
                    "intellect_user": [
                        {"npc": "Usuário de Intelecto", "text": "Nem tudo se resolve com músculos, sabia? Às vezes é preciso estratégia."},
                        {"npc": "Usuário de Intelecto", "text": "Sua força seria muito mais eficaz se combinada com um plano inteligente."}
                    ],
                    "impressed_peer": [
                        {"npc": "Colega", "text": "Uau! Você levantou aquilo como se não pesasse nada!"},
                        {"npc": "Colega", "text": "Poderia nos ajudar a mover alguns equipamentos pesados para o laboratório?"}
                    ]
                },
                "Manipulação do Tempo": {
                    "mentor": [
                        {"npc": "Mentor", "text": "Seu poder sobre o tempo é extremamente raro. Use-o com sabedoria, pois cada alteração tem consequências."},
                        {"npc": "Mentor", "text": "O tempo é a mais fundamental das forças. Compreendê-lo é compreender o universo."}
                    ],
                    "curious_peer": [
                        {"npc": "Colega Curioso", "text": "É verdade que você pode ver o futuro? Ou voltar no tempo?"},
                        {"npc": "Colega Curioso", "text": "Como é experimentar o tempo de forma diferente de todos nós?"}
                    ],
                    "impressed_peer": [
                        {"npc": "Colega", "text": "A forma como você desacelerou aquele objeto em queda foi incrível!"},
                        {"npc": "Colega", "text": "Seu poder deve ser útil para nunca se atrasar para as aulas, hein?"}
                    ]
                }
            },
            "club": {
                "1": {  # Clube das Chamas
                    "club_leader": [
                        {"npc": "Kai Flameheart", "text": "Mostre a intensidade que define nosso clube! Não aceite menos que a vitória!"},
                        {"npc": "Kai Flameheart", "text": "Lembre-se do nosso lema: 'A chama mais brilhante forja o espírito mais forte!'"}
                    ],
                    "rival_club_member": [
                        {"npc": "Membro dos Elementalistas", "text": "Típico do Clube das Chamas - tudo força, nenhum controle."},
                        {"npc": "Membro dos Elementalistas", "text": "Seu clube tem potencial, mas falta refinamento e equilíbrio."}
                    ],
                    "club_member": [
                        {"npc": "Colega de Clube", "text": "Vamos mostrar a eles o poder das chamas! Estamos com você!"},
                        {"npc": "Colega de Clube", "text": "Depois do treino, vamos todos para o café da esquina. Tradição do clube!"}
                    ]
                },
                "2": {  # Ilusionistas Mentais
                    "club_leader": [
                        {"npc": "Luna Mindweaver", "text": "A mente é a arma mais poderosa. Use-a para ver além das aparências."},
                        {"npc": "Luna Mindweaver", "text": "Nosso clube valoriza a sutileza e a percepção. Mostre que você entende isso."}
                    ],
                    "rival_club_member": [
                        {"npc": "Membro do Conselho Político", "text": "Vocês Ilusionistas acham que podem ler mentes, mas não entendem nada de estratégia real."},
                        {"npc": "Membro do Conselho Político", "text": "Ilusões são interessantes, mas o verdadeiro poder está na influência concreta."}
                    ],
                    "club_member": [
                        {"npc": "Colega de Clube", "text": "Percebi uma mudança sutil na sua aura mental. Tem praticado as técnicas que ensinei?"},
                        {"npc": "Colega de Clube", "text": "Vamos nos reunir na sala de meditação mais tarde. Descobrimos algo fascinante."}
                    ]
                },
                "3": {  # Conselho Político
                    "club_leader": [
                        {"npc": "Alexander Strategos", "text": "Cada interação é uma negociação. Cada palavra, um movimento no tabuleiro."},
                        {"npc": "Alexander Strategos", "text": "Nosso clube controla a política estudantil. Use essa influência com sabedoria."}
                    ],
                    "rival_club_member": [
                        {"npc": "Membro dos Ilusionistas", "text": "Vocês do Conselho são tão previsíveis com suas manipulações óbvias."},
                        {"npc": "Membro dos Ilusionistas", "text": "Política é um jogo superficial comparado às profundezas da mente."}
                    ],
                    "club_member": [
                        {"npc": "Colega de Clube", "text": "Temos uma reunião estratégica hoje à noite. Sua presença é importante."},
                        {"npc": "Colega de Clube", "text": "Consegui aquelas informações que você pediu. Muito úteis para nosso próximo movimento."}
                    ]
                },
                "4": {  # Elementalistas
                    "club_leader": [
                        {"npc": "Gaia Naturae", "text": "Busque o equilíbrio em todas as coisas. Essa é a essência do nosso clube."},
                        {"npc": "Gaia Naturae", "text": "Os elementos não são ferramentas, são extensões de nós mesmos. Respeite-os."}
                    ],
                    "rival_club_member": [
                        {"npc": "Membro do Clube das Chamas", "text": "Vocês Elementalistas são tão lentos com toda essa conversa de 'equilíbrio'."},
                        {"npc": "Membro do Clube das Chamas", "text": "Por que se preocupar com todos os elementos quando pode se especializar em um?"}
                    ],
                    "club_member": [
                        {"npc": "Colega de Clube", "text": "A meditação elemental de hoje será no jardim zen. Não se atrase."},
                        {"npc": "Colega de Clube", "text": "Sua conexão com os elementos está ficando mais forte. Posso sentir."}
                    ]
                },
                "5": {  # Clube de Combate
                    "club_leader": [
                        {"npc": "Ryuji Battleborn", "text": "A disciplina forja o guerreiro. Nunca esqueça seu treinamento."},
                        {"npc": "Ryuji Battleborn", "text": "Nosso clube valoriza a força, mas também a honra. Uma vitória sem honra não é vitória."}
                    ],
                    "rival_club_member": [
                        {"npc": "Membro do Conselho Político", "text": "O Clube de Combate é tão... primitivo. A verdadeira batalha acontece nas sombras."},
                        {"npc": "Membro do Conselho Político", "text": "Força física impressiona apenas os simples. O poder real está na influência."}
                    ],
                    "club_member": [
                        {"npc": "Colega de Clube", "text": "Treino extra hoje à noite. O torneio está chegando e precisamos estar preparados."},
                        {"npc": "Colega de Clube", "text": "Sua técnica melhorou muito. Continue assim e logo enfrentará o próprio Ryuji."}
                    ]
                }
            }
        }
        
        logger.info("Initialized default dialogue templates")
    
    def _initialize_default_outcome_templates(self):
        """
        Initializes default outcome templates.
        """
        self.outcome_templates = {
            "origin": {
                "Bairro Popular": [
                    {"text": "Sua experiência nas ruas te deu uma perspicácia que surpreendeu a todos.", "attribute_bonus": {"charisma": 2}},
                    {"text": "Você mostrou que determinação e esperteza valem mais que privilégios.", "attribute_bonus": {"power_stat": 1, "charisma": 1}},
                    {"text": "Sua abordagem direta e prática resolveu o problema quando teorias falharam.", "attribute_bonus": {"intellect": 1, "power_stat": 1}}
                ],
                "Família de Elite": [
                    {"text": "Seus contatos e conhecimentos privilegiados abriram portas que estavam fechadas para outros.", "attribute_bonus": {"charisma": 2}},
                    {"text": "Você provou que nem todos da elite são arrogantes, ganhando o respeito dos colegas.", "attribute_bonus": {"charisma": 1, "intellect": 1}},
                    {"text": "Sua educação refinada permitiu que você encontrasse uma solução elegante.", "attribute_bonus": {"intellect": 2}}
                ],
                "Órfão": [
                    {"text": "Sua independência e resiliência impressionaram até os mais céticos.", "attribute_bonus": {"power_stat": 2}},
                    {"text": "Você transformou a ausência de laços familiares em uma força, não uma fraqueza.", "attribute_bonus": {"charisma": 1, "power_stat": 1}},
                    {"text": "Sua capacidade de se adaptar e sobreviver sozinho provou ser uma vantagem crucial.", "attribute_bonus": {"intellect": 1, "power_stat": 1}}
                ],
                "Transferido": [
                    {"text": "Sua perspectiva externa trouxe uma solução inovadora que ninguém havia considerado.", "attribute_bonus": {"intellect": 2}},
                    {"text": "Você usou conhecimentos de sua escola anterior para superar o desafio.", "attribute_bonus": {"intellect": 1, "power_stat": 1}},
                    {"text": "Sua adaptabilidade como transferido te permitiu navegar a situação com facilidade.", "attribute_bonus": {"charisma": 1, "intellect": 1}}
                ],
                "Comunidade Isolada": [
                    {"text": "Seus conhecimentos tradicionais ofereceram uma solução que a ciência moderna não conseguia.", "attribute_bonus": {"intellect": 2}},
                    {"text": "Sua conexão com a natureza e os elementos surpreendeu a todos.", "attribute_bonus": {"power_stat": 1, "intellect": 1}},
                    {"text": "Você mostrou o valor de uma perspectiva diferente e única.", "attribute_bonus": {"charisma": 2}}
                ]
            },
            "power": {
                "Fogo": [
                    {"text": "As chamas responderam ao seu comando com precisão impressionante.", "attribute_bonus": {"power_stat": 2}},
                    {"text": "Você demonstrou que o fogo pode criar e iluminar, não apenas destruir.", "attribute_bonus": {"charisma": 1, "power_stat": 1}},
                    {"text": "Seu controle sobre o calor criou a atmosfera perfeita para a situação.", "attribute_bonus": {"charisma": 2}}
                ],
                "Água": [
                    {"text": "Como a água, você se adaptou perfeitamente às circunstâncias.", "attribute_bonus": {"intellect": 2}},
                    {"text": "Sua capacidade de fluir ao redor dos obstáculos levou a uma solução elegante.", "attribute_bonus": {"dexterity": 1, "intellect": 1}},
                    {"text": "A calma e clareza de seu poder aquático acalmou a situação tensa.", "attribute_bonus": {"charisma": 2}}
                ],
                "Terra": [
                    {"text": "Sua firmeza inabalável como a própria terra garantiu o sucesso.", "attribute_bonus": {"power_stat": 2}},
                    {"text": "Você criou uma fundação sólida sobre a qual todos puderam construir.", "attribute_bonus": {"charisma": 1, "power_stat": 1}},
                    {"text": "Sua paciência e persistência, qualidades da terra, foram recompensadas.", "attribute_bonus": {"intellect": 1, "power_stat": 1}}
                ],
                "Ar": [
                    {"text": "Sua agilidade e pensamento rápido como o vento superaram todos os obstáculos.", "attribute_bonus": {"dexterity": 2}},
                    {"text": "Você encontrou espaço para manobrar onde outros viram apenas barreiras.", "attribute_bonus": {"dexterity": 1, "intellect": 1}},
                    {"text": "Suas palavras, carregadas pelo ar, inspiraram todos ao seu redor.", "attribute_bonus": {"charisma": 2}}
                ],
                "Telepatia": [
                    {"text": "Sua compreensão profunda das mentes alheias revelou o caminho perfeito.", "attribute_bonus": {"intellect": 2}},
                    {"text": "Você coordenou perfeitamente as ações do grupo através de comunicação telepática.", "attribute_bonus": {"charisma": 1, "intellect": 1}},
                    {"text": "Sua capacidade de sentir emoções criou uma conexão profunda com os presentes.", "attribute_bonus": {"charisma": 2}}
                ],
                "Força": [
                    {"text": "Sua demonstração de poder físico resolveu a situação imediatamente.", "attribute_bonus": {"power_stat": 2}},
                    {"text": "Você mostrou que força pode ser usada para proteger e construir, não apenas destruir.", "attribute_bonus": {"charisma": 1, "power_stat": 1}},
                    {"text": "Seu controle preciso sobre sua força impressionou a todos.", "attribute_bonus": {"dexterity": 1, "power_stat": 1}}
                ],
                "Manipulação do Tempo": [
                    {"text": "Sua manipulação sutil do fluxo temporal criou a oportunidade perfeita.", "attribute_bonus": {"intellect": 2}},
                    {"text": "Você demonstrou que timing é tudo, e ninguém entende isso melhor que você.", "attribute_bonus": {"dexterity": 1, "intellect": 1}},
                    {"text": "Sua capacidade de prever reações através de pequenos saltos temporais foi decisiva.", "attribute_bonus": {"charisma": 1, "intellect": 1}}
                ]
            },
            "club": {
                "1": [  # Clube das Chamas
                    {"text": "A intensidade característica do Clube das Chamas brilhou através de suas ações.", "attribute_bonus": {"power_stat": 2}},
                    {"text": "Você provou que a paixão e determinação do seu clube podem superar qualquer obstáculo.", "attribute_bonus": {"power_stat": 1, "charisma": 1}},
                    {"text": "Kai Flameheart ficaria orgulhoso de como você representou o espírito do clube.", "affinity_change": {"Kai Flameheart": 5}}
                ],
                "2": [  # Ilusionistas Mentais
                    {"text": "Sua sutileza e percepção, marcas registradas dos Ilusionistas Mentais, levaram ao sucesso.", "attribute_bonus": {"intellect": 2}},
                    {"text": "Você manipulou a situação com a precisão mental que seu clube valoriza.", "attribute_bonus": {"intellect": 1, "charisma": 1}},
                    {"text": "Luna Mindweaver notou sua habilidade em ver além das aparências.", "affinity_change": {"Luna Mindweaver": 5}}
                ],
                "3": [  # Conselho Político
                    {"text": "Suas habilidades diplomáticas refletiram perfeitamente os valores do Conselho Político.", "attribute_bonus": {"charisma": 2}},
                    {"text": "Você transformou um potencial conflito em uma oportunidade de aliança, como um verdadeiro estrategista.", "attribute_bonus": {"intellect": 1, "charisma": 1}},
                    {"text": "Alexander Strategos observou sua manobra política com aprovação.", "affinity_change": {"Alexander Strategos": 5}}
                ],
                "4": [  # Elementalistas
                    {"text": "O equilíbrio e harmonia que você demonstrou são a essência dos Elementalistas.", "attribute_bonus": {"intellect": 1, "power_stat": 1}},
                    {"text": "Sua conexão com todos os elementos provou ser superior à especialização limitada.", "attribute_bonus": {"power_stat": 2}},
                    {"text": "Gaia Naturae sorriu ao ver como você honrou os princípios do clube.", "affinity_change": {"Gaia Naturae": 5}}
                ],
                "5": [  # Clube de Combate
                    {"text": "A disciplina e determinação do Clube de Combate foram evidentes em cada movimento seu.", "attribute_bonus": {"power_stat": 2}},
                    {"text": "Você enfrentou o desafio com a honra e coragem de um verdadeiro guerreiro.", "attribute_bonus": {"power_stat": 1, "charisma": 1}},
                    {"text": "Ryuji Battleborn reconheceu seu espírito de lutador com um aceno de aprovação.", "affinity_change": {"Ryuji Battleborn": 5}}
                ]
            }
        }
        
        logger.info("Initialized default outcome templates")
    
    def generate_choices(self, player_data: Dict[str, Any], context: str = "general") -> List[Dict[str, Any]]:
        """
        Generates personalized choices based on player attributes.
        
        Args:
            player_data: Player data containing attributes like origin, power, and club
            context: Context for the choices (e.g., "combat", "social", "academic")
        
        Returns:
            List of choice objects with text and potential attribute bonuses
        """
        choices = []
        
        # Get player attributes
        origin = player_data.get("origin", "")
        power = player_data.get("power", "")
        club_id = str(player_data.get("club_id", ""))
        
        # Add origin-based choice
        if origin and origin in self.choice_templates.get("origin", {}):
            origin_choices = self.choice_templates["origin"][origin]
            if origin_choices:
                choices.append(random.choice(origin_choices))
        
        # Add power-based choice
        if power and power in self.choice_templates.get("power", {}):
            power_choices = self.choice_templates["power"][power]
            if power_choices:
                choices.append(random.choice(power_choices))
        
        # Add club-based choice
        if club_id and club_id in self.choice_templates.get("club", {}):
            club_choices = self.choice_templates["club"][club_id]
            if club_choices:
                choices.append(random.choice(club_choices))
        
        # If we couldn't generate personalized choices, add some generic ones
        if not choices:
            choices = [
                {"text": "Abordar a situação diretamente.", "attribute_bonus": {"power_stat": 1}},
                {"text": "Analisar cuidadosamente antes de agir.", "attribute_bonus": {"intellect": 1}},
                {"text": "Tentar uma abordagem diplomática.", "attribute_bonus": {"charisma": 1}}
            ]
        
        # Ensure we have at least 3 choices
        while len(choices) < 3:
            # Add generic choices if needed
            choices.append({
                "text": "Confiar em seu instinto e habilidades.",
                "attribute_bonus": {"power_stat": 1}
            })
        
        return choices
    
    def generate_dialogue(self, player_data: Dict[str, Any], npc_type: str) -> Dict[str, Any]:
        """
        Generates personalized dialogue based on player attributes.
        
        Args:
            player_data: Player data containing attributes like origin, power, and club
            npc_type: Type of NPC (e.g., "professor", "student", "mentor")
        
        Returns:
            Dialogue object with NPC name and text
        """
        # Get player attributes
        origin = player_data.get("origin", "")
        power = player_data.get("power", "")
        club_id = str(player_data.get("club_id", ""))
        
        # Try to get origin-based dialogue
        if origin and origin in self.dialogue_templates.get("origin", {}):
            origin_dialogues = self.dialogue_templates["origin"][origin]
            if npc_type in origin_dialogues and origin_dialogues[npc_type]:
                return random.choice(origin_dialogues[npc_type])
        
        # Try to get power-based dialogue
        if power and power in self.dialogue_templates.get("power", {}):
            power_dialogues = self.dialogue_templates["power"][power]
            if npc_type in power_dialogues and power_dialogues[npc_type]:
                return random.choice(power_dialogues[npc_type])
        
        # Try to get club-based dialogue
        if club_id and club_id in self.dialogue_templates.get("club", {}):
            club_dialogues = self.dialogue_templates["club"][club_id]
            if npc_type in club_dialogues and club_dialogues[npc_type]:
                return random.choice(club_dialogues[npc_type])
        
        # If no personalized dialogue found, return a generic one
        return {"npc": "NPC", "text": "Interessante... Vamos ver como você lida com isso."}
    
    def generate_outcome(self, player_data: Dict[str, Any], choice_index: int) -> Dict[str, Any]:
        """
        Generates a personalized outcome based on player attributes and choice.
        
        Args:
            player_data: Player data containing attributes like origin, power, and club
            choice_index: Index of the chosen option
        
        Returns:
            Outcome object with text and potential attribute bonuses or affinity changes
        """
        # Get player attributes
        origin = player_data.get("origin", "")
        power = player_data.get("power", "")
        club_id = str(player_data.get("club_id", ""))
        
        # Determine which attribute to use for the outcome based on choice index
        # This is a simple way to vary outcomes based on choices
        if choice_index == 0 and origin and origin in self.outcome_templates.get("origin", {}):
            outcomes = self.outcome_templates["origin"][origin]
            if outcomes:
                return random.choice(outcomes)
        elif choice_index == 1 and power and power in self.outcome_templates.get("power", {}):
            outcomes = self.outcome_templates["power"][power]
            if outcomes:
                return random.choice(outcomes)
        elif choice_index == 2 and club_id and club_id in self.outcome_templates.get("club", {}):
            outcomes = self.outcome_templates["club"][club_id]
            if outcomes:
                return random.choice(outcomes)
        
        # If no personalized outcome found, return a generic one
        return {
            "text": "Você lidou com a situação adequadamente.",
            "attribute_bonus": {"exp": 10}
        }
    
    def personalize_chapter(self, chapter_data: Dict[str, Any], player_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Personalizes a chapter based on player attributes.
        
        Args:
            chapter_data: Original chapter data
            player_data: Player data containing attributes
        
        Returns:
            Personalized chapter data
        """
        # Create a copy of the chapter data to modify
        personalized_chapter = chapter_data.copy()
        
        # Add personalized choices if the chapter has choices
        if "choices" in personalized_chapter and personalized_chapter["choices"]:
            # Keep the original choices
            original_choices = personalized_chapter["choices"].copy()
            
            # Generate personalized choices
            personalized_choices = self.generate_choices(player_data)
            
            # Add personalized choices to the original ones
            # We'll keep the original choices' next_dialogue values
            for i, p_choice in enumerate(personalized_choices):
                if i < len(original_choices):
                    # Merge the personalized choice with the original one
                    merged_choice = original_choices[i].copy()
                    merged_choice["text"] = p_choice["text"]
                    if "attribute_bonus" in p_choice:
                        merged_choice["attribute_bonus"] = p_choice["attribute_bonus"]
                    original_choices[i] = merged_choice
                else:
                    # If we have more personalized choices than original ones,
                    # add them with a default next_dialogue
                    p_choice["next_dialogue"] = 0
                    original_choices.append(p_choice)
            
            personalized_chapter["choices"] = original_choices
        
        # Personalize dialogues if the chapter has dialogues
        if "dialogues" in personalized_chapter and personalized_chapter["dialogues"]:
            for i, dialogue in enumerate(personalized_chapter["dialogues"]):
                # Replace placeholders in dialogue text
                if "text" in dialogue:
                    dialogue["text"] = self._replace_placeholders(dialogue["text"], player_data)
                
                # If this is an NPC dialogue, consider personalizing it
                if "npc" in dialogue and dialogue["npc"] != "Narrador" and random.random() < 0.3:
                    # 30% chance to replace with a personalized dialogue
                    npc_type = self._get_npc_type(dialogue["npc"])
                    personalized_dialogue = self.generate_dialogue(player_data, npc_type)
                    if personalized_dialogue:
                        # Keep the original NPC name
                        personalized_dialogue["npc"] = dialogue["npc"]
                        personalized_chapter["dialogues"][i] = personalized_dialogue
        
        return personalized_chapter
    
    def _replace_placeholders(self, text: str, player_data: Dict[str, Any]) -> str:
        """
        Replaces placeholders in text with player data.
        
        Args:
            text: Text with placeholders
            player_data: Player data
        
        Returns:
            Text with placeholders replaced
        """
        # Replace {player_name}
        if "{player_name}" in text and "name" in player_data:
            text = text.replace("{player_name}", player_data["name"])
        
        # Replace {player_power}
        if "{player_power}" in text and "power" in player_data:
            text = text.replace("{player_power}", player_data["power"])
        
        # Replace {player_origin}
        if "{player_origin}" in text and "origin" in player_data:
            text = text.replace("{player_origin}", player_data["origin"])
        
        # Replace {club_name}
        if "{club_name}" in text and "club_name" in player_data:
            text = text.replace("{club_name}", player_data["club_name"])
        
        # Replace {player_element} - assuming it's the same as power for elemental powers
        if "{player_element}" in text and "power" in player_data:
            power = player_data["power"]
            if power in ["Fogo", "Água", "Terra", "Ar"]:
                text = text.replace("{player_element}", power)
            else:
                text = text.replace("{player_element}", "desconhecido")
        
        return text
    
    def _get_npc_type(self, npc_name: str) -> str:
        """
        Determines the type of an NPC based on their name.
        
        Args:
            npc_name: Name of the NPC
        
        Returns:
            Type of the NPC
        """
        npc_types = {
            "Professor": "professor",
            "Professora": "professor",
            "Diretor": "professor",
            "Mentor": "mentor",
            "Kai Flameheart": "club_leader",
            "Luna Mindweaver": "club_leader",
            "Alexander Strategos": "club_leader",
            "Gaia Naturae": "club_leader",
            "Ryuji Battleborn": "club_leader",
            "Estudante": "student",
            "Colega": "friendly_student"
        }
        
        # Check if the NPC name contains any of the keys
        for key, npc_type in npc_types.items():
            if key in npc_name:
                return npc_type
        
        # Default to generic NPC
        return "npc"