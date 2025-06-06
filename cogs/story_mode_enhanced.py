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

logger = logging.getLogger('tokugawa_bot')

# Enhanced Story Mode - Inspired by "unOrdinary"
# This file extends the original story mode with richer narratives, hierarchical systems,
# character backgrounds, hidden secrets, and climactic events.

# Hierarchy System based on "unOrdinary"
HIERARCHY_TIERS = {
    5: {"name": "Rei/Rainha", "description": "Os mais poderosos da academia, respeitados e temidos por todos."},
    4: {"name": "Jack/Ás", "description": "Elite da academia, segundos apenas para o Rei/Rainha."},
    3: {"name": "Elite", "description": "Estudantes de alto nível com habilidades excepcionais."},
    2: {"name": "Médio-Alto", "description": "Estudantes com poderes acima da média."},
    1: {"name": "Médio", "description": "Estudantes com poderes medianos."},
    0: {"name": "Baixo", "description": "Estudantes com poderes fracos ou sem poderes."}
}

# Character Backgrounds
CHARACTER_BACKGROUNDS = {
    "Kai Flameheart": {
        "background": "Nascido em uma família de manipuladores de fogo, Kai sempre foi considerado um prodígio. Seus pais eram heróis conhecidos, mas morreram em uma missão quando ele tinha apenas 10 anos. Desde então, ele jurou se tornar o mais forte para proteger aqueles que ama.",
        "motivation": "Tornar-se forte o suficiente para nunca mais perder alguém importante.",
        "secrets": "Kai esconde que, em momentos de extrema emoção, perde o controle de seus poderes, o que já causou acidentes graves no passado."
    },
    "Luna Mindweaver": {
        "background": "Luna cresceu isolada devido à natureza de seus poderes. Capaz de ver os pensamentos dos outros desde criança, ela nunca conseguiu ter uma vida normal. A Academia Tokugawa foi o primeiro lugar onde ela encontrou pessoas que a entendiam.",
        "motivation": "Encontrar um modo de controlar seus poderes para poder viver uma vida normal.",
        "secrets": "Luna descobriu documentos secretos indicando que a academia está conduzindo experimentos com estudantes de alto potencial."
    },
    "Alexander Strategos": {
        "background": "Filho de um político influente, Alexander cresceu nos bastidores do poder. Seu dom de persuasão se manifestou cedo, e ele logo aprendeu a manipular situações a seu favor. Veio para a academia não para aprender, mas para criar uma rede de contatos poderosos para o futuro.",
        "motivation": "Construir uma base de poder para eventualmente entrar na política global.",
        "secrets": "Alexander mantém um dossiê com segredos de todos os estudantes influentes, que usa como garantia quando necessário."
    },
    "Gaia Naturae": {
        "background": "Gaia cresceu em uma comunidade isolada que venerava os elementos naturais. Quando seus poderes se manifestaram, ela foi considerada uma escolhida. Veio para a academia relutantemente, enviada pelos anciãos para aprender sobre o mundo moderno.",
        "motivation": "Encontrar um equilíbrio entre o mundo moderno e suas tradições ancestrais.",
        "secrets": "Gaia pode se comunicar com espíritos elementais, algo que esconde por temer ser considerada louca."
    },
    "Ryuji Battleborn": {
        "background": "Descendente de uma linhagem de guerreiros lendários, Ryuji treina desde que consegue se lembrar. Seu pai, extremamente rigoroso, nunca aceitou nada menos que a perfeição. Ryuji veio para a academia para provar seu valor e sair da sombra de seus ancestrais.",
        "motivation": "Superar o legado de sua família e definir seu próprio caminho como guerreiro.",
        "secrets": "Ryuji sofre de uma condição que enfraquece seu corpo após usar seus poderes no máximo, algo que esconde a todo custo."
    },
    "Diretor Sombrio": {
        "background": "Antes conhecido como Prometheus, ele foi um dos primeiros usuários de poderes a se revelar ao mundo. Após testemunhar o preconceito e perseguição, decidiu criar um santuário para os jovens com habilidades especiais.",
        "motivation": "Preparar a próxima geração para um inevitável conflito entre usuários de poderes e o resto da humanidade.",
        "secrets": "O Diretor está lentamente perdendo o controle de seus poderes devido a um experimento fracassado, e busca desesperadamente um sucessor."
    }
}

