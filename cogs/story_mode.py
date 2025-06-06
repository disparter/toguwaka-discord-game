import discord
from discord.ext import commands
from discord import app_commands
import logging
import random
import asyncio
import json
from datetime import datetime
from utils.database import get_player, update_player, get_club, get_all_clubs
from utils.embeds import create_basic_embed, create_event_embed
from utils.game_mechanics import calculate_level_from_exp
from cogs.story_mode_enhanced import (
    enhance_story_mode, get_character_background, get_hierarchy_tier,
    get_hidden_secret, get_climactic_event, get_story_arc,
    HIERARCHY_TIERS, CHARACTER_BACKGROUNDS, HIDDEN_SECRETS, CLIMACTIC_EVENTS
)

logger = logging.getLogger('tokugawa_bot')

# Story mode progression tracking
# This will be stored in the player's data
# Format: {
#   "current_year": 1,
#   "current_chapter": 1,
#   "current_challenge_chapter": null,  # Will be set to a chapter number when in a challenge chapter
#   "completed_chapters": [],
#   "completed_challenge_chapters": [],  # List of completed challenge chapters
#   "club_progress": {},
#   "villain_defeats": [],
#   "minion_defeats": [],
#   "hierarchy_tier": 0,  # Player's position in the hierarchy (0-5)
#   "hierarchy_points": 0,  # Points accumulated towards advancing in the hierarchy
#   "discovered_secrets": [],  # List of discovered secret locations
#   "special_items": [],  # Special items obtained during the story
#   "character_relationships": {},  # Relationship levels with NPCs
#   "story_choices": {}  # Record of significant story choices made
# }

# Story chapters structure - Base structure that will be enhanced
BASE_STORY_CHAPTERS = {
    1: {  # Year 1
        1: {
            "title": "Meu Primeiro Dia de Aula",
            "description": "Seu primeiro dia na Academia Tokugawa. Conheça a escola e seus colegas.",
            "dialogues": [
                {"npc": "Diretor", "text": "Bem-vindo à Academia Tokugawa! Estamos felizes em receber mais um estudante com habilidades especiais."},
                {"npc": "Diretor", "text": "Aqui você aprenderá a controlar e aprimorar seus poderes, além de receber uma educação de primeira classe."},
                {"npc": "Diretor", "text": "Lembre-se: com grandes poderes, vêm grandes responsabilidades. Esperamos que você honre o nome da nossa academia."},
                {"npc": "Junie", "text": "Olá! Eu sou Junie, sua assistente virtual. Estou aqui para ajudar com qualquer dúvida que você tenha sobre a academia."},
                {"npc": "Junie", "text": "Vamos começar com um tour pela escola? Temos vários clubes que você pode conhecer!"}
            ],
            "choices": [
                {"text": "Sim, vamos conhecer os clubes!", "next_dialogue": 5},
                {"text": "Prefiro explorar por conta própria.", "next_dialogue": 6}
            ],
            "completion_exp": 50,
            "completion_tusd": 100,
            "next_chapter": 2
        },
        2: {
            "title": "Registro no Clube",
            "description": "Escolha um clube para se juntar e conheça seu líder.",
            "dialogues": [
                {"npc": "Junie", "text": "Agora é hora de escolher um clube! Cada clube tem seu próprio foco e atividades."},
                {"npc": "Junie", "text": "Você já está registrado no clube {club_name}. Vamos conhecer o líder do clube!"}
            ],
            "club_leaders": {
                1: {"name": "Kai Flameheart", "description": "Um jovem de cabelos vermelhos e temperamento explosivo, mas com um coração leal."},
                2: {"name": "Luna Mindweaver", "description": "Uma garota misteriosa de olhos violeta que parece sempre saber o que você está pensando."},
                3: {"name": "Alexander Strategos", "description": "Um rapaz calculista de óculos que analisa cada situação como um jogo de xadrez."},
                4: {"name": "Gaia Naturae", "description": "Uma estudante serena conectada com a natureza, capaz de manipular todos os elementos."},
                5: {"name": "Ryuji Battleborn", "description": "Um lutador disciplinado que valoriza a força e a honra acima de tudo."}
            },
            "club_dialogues": {
                1: [  # Clube das Chamas
                    {"npc": "Kai Flameheart", "text": "Então você é o novato? Espero que tenha coragem suficiente para aguentar o calor do nosso treinamento!"},
                    {"npc": "Kai Flameheart", "text": "No Clube das Chamas, valorizamos a paixão e a intensidade. Nossos poderes são destrutivos, mas aprendemos a controlá-los."},
                    {"npc": "Kai Flameheart", "text": "Estamos sempre em rivalidade com os Elementalistas, mas é uma competição saudável... na maioria das vezes."}
                ],
                2: [  # Ilusionistas Mentais
                    {"npc": "Luna Mindweaver", "text": "Ah, uma nova mente para nossa coleção. Bem-vindo aos Ilusionistas Mentais."},
                    {"npc": "Luna Mindweaver", "text": "Aqui exploramos os recantos da mente e os limites da percepção. A realidade é apenas o que acreditamos que seja."},
                    {"npc": "Luna Mindweaver", "text": "Tenha cuidado com o Conselho Político. Eles sempre têm segundas intenções... não que nós não tenhamos também."}
                ],
                3: [  # Conselho Político
                    {"npc": "Alexander Strategos", "text": "Um novo peão no tabuleiro. Interessante. Bem-vindo ao Conselho Político."},
                    {"npc": "Alexander Strategos", "text": "Nosso clube controla a política estudantil da academia. Influência e estratégia são nossas armas."},
                    {"npc": "Alexander Strategos", "text": "Os Ilusionistas pensam que podem ler nossas mentes, mas sempre estamos três passos à frente."}
                ],
                4: [  # Elementalistas
                    {"npc": "Gaia Naturae", "text": "A natureza te trouxe até nós. Seja bem-vindo aos Elementalistas."},
                    {"npc": "Gaia Naturae", "text": "Estudamos a harmonia dos elementos e como utilizá-los em equilíbrio com o mundo ao nosso redor."},
                    {"npc": "Gaia Naturae", "text": "O Clube das Chamas tem poder, mas falta-lhes controle e respeito pelos elementos."}
                ],
                5: [  # Clube de Combate
                    {"npc": "Ryuji Battleborn", "text": "Mais um guerreiro se junta às nossas fileiras. Mostre seu valor no Clube de Combate."},
                    {"npc": "Ryuji Battleborn", "text": "Aqui, aprimoramos nossas técnicas de luta e nos tornamos mais fortes a cada dia. A disciplina é nossa fundação."},
                    {"npc": "Ryuji Battleborn", "text": "Todos os outros clubes têm suas forças, mas no final, é o guerreiro mais forte que permanece de pé."}
                ]
            },
            "completion_exp": 75,
            "completion_tusd": 150,
            "next_chapter": 3
        },
        3: {
            "title": "Primeiro Desafio",
            "description": "Enfrente seu primeiro desafio na academia: um estudante valentão que está intimidando os calouros.",
            "dialogues": [
                {"npc": "Estudante Assustado", "text": "P-por favor, ajude! Tem um valentão do terceiro ano intimidando todos os calouros!"},
                {"npc": "Junie", "text": "Isso é um problema sério. Como você quer lidar com isso?"}
            ],
            "choices": [
                {"text": "Confrontar o valentão diretamente", "next_dialogue": 2, "attribute_check": "power_stat", "threshold": 7},
                {"text": "Tentar conversar e resolver pacificamente", "next_dialogue": 3, "attribute_check": "charisma", "threshold": 7},
                {"text": "Elaborar um plano estratégico", "next_dialogue": 4, "attribute_check": "intellect", "threshold": 7},
                {"text": "Pedir ajuda a um professor", "next_dialogue": 5}
            ],
            "minion_battle": {
                "name": "Drake, o Valentão",
                "description": "Um estudante arrogante do terceiro ano que gosta de intimidar os mais fracos.",
                "power": "Super Força",
                "level": 5,
                "hp": 100,
                "attributes": {
                    "dexterity": 8,
                    "intellect": 5,
                    "charisma": 3,
                    "power_stat": 10
                }
            },
            "completion_exp": 100,
            "completion_tusd": 200,
            "next_chapter": 4
        },
        4: {
            "title": "Aula de Controle de Poder",
            "description": "Participe de uma aula especial sobre controle de poderes e aprenda técnicas importantes.",
            "dialogues": [
                {"npc": "Professor de Controle", "text": "Bem-vindos à aula de Controle de Poder. Aqui vocês aprenderão a dominar suas habilidades."},
                {"npc": "Professor de Controle", "text": "O controle é tão importante quanto a força. Um poder descontrolado pode ser perigoso para todos."},
                {"npc": "Professor de Controle", "text": "Vamos começar com um exercício básico. Concentre-se e tente canalizar seu poder para este cristal."}
            ],
            "choices": [
                {"text": "Concentrar-se intensamente", "next_dialogue": 3, "attribute_check": "intellect", "threshold": 6},
                {"text": "Usar toda sua força", "next_dialogue": 4, "attribute_check": "power_stat", "threshold": 6}
            ],
            "completion_exp": 120,
            "completion_tusd": 220,
            "next_chapter": 5
        },
        5: {
            "title": "Rivalidade entre Clubes",
            "description": "Uma disputa entre clubes está causando tensão na academia. Você precisa decidir como se posicionar.",
            "dialogues": [
                {"npc": "Estudante do seu Clube", "text": "Precisamos da sua ajuda! Estamos tendo problemas com o clube rival."},
                {"npc": "Estudante do seu Clube", "text": "Eles estão dizendo que roubamos suas ideias para o festival, mas isso não é verdade!"},
                {"npc": "Estudante do Clube Rival", "text": "Ei, você! Seu clube está roubando nossas ideias. Isso não vai ficar assim!"}
            ],
            "choices": [
                {"text": "Defender seu clube", "next_dialogue": 3},
                {"text": "Tentar mediar o conflito", "next_dialogue": 4, "attribute_check": "charisma", "threshold": 8},
                {"text": "Investigar o que realmente aconteceu", "next_dialogue": 5, "attribute_check": "intellect", "threshold": 8}
            ],
            "completion_exp": 130,
            "completion_tusd": 240,
            "next_chapter": 6
        },
        6: {
            "title": "Torneio de Habilidades",
            "description": "Participe do torneio semestral de habilidades da academia e mostre seu valor.",
            "dialogues": [
                {"npc": "Organizador do Torneio", "text": "Bem-vindo ao Torneio de Habilidades! Este é o evento mais aguardado do semestre."},
                {"npc": "Organizador do Torneio", "text": "Aqui você enfrentará outros estudantes em desafios que testarão todos os seus atributos."},
                {"npc": "Organizador do Torneio", "text": "Prepare-se, pois o torneio está prestes a começar!"}
            ],
            "minion_battle": {
                "name": "Finalista do Torneio",
                "description": "Um estudante talentoso que chegou à final do torneio.",
                "power": "Habilidades Diversas",
                "level": 7,
                "hp": 120,
                "attributes": {
                    "dexterity": 10,
                    "intellect": 10,
                    "charisma": 8,
                    "power_stat": 12
                }
            },
            "completion_exp": 150,
            "completion_tusd": 300,
            "next_chapter": 7
        },
        7: {
            "title": "Mistério na Biblioteca",
            "description": "Estranhos eventos estão acontecendo na biblioteca da academia. Investigue o que está ocorrendo.",
            "dialogues": [
                {"npc": "Bibliotecária", "text": "Algo estranho está acontecendo aqui. Livros desaparecem e reaparecem em lugares diferentes."},
                {"npc": "Bibliotecária", "text": "Alguns estudantes relataram ouvir sussurros nas estantes mais antigas."},
                {"npc": "Bibliotecária", "text": "Você poderia investigar? Tenho medo de que seja algo perigoso."}
            ],
            "choices": [
                {"text": "Investigar as estantes antigas", "next_dialogue": 3},
                {"text": "Procurar por pistas nos livros desaparecidos", "next_dialogue": 4, "attribute_check": "intellect", "threshold": 9},
                {"text": "Montar uma armadilha para pegar o responsável", "next_dialogue": 5, "attribute_check": "dexterity", "threshold": 9}
            ],
            "completion_exp": 170,
            "completion_tusd": 320,
            "next_chapter": 8
        },
        8: {
            "title": "Excursão ao Mundo Exterior",
            "description": "Participe de uma excursão escolar ao mundo exterior, onde os estudantes podem praticar suas habilidades em um ambiente real.",
            "dialogues": [
                {"npc": "Professor Responsável", "text": "Esta excursão é uma oportunidade para vocês aplicarem o que aprenderam em um ambiente real."},
                {"npc": "Professor Responsável", "text": "Lembrem-se: discrição é essencial. Não queremos chamar atenção desnecessária para nossas habilidades."},
                {"npc": "Professor Responsável", "text": "Dividam-se em grupos e explorem a cidade. Estarei disponível se precisarem de ajuda."}
            ],
            "choices": [
                {"text": "Explorar a área comercial", "next_dialogue": 3},
                {"text": "Visitar o parque da cidade", "next_dialogue": 4},
                {"text": "Investigar rumores sobre atividades suspeitas", "next_dialogue": 5, "attribute_check": "intellect", "threshold": 10}
            ],
            "completion_exp": 190,
            "completion_tusd": 350,
            "next_chapter": 9
        },
        9: {
            "title": "Segredos da Academia",
            "description": "Descubra segredos ocultos sobre a história da Academia Tokugawa e seu verdadeiro propósito.",
            "dialogues": [
                {"npc": "Estudante Misterioso", "text": "Psst! Ei, você! Já se perguntou por que esta academia foi realmente fundada?"},
                {"npc": "Estudante Misterioso", "text": "Há segredos escondidos nos porões antigos. Segredos que a administração não quer que saibamos."},
                {"npc": "Estudante Misterioso", "text": "Quer descobrir a verdade? Siga-me, mas não conte a ninguém sobre esta conversa."}
            ],
            "choices": [
                {"text": "Seguir o estudante misterioso", "next_dialogue": 3},
                {"text": "Recusar e reportar à administração", "next_dialogue": 4},
                {"text": "Fingir aceitar, mas investigar por conta própria", "next_dialogue": 5, "attribute_check": "charisma", "threshold": 11}
            ],
            "completion_exp": 210,
            "completion_tusd": 380,
            "next_chapter": 10
        },
        10: {
            "title": "O Diretor Sombrio",
            "description": "Confronte o verdadeiro poder por trás da Academia Tokugawa e descubra suas intenções.",
            "dialogues": [
                {"npc": "Diretor Sombrio", "text": "Então você descobriu nossos segredos. Impressionante para um estudante do primeiro ano."},
                {"npc": "Diretor Sombrio", "text": "A Academia Tokugawa não é apenas uma escola. É um centro de treinamento para a próxima geração de guerreiros."},
                {"npc": "Diretor Sombrio", "text": "O mundo está à beira de uma guerra entre usuários de poderes. Estamos preparando vocês para sobreviver."},
                {"npc": "Diretor Sombrio", "text": "A questão é: você vai se juntar a nós ou se opor a nós? De qualquer forma, você não sairá daqui com essas informações."}
            ],
            "villain_battle": {
                "name": "Diretor Sombrio",
                "description": "O verdadeiro poder por trás da Academia Tokugawa, com habilidades que transcendem o comum.",
                "power": "Manipulação de Realidade",
                "level": 15,
                "hp": 300,
                "attributes": {
                    "dexterity": 18,
                    "intellect": 20,
                    "charisma": 19,
                    "power_stat": 22
                }
            },
            "completion_exp": 500,
            "completion_tusd": 1000,
            "next_chapter": 1,
            "next_year": 2
        }
    }
}