# Enhanced Story Arcs
STORY_ARCS = {
    "Ano 1": {
        "title": "Despertar",
        "description": "Seu primeiro ano na Academia Tokugawa, onde você descobre seus poderes e o verdadeiro propósito da escola.",
        "chapters": range(1, 11),  # Chapters 1-10
        "villain": "Diretor Sombrio",
        "theme": "Descoberta e Adaptação"
    },
    "Ano 2": {
        "title": "Hierarquia",
        "description": "Enquanto você sobe na hierarquia da academia, descobre as complexas políticas de poder entre os estudantes.",
        "chapters": range(1, 11),  # Chapters 1-10
        "villain": "O Usurpador",
        "theme": "Poder e Responsabilidade"
    },
    "Ano 3": {
        "title": "Conspiração",
        "description": "Uma conspiração antiga ameaça a academia e todos os usuários de poderes do mundo.",
        "chapters": range(1, 11),  # Chapters 1-10
        "villain": "A Organização",
        "theme": "Lealdade e Traição"
    }
}

# Hidden Secrets and Locations
HIDDEN_SECRETS = {
    "Biblioteca Proibida": {
        "description": "Uma seção secreta da biblioteca contendo conhecimentos proibidos sobre a origem dos poderes.",
        "requirements": {"intellect": 12},
        "rewards": {"exp": 200, "tusd": 300, "special_item": "Tomo do Conhecimento Proibido"}
    },
    "Laboratório Subterrâneo": {
        "description": "Um laboratório secreto sob a academia onde experimentos questionáveis são conduzidos.",
        "requirements": {"dexterity": 10, "intellect": 8},
        "rewards": {"exp": 250, "tusd": 350, "special_ability": "Resistência a Experimentos"}
    },
    "Sala do Conselho": {
        "description": "A sala onde os verdadeiros líderes da academia se reúnem para tomar decisões importantes.",
        "requirements": {"charisma": 15},
        "rewards": {"exp": 300, "tusd": 400, "hierarchy_boost": 1}
    },
    "Arena Oculta": {
        "description": "Uma arena secreta onde os estudantes mais fortes lutam sem regras ou supervisão.",
        "requirements": {"power_stat": 15},
        "rewards": {"exp": 350, "tusd": 450, "combat_technique": "Golpe Proibido"}
    },
    "Santuário Elemental": {
        "description": "Um local sagrado onde a conexão com os elementos é mais forte, permitindo treinamento avançado.",
        "requirements": {"club_id": 4, "power_stat": 12},
        "rewards": {"exp": 280, "tusd": 380, "elemental_affinity": True}
    }
}

# Climactic Events
CLIMACTIC_EVENTS = {
    "Torneio Anual": {
        "description": "O maior evento da academia, onde estudantes de todos os anos competem por glória e reconhecimento.",
        "requirements": {"level": 10},
        "rewards": {"exp": 500, "tusd": 1000, "hierarchy_points": 3},
        "frequency": "yearly"
    },
    "Invasão Misteriosa": {
        "description": "Intrusos desconhecidos invadem a academia, forçando estudantes e professores a se unirem para defender o campus.",
        "requirements": {"level": 15},
        "rewards": {"exp": 700, "tusd": 1500, "special_item": "Insígnia de Defensor"},
        "frequency": "random"
    },
    "Eclipse de Poder": {
        "description": "Um fenômeno raro que amplifica todos os poderes temporariamente, mas também causa instabilidade e conflitos.",
        "requirements": {"level": 20},
        "rewards": {"exp": 1000, "tusd": 2000, "temporary_power_boost": 5},
        "frequency": "rare"
    }
}