# Apply enhancements to the base story chapters
STORY_CHAPTERS = enhance_story_mode(BASE_STORY_CHAPTERS)

# Challenge chapters structure - based on strength levels
CHALLENGE_CHAPTERS = {
    1: {  # Tier 1 (⭐)
        1: {
            "title": "Desafio de Força: Iniciante",
            "description": "Um desafio para testar suas habilidades básicas. Adequado para estudantes de nível 1 de força.",
            "dialogues": [
                {"npc": "Instrutor de Treinamento", "text": "Bem-vindo ao seu primeiro desafio de força! Aqui testamos as habilidades dos estudantes com base em seu nível de poder."},
                {"npc": "Instrutor de Treinamento", "text": "Como um estudante de nível 1 de força, você enfrentará desafios adequados para suas habilidades atuais."},
                {"npc": "Instrutor de Treinamento", "text": "Não se preocupe, todos começam de algum lugar. Com treino e dedicação, você poderá enfrentar desafios mais difíceis no futuro."}
            ],
            "minion_battle": {
                "name": "Estudante Novato",
                "description": "Um estudante do primeiro ano que está apenas começando a desenvolver seus poderes.",
                "power": "Habilidades Básicas",
                "level": 2,
                "hp": 50,
                "attributes": {
                    "dexterity": 6,
                    "intellect": 5,
                    "charisma": 5,
                    "power_stat": 6
                }
            },
            "completion_exp": 60,
            "completion_tusd": 120
        }
    },
    2: {  # Tier 2 (⭐⭐)
        1: {
            "title": "Desafio de Força: Intermediário",
            "description": "Um desafio mais complexo para estudantes que já desenvolveram um bom controle sobre seus poderes.",
            "dialogues": [
                {"npc": "Instrutor de Treinamento", "text": "Vejo que você já desenvolveu suas habilidades além do nível básico. Muito bom!"},
                {"npc": "Instrutor de Treinamento", "text": "Este desafio testará não apenas sua força, mas também sua capacidade de usar seus poderes de forma estratégica."},
                {"npc": "Instrutor de Treinamento", "text": "Estudantes de nível 2 de força como você têm potencial para se tornarem muito poderosos com o treinamento adequado."}
            ],
            "minion_battle": {
                "name": "Estudante Intermediário",
                "description": "Um estudante do segundo ano com controle moderado sobre seus poderes.",
                "power": "Habilidades Intermediárias",
                "level": 4,
                "hp": 75,
                "attributes": {
                    "dexterity": 8,
                    "intellect": 7,
                    "charisma": 6,
                    "power_stat": 8
                }
            },
            "completion_exp": 90,
            "completion_tusd": 180
        }
    },
    3: {  # Tier 3 (⭐⭐⭐)
        1: {
            "title": "Desafio de Força: Avançado",
            "description": "Um desafio significativo que requer habilidades bem desenvolvidas e controle preciso dos poderes.",
            "dialogues": [
                {"npc": "Instrutor de Elite", "text": "Impressionante! Poucos estudantes alcançam o nível 3 de força tão cedo em sua jornada acadêmica."},
                {"npc": "Instrutor de Elite", "text": "Este desafio testará os limites de suas habilidades atuais. Prepare-se para usar todo o seu potencial."},
                {"npc": "Instrutor de Elite", "text": "Estudantes de nível 3 como você são considerados a elite entre os alunos regulares da academia."}
            ],
            "minion_battle": {
                "name": "Estudante Avançado",
                "description": "Um estudante do terceiro ano com excelente controle sobre seus poderes.",
                "power": "Habilidades Avançadas",
                "level": 6,
                "hp": 100,
                "attributes": {
                    "dexterity": 10,
                    "intellect": 9,
                    "charisma": 8,
                    "power_stat": 11
                }
            },
            "completion_exp": 120,
            "completion_tusd": 240
        }
    },
    4: {  # Tier 4 (⭐⭐⭐⭐)
        1: {
            "title": "Desafio de Força: Elite",
            "description": "Um desafio extremamente difícil reservado para os estudantes mais talentosos da academia.",
            "dialogues": [
                {"npc": "Instrutor Especial", "text": "Extraordinário! Estudantes de nível 4 de força são raros mesmo entre os formandos."},
                {"npc": "Instrutor Especial", "text": "Este desafio foi projetado para testar os limites dos estudantes mais poderosos. Poucos conseguem completá-lo."},
                {"npc": "Instrutor Especial", "text": "Seu potencial é imenso. Com o treinamento adequado, você pode se tornar um dos estudantes mais poderosos da história da academia."}
            ],
            "minion_battle": {
                "name": "Estudante de Elite",
                "description": "Um dos estudantes mais talentosos da academia, com poderes que rivalizam com os dos professores.",
                "power": "Habilidades de Elite",
                "level": 8,
                "hp": 150,
                "attributes": {
                    "dexterity": 13,
                    "intellect": 12,
                    "charisma": 10,
                    "power_stat": 14
                }
            },
            "completion_exp": 180,
            "completion_tusd": 360
        }
    },
    5: {  # Tier 5 (⭐⭐⭐⭐⭐)
        1: {
            "title": "Desafio de Força: Lendário",
            "description": "O desafio mais difícil da academia, reservado apenas para os estudantes com potencial lendário.",
            "dialogues": [
                {"npc": "Diretor", "text": "Incrível! Em todos os meus anos como diretor, vi apenas um punhado de estudantes com nível 5 de força."},
                {"npc": "Diretor", "text": "Este desafio foi criado para testar os limites dos estudantes mais excepcionais. Muitos professores não conseguiriam completá-lo."},
                {"npc": "Diretor", "text": "Seu potencial é verdadeiramente lendário. Estou ansioso para ver o que você realizará no futuro."}
            ],
            "minion_battle": {
                "name": "Prodígio Lendário",
                "description": "Um estudante com habilidades que transcendem o comum, considerado um prodígio mesmo entre a elite.",
                "power": "Habilidades Lendárias",
                "level": 10,
                "hp": 200,
                "attributes": {
                    "dexterity": 16,
                    "intellect": 15,
                    "charisma": 13,
                    "power_stat": 18
                }
            },
            "completion_exp": 250,
            "completion_tusd": 500
        }
    }
}

# Club NPCs
CLUB_NPCS = {
    1: [  # Clube das Chamas
        {"name": "Kai Flameheart", "role": "Líder", "power": "Explosão de Fogo", "personality": "Intenso e leal"},
        {"name": "Ember", "role": "Vice-líder", "power": "Manipulação de Calor", "personality": "Calma e calculista"},
        {"name": "Blaze", "role": "Membro", "power": "Corpo de Magma", "personality": "Impulsivo e enérgico"}
    ],
    2: [  # Ilusionistas Mentais
        {"name": "Luna Mindweaver", "role": "Líder", "power": "Ilusão Total", "personality": "Misteriosa e perspicaz"},
        {"name": "Mirage", "role": "Vice-líder", "power": "Manipulação de Memória", "personality": "Gentil mas manipulador"},
        {"name": "Enigma", "role": "Membro", "power": "Projeção Astral", "personality": "Introvertido e observador"}
    ],
    3: [  # Conselho Político
        {"name": "Alexander Strategos", "role": "Líder", "power": "Persuasão Absoluta", "personality": "Calculista e ambicioso"},
        {"name": "Victoria", "role": "Vice-líder", "power": "Detecção de Mentiras", "personality": "Justa e rigorosa"},
        {"name": "Machiavelli", "role": "Membro", "power": "Manipulação Emocional", "personality": "Astuto e oportunista"}
    ],
    4: [  # Elementalistas
        {"name": "Gaia Naturae", "role": "Líder", "power": "Harmonia Elemental", "personality": "Serena e sábia"},
        {"name": "Aero", "role": "Vice-líder", "power": "Controle do Ar", "personality": "Livre e imprevisível"},
        {"name": "Terra", "role": "Membro", "power": "Manipulação da Terra", "personality": "Estável e confiável"}
    ],
    5: [  # Clube de Combate
        {"name": "Ryuji Battleborn", "role": "Líder", "power": "Força Sobre-Humana", "personality": "Disciplinado e honrado"},
        {"name": "Fist", "role": "Vice-líder", "power": "Impacto de Choque", "personality": "Agressivo mas justo"},
        {"name": "Shadow", "role": "Membro", "power": "Velocidade Extrema", "personality": "Silencioso e letal"}
    ]
}