# Enhanced Year 1 Chapters with richer narrative
ENHANCED_STORY_CHAPTERS = {
    1: {  # Year 1
        1: {
            "title": "Despertar",
            "description": "Seu primeiro dia na Academia Tokugawa. Um novo mundo de possibilidades se abre diante de você.",
            "dialogues": [
                {"npc": "Diretor", "text": "Bem-vindo à Academia Tokugawa! Estamos felizes em receber mais um estudante com habilidades especiais."},
                {"npc": "Diretor", "text": "Aqui você aprenderá a controlar e aprimorar seus poderes, além de receber uma educação de primeira classe."},
                {"npc": "Diretor", "text": "Lembre-se: com grandes poderes, vêm grandes responsabilidades. Esperamos que você honre o nome da nossa academia."},
                {"npc": "Junie", "text": "Olá! Eu sou Junie, sua assistente virtual. Estou aqui para ajudar com qualquer dúvida que você tenha sobre a academia."},
                {"npc": "Junie", "text": "A Academia Tokugawa não é uma escola comum. Aqui, os estudantes são classificados em uma hierarquia baseada em seus poderes."},
                {"npc": "Junie", "text": "Os mais fortes ocupam posições de liderança, como Rei ou Rainha, Jack e Ás. Eles são responsáveis por manter a ordem."},
                {"npc": "Junie", "text": "Vamos começar com um tour pela escola? Temos vários clubes que você pode conhecer!"},
                {"npc": "Junie", "text": "Entendo que você queira saber mais sobre nossa hierarquia. É um sistema fascinante que define a vida social na academia."},
                {"npc": "Junie", "text": "No topo da hierarquia estão os Reis e Rainhas - estudantes de nível 5 com poderes extraordinários. Eles são respeitados e temidos por todos."},
                {"npc": "Junie", "text": "Logo abaixo estão os Jack e Ás - nível 4, a elite da academia, segundos apenas para o Rei/Rainha. Eles geralmente são os braços direitos dos líderes."},
                {"npc": "Junie", "text": "O nível 3 é composto pela Elite - estudantes com habilidades excepcionais que se destacam em suas áreas."},
                {"npc": "Junie", "text": "No nível 2 temos os estudantes Médio-Alto, com poderes acima da média, mas não excepcionais."},
                {"npc": "Junie", "text": "O nível 1 é formado pelos estudantes Médios, com poderes medianos que formam a maioria da população estudantil."},
                {"npc": "Junie", "text": "Por fim, no nível 0 estão os estudantes de Baixo nível, com poderes fracos ou sem poderes. Infelizmente, eles frequentemente enfrentam dificuldades sociais."},
                {"npc": "Junie", "text": "Sua posição na hierarquia será determinada por suas habilidades, conquistas e como você se relaciona com os outros estudantes."},
                {"npc": "Junie", "text": "Agora que você entende melhor nosso sistema, o que gostaria de fazer a seguir?"}
            ],
            "choices": [
                {"text": "Sim, vamos conhecer os clubes!", "next_dialogue": 7},
                {"text": "Prefiro explorar por conta própria.", "next_dialogue": 8},
                {"text": "Conte-me mais sobre essa hierarquia.", "next_dialogue": 9}
            ],
            "additional_choices": {
                9: [
                    {"text": "Agora vamos conhecer os clubes!", "next_dialogue": 7},
                    {"text": "Prefiro explorar por conta própria.", "next_dialogue": 8}
                ]
            },
            "completion_exp": 50,
            "completion_tusd": 100,
            "next_chapter": 2
        },
        2: {
            "title": "Seu Lugar na Hierarquia",
            "description": "Descubra onde você se encaixa na complexa hierarquia da Academia Tokugawa.",
            "dialogues": [
                {"npc": "Junie", "text": "Agora que você conhece um pouco da academia, é hora de determinar sua posição inicial na hierarquia."},
                {"npc": "Junie", "text": "Todos os novos estudantes passam por uma avaliação para determinar seu nível. Isso afetará como os outros estudantes te tratam."},
                {"npc": "Avaliador", "text": "Vamos ver o que você pode fazer. Não se preocupe, esta é apenas uma avaliação inicial. Sua posição pode mudar com o tempo."},
                {"npc": "Avaliador", "text": "Concentre-se e mostre seu poder. Não se contenha."}
            ],
            "choices": [
                {"text": "Usar todo seu poder", "next_dialogue": 4, "attribute_check": "power_stat", "threshold": 10},
                {"text": "Mostrar controle preciso", "next_dialogue": 5, "attribute_check": "intellect", "threshold": 10},
                {"text": "Demonstrar versatilidade", "next_dialogue": 6, "attribute_check": "dexterity", "threshold": 10}
            ],
            "hierarchy_placement": True,
            "completion_exp": 75,
            "completion_tusd": 150,
            "next_chapter": 3
        },
        3: {
            "title": "Registro no Clube",
            "description": "Escolha um clube para se juntar e conheça seu líder, descobrindo mais sobre a história deles.",
            "dialogues": [
                {"npc": "Junie", "text": "Agora é hora de escolher um clube! Cada clube tem seu próprio foco, atividades e história."},
                {"npc": "Junie", "text": "Os clubes não são apenas para treinamento, mas também formam alianças e rivalidades importantes na hierarquia da academia."},
                {"npc": "Junie", "text": "Você já está registrado no clube {club_name}. Vamos conhecer o líder do clube e sua história!"}
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
                    {"npc": "Kai Flameheart", "text": "Deixe-me contar um pouco sobre mim. Perdi meus pais quando era criança - eles eram heróis, sabe? Desde então, jurei me tornar forte o suficiente para proteger aqueles que amo."},
                    {"npc": "Kai Flameheart", "text": "Estamos sempre em rivalidade com os Elementalistas. Eles acham que são superiores com seu 'equilíbrio', mas quando o perigo chega, é o fogo puro que protege."}
                ],
                2: [  # Ilusionistas Mentais
                    {"npc": "Luna Mindweaver", "text": "Ah, uma nova mente para nossa coleção. Bem-vindo aos Ilusionistas Mentais."},
                    {"npc": "Luna Mindweaver", "text": "Aqui exploramos os recantos da mente e os limites da percepção. A realidade é apenas o que acreditamos que seja."},
                    {"npc": "Luna Mindweaver", "text": "Cresci isolada por causa dos meus poderes. Consigo ver os pensamentos dos outros desde criança - um dom e uma maldição. Esta academia foi o primeiro lugar onde me senti compreendida."},
                    {"npc": "Luna Mindweaver", "text": "Tenha cuidado com o Conselho Político. Eles sempre têm segundas intenções... não que nós não tenhamos também."}
                ],
                3: [  # Conselho Político
                    {"npc": "Alexander Strategos", "text": "Um novo peão no tabuleiro. Interessante. Bem-vindo ao Conselho Político."},
                    {"npc": "Alexander Strategos", "text": "Nosso clube controla a política estudantil da academia. Influência e estratégia são nossas armas."},
                    {"npc": "Alexander Strategos", "text": "Cresci nos bastidores do poder, observando meu pai manipular a política nacional. Aprendi cedo que o verdadeiro poder não está na força bruta, mas na capacidade de influenciar os outros."},
                    {"npc": "Alexander Strategos", "text": "Os Ilusionistas pensam que podem ler nossas mentes, mas sempre estamos três passos à frente. Lembre-se: nesta academia, informação é poder."}
                ],
                4: [  # Elementalistas
                    {"npc": "Gaia Naturae", "text": "A natureza te trouxe até nós. Seja bem-vindo aos Elementalistas."},
                    {"npc": "Gaia Naturae", "text": "Estudamos a harmonia dos elementos e como utilizá-los em equilíbrio com o mundo ao nosso redor."},
                    {"npc": "Gaia Naturae", "text": "Venho de uma comunidade isolada que venera os elementos. Quando meus poderes se manifestaram, fui enviada para cá para aprender sobre o mundo moderno, embora parte de mim ainda anseie pela simplicidade da minha vila."},
                    {"npc": "Gaia Naturae", "text": "O Clube das Chamas tem poder, mas falta-lhes controle e respeito pelos elementos. O verdadeiro domínio vem do equilíbrio, não da destruição."}
                ],
                5: [  # Clube de Combate
                    {"npc": "Ryuji Battleborn", "text": "Mais um guerreiro se junta às nossas fileiras. Mostre seu valor no Clube de Combate."},
                    {"npc": "Ryuji Battleborn", "text": "Aqui, aprimoramos nossas técnicas de luta e nos tornamos mais fortes a cada dia. A disciplina é nossa fundação."},
                    {"npc": "Ryuji Battleborn", "text": "Sou descendente de uma linhagem de guerreiros lendários. Meu pai nunca aceitou nada menos que a perfeição. Vim para a academia para provar meu valor e criar meu próprio legado."},
                    {"npc": "Ryuji Battleborn", "text": "Todos os outros clubes têm suas forças, mas no final, é o guerreiro mais forte que permanece de pé. Na hierarquia desta academia, respeitamos apenas aqueles que provam seu valor em combate."}
                ]
            },
            "completion_exp": 100,
            "completion_tusd": 200,
            "next_chapter": 4
        },
        3: {
            "title": "Rivalidades e Alianças",
            "description": "Descubra as complexas relações entre os clubes e como elas afetam a hierarquia da academia.",
            "dialogues": [
                {"npc": "Junie", "text": "Agora que você está estabelecido em seu clube, é hora de entender melhor as dinâmicas entre os diferentes grupos da academia."},
                {"npc": "Junie", "text": "As rivalidades e alianças entre clubes moldam a política da academia e podem afetar sua posição na hierarquia."},
                {"npc": "Junie", "text": "Cada clube tem seus aliados e rivais naturais. Conhecer essas relações pode ser crucial para sua sobrevivência social."},
                {"npc": "Estudante Veterano", "text": "Ei, novato! Já percebeu como funciona a coisa por aqui? Não é só sobre poder individual - é sobre quem você conhece e quem te apoia."}
            ],
            "choices": [
                {"text": "Perguntar sobre alianças secretas", "next_dialogue": 4, "attribute_check": "charisma", "threshold": 8},
                {"text": "Investigar rivalidades históricas", "next_dialogue": 5, "attribute_check": "intellect", "threshold": 8},
                {"text": "Oferecer-se para mediar conflitos", "next_dialogue": 6, "attribute_check": "charisma", "threshold": 10}
            ],
            "club_specific_dialogues": {
                1: [  # Clube das Chamas
                    {"npc": "Ember", "text": "Como membro do Clube das Chamas, você deve saber que os Elementalistas são nossos rivais históricos. Eles acham que seu 'equilíbrio' é superior à nossa intensidade."},
                    {"npc": "Ember", "text": "Por outro lado, temos uma boa relação com o Clube de Combate. Eles respeitam nossa força e paixão."},
                    {"npc": "Ember", "text": "Cuidado com os Ilusionistas Mentais e o Conselho Político - eles são mestres em manipulação e podem usar suas palavras contra você."}
                ],
                2: [  # Ilusionistas Mentais
                    {"npc": "Mirage", "text": "No mundo dos Ilusionistas, informação é poder. Temos olhos e ouvidos em todos os lugares."},
                    {"npc": "Mirage", "text": "Nossa maior rivalidade é com o Conselho Político - ambos lutamos pelo controle da informação, mas com métodos diferentes."},
                    {"npc": "Mirage", "text": "Mantemos uma aliança tácita com os Elementalistas. Eles valorizam o conhecimento tanto quanto nós."}
                ],
                3: [  # Conselho Político
                    {"npc": "Victoria", "text": "O Conselho Político tem conexões em todos os níveis da academia. Conhecemos os segredos que mantêm esta instituição funcionando."},
                    {"npc": "Victoria", "text": "Os Ilusionistas pensam que podem nos superar em nosso próprio jogo. Que ingenuidade."},
                    {"npc": "Victoria", "text": "Mantemos relações cordiais com o Clube das Chamas - sua força bruta é útil quando a diplomacia falha."}
                ],
                4: [  # Elementalistas
                    {"npc": "Aero", "text": "Os Elementalistas buscam harmonia, mas isso não significa que não temos rivais. O Clube das Chamas representa tudo o que rejeitamos - poder sem controle."},
                    {"npc": "Aero", "text": "Temos afinidade com os Ilusionistas Mentais. Ambos valorizamos o conhecimento e a compreensão profunda."},
                    {"npc": "Aero", "text": "O Clube de Combate? Respeitamos sua disciplina, mas seus métodos são muito diretos para nosso gosto."}
                ],
                5: [  # Clube de Combate
                    {"npc": "Fist", "text": "No Clube de Combate, respeitamos a força acima de tudo. O Clube das Chamas compartilha dessa filosofia."},
                    {"npc": "Fist", "text": "Não confiamos nos manipuladores do Conselho Político e dos Ilusionistas. Preferimos resolver as coisas diretamente."},
                    {"npc": "Fist", "text": "Os Elementalistas têm poder, mas falta-lhes a determinação para usá-lo quando necessário."}
                ]
            },
            "completion_exp": 125,
            "completion_tusd": 250,
            "next_chapter": 4
        },
        4: {
            "title": "O Segredo da Biblioteca",
            "description": "Descubra um segredo oculto na biblioteca da academia que pode mudar sua compreensão sobre os poderes.",
            "dialogues": [
                {"npc": "Junie", "text": "A biblioteca da Academia Tokugawa contém conhecimentos acumulados por séculos sobre usuários de poderes."},
                {"npc": "Junie", "text": "Recentemente, ouvi rumores sobre uma seção restrita que contém informações sobre a origem dos poderes."},
                {"npc": "Bibliotecária", "text": "Bem-vindo à biblioteca. Sinta-se à vontade para explorar as estantes, mas lembre-se: alguns conhecimentos são restritos aos estudantes de níveis mais altos."},
                {"npc": "Estudante Misterioso", "text": "Psst! Você parece curioso. Já ouviu falar da Biblioteca Proibida? Dizem que contém segredos sobre a verdadeira natureza dos nossos poderes..."}
            ],
            "choices": [
                {"text": "Pedir permissão para acessar a seção restrita", "next_dialogue": 4, "attribute_check": "charisma", "threshold": 12},
                {"text": "Procurar uma entrada secreta", "next_dialogue": 5, "attribute_check": "dexterity", "threshold": 10},
                {"text": "Pesquisar nos arquivos normais por pistas", "next_dialogue": 6, "attribute_check": "intellect", "threshold": 10}
            ],
            "hidden_secret_discovery": "Biblioteca Proibida",
            "completion_exp": 150,
            "completion_tusd": 300,
            "next_chapter": 5
        },
        5: {
            "title": "O Primeiro Desafio",
            "description": "Enfrente seu primeiro grande desafio na academia: um estudante valentão que está intimidando os calouros.",
            "dialogues": [
                {"npc": "Estudante Assustado", "text": "P-por favor, você precisa ajudar! Drake está aterrorizando os calouros de novo!"},
                {"npc": "Junie", "text": "Drake é um estudante do terceiro ano conhecido por intimidar os mais fracos para subir na hierarquia."},
                {"npc": "Junie", "text": "Este pode ser um bom momento para você provar seu valor na academia."},
                {"npc": "Drake", "text": "Olha só, mais um novato querendo bancar o herói? Vamos ver do que você é feito!"}
            ],
            "choices": [
                {"text": "Enfrentar Drake diretamente", "next_dialogue": 4, "attribute_check": "power_stat", "threshold": 12},
                {"text": "Usar estratégia e inteligência", "next_dialogue": 5, "attribute_check": "intellect", "threshold": 12},
                {"text": "Tentar resolver diplomaticamente", "next_dialogue": 6, "attribute_check": "charisma", "threshold": 15}
            ],
            "battle": {
                "opponent": "Drake, o Valentão",
                "power_level": 15,
                "rewards": {
                    "victory": {"exp": 200, "tusd": 400, "hierarchy_points": 2},
                    "defeat": {"exp": 50, "tusd": 100}
                }
            },
            "completion_exp": 175,
            "completion_tusd": 350,
            "next_chapter": 6
        }
    }
}