class StoryMode(commands.Cog):
    """Cog for the story mode functionality."""

    def __init__(self, bot):
        self.bot = bot
        self.active_stories = {}  # {user_id: {current_dialogue: int, chapter_data: dict}}
        self.climactic_events = {}  # Track active climactic events

        # Start a background task to check for climactic events
        self.climactic_event_task = self.bot.loop.create_task(self.check_for_climactic_events())

    async def check_for_climactic_events(self):
        """Background task to periodically check for and trigger climactic events."""
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            try:
                # Check for climactic events every hour
                await asyncio.sleep(3600)  # 3600 seconds = 1 hour

                # Get all active players
                # This is a simplified approach - in a real implementation, you'd want to
                # check only players who are currently active or in specific channels
                for guild in self.bot.guilds:
                    for member in guild.members:
                        if not member.bot:
                            await self.check_player_for_events(member.id)
            except Exception as e:
                logger.error(f"Error in check_for_climactic_events: {e}")
                await asyncio.sleep(60)  # Wait a minute before retrying

    async def check_player_for_events(self, user_id):
        """Check if a player is eligible for any climactic events."""
        try:
            player = get_player(user_id)
            if not player:
                return

            # Get story progress
            story_progress = player.get('story_progress', None)
            if not story_progress:
                return
            elif isinstance(story_progress, str):
                story_progress = json.loads(story_progress)

            # Get player level
            level = player.get('level', 1)

            # Check each event
            for event_name, event_data in CLIMACTIC_EVENTS.items():
                # Skip if player doesn't meet level requirement
                if level < event_data.get('requirements', {}).get('level', 0):
                    continue

                # Skip if event is already active for this player
                if self.climactic_events.get(user_id) == event_name:
                    continue

                # Skip if event has already been completed recently
                last_completion = story_progress.get('climactic_events', {}).get(event_name, 0)
                if last_completion:
                    # For yearly events, check if it's been at least 30 days
                    if event_data.get('frequency') == 'yearly' and (datetime.now().timestamp() - last_completion) < 2592000:  # 30 days
                        continue
                    # For random events, check if it's been at least 7 days
                    if event_data.get('frequency') == 'random' and (datetime.now().timestamp() - last_completion) < 604800:  # 7 days
                        continue
                    # For rare events, check if it's been at least 90 days
                    if event_data.get('frequency') == 'rare' and (datetime.now().timestamp() - last_completion) < 7776000:  # 90 days
                        continue

                # Determine if event should trigger
                should_trigger = False
                if event_data.get('frequency') == 'yearly':
                    # Yearly events have a 100% chance when eligible
                    should_trigger = True
                elif event_data.get('frequency') == 'random':
                    # Random events have a 10% chance when eligible
                    should_trigger = random.random() < 0.1
                elif event_data.get('frequency') == 'rare':
                    # Rare events have a 2% chance when eligible
                    should_trigger = random.random() < 0.02

                if should_trigger:
                    # Mark event as active for this player
                    self.climactic_events[user_id] = event_name

                    # Try to find a channel to send the event notification
                    user = self.bot.get_user(user_id)
                    if user:
                        try:
                            await user.send(embed=self.create_climactic_event_embed(event_name, event_data))
                        except:
                            # If DM fails, try to find a guild channel
                            for guild in self.bot.guilds:
                                member = guild.get_member(user_id)
                                if member:
                                    # Look for a general or bot channel
                                    channel = discord.utils.get(guild.text_channels, name='geral') or \
                                             discord.utils.get(guild.text_channels, name='general') or \
                                             discord.utils.get(guild.text_channels, name='bot-commands')
                                    if channel and channel.permissions_for(guild.me).send_messages:
                                        await channel.send(
                                            f"{member.mention}, um evento especial está ocorrendo!",
                                            embed=self.create_climactic_event_embed(event_name, event_data)
                                        )
                                        break
                    break  # Only trigger one event at a time
        except Exception as e:
            logger.error(f"Error in check_player_for_events: {e}")

    def create_climactic_event_embed(self, event_name, event_data):
        """Create an embed for a climactic event."""
        embed = create_basic_embed(
            title=f"Evento Especial: {event_name}",
            description=event_data.get('description', 'Um evento especial está ocorrendo!'),
            color=0x9932CC  # Dark Orchid
        )

        # Add rewards info
        rewards = event_data.get('rewards', {})
        rewards_text = ""
        if 'exp' in rewards:
            rewards_text += f"**Experiência:** {rewards['exp']} EXP\n"
        if 'tusd' in rewards:
            rewards_text += f"**TUSD:** {rewards['tusd']} 💰\n"
        if 'hierarchy_points' in rewards:
            rewards_text += f"**Pontos de Hierarquia:** {rewards['hierarchy_points']}\n"
        if 'special_item' in rewards:
            rewards_text += f"**Item Especial:** {rewards['special_item']}\n"
        if 'temporary_power_boost' in rewards:
            rewards_text += f"**Aumento Temporário de Poder:** +{rewards['temporary_power_boost']}\n"

        if rewards_text:
            embed.add_field(
                name="Recompensas Potenciais",
                value=rewards_text,
                inline=False
            )

        embed.add_field(
            name="Como Participar",
            value="Use o comando `/evento participar` para se juntar a este evento especial!",
            inline=False
        )

        return embed

    # Group for story commands
    story_group = app_commands.Group(name="historia", description="Comandos do modo história da Academia Tokugawa")

    # Group for event commands
    event_group = app_commands.Group(name="evento", description="Comandos para eventos especiais da Academia Tokugawa")

    @event_group.command(name="participar", description="Participar de um evento especial ativo")
    async def slash_participate_event(self, interaction: discord.Interaction):
        """Participate in an active climactic event."""
        try:
            # Check if player exists
            player = get_player(interaction.user.id)
            if not player:
                await interaction.response.send_message(
                    f"{interaction.user.mention}, você ainda não está registrado na Academia Tokugawa. "
                    f"Use /registro ingressar para criar seu personagem."
                )
                return

            # Check if player has an active event
            active_event = self.climactic_events.get(interaction.user.id)
            if not active_event:
                await interaction.response.send_message(
                    f"{interaction.user.mention}, você não tem nenhum evento especial ativo no momento. "
                    f"Eventos especiais ocorrem periodicamente. Fique atento às notificações!"
                )
                return

            # Get event data
            event_data = CLIMACTIC_EVENTS.get(active_event)
            if not event_data:
                await interaction.response.send_message("Erro ao encontrar dados do evento. Por favor, tente novamente mais tarde.")
                return

            # Get story progress
            story_progress = player.get('story_progress', None)
            if not story_progress:
                await interaction.response.send_message("Erro ao encontrar seu progresso na história. Por favor, tente novamente mais tarde.")
                return
            elif isinstance(story_progress, str):
                story_progress = json.loads(story_progress)

            # Initialize climactic_events if not present
            if 'climactic_events' not in story_progress:
                story_progress['climactic_events'] = {}

            # Mark event as completed
            story_progress['climactic_events'][active_event] = datetime.now().timestamp()

            # Calculate rewards
            rewards = event_data.get('rewards', {})
            exp_reward = rewards.get('exp', 0)
            tusd_reward = rewards.get('tusd', 0)
            hierarchy_points = rewards.get('hierarchy_points', 0)
            special_item = rewards.get('special_item', None)
            power_boost = rewards.get('temporary_power_boost', 0)

            # Update player data
            new_exp = player["exp"] + exp_reward
            new_tusd = player["tusd"] + tusd_reward

            # Check for level up
            new_level = calculate_level_from_exp(new_exp)
            level_up = new_level > player["level"]

            # Update hierarchy tier if points are awarded
            if hierarchy_points > 0:
                story_progress['hierarchy_points'] = story_progress.get('hierarchy_points', 0) + hierarchy_points
                # Every 10 points, increase tier by 1 (up to max of 5)
                if story_progress['hierarchy_points'] >= 10:
                    tier_increase = story_progress['hierarchy_points'] // 10
                    story_progress['hierarchy_tier'] = min(5, story_progress.get('hierarchy_tier', 0) + tier_increase)
                    story_progress['hierarchy_points'] = story_progress['hierarchy_points'] % 10

            # Add special item if any
            if special_item:
                if 'special_items' not in story_progress:
                    story_progress['special_items'] = []
                story_progress['special_items'].append(special_item)

            # Apply temporary power boost if any
            power_boost_end = None
            if power_boost > 0:
                # Boost lasts for 24 hours
                power_boost_end = datetime.now().timestamp() + 86400  # 24 hours

            # Prepare update data
            update_data = {
                "exp": new_exp,
                "tusd": new_tusd,
                "story_progress": json.dumps(story_progress)
            }

            if level_up:
                update_data["level"] = new_level

            if power_boost > 0:
                update_data["power_boost"] = power_boost
                update_data["power_boost_end"] = power_boost_end

            # Update player in database
            success = update_player(interaction.user.id, **update_data)

            if success:
                # Remove event from active events
                del self.climactic_events[interaction.user.id]

                # Create completion embed
                embed = create_basic_embed(
                    title=f"Evento Concluído: {active_event}",
                    description=f"Você participou com sucesso do evento especial!",
                    color=0x9932CC  # Dark Orchid
                )

                # Add rewards to embed
                rewards_text = ""
                if exp_reward > 0:
                    rewards_text += f"**Experiência:** +{exp_reward} EXP\n"
                if tusd_reward > 0:
                    rewards_text += f"**TUSD:** +{tusd_reward} 💰\n"
                if hierarchy_points > 0:
                    rewards_text += f"**Pontos de Hierarquia:** +{hierarchy_points}\n"
                if special_item:
                    rewards_text += f"**Item Especial:** {special_item}\n"
                if power_boost > 0:
                    rewards_text += f"**Aumento Temporário de Poder:** +{power_boost} (24 horas)\n"

                if rewards_text:
                    embed.add_field(
                        name="Recompensas Recebidas",
                        value=rewards_text,
                        inline=False
                    )

                # Add level up message if applicable
                if level_up:
                    embed.add_field(
                        name="Nível Aumentado!",
                        value=f"Você subiu para o nível {new_level}!",
                        inline=False
                    )

                await interaction.response.send_message(embed=embed)
            else:
                await interaction.response.send_message("Ocorreu um erro ao processar o evento. Por favor, tente novamente mais tarde.")
        except Exception as e:
            logger.error(f"Error in slash_participate_event: {e}")
            await interaction.response.send_message("Ocorreu um erro ao participar do evento. Por favor, tente novamente mais tarde.")

    @story_group.command(name="iniciar", description="Iniciar ou continuar sua jornada no modo história")
    async def slash_start_story(self, interaction: discord.Interaction):
        """Start or continue the story mode."""
        try:
            # Check if player exists
            player = get_player(interaction.user.id)
            if not player:
                await interaction.response.send_message(
                    f"{interaction.user.mention}, você ainda não está registrado na Academia Tokugawa. "
                    f"Use /registro ingressar para criar seu personagem."
                )
                return

            # Check if player has story progress
            story_progress = player.get('story_progress', None)
            if not story_progress:
                # Initialize story progress
                story_progress = {
                    "current_year": 1,
                    "current_chapter": 1,
                    "current_challenge_chapter": None,
                    "completed_chapters": [],
                    "completed_challenge_chapters": [],
                    "club_progress": {},
                    "villain_defeats": [],
                    "minion_defeats": [],
                    "hierarchy_tier": 0,
                    "hierarchy_points": 0,
                    "discovered_secrets": [],
                    "special_items": [],
                    "character_relationships": {},
                    "story_choices": {}
                }

                # Update player with initial story progress
                update_player(interaction.user.id, story_progress=json.dumps(story_progress))
            elif isinstance(story_progress, str):
                # Parse JSON string to dict
                story_progress = json.loads(story_progress)

            # Get current chapter data
            year = story_progress["current_year"]
            chapter = story_progress["current_chapter"]

            if year in STORY_CHAPTERS and chapter in STORY_CHAPTERS[year]:
                chapter_data = STORY_CHAPTERS[year][chapter]

                # Send chapter intro
                embed = create_basic_embed(
                    title=f"Ano {year}, Capítulo {chapter}: {chapter_data['title']}",
                    description=chapter_data['description'],
                    color=0x9370DB  # Medium Purple
                )

                await interaction.response.send_message(embed=embed)

                # Start the story dialogue
                self.active_stories[interaction.user.id] = {
                    "current_dialogue": 0,
                    "chapter_data": chapter_data
                }

                # Send first dialogue
                await self.send_next_dialogue(interaction.user.id, interaction.channel)
            else:
                await interaction.response.send_message(
                    f"{interaction.user.mention}, não foi possível encontrar o próximo capítulo da história. "
                    f"Novos capítulos serão adicionados em breve!"
                )
        except Exception as e:
            logger.error(f"Error in slash_start_story: {e}")
            await interaction.response.send_message("Ocorreu um erro ao iniciar o modo história. Por favor, tente novamente mais tarde.")

    @story_group.command(name="desafio", description="Iniciar ou continuar um desafio baseado no seu nível de força")
    async def slash_challenge(self, interaction: discord.Interaction):
        """Start or continue a challenge chapter based on strength level."""
        try:
            # Check if player exists
            player = get_player(interaction.user.id)
            if not player:
                await interaction.response.send_message(
                    f"{interaction.user.mention}, você ainda não está registrado na Academia Tokugawa. "
                    f"Use /registro ingressar para criar seu personagem."
                )
                return

            # Get player's strength level
            strength_level = player.get('strength_level', 1)

            # Check if challenge chapters exist for this strength level
            if strength_level not in CHALLENGE_CHAPTERS:
                await interaction.response.send_message(
                    f"{interaction.user.mention}, não há desafios disponíveis para seu nível de força atual ({strength_level})."
                )
                return

            # Check if player has story progress
            story_progress = player.get('story_progress', None)
            if not story_progress:
                await interaction.response.send_message(
                    f"{interaction.user.mention}, você precisa iniciar o modo história primeiro. "
                    f"Use /historia iniciar para começar sua jornada!"
                )
                return
            elif isinstance(story_progress, str):
                # Parse JSON string to dict
                story_progress = json.loads(story_progress)

            # Initialize challenge chapter if not present
            if 'current_challenge_chapter' not in story_progress:
                story_progress['current_challenge_chapter'] = 1
            if 'completed_challenge_chapters' not in story_progress:
                story_progress['completed_challenge_chapters'] = []

            # Get current challenge chapter
            challenge_chapter = story_progress.get('current_challenge_chapter', 1)

            # Check if challenge chapter exists
            if challenge_chapter not in CHALLENGE_CHAPTERS[strength_level]:
                # If the chapter doesn't exist, set to the first chapter
                challenge_chapter = 1
                story_progress['current_challenge_chapter'] = challenge_chapter

            # Get challenge chapter data
            chapter_data = CHALLENGE_CHAPTERS[strength_level][challenge_chapter]

            # Send chapter intro
            embed = create_basic_embed(
                title=f"Desafio de Força Nível {strength_level}, Capítulo {challenge_chapter}: {chapter_data['title']}",
                description=chapter_data['description'],
                color=0xFF4500  # Orange-Red for challenge chapters
            )

            await interaction.response.send_message(embed=embed)

            # Start the story dialogue
            self.active_stories[interaction.user.id] = {
                "current_dialogue": 0,
                "chapter_data": chapter_data,
                "is_challenge": True,
                "strength_level": strength_level,
                "challenge_chapter": challenge_chapter
            }

            # Send first dialogue
            await self.send_next_dialogue(interaction.user.id, interaction.channel)
        except Exception as e:
            logger.error(f"Error in slash_challenge: {e}")
            await interaction.response.send_message("Ocorreu um erro ao iniciar o desafio. Por favor, tente novamente mais tarde.")

    @story_group.command(name="status", description="Verificar seu progresso no modo história")
    async def slash_story_status(self, interaction: discord.Interaction):
        """Check story mode progress."""
        try:
            # Check if player exists
            player = get_player(interaction.user.id)
            if not player:
                await interaction.response.send_message(
                    f"{interaction.user.mention}, você ainda não está registrado na Academia Tokugawa. "
                    f"Use /registro ingressar para criar seu personagem."
                )
                return

            # Check if player has story progress
            story_progress = player.get('story_progress', None)
            if not story_progress:
                await interaction.response.send_message(
                    f"{interaction.user.mention}, você ainda não iniciou o modo história. "
                    f"Use /historia iniciar para começar sua jornada!"
                )
                return
            elif isinstance(story_progress, str):
                # Parse JSON string to dict
                story_progress = json.loads(story_progress)

            # Create embed with story progress
            embed = create_basic_embed(
                title=f"Progresso da História de {player['name']}",
                description=f"Acompanhe sua jornada na Academia Tokugawa!",
                color=0x9370DB  # Medium Purple
            )

            # Add current progress
            current_status = f"**Ano:** {story_progress['current_year']}\n**Capítulo:** {story_progress['current_chapter']}"

            # Add challenge chapter info if in one
            if story_progress.get('current_challenge_chapter'):
                current_status += f"\n**Capítulo de Desafio:** {story_progress['current_challenge_chapter']}"

            embed.add_field(
                name="Progresso Atual",
                value=current_status,
                inline=False
            )

            # Add completed chapters
            completed = story_progress.get('completed_chapters', [])
            if completed:
                completed_text = "\n".join([f"Ano {c.split('-')[0]}, Capítulo {c.split('-')[1]}" for c in completed])
            else:
                completed_text = "Nenhum capítulo concluído ainda."

            embed.add_field(
                name="Capítulos Concluídos",
                value=completed_text,
                inline=False
            )

            # Add completed challenge chapters
            completed_challenges = story_progress.get('completed_challenge_chapters', [])
            if completed_challenges:
                challenges_text = "\n".join([f"Nível {c.split('-')[0]}, Capítulo {c.split('-')[1]}" for c in completed_challenges])
                embed.add_field(
                    name="Desafios de Força Concluídos",
                    value=challenges_text,
                    inline=False
                )

            # Add villain defeats if any
            villains = story_progress.get('villain_defeats', [])
            if villains:
                villains_text = "\n".join(villains)
                embed.add_field(
                    name="Vilões Derrotados",
                    value=villains_text,
                    inline=False
                )

            # Add strength level info
            strength_level = player.get('strength_level', 1)
            from utils.game_mechanics import STRENGTH_LEVELS
            embed.add_field(
                name="Nível de Força",
                value=f"{strength_level} {STRENGTH_LEVELS.get(strength_level, '⭐')}",
                inline=True
            )

            # Add hierarchy tier info
            hierarchy_tier = story_progress.get('hierarchy_tier', 0)
            hierarchy_info = get_hierarchy_tier(hierarchy_tier)
            embed.add_field(
                name="Posição na Hierarquia",
                value=f"{hierarchy_info['name']} (Nível {hierarchy_tier})\n{hierarchy_info['description']}",
                inline=False
            )

            # Add discovered secrets if any
            discovered_secrets = story_progress.get('discovered_secrets', [])
            if discovered_secrets:
                secrets_text = "\n".join(discovered_secrets)
                embed.add_field(
                    name="Segredos Descobertos",
                    value=secrets_text,
                    inline=False
                )

            # Add special items if any
            special_items = story_progress.get('special_items', [])
            if special_items:
                items_text = "\n".join(special_items)
                embed.add_field(
                    name="Itens Especiais",
                    value=items_text,
                    inline=False
                )

            await interaction.response.send_message(embed=embed)
        except Exception as e:
            logger.error(f"Error in slash_story_status: {e}")
            await interaction.response.send_message("Ocorreu um erro ao verificar o progresso da história. Por favor, tente novamente mais tarde.")

    async def send_next_dialogue(self, user_id, channel):
        """Send the next dialogue in the story."""
        if user_id not in self.active_stories:
            return

        story_data = self.active_stories[user_id]
        current_dialogue = story_data["current_dialogue"]
        chapter_data = story_data["chapter_data"]

        # Check if we've reached the end of dialogues
        if current_dialogue >= len(chapter_data["dialogues"]):
            # Check if there are choices to make
            if "choices" in chapter_data:
                await self.send_choices(user_id, channel, chapter_data["choices"])
            else:
                # Complete the chapter
                await self.complete_chapter(user_id, channel)
            return

        # Get the current dialogue
        dialogue = chapter_data["dialogues"][current_dialogue]

        # Get player data for personalization
        player = get_player(user_id)
        club = get_club(player['club_id']) if player and player.get('club_id') else None

        # Replace placeholders in text
        text = dialogue["text"]
        if "{player_name}" in text:
            text = text.replace("{player_name}", player['name'])
        if "{club_name}" in text and club:
            text = text.replace("{club_name}", club['name'])

        # Create embed for dialogue
        embed = create_basic_embed(
            title=f"{dialogue['npc']}",
            description=text,
            color=0x9370DB  # Medium Purple
        )

        # Send the dialogue
        message = await channel.send(embed=embed)

        # Increment dialogue counter
        self.active_stories[user_id]["current_dialogue"] += 1

        # Wait a moment before sending next dialogue
        await asyncio.sleep(3)

        # Send next dialogue
        await self.send_next_dialogue(user_id, channel)

    async def send_choices(self, user_id, channel, choices):
        """Send choices for the player to make."""
        # Create embed for choices
        embed = create_basic_embed(
            title="O que você vai fazer?",
            description="Escolha sua próxima ação:",
            color=0x9370DB  # Medium Purple
        )

        # Create buttons for choices
        view = discord.ui.View(timeout=60)

        for i, choice in enumerate(choices):
            button = discord.ui.Button(label=choice["text"], style=discord.ButtonStyle.primary, custom_id=str(i))

            # Create a factory function to properly capture the loop variable
            def create_callback(index):
                async def button_callback(interaction):
                    if interaction.user.id != user_id:
                        await interaction.response.send_message("Esta não é sua história!", ephemeral=True)
                        return

                    # Disable all buttons
                    for child in view.children:
                        child.disabled = True
                    await interaction.message.edit(view=view)

                    # Process the choice
                    chosen = choices[index]

                    # Check if there's an attribute check
                    if "attribute_check" in chosen:
                        player = get_player(user_id)
                        attribute = chosen["attribute_check"]
                        threshold = chosen["threshold"]

                        if player[attribute] >= threshold:
                            await interaction.response.send_message(f"Seu {attribute} é alto o suficiente para esta ação!")

                            # Set the next dialogue based on successful check
                            self.active_stories[user_id]["current_dialogue"] = chosen["next_dialogue"]

                            # Continue the story
                            await self.send_next_dialogue(user_id, channel)
                        else:
                            await interaction.response.send_message(
                                f"Seu {attribute} não é alto o suficiente para esta ação. "
                                f"Você precisa de pelo menos {threshold}, mas tem apenas {player[attribute]}."
                            )

                            # Let the player choose again
                            await self.send_choices(user_id, channel, choices)
                    else:
                        await interaction.response.send_message(f"Você escolheu: {chosen['text']}")

                        # Set the next dialogue
                        self.active_stories[user_id]["current_dialogue"] = chosen["next_dialogue"]

                        # Continue the story
                        await self.send_next_dialogue(user_id, channel)

                return button_callback

            # Assign the callback created with the correct index
            button.callback = create_callback(i)
            view.add_item(button)

        # Send the choices
        await channel.send(embed=embed, view=view)

    async def complete_chapter(self, user_id, channel):
        """Complete the current chapter and give rewards."""
        if user_id not in self.active_stories:
            return

        story_data = self.active_stories[user_id]
        chapter_data = story_data["chapter_data"]
        is_challenge = story_data.get("is_challenge", False)

        # Get player data
        player = get_player(user_id)
        if not player:
            return

        # Get story progress
        story_progress = player.get('story_progress', None)
        if not story_progress:
            return
        elif isinstance(story_progress, str):
            story_progress = json.loads(story_progress)

        # Initialize challenge fields if not present
        if 'current_challenge_chapter' not in story_progress:
            story_progress['current_challenge_chapter'] = None
        if 'completed_challenge_chapters' not in story_progress:
            story_progress['completed_challenge_chapters'] = []

        # Calculate rewards
        exp_reward = chapter_data.get("completion_exp", 50)
        tusd_reward = chapter_data.get("completion_tusd", 100)

        # Handle regular chapter or challenge chapter
        if is_challenge:
            # This is a challenge chapter
            strength_level = story_data["strength_level"]
            challenge_chapter = story_data["challenge_chapter"]

            # Add to completed challenge chapters
            chapter_key = f"{strength_level}-{challenge_chapter}"
            if chapter_key not in story_progress["completed_challenge_chapters"]:
                story_progress["completed_challenge_chapters"].append(chapter_key)

            # Set next challenge chapter
            if challenge_chapter + 1 in CHALLENGE_CHAPTERS.get(strength_level, {}):
                story_progress["current_challenge_chapter"] = challenge_chapter + 1
            else:
                # No more challenge chapters for this strength level
                story_progress["current_challenge_chapter"] = None

            # Create completion embed
            embed = create_basic_embed(
                title=f"Desafio Concluído!",
                description=f"Você completou o Desafio de Força Nível {strength_level}, Capítulo {challenge_chapter}: {chapter_data['title']}",
                color=0xFF4500  # Orange-Red
            )
        else:
            # This is a regular chapter
            year = story_progress["current_year"]
            chapter = story_progress["current_chapter"]

            # Add to completed chapters
            chapter_key = f"{year}-{chapter}"
            if chapter_key not in story_progress["completed_chapters"]:
                story_progress["completed_chapters"].append(chapter_key)

            # Set next chapter
            if "next_chapter" in chapter_data:
                story_progress["current_chapter"] = chapter_data["next_chapter"]
            else:
                # Move to next year if no more chapters in current year
                story_progress["current_year"] += 1
                story_progress["current_chapter"] = 1

            # Create completion embed
            embed = create_basic_embed(
                title=f"Capítulo Concluído!",
                description=f"Você completou o Ano {year}, Capítulo {chapter}: {chapter_data['title']}",
                color=0x00FF00  # Green
            )

            # Handle hierarchy placement if this chapter has it
            if chapter_data.get("hierarchy_placement", False):
                # Calculate hierarchy tier based on player's attributes
                power_stat = player.get("power_stat", 0)
                intellect = player.get("intellect", 0)
                dexterity = player.get("dexterity", 0)
                charisma = player.get("charisma", 0)

                # Simple algorithm: average of attributes, weighted towards power_stat
                hierarchy_score = (power_stat * 2 + intellect + dexterity + charisma) / 5

                # Determine tier (0-5)
                if hierarchy_score >= 18:
                    new_tier = 5  # Rei/Rainha
                elif hierarchy_score >= 15:
                    new_tier = 4  # Jack/Ás
                elif hierarchy_score >= 12:
                    new_tier = 3  # Elite
                elif hierarchy_score >= 9:
                    new_tier = 2  # Médio-Alto
                elif hierarchy_score >= 6:
                    new_tier = 1  # Médio
                else:
                    new_tier = 0  # Baixo

                # Update hierarchy tier
                old_tier = story_progress.get("hierarchy_tier", 0)
                story_progress["hierarchy_tier"] = new_tier

                # Add hierarchy placement to embed
                hierarchy_info = get_hierarchy_tier(new_tier)
                embed.add_field(
                    name="Posição na Hierarquia",
                    value=f"Você foi classificado como: **{hierarchy_info['name']}** (Nível {new_tier})\n{hierarchy_info['description']}",
                    inline=False
                )

                if new_tier > old_tier:
                    embed.add_field(
                        name="Promoção!",
                        value=f"Você subiu na hierarquia da academia! De {get_hierarchy_tier(old_tier)['name']} para {hierarchy_info['name']}.",
                        inline=False
                    )

            # Check for secret discoveries based on player attributes
            for secret_name, secret_data in HIDDEN_SECRETS.items():
                requirements_met = True
                for attr, value in secret_data.get("requirements", {}).items():
                    if attr == "club_id":
                        if player.get("club_id") != value:
                            requirements_met = False
                            break
                    elif player.get(attr, 0) < value:
                        requirements_met = False
                        break

                # If requirements are met and secret not already discovered, add it
                if requirements_met and secret_name not in story_progress.get("discovered_secrets", []):
                    if "discovered_secrets" not in story_progress:
                        story_progress["discovered_secrets"] = []

                    story_progress["discovered_secrets"].append(secret_name)

                    # Add rewards
                    rewards = secret_data.get("rewards", {})
                    exp_reward += rewards.get("exp", 0)
                    tusd_reward += rewards.get("tusd", 0)

                    # Add special item if any
                    if "special_item" in rewards:
                        if "special_items" not in story_progress:
                            story_progress["special_items"] = []

                        story_progress["special_items"].append(rewards["special_item"])

                    # Add hierarchy boost if any
                    if "hierarchy_boost" in rewards:
                        story_progress["hierarchy_tier"] = min(5, story_progress.get("hierarchy_tier", 0) + rewards["hierarchy_boost"])

                    # Add secret discovery to embed
                    embed.add_field(
                        name="Segredo Descoberto!",
                        value=f"Você descobriu: **{secret_name}**\n{secret_data['description']}",
                        inline=False
                    )

                    # Only discover one secret per chapter for better pacing
                    break

        # Update player exp and tusd
        new_exp = player["exp"] + exp_reward
        new_tusd = player["tusd"] + tusd_reward

        # Check for level up
        new_level = calculate_level_from_exp(new_exp)
        level_up = new_level > player["level"]

        # Prepare update data
        update_data = {
            "exp": new_exp,
            "tusd": new_tusd,
            "story_progress": json.dumps(story_progress)
        }

        if level_up:
            update_data["level"] = new_level

        # Update player in database
        success = update_player(user_id, **update_data)

        if success:
            # Add rewards to embed
            embed.add_field(
                name="Recompensas",
                value=f"**Experiência:** +{exp_reward} EXP\n"
                      f"**TUSD:** +{tusd_reward} 💰",
                inline=False
            )

            # Add level up message if applicable
            if level_up:
                embed.add_field(
                    name="Nível Aumentado!",
                    value=f"Você subiu para o nível {new_level}!",
                    inline=False
                )

            # Add next chapter info for regular chapters
            if not is_challenge:
                next_year = story_progress["current_year"]
                next_chapter = story_progress["current_chapter"]

                if next_year in STORY_CHAPTERS and next_chapter in STORY_CHAPTERS[next_year]:
                    next_chapter_data = STORY_CHAPTERS[next_year][next_chapter]
                    embed.add_field(
                        name="Próximo Capítulo",
                        value=f"Ano {next_year}, Capítulo {next_chapter}: {next_chapter_data['title']}",
                        inline=False
                    )
                else:
                    embed.add_field(
                        name="Próximo Capítulo",
                        value="Novos capítulos serão adicionados em breve!",
                        inline=False
                    )
            # Add next challenge chapter info for challenge chapters
            else:
                next_challenge = story_progress.get("current_challenge_chapter")
                if next_challenge and next_challenge in CHALLENGE_CHAPTERS.get(strength_level, {}):
                    next_chapter_data = CHALLENGE_CHAPTERS[strength_level][next_challenge]
                    embed.add_field(
                        name="Próximo Desafio",
                        value=f"Nível {strength_level}, Capítulo {next_challenge}: {next_chapter_data['title']}",
                        inline=False
                    )
                else:
                    embed.add_field(
                        name="Próximo Desafio",
                        value="Você completou todos os desafios disponíveis para seu nível de força!",
                        inline=False
                    )

            await channel.send(embed=embed)

            # Clean up active story
            if user_id in self.active_stories:
                del self.active_stories[user_id]
        else:
            await channel.send("Ocorreu um erro ao completar o capítulo. Por favor, tente novamente mais tarde.")

    @commands.command(name="historia")
    async def story(self, ctx):
        """Iniciar ou continuar o modo história."""
        # Check if player exists
        player = get_player(ctx.author.id)
        if not player:
            await ctx.send(f"{ctx.author.mention}, você ainda não está registrado na Academia Tokugawa. Use !ingressar para criar seu personagem.")
            return

        # Check if player has story progress
        story_progress = player.get('story_progress', None)
        if not story_progress:
            # Initialize story progress
            story_progress = {
                "current_year": 1,
                "current_chapter": 1,
                "current_challenge_chapter": None,
                "completed_chapters": [],
                "completed_challenge_chapters": [],
                "club_progress": {},
                "villain_defeats": [],
                "minion_defeats": [],
                "hierarchy_tier": 0,
                "hierarchy_points": 0,
                "discovered_secrets": [],
                "special_items": [],
                "character_relationships": {},
                "story_choices": {},
                "climactic_events": {}
            }

            # Update player with initial story progress
            update_player(ctx.author.id, story_progress=json.dumps(story_progress))
        elif isinstance(story_progress, str):
            # Parse JSON string to dict
            story_progress = json.loads(story_progress)

        # Get current chapter data
        year = story_progress["current_year"]
        chapter = story_progress["current_chapter"]

        if year in STORY_CHAPTERS and chapter in STORY_CHAPTERS[year]:
            chapter_data = STORY_CHAPTERS[year][chapter]

            # Send chapter intro
            embed = create_basic_embed(
                title=f"Ano {year}, Capítulo {chapter}: {chapter_data['title']}",
                description=chapter_data['description'],
                color=0x9370DB  # Medium Purple
            )

            await ctx.send(embed=embed)

            # Start the story dialogue
            self.active_stories[ctx.author.id] = {
                "current_dialogue": 0,
                "chapter_data": chapter_data
            }

            # Send first dialogue
            await self.send_next_dialogue(ctx.author.id, ctx.channel)
        else:
            await ctx.send(
                f"{ctx.author.mention}, não foi possível encontrar o próximo capítulo da história. "
                f"Novos capítulos serão adicionados em breve!"
            )

async def setup(bot):
    """Add the cog to the bot."""
    from utils.command_registrar import CommandRegistrar

    # Create and add the cog
    cog = StoryMode(bot)
    await bot.add_cog(cog)
    logger.info("StoryMode cog loaded")

    # Register commands using the CommandRegistrar
    await CommandRegistrar.register_commands(bot, cog)