# Function to integrate the enhanced story mode with the existing system
def enhance_story_mode(original_chapters):
    """
    Enhances the original story chapters with the new content.
    This function will be called to merge the enhanced content with the existing structure.
    """
    enhanced_chapters = original_chapters.copy()

    # Update Year 1 chapters with enhanced content
    for year, chapters in ENHANCED_STORY_CHAPTERS.items():
        if year not in enhanced_chapters:
            enhanced_chapters[year] = {}

        for chapter_num, chapter_data in chapters.items():
            enhanced_chapters[year][chapter_num] = chapter_data

    return enhanced_chapters

# This function will be imported and used in the main story_mode.py file
def get_character_background(character_name):
    """
    Returns the background story for a specific character.
    """
    return CHARACTER_BACKGROUNDS.get(character_name, {})

def get_hierarchy_tier(level):
    """
    Returns the hierarchy tier information based on power level.
    """
    return HIERARCHY_TIERS.get(level, HIERARCHY_TIERS[0])

def get_hidden_secret(secret_name):
    """
    Returns information about a hidden secret location.
    """
    return HIDDEN_SECRETS.get(secret_name, {})

def get_climactic_event(event_name):
    """
    Returns information about a climactic event.
    """
    return CLIMACTIC_EVENTS.get(event_name, {})

def get_story_arc(year):
    """
    Returns information about a story arc for a specific year.
    """
    return STORY_ARCS.get(f"Ano {year}", {})
