import discord
from discord.ext import commands
from discord import app_commands
import logging
import random
import asyncio
import json
import os
from datetime import datetime
from utils.db_provider import get_player, update_player, get_club, store_cooldown
from utils.embeds import create_basic_embed
from utils.game_mechanics import RARITIES
from src.bot.cogs.activities import COOLDOWNS, COOLDOWN_DURATIONS

logger = logging.getLogger('tokugawa_bot')

# Load JSON data
def load_json(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading JSON file {file_path}: {e}")
        return {}

# Load all economy data from JSON files
ITEM_CATEGORIES = load_json('data/economy/item_categories.json')
ITEM_TYPES = load_json('data/economy/item_types.json')
SEASONS = load_json('data/economy/seasons.json')
ALTERNATIVE_CURRENCIES = load_json('data/economy/alternative_currencies.json')

# Load more economy data from JSON files
SPECIAL_CURRENCY_ITEMS = load_json('data/economy/special_currency_items.json')
ITEM_EXCHANGES = load_json('data/economy/item_exchanges.json')

# Load items from new category-based structure
TRAINING_ITEMS = load_json('data/economy/items/training_items.json')
COMBAT_ITEMS = load_json('data/economy/items/combat_items.json')
ENERGY_ITEMS = load_json('data/economy/items/energy_items.json')
ATTRIBUTE_ITEMS = load_json('data/economy/items/attribute_items.json')
SOCIAL_ITEMS = load_json('data/economy/items/social_items.json')

# Itens sazonais (baseados na estação/bimestre)
SEASONAL_ITEMS = load_json('data/economy/seasonal_items.json')

# Itens de eventos especiais (desbloqueados por eventos específicos)
EVENT_ITEMS = load_json('data/economy/event_items.json')

# Itens lendários (desbloqueados por progresso avançado ou eventos especiais)
LEGENDARY_ITEMS = load_json('data/economy/legendary_items.json')

# Itens temáticos de clubes (disponíveis apenas para membros de clubes específicos)
CLUB_ITEMS = load_json('data/economy/club_items.json')

# Função para obter os itens disponíveis com base no bimestre atual, eventos ativos, nível do jogador e clube
def get_available_shop_items(bimestre=1, active_events=None, player_level=1, player_club=None, current_date=None):
    """
    Retorna os itens disponíveis na loja com base no bimestre atual, eventos ativos, nível do jogador e clube.

    Args:
        bimestre (int): O bimestre atual (1-4)
        active_events (list): Lista de eventos ativos
        player_level (int): Nível atual do jogador
        player_club (str): Clube do jogador
        current_date (datetime): Data atual para rotação de itens

    Returns:
        dict: Dicionário com categorias de itens disponíveis na loja
    """
    if active_events is None:
        active_events = []

    if current_date is None:
        current_date = datetime.now()

    # Inicializa o dicionário de itens por categoria
    available_items = {
        "consumable": [],
        "accessory": [],
        "equipment": [],
        "legendary": [],
        "thematic": []
    }

    # Adiciona itens de treinamento
    for item in TRAINING_ITEMS:
        item_type = item.get("type", "consumable")
        if item_type in available_items:
            available_items[item_type].append(item)

    # Adiciona itens de combate
    for item in COMBAT_ITEMS:
        item_type = item.get("type", "consumable")
        if item_type in available_items:
            available_items[item_type].append(item)

    # Adiciona itens de energia
    for item in ENERGY_ITEMS:
        item_type = item.get("type", "consumable")
        if item_type in available_items:
            available_items[item_type].append(item)

    # Adiciona itens de atributo
    for item in ATTRIBUTE_ITEMS:
        item_type = item.get("type", "consumable")
        if item_type in available_items:
            available_items[item_type].append(item)

    # Adiciona itens sociais
    for item in SOCIAL_ITEMS:
        item_type = item.get("type", "consumable")
        if item_type in available_items:
            available_items[item_type].append(item)

    # Adiciona itens sazonais com base no bimestre atual
    season = SEASONS.get(bimestre, "spring")
    if season in SEASONAL_ITEMS:
        for item in SEASONAL_ITEMS[season]:
            item_type = item.get("type", "consumable")
            if item_type in available_items:
                available_items[item_type].append(item)

    # Adiciona itens de eventos ativos
    for event in active_events:
        if event in EVENT_ITEMS:
            for item in EVENT_ITEMS[event]:
                item_type = item.get("type", "consumable")
                if item_type in available_items:
                    available_items[item_type].append(item)

    # Adiciona itens lendários com base no nível do jogador
    for item in LEGENDARY_ITEMS:
        if player_level >= item.get("level_required", 1):
            available_items["legendary"].append(item)

    # Adiciona itens temáticos de clube se o jogador pertencer a um clube
    if player_club and player_club in CLUB_ITEMS:
        for item in CLUB_ITEMS[player_club]:
            item_type = item.get("type", "consumable")
            if item_type in available_items:
                available_items["thematic"].append(item)

    return available_items

# Lista de itens da loja (para compatibilidade com código existente)
SHOP_ITEMS = []
SHOP_ITEMS.extend(TRAINING_ITEMS)
SHOP_ITEMS.extend(COMBAT_ITEMS)
SHOP_ITEMS.extend(ENERGY_ITEMS)
SHOP_ITEMS.extend(ATTRIBUTE_ITEMS)
SHOP_ITEMS.extend(SOCIAL_ITEMS)

# Categorias de técnicas
TECHNIQUE_CATEGORIES = {
    "attack": "Ataque",
    "defense": "Defesa",
    "support": "Suporte",
    "tactical": "Tática Especial"
}

# Níveis de técnicas
TECHNIQUE_TIERS = {
    "basic": "Básica",
    "advanced": "Avançada",
    "exclusive": "Exclusiva",
    "master": "Mestre"
}

# Sistema de técnicas expandido
TECHNIQUES = [
    # Técnicas Básicas (disponíveis para todos no início)
    {
        "id": 1,
        "name": "Golpe Relâmpago",
        "description": "Um ataque rápido que surpreende o oponente. +30% de chance de vencer duelos físicos.",
        "type": "physical",
        "category": "attack",
        "tier": "basic",
        "level": 1,
        "max_level": 3,
        "club_required": None,
        "effects": {"duel_boost": {"type": "physical", "amount": 0.3}},
        "evolution": {
            "2": {"name": "Golpe Relâmpago Aprimorado", "description": "Um ataque rápido com maior precisão. +35% de chance de vencer duelos físicos.", "effects": {"duel_boost": {"type": "physical", "amount": 0.35}}},
            "3": {"name": "Golpe Relâmpago Supremo", "description": "Um ataque rápido com precisão mortal. +40% de chance de vencer duelos físicos e 10% de dano adicional.", "effects": {"duel_boost": {"type": "physical", "amount": 0.4}, "damage_boost": 0.1}}
        }
    },
    {
        "id": 2,
        "name": "Manipulação Mental",
        "description": "Confunde a mente do oponente. +30% de chance de vencer duelos mentais.",
        "type": "mental",
        "category": "attack",
        "tier": "basic",
        "level": 1,
        "max_level": 3,
        "club_required": None,
        "effects": {"duel_boost": {"type": "mental", "amount": 0.3}},
        "evolution": {
            "2": {"name": "Manipulação Mental Aprimorada", "description": "Confunde a mente do oponente com maior eficácia. +35% de chance de vencer duelos mentais.", "effects": {"duel_boost": {"type": "mental", "amount": 0.35}}},
            "3": {"name": "Manipulação Mental Suprema", "description": "Domina completamente a mente do oponente. +40% de chance de vencer duelos mentais e 15% de chance de confundir o oponente por 1 turno.", "effects": {"duel_boost": {"type": "mental", "amount": 0.4}, "confusion_chance": 0.15}}
        }
    },
    {
        "id": 3,
        "name": "Estratégia Básica",
        "description": "Planeja alguns passos à frente. +30% de chance de vencer duelos estratégicos.",
        "type": "strategic",
        "category": "tactical",
        "tier": "basic",
        "level": 1,
        "max_level": 3,
        "club_required": None,
        "effects": {"duel_boost": {"type": "strategic", "amount": 0.3}},
        "evolution": {
            "2": {"name": "Estratégia Intermediária", "description": "Planeja vários passos à frente. +35% de chance de vencer duelos estratégicos.", "effects": {"duel_boost": {"type": "strategic", "amount": 0.35}}},
            "3": {"name": "Estratégia Mestre", "description": "Planeja todo o duelo antecipadamente. +40% de chance de vencer duelos estratégicos e 20% de chance de prever o próximo movimento do oponente.", "effects": {"duel_boost": {"type": "strategic", "amount": 0.4}, "prediction_chance": 0.2}}
        }
    },
    {
        "id": 4,
        "name": "Charme Básico",
        "description": "Encanta com palavras simples. +30% de chance de vencer duelos sociais.",
        "type": "social",
        "category": "support",
        "tier": "basic",
        "level": 1,
        "max_level": 3,
        "club_required": None,
        "effects": {"duel_boost": {"type": "social", "amount": 0.3}},
        "evolution": {
            "2": {"name": "Charme Intermediário", "description": "Encanta com palavras elaboradas. +35% de chance de vencer duelos sociais.", "effects": {"duel_boost": {"type": "social", "amount": 0.35}}},
            "3": {"name": "Charme Irresistível", "description": "Encanta qualquer um com palavras doces. +40% de chance de vencer duelos sociais e 10% de chance de ganhar um aliado temporário.", "effects": {"duel_boost": {"type": "social", "amount": 0.4}, "ally_chance": 0.1}}
        }
    },
    {
        "id": 5,
        "name": "Escudo Básico",
        "description": "Cria uma barreira simples que absorve parte do dano. Reduz o dano recebido em 15%.",
        "type": "all",
        "category": "defense",
        "tier": "basic",
        "level": 1,
        "max_level": 3,
        "club_required": None,
        "effects": {"damage_reduction": 0.15},
        "evolution": {
            "2": {"name": "Escudo Intermediário", "description": "Cria uma barreira mais resistente. Reduz o dano recebido em 25%.", "effects": {"damage_reduction": 0.25}},
            "3": {"name": "Escudo Avançado", "description": "Cria uma barreira quase impenetrável. Reduz o dano recebido em 35% e tem 10% de chance de refletir parte do dano.", "effects": {"damage_reduction": 0.35, "reflect_chance": 0.1}}
        }
    },

    # Técnicas Avançadas (desbloqueadas por progressão)
    {
        "id": 6,
        "name": "Punho de Aço",
        "description": "Fortalece os punhos para um impacto devastador. +35% de chance de vencer duelos físicos.",
        "type": "physical",
        "category": "attack",
        "tier": "advanced",
        "level": 1,
        "max_level": 3,
        "club_required": None,
        "unlock_requirement": {"level": 5},
        "effects": {"duel_boost": {"type": "physical", "amount": 0.35}},
        "evolution": {
            "2": {"name": "Punho de Titânio", "description": "Fortalece os punhos com a dureza do titânio. +40% de chance de vencer duelos físicos e 15% de dano adicional.", "effects": {"duel_boost": {"type": "physical", "amount": 0.4}, "damage_boost": 0.15}},
            "3": {"name": "Punho Devastador", "description": "Fortalece os punhos com poder inimaginável. +45% de chance de vencer duelos físicos, 25% de dano adicional e 10% de chance de atordoar o oponente.", "effects": {"duel_boost": {"type": "physical", "amount": 0.45}, "damage_boost": 0.25, "stun_chance": 0.1}}
        }
    },
    {
        "id": 7,
        "name": "Barreira Mental",
        "description": "Cria uma barreira que protege contra ataques mentais. +35% de chance de vencer duelos mentais.",
        "type": "mental",
        "category": "defense",
        "tier": "advanced",
        "level": 1,
        "max_level": 3,
        "club_required": None,
        "unlock_requirement": {"level": 5},
        "effects": {"duel_boost": {"type": "mental", "amount": 0.35}},
        "evolution": {
            "2": {"name": "Barreira Mental Reforçada", "description": "Cria uma barreira mental quase impenetrável. +40% de chance de vencer duelos mentais e 20% de redução de dano mental.", "effects": {"duel_boost": {"type": "mental", "amount": 0.4}, "mental_damage_reduction": 0.2}},
            "3": {"name": "Fortaleza Mental", "description": "Cria uma fortaleza mental inexpugnável. +45% de chance de vencer duelos mentais, 30% de redução de dano mental e 15% de chance de refletir ataques mentais.", "effects": {"duel_boost": {"type": "mental", "amount": 0.45}, "mental_damage_reduction": 0.3, "mental_reflect_chance": 0.15}}
        }
    },
    {
        "id": 8,
        "name": "Tática Avançada",
        "description": "Utiliza táticas de guerra avançadas. +35% de chance de vencer duelos estratégicos.",
        "type": "strategic",
        "category": "tactical",
        "tier": "advanced",
        "level": 1,
        "max_level": 3,
        "club_required": None,
        "unlock_requirement": {"level": 5},
        "effects": {"duel_boost": {"type": "strategic", "amount": 0.35}},
        "evolution": {
            "2": {"name": "Tática de Guerra", "description": "Utiliza táticas de guerra complexas. +40% de chance de vencer duelos estratégicos e 15% de chance de prever movimentos do oponente.", "effects": {"duel_boost": {"type": "strategic", "amount": 0.4}, "prediction_chance": 0.15}},
            "3": {"name": "Tática Suprema", "description": "Domina completamente o campo de batalha. +45% de chance de vencer duelos estratégicos, 25% de chance de prever movimentos e 10% de chance de contra-atacar automaticamente.", "effects": {"duel_boost": {"type": "strategic", "amount": 0.45}, "prediction_chance": 0.25, "counter_chance": 0.1}}
        }
    },
    {
        "id": 9,
        "name": "Persuasão Avançada",
        "description": "Técnica de persuasão que influencia a vontade dos outros. +35% de chance de vencer duelos sociais.",
        "type": "social",
        "category": "support",
        "tier": "advanced",
        "level": 1,
        "max_level": 3,
        "club_required": None,
        "unlock_requirement": {"level": 5},
        "effects": {"duel_boost": {"type": "social", "amount": 0.35}},
        "evolution": {
            "2": {"name": "Persuasão Carismática", "description": "Técnica de persuasão que atrai seguidores. +40% de chance de vencer duelos sociais e 15% de chance de ganhar um aliado temporário.", "effects": {"duel_boost": {"type": "social", "amount": 0.4}, "ally_chance": 0.15}},
            "3": {"name": "Persuasão Suprema", "description": "Técnica de persuasão que dobra a vontade dos outros. +45% de chance de vencer duelos sociais, 25% de chance de ganhar um aliado e 10% de chance de converter um inimigo.", "effects": {"duel_boost": {"type": "social", "amount": 0.45}, "ally_chance": 0.25, "convert_chance": 0.1}}
        }
    },
    {
        "id": 10,
        "name": "Concentração Focada",
        "description": "Foca sua energia em um objetivo. +25% de chance de vencer qualquer tipo de duelo.",
        "type": "all",
        "category": "support",
        "tier": "advanced",
        "level": 1,
        "max_level": 3,
        "club_required": None,
        "unlock_requirement": {"level": 10},
        "effects": {"duel_boost": {"type": "all", "amount": 0.25}},
        "evolution": {
            "2": {"name": "Concentração Intensa", "description": "Foca intensamente sua energia. +30% de chance de vencer qualquer tipo de duelo e +10% de precisão.", "effects": {"duel_boost": {"type": "all", "amount": 0.3}, "accuracy_boost": 0.1}},
            "3": {"name": "Concentração Total", "description": "Foca toda sua energia em um único objetivo. +35% de chance de vencer qualquer tipo de duelo, +20% de precisão e +10% de chance crítica.", "effects": {"duel_boost": {"type": "all", "amount": 0.35}, "accuracy_boost": 0.2, "critical_chance": 0.1}}
        }
    },

    # Técnicas Exclusivas de Clubes
    {
        "id": 11,
        "name": "Técnica do Dragão",
        "description": "Técnica ancestral que canaliza a força de um dragão. +40% de chance de vencer duelos físicos.",
        "type": "physical",
        "category": "attack",
        "tier": "exclusive",
        "level": 1,
        "max_level": 3,
        "club_required": "Clube das Chamas",
        "effects": {"duel_boost": {"type": "physical", "amount": 0.4}},
        "evolution": {
            "2": {"name": "Fúria do Dragão", "description": "Libera a fúria de um dragão ancestral. +45% de chance de vencer duelos físicos e 20% de dano adicional de fogo.", "effects": {"duel_boost": {"type": "physical", "amount": 0.45}, "fire_damage": 0.2}},
            "3": {"name": "Rugido do Dragão Celestial", "description": "Invoca o poder de um dragão celestial. +50% de chance de vencer duelos físicos, 30% de dano adicional de fogo e 15% de chance de queimar o oponente.", "effects": {"duel_boost": {"type": "physical", "amount": 0.5}, "fire_damage": 0.3, "burn_chance": 0.15}}
        }
    },
    {
        "id": 12,
        "name": "Ilusão Básica",
        "description": "Cria ilusões simples que confundem o oponente. +40% de chance de vencer duelos mentais.",
        "type": "mental",
        "category": "tactical",
        "tier": "exclusive",
        "level": 1,
        "max_level": 3,
        "club_required": "Ilusionistas Mentais",
        "effects": {"duel_boost": {"type": "mental", "amount": 0.4}},
        "evolution": {
            "2": {"name": "Ilusão Complexa", "description": "Cria ilusões complexas que desorientam o oponente. +45% de chance de vencer duelos mentais e 20% de chance de confundir o oponente.", "effects": {"duel_boost": {"type": "mental", "amount": 0.45}, "confusion_chance": 0.2}},
            "3": {"name": "Ilusão Suprema", "description": "Cria ilusões tão reais que confundem até os mais perspicazes. +50% de chance de vencer duelos mentais, 30% de chance de confundir o oponente e 15% de chance de fazê-lo atacar a si mesmo.", "effects": {"duel_boost": {"type": "mental", "amount": 0.5}, "confusion_chance": 0.3, "self_attack_chance": 0.15}}
        }
    },
    {
        "id": 13,
        "name": "Xadrez Tático",
        "description": "Visualiza o duelo como um jogo de xadrez. +40% de chance de vencer duelos estratégicos.",
        "type": "strategic",
        "category": "tactical",
        "tier": "exclusive",
        "level": 1,
        "max_level": 3,
        "club_required": "Conselho Estratégico",
        "effects": {"duel_boost": {"type": "strategic", "amount": 0.4}},
        "evolution": {
            "2": {"name": "Xadrez Tridimensional", "description": "Visualiza o duelo como um jogo de xadrez em múltiplas dimensões. +45% de chance de vencer duelos estratégicos e 20% de chance de prever movimentos do oponente.", "effects": {"duel_boost": {"type": "strategic", "amount": 0.45}, "prediction_chance": 0.2}},
            "3": {"name": "Xadrez Dimensional", "description": "Visualiza o duelo como um jogo de xadrez multidimensional. +50% de chance de vencer duelos estratégicos, 30% de chance de prever movimentos e 15% de chance de manipular o campo de batalha.", "effects": {"duel_boost": {"type": "strategic", "amount": 0.5}, "prediction_chance": 0.3, "field_manipulation": 0.15}}
        }
    },
    {
        "id": 14,
        "name": "Oratória Básica",
        "description": "Utiliza técnicas de oratória para influenciar os outros. +40% de chance de vencer duelos sociais.",
        "type": "social",
        "category": "support",
        "tier": "exclusive",
        "level": 1,
        "max_level": 3,
        "club_required": "Conselho Político",
        "effects": {"duel_boost": {"type": "social", "amount": 0.4}},
        "evolution": {
            "2": {"name": "Oratória Avançada", "description": "Domina técnicas avançadas de oratória. +45% de chance de vencer duelos sociais e 20% de chance de ganhar aliados.", "effects": {"duel_boost": {"type": "social", "amount": 0.45}, "ally_chance": 0.2}},
            "3": {"name": "Oratória Letal", "description": "Domina completamente a arte da oratória. +50% de chance de vencer duelos sociais, 30% de chance de ganhar aliados e 15% de chance de diminuir a moral do oponente.", "effects": {"duel_boost": {"type": "social", "amount": 0.5}, "ally_chance": 0.3, "morale_reduction": 0.15}}
        }
    },
    {
        "id": 15,
        "name": "Despertar Básico",
        "description": "Desperta parte do potencial oculto dentro de si. +30% de chance de vencer qualquer tipo de duelo.",
        "type": "all",
        "category": "support",
        "tier": "exclusive",
        "level": 1,
        "max_level": 3,
        "club_required": "Academia Principal",
        "effects": {"duel_boost": {"type": "all", "amount": 0.3}},
        "evolution": {
            "2": {"name": "Despertar Avançado", "description": "Desperta grande parte do potencial oculto. +35% de chance de vencer qualquer tipo de duelo e +15% em todos os atributos.", "effects": {"duel_boost": {"type": "all", "amount": 0.35}, "attribute_boost_all": 0.15}},
            "3": {"name": "Despertar Interior", "description": "Desperta todo o potencial oculto dentro de si. +40% de chance de vencer qualquer tipo de duelo, +25% em todos os atributos e +10% de chance de ação extra.", "effects": {"duel_boost": {"type": "all", "amount": 0.4}, "attribute_boost_all": 0.25, "extra_action_chance": 0.1}}
        }
    },

    # Técnicas Especiais Sazonais
    {
        "id": 16,
        "name": "Aura Primaveril",
        "description": "Canaliza a energia da primavera. +30% de chance de vencer duelos sociais e +15% de carisma.",
        "type": "social",
        "category": "support",
        "tier": "exclusive",
        "level": 1,
        "max_level": 3,
        "seasonal": "spring",
        "effects": {"duel_boost": {"type": "social", "amount": 0.3}, "attribute_boost": {"charisma": 0.15}},
        "evolution": {
            "2": {"name": "Florescimento", "description": "Floresce como as cerejeiras na primavera. +35% de chance de vencer duelos sociais, +20% de carisma e +10% de regeneração.", "effects": {"duel_boost": {"type": "social", "amount": 0.35}, "attribute_boost": {"charisma": 0.2}, "regeneration": 0.1}},
            "3": {"name": "Renascimento Primaveril", "description": "Renova-se completamente como a natureza na primavera. +40% de chance de vencer duelos sociais, +25% de carisma, +15% de regeneração e +10% de chance de inspirar aliados.", "effects": {"duel_boost": {"type": "social", "amount": 0.4}, "attribute_boost": {"charisma": 0.25}, "regeneration": 0.15, "inspire_chance": 0.1}}
        }
    },
    {
        "id": 17,
        "name": "Calor Estival",
        "description": "Canaliza o calor do verão. +30% de chance de vencer duelos físicos e +15% de dano adicional.",
        "type": "physical",
        "category": "attack",
        "tier": "exclusive",
        "level": 1,
        "max_level": 3,
        "seasonal": "summer",
        "effects": {"duel_boost": {"type": "physical", "amount": 0.3}, "damage_boost": 0.15},
        "evolution": {
            "2": {"name": "Fúria Solar", "description": "Canaliza a fúria do sol do verão. +35% de chance de vencer duelos físicos, +20% de dano adicional e +10% de velocidade.", "effects": {"duel_boost": {"type": "physical", "amount": 0.35}, "damage_boost": 0.2, "speed_boost": 0.1}},
            "3": {"name": "Sol Escaldante", "description": "Libera o poder máximo do sol do verão. +40% de chance de vencer duelos físicos, +25% de dano adicional, +15% de velocidade e +10% de chance de queimar o oponente.", "effects": {"duel_boost": {"type": "physical", "amount": 0.4}, "damage_boost": 0.25, "speed_boost": 0.15, "burn_chance": 0.1}}
        }
    },
    {
        "id": 18,
        "name": "Reflexão Outonal",
        "description": "Canaliza a introspecção do outono. +30% de chance de vencer duelos mentais e +15% de intelecto.",
        "type": "mental",
        "category": "tactical",
        "tier": "exclusive",
        "level": 1,
        "max_level": 3,
        "seasonal": "autumn",
        "effects": {"duel_boost": {"type": "mental", "amount": 0.3}, "attribute_boost": {"intellect": 0.15}},
        "evolution": {
            "2": {"name": "Sabedoria Outonal", "description": "Absorve a sabedoria das folhas que caem no outono. +35% de chance de vencer duelos mentais, +20% de intelecto e +10% de resistência mental.", "effects": {"duel_boost": {"type": "mental", "amount": 0.35}, "attribute_boost": {"intellect": 0.2}, "mental_resistance": 0.1}},
            "3": {"name": "Pilares Antigos", "description": "Conecta-se com a sabedoria ancestral do outono. +40% de chance de vencer duelos mentais, +25% de intelecto, +15% de resistência mental e +10% de chance de encontrar artefatos raros.", "effects": {"duel_boost": {"type": "mental", "amount": 0.4}, "attribute_boost": {"intellect": 0.25}, "mental_resistance": 0.15, "artifact_find_chance": 0.1}}
        }
    },
    {
        "id": 19,
        "name": "Gélido Invernal",
        "description": "Canaliza o frio do inverno. +30% de chance de vencer duelos estratégicos e +15% de defesa.",
        "type": "strategic",
        "category": "defense",
        "tier": "exclusive",
        "level": 1,
        "max_level": 3,
        "seasonal": "winter",
        "effects": {"duel_boost": {"type": "strategic", "amount": 0.3}, "defense_boost": 0.15},
        "evolution": {
            "2": {"name": "Tempestade de Neve", "description": "Invoca uma tempestade de neve que confunde os inimigos. +35% de chance de vencer duelos estratégicos, +20% de defesa e +10% de chance de congelar o oponente.", "effects": {"duel_boost": {"type": "strategic", "amount": 0.35}, "defense_boost": 0.2, "freeze_chance": 0.1}},
            "3": {"name": "Presença Fantasmal", "description": "Torna-se como um fantasma na névoa do inverno. +40% de chance de vencer duelos estratégicos, +25% de defesa, +15% de chance de congelar o oponente e +10% de furtividade.", "effects": {"duel_boost": {"type": "strategic", "amount": 0.4}, "defense_boost": 0.25, "freeze_chance": 0.15, "stealth": 0.1}}
        }
    },
    {
        "id": 20,
        "name": "Harmonia Elemental",
        "description": "Harmoniza as energias das quatro estações. +25% de chance de vencer qualquer tipo de duelo e +10% em todos os atributos.",
        "type": "all",
        "category": "support",
        "tier": "master",
        "level": 1,
        "max_level": 3,
        "unlock_requirement": {"level": 20, "techniques_mastered": 4},
        "effects": {"duel_boost": {"type": "all", "amount": 0.25}, "attribute_boost_all": 0.1},
        "evolution": {
            "2": {"name": "Equilíbrio Cósmico", "description": "Alcança o equilíbrio perfeito entre as energias cósmicas. +30% de chance de vencer qualquer tipo de duelo, +15% em todos os atributos e +10% de resistência a todos os elementos.", "effects": {"duel_boost": {"type": "all", "amount": 0.3}, "attribute_boost_all": 0.15, "elemental_resistance": 0.1}},
            "3": {"name": "Transcendência", "description": "Transcende as limitações mortais. +35% de chance de vencer qualquer tipo de duelo, +20% em todos os atributos, +15% de resistência a todos os elementos e +10% de chance de ação extra.", "effects": {"duel_boost": {"type": "all", "amount": 0.35}, "attribute_boost_all": 0.2, "elemental_resistance": 0.15, "extra_action_chance": 0.1}}
        }
    }
]

class Economy(commands.Cog):
    """Cog for economy and shop commands."""

    def __init__(self, bot):
        self.bot = bot
        self.market_listings = {}  # {listing_id: {seller_id, item_id, price, item_data}}
        self.next_listing_id = 1
        self.exchange_cooldowns = {}  # {user_id: timestamp}

    def _check_cooldown(self, user_id, command):
        """Check if a command is on cooldown for a user."""
        now = datetime.now().timestamp()

        # Initialize user cooldowns if not exists
        if user_id not in COOLDOWNS:
            COOLDOWNS[user_id] = {}

        # Check if command is on cooldown
        if command in COOLDOWNS[user_id] and COOLDOWNS[user_id][command] > now:
            # Calculate remaining time
            remaining = COOLDOWNS[user_id][command] - now
            minutes, seconds = divmod(int(remaining), 60)
            hours, minutes = divmod(minutes, 60)

            if hours > 0:
                time_str = f"{hours}h {minutes}m {seconds}s"
            elif minutes > 0:
                time_str = f"{minutes}m {seconds}s"
            else:
                time_str = f"{seconds}s"

            return time_str

        return None

    def _set_cooldown(self, user_id, command, custom_duration=None):
        """Set a cooldown for a command for a user.

        Args:
            user_id: The user ID
            command: The command name
            custom_duration: Optional custom duration in seconds. If not provided, uses the default duration.
        """
        if user_id not in COOLDOWNS:
            COOLDOWNS[user_id] = {}

        duration = custom_duration if custom_duration is not None else COOLDOWN_DURATIONS.get(command, 3600)  # Default 1 hour
        expiry_time = datetime.now().timestamp() + duration
        COOLDOWNS[user_id][command] = expiry_time

        # Store cooldown in database
        try:
            store_cooldown(user_id, command, expiry_time)
        except Exception as e:
            logger.error(f"Error storing cooldown in database: {e}")

    # Group for economy commands
    economy_group = app_commands.Group(name="economia", description="Comandos de economia da Academia Tokugawa")

    # Group for technique commands
    technique_group = app_commands.Group(name="tecnica", description="Comandos relacionados às técnicas da Academia Tokugawa")

    @technique_group.command(name="evoluir", description="Evoluir uma técnica para o próximo nível")
    async def slash_evolve_technique(self, interaction: discord.Interaction, technique_id: int):
        """Evolui uma técnica para o próximo nível."""
        # Check if player exists
        player = get_player(interaction.user.id)
        if not player:
            await interaction.response.send_message(f"{interaction.user.mention}, você ainda não está registrado na Academia Tokugawa. Use /registro ingressar para criar seu personagem.", ephemeral=True)
            return

        # Check if player has the technique
        techniques = player["techniques"]
        if str(technique_id) not in techniques:
            await interaction.response.send_message(f"{interaction.user.mention}, você não possui esta técnica. Use `/tecnica listar` para ver suas técnicas.", ephemeral=True)
            return

        # Get the technique from player's techniques
        player_technique = techniques[str(technique_id)]

        # Get the full technique data from TECHNIQUES
        full_technique = next((t for t in TECHNIQUES if t["id"] == technique_id), None)
        if not full_technique:
            await interaction.response.send_message(f"{interaction.user.mention}, técnica não encontrada no sistema.")
            return

        # Check if technique can be evolved
        current_level = player_technique.get("level", 1)
        max_level = full_technique.get("max_level", 3)

        if current_level >= max_level:
            await interaction.response.send_message(f"{interaction.user.mention}, a técnica **{player_technique['name']}** já está no nível máximo ({current_level}/{max_level}).")
            return

        # Check evolution requirements
        # For now, we'll just require some TUSD and experience points
        evolution_cost = {
            1: 500,  # Level 1 to 2
            2: 1000,  # Level 2 to 3
        }

        exp_requirement = {
            1: 1000,  # Level 1 to 2
            2: 3000,  # Level 2 to 3
        }

        cost = evolution_cost.get(current_level, 1000)
        exp_needed = exp_requirement.get(current_level, 1000)

        # Check if player has enough TUSD
        if player["tusd"] < cost:
            await interaction.response.send_message(f"{interaction.user.mention}, você não tem TUSD suficiente para evoluir esta técnica. Custo: {cost} TUSD, Seu saldo: {player['tusd']} TUSD")
            return

        # Check if player has enough experience
        if player["exp"] < exp_needed:
            await interaction.response.send_message(f"{interaction.user.mention}, você não tem experiência suficiente para evoluir esta técnica. Necessário: {exp_needed} EXP, Sua EXP: {player['exp']} EXP")
            return

        # Get the evolution data
        next_level = current_level + 1
        evolution_data = full_technique["evolution"].get(str(next_level))

        if not evolution_data:
            await interaction.response.send_message(f"{interaction.user.mention}, não foi possível encontrar os dados de evolução para o nível {next_level}.")
            return

        # Update the technique
        player_technique["level"] = next_level
        player_technique["name"] = evolution_data["name"]
        player_technique["description"] = evolution_data["description"]
        player_technique["effects"] = evolution_data["effects"]

        # Update player data
        update_data = {
            "tusd": player["tusd"] - cost,
            "exp": player["exp"] - exp_needed,
            "techniques": json.dumps(techniques)
        }

        # Update player in database
        success = update_player(interaction.user.id, **update_data)

        if success:
            # Create evolution confirmation embed
            tier_name = TECHNIQUE_TIERS.get(full_technique["tier"], full_technique["tier"].capitalize())
            category_name = TECHNIQUE_CATEGORIES.get(full_technique["category"], full_technique["category"].capitalize())

            embed = create_basic_embed(
                title="Técnica Evoluída!",
                description=f"Você evoluiu a técnica **{player_technique['name']}** para o nível {next_level}/{max_level}!\n\n"
                            f"Custo: {cost} TUSD e {exp_needed} EXP\n"
                            f"Saldo atual: {update_data['tusd']} TUSD 💰 | EXP: {update_data['exp']} EXP",
                color=0x9370DB  # Medium Purple
            )

            embed.add_field(
                name="Detalhes da Técnica",
                value=f"Tipo: {full_technique['type'].capitalize()} | Categoria: {category_name} | Nível: {tier_name}\n"
                      f"Descrição: {player_technique['description']}",
                inline=False
            )

            # Add effects details
            effects_text = []
            for effect_type, effect_value in player_technique["effects"].items():
                if effect_type == "duel_boost":
                    duel_type = effect_value["type"]
                    amount = effect_value["amount"] * 100
                    effects_text.append(f"+{amount:.0f}% de chance em duelos {duel_type}")
                elif effect_type == "damage_boost":
                    amount = effect_value * 100
                    effects_text.append(f"+{amount:.0f}% de dano")
                elif effect_type == "damage_reduction":
                    amount = effect_value * 100
                    effects_text.append(f"-{amount:.0f}% de dano recebido")
                elif effect_type == "attribute_boost":
                    for attr, boost in effect_value.items():
                        amount = boost * 100
                        effects_text.append(f"+{amount:.0f}% em {attr}")
                elif effect_type == "attribute_boost_all":
                    amount = effect_value * 100
                    effects_text.append(f"+{amount:.0f}% em todos os atributos")
                else:
                    effects_text.append(f"{effect_type}: {effect_value}")

            if effects_text:
                embed.add_field(
                    name="Efeitos",
                    value="\n".join(effects_text),
                    inline=False
                )

            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Ocorreu um erro ao evoluir a técnica. Por favor, tente novamente mais tarde.")

    @technique_group.command(name="listar", description="Listar todas as suas técnicas")
    async def slash_list_techniques(self, interaction: discord.Interaction):
        """Lista todas as técnicas do jogador."""
        # Check if player exists
        player = get_player(interaction.user.id)
        if not player:
            await interaction.response.send_message(f"{interaction.user.mention}, você ainda não está registrado na Academia Tokugawa. Use /registro ingressar para criar seu personagem.")
            return

        # Get player's techniques
        techniques = player["techniques"]

        if not techniques:
            await interaction.response.send_message(f"{interaction.user.mention}, você ainda não aprendeu nenhuma técnica. Compre pergaminhos de técnicas na loja para aprender novas técnicas.")
            return

        # Create techniques embed
        embed = create_basic_embed(
            title="Suas Técnicas",
            description=f"Você conhece {len(techniques)} técnicas. Use `/tecnica evoluir <id>` para evoluir uma técnica.",
            color=0x9370DB  # Medium Purple
        )

        # Group techniques by category
        techniques_by_category = {}
        for tech_id, technique in techniques.items():
            category = technique.get("category", "unknown")
            if category not in techniques_by_category:
                techniques_by_category[category] = []
            techniques_by_category[category].append((tech_id, technique))

        # Add techniques to embed by category
        for category, techs in techniques_by_category.items():
            category_name = TECHNIQUE_CATEGORIES.get(category, "Outras")
            embed.add_field(
                name=f"--- {category_name} ---",
                value="",
                inline=False
            )

            for tech_id, technique in techs:
                # Get the full technique data to check max level
                full_technique = next((t for t in TECHNIQUES if t["id"] == int(tech_id)), None)
                max_level = full_technique.get("max_level", 3) if full_technique else 3
                current_level = technique.get("level", 1)

                # Get tier name
                tier_name = ""
                if "tier" in technique:
                    tier_name = f" | {TECHNIQUE_TIERS.get(technique['tier'], technique['tier'].capitalize())}"

                # Add seasonal tag if applicable
                seasonal_tag = ""
                if full_technique and "seasonal" in full_technique:
                    season_names = {
                        "spring": "Primavera",
                        "summer": "Verão",
                        "autumn": "Outono",
                        "winter": "Inverno"
                    }
                    season_name = season_names.get(full_technique["seasonal"], full_technique["seasonal"])
                    seasonal_tag = f" [Sazonal: {season_name}]"

                embed.add_field(
                    name=f"{tech_id}. {technique['name']} (Nível {current_level}/{max_level}){tier_name}{seasonal_tag}",
                    value=f"Tipo: {technique['type'].capitalize()}\n{technique['description']}",
                    inline=False
                )

        await interaction.response.send_message(embed=embed)

    @technique_group.command(name="info", description="Ver informações detalhadas sobre uma técnica")
    async def slash_technique_info(self, interaction: discord.Interaction, technique_id: int):
        """Mostra informações detalhadas sobre uma técnica."""
        # Check if player exists
        player = get_player(interaction.user.id)
        if not player:
            await interaction.response.send_message(f"{interaction.user.mention}, você ainda não está registrado na Academia Tokugawa. Use /registro ingressar para criar seu personagem.")
            return

        # Check if player has the technique
        techniques = player["techniques"]
        if str(technique_id) not in techniques:
            await interaction.response.send_message(f"{interaction.user.mention}, você não possui esta técnica. Use `/tecnica listar` para ver suas técnicas.")
            return

        # Get the technique from player's techniques
        player_technique = techniques[str(technique_id)]

        # Get the full technique data from TECHNIQUES
        full_technique = next((t for t in TECHNIQUES if t["id"] == technique_id), None)
        if not full_technique:
            await interaction.response.send_message(f"{interaction.user.mention}, técnica não encontrada no sistema.")
            return

        # Get technique details
        current_level = player_technique.get("level", 1)
        max_level = full_technique.get("max_level", 3)
        tier_name = TECHNIQUE_TIERS.get(full_technique["tier"], full_technique["tier"].capitalize())
        category_name = TECHNIQUE_CATEGORIES.get(full_technique["category"], full_technique["category"].capitalize())

        # Create technique info embed
        embed = create_basic_embed(
            title=f"Técnica: {player_technique['name']}",
            description=f"Nível: {current_level}/{max_level} | Tipo: {player_technique['type'].capitalize()} | Categoria: {category_name} | Nível: {tier_name}\n\n"
                        f"{player_technique['description']}",
            color=0x9370DB  # Medium Purple
        )

        # Add effects details
        effects_text = []
        for effect_type, effect_value in player_technique["effects"].items():
            if effect_type == "duel_boost":
                duel_type = effect_value["type"]
                amount = effect_value["amount"] * 100
                effects_text.append(f"+{amount:.0f}% de chance em duelos {duel_type}")
            elif effect_type == "damage_boost":
                amount = effect_value * 100
                effects_text.append(f"+{amount:.0f}% de dano")
            elif effect_type == "damage_reduction":
                amount = effect_value * 100
                effects_text.append(f"-{amount:.0f}% de dano recebido")
            elif effect_type == "attribute_boost":
                for attr, boost in effect_value.items():
                    amount = boost * 100
                    effects_text.append(f"+{amount:.0f}% em {attr}")
            elif effect_type == "attribute_boost_all":
                amount = effect_value * 100
                effects_text.append(f"+{amount:.0f}% em todos os atributos")
            else:
                effects_text.append(f"{effect_type}: {effect_value}")

        if effects_text:
            embed.add_field(
                name="Efeitos Atuais",
                value="\n".join(effects_text),
                inline=False
            )

        # Add evolution info if technique can be evolved
        if current_level < max_level:
            next_level = current_level + 1
            evolution_data = full_technique["evolution"].get(str(next_level))

            if evolution_data:
                # Calculate evolution cost
                evolution_cost = {
                    1: 500,  # Level 1 to 2
                    2: 1000,  # Level 2 to 3
                }

                exp_requirement = {
                    1: 1000,  # Level 1 to 2
                    2: 3000,  # Level 2 to 3
                }

                cost = evolution_cost.get(current_level, 1000)
                exp_needed = exp_requirement.get(current_level, 1000)

                embed.add_field(
                    name=f"Próxima Evolução (Nível {next_level})",
                    value=f"Nome: {evolution_data['name']}\nDescrição: {evolution_data['description']}\n\n"
                          f"Custo: {cost} TUSD e {exp_needed} EXP",
                    inline=False
                )

                # Add next level effects
                next_effects_text = []
                for effect_type, effect_value in evolution_data["effects"].items():
                    if effect_type == "duel_boost":
                        duel_type = effect_value["type"]
                        amount = effect_value["amount"] * 100
                        next_effects_text.append(f"+{amount:.0f}% de chance em duelos {duel_type}")
                    elif effect_type == "damage_boost":
                        amount = effect_value * 100
                        next_effects_text.append(f"+{amount:.0f}% de dano")
                    elif effect_type == "damage_reduction":
                        amount = effect_value * 100
                        next_effects_text.append(f"-{amount:.0f}% de dano recebido")
                    elif effect_type == "attribute_boost":
                        for attr, boost in effect_value.items():
                            amount = boost * 100
                            next_effects_text.append(f"+{amount:.0f}% em {attr}")
                    elif effect_type == "attribute_boost_all":
                        amount = effect_value * 100
                        next_effects_text.append(f"+{amount:.0f}% em todos os atributos")
                    else:
                        next_effects_text.append(f"{effect_type}: {effect_value}")

                if next_effects_text:
                    embed.add_field(
                        name="Efeitos da Próxima Evolução",
                        value="\n".join(next_effects_text),
                        inline=False
                    )

        await interaction.response.send_message(embed=embed)

    @economy_group.command(name="loja", description="Acessar a loja da Academia Tokugawa")
    async def slash_shop(self, interaction: discord.Interaction):
        """Slash command version of the shop command."""
        # Check if player exists
        player = get_player(interaction.user.id)
        if not player:
            await interaction.response.send_message(f"{interaction.user.mention}, você ainda não está registrado na Academia Tokugawa. Use /registro ingressar para criar seu personagem.")
            return

        # Get player's story progress to determine current bimester and active events
        story_progress = player.get('story_progress', {})
        bimestre = story_progress.get('bimestre_corrente', 1)
        active_events = story_progress.get('eventos_ativos', [])
        player_level = player.get('level', 1)
        player_club = player.get('club', None)

        # Get available items based on bimester, active events, player level, and club
        available_items = get_available_shop_items(
            bimestre=bimestre, 
            active_events=active_events,
            player_level=player_level,
            player_club=player_club
        )

        # Create shop embed
        season_name = {
            "spring": "Primavera",
            "summer": "Verão",
            "autumn": "Outono",
            "winter": "Inverno"
        }.get(SEASONS.get(bimestre, "spring"), "Primavera")

        # Get player's alternative currencies
        alt_currencies = player.get('currencies', {})
        currency_display = f"Você tem {player['tusd']} TUSD 💰\n"

        # Add seasonal currency if applicable
        season = SEASONS.get(bimestre, "spring")
        season_token = f"{season}_token"
        if season_token in ALTERNATIVE_CURRENCIES:
            currency_info = ALTERNATIVE_CURRENCIES[season_token]
            currency_amount = alt_currencies.get(season_token, 0)
            currency_display += f"{currency_info['icon']} {currency_amount} {currency_info['name']}\n"

        # Add event currency if player has any
        if 'event_token' in alt_currencies and alt_currencies['event_token'] > 0:
            currency_info = ALTERNATIVE_CURRENCIES['event_token']
            currency_display += f"{currency_info['icon']} {alt_currencies['event_token']} {currency_info['name']}\n"

        embed = create_basic_embed(
            title=f"Loja da Academia Tokugawa - {season_name}",
            description=f"Bem-vindo à loja oficial da Academia!\n{currency_display}\n"
                        f"Estamos no {bimestre}º bimestre ({season_name}). Aproveite os itens sazonais!\n\n"
                        f"Para comprar um item, use o comando `/economia comprar <id>`",
            color=0xFFD700  # Gold
        )

        # Add items to embed by type
        for item_type, items in available_items.items():
            if not items:  # Skip empty categories
                continue

            type_name = ITEM_TYPES.get(item_type, item_type.capitalize())
            embed.add_field(
                name=f"--- {type_name} ---",
                value="",
                inline=False
            )

            for item in items:
                rarity = RARITIES.get(item["rarity"], RARITIES["common"])
                category = item.get("category", "fixed")

                # Add special indicators for seasonal or event items
                special_tag = ""
                if category == "seasonal":
                    special_tag = f" [Sazonal: {season_name}]"
                elif category == "event":
                    event_name = item.get("event", "").replace("_", " ").title()
                    special_tag = f" [Evento: {event_name}]"
                elif category == "thematic" and "club_required" in item:
                    club_name = item["club_required"].replace("_", " ").title()
                    special_tag = f" [Clube: {club_name}]"

                # Check if item requires alternative currency
                price_display = f"{item['price']} TUSD"
                if "currency" in item and item["currency"] in ALTERNATIVE_CURRENCIES:
                    currency_info = ALTERNATIVE_CURRENCIES[item["currency"]]
                    price_display = f"{item['price']} {currency_info['icon']} {currency_info['name']}"

                embed.add_field(
                    name=f"{item['id']}. {rarity['emoji']} {item['name']} - {price_display}{special_tag}",
                    value=f"{item['description']}\nTipo: {ITEM_TYPES.get(item_type, item_type.capitalize())}",
                    inline=False
                )

        # Add special currency items if applicable
        season_token = f"{season}_token"
        if season_token in SPECIAL_CURRENCY_ITEMS:
            embed.add_field(
                name=f"--- Itens Especiais ({ALTERNATIVE_CURRENCIES[season_token]['name']}) ---",
                value="",
                inline=False
            )

            for item in SPECIAL_CURRENCY_ITEMS[season_token]:
                rarity = RARITIES.get(item["rarity"], RARITIES["common"])
                currency_info = ALTERNATIVE_CURRENCIES[item["currency"]]

                embed.add_field(
                    name=f"{item['id']}. {rarity['emoji']} {item['name']} - {item['price']} {currency_info['icon']} {currency_info['name']}",
                    value=f"{item['description']}\nTipo: {ITEM_TYPES.get(item['type'], item['type'].capitalize())}",
                    inline=False
                )

        # Add item exchanges section
        if ITEM_EXCHANGES:
            embed.add_field(
                name="--- Sistema de Trocas ---",
                value="Troque itens antigos por novos itens ou moedas especiais!",
                inline=False
            )

            for exchange in ITEM_EXCHANGES:
                requirements = []
                if "items" in exchange["requirements"]:
                    req = exchange["requirements"]["items"]
                    requirements.append(f"{req['count']} itens de raridade {req.get('rarity', 'qualquer').capitalize()}")

                if "currency" in exchange["requirements"]:
                    req = exchange["requirements"]["currency"]
                    requirements.append(f"{req['amount']} {req['type']}")

                reward = ""
                if "item_rarity" in exchange["reward"]:
                    reward = f"1 item de raridade {exchange['reward']['item_rarity'].capitalize()}"
                    if exchange["reward"].get("random", False):
                        reward += " aleatório"

                if "currency" in exchange["reward"]:
                    req = exchange["reward"]["currency"]
                    reward = f"{req['amount']} {req['type']}"

                embed.add_field(
                    name=f"Troca #{exchange['id']}: {exchange['name']}",
                    value=f"{exchange['description']}\nRequisitos: {', '.join(requirements)}\nRecompensa: {reward}",
                    inline=False
                )

        await interaction.response.send_message(embed=embed)

    @economy_group.command(name="comprar", description="Comprar um item da loja")
    async def slash_buy(self, interaction: discord.Interaction, item_id: int):
        """Slash command version of the buy command."""
        # Check if player exists
        player = get_player(interaction.user.id)
        if not player:
            await interaction.response.send_message(f"{interaction.user.mention}, você ainda não está registrado na Academia Tokugawa. Use /registro ingressar para criar seu personagem.")
            return

        # Get player's story progress to determine current bimester and active events
        story_progress = player.get('story_progress', {})
        bimestre = story_progress.get('bimestre_corrente', 1)
        active_events = story_progress.get('eventos_ativos', [])
        player_level = player.get('level', 1)
        player_club = player.get('club', None)

        # Get player's alternative currencies
        alt_currencies = player.get('currencies', {})

        # Get current season
        season = SEASONS.get(bimestre, "spring")
        season_token = f"{season}_token"

        # Get available items based on bimester, active events, player level, and club
        available_items_dict = get_available_shop_items(
            bimestre=bimestre, 
            active_events=active_events,
            player_level=player_level,
            player_club=player_club
        )

        # Flatten the items dictionary for easier searching
        available_items = []
        for item_list in available_items_dict.values():
            available_items.extend(item_list)

        # Check special currency items
        if season_token in SPECIAL_CURRENCY_ITEMS:
            available_items.extend(SPECIAL_CURRENCY_ITEMS[season_token])

        # Find the item
        item = next((i for i in available_items if i["id"] == item_id), None)
        if not item:
            await interaction.response.send_message(f"{interaction.user.mention}, item não encontrado ou não disponível neste momento. Use `/economia loja` para ver os itens disponíveis.")
            return

        # Check if item requires alternative currency
        if "currency" in item and item["currency"] in ALTERNATIVE_CURRENCIES:
            currency_type = item["currency"]
            currency_info = ALTERNATIVE_CURRENCIES[currency_type]

            # Check if player has enough of the alternative currency
            if alt_currencies.get(currency_type, 0) < item["price"]:
                await interaction.response.send_message(
                    f"{interaction.user.mention}, você não tem {currency_info['name']} suficiente para comprar este item. "
                    f"Preço: {item['price']} {currency_info['name']}, Seu saldo: {alt_currencies.get(currency_type, 0)} {currency_info['name']}"
                )
                return

            # Process the purchase with alternative currency
            inventory = player["inventory"]

            # Add item to inventory
            if str(item["id"]) in inventory:
                # If player already has this item, increase quantity
                inventory[str(item["id"])]["quantity"] += 1
            else:
                # Add new item to inventory
                inventory_item = {
                    "id": item["id"],
                    "name": item["name"],
                    "description": item["description"],
                    "type": item["type"],
                    "rarity": item["rarity"],
                    "effects": item["effects"],
                    "quantity": 1
                }

                # Add category and season/event info if applicable
                if "category" in item:
                    inventory_item["category"] = item["category"]
                if "season" in item:
                    inventory_item["season"] = item["season"]
                if "event" in item:
                    inventory_item["event"] = item["event"]

                inventory[str(item["id"])] = inventory_item

            # Update player data
            alt_currencies[currency_type] = alt_currencies.get(currency_type, 0) - item["price"]
            update_data = {
                "currencies": json.dumps(alt_currencies),
                "inventory": json.dumps(inventory)
            }
        else:
            # Standard TUSD purchase
            # Apply club discount if applicable
            from utils.club_perks import apply_shop_discount
            original_price = item["price"]
            discounted_price = apply_shop_discount(original_price, player.get('club_id'))

            # Check if player has enough TUSD
            if player["tusd"] < discounted_price:
                # Show original and discounted price if there's a discount
                if discounted_price < original_price:
                    await interaction.response.send_message(f"{interaction.user.mention}, você não tem TUSD suficiente para comprar este item. Preço: ~~{original_price}~~ {discounted_price} TUSD (Desconto de Clube), Seu saldo: {player['tusd']} TUSD")
                else:
                    await interaction.response.send_message(f"{interaction.user.mention}, você não tem TUSD suficiente para comprar este item. Preço: {discounted_price} TUSD, Seu saldo: {player['tusd']} TUSD")
                return

            # Store the discounted price for later use
            item["discounted_price"] = discounted_price

            # Process the purchase
            inventory = player["inventory"]

            # Add item to inventory
            if str(item["id"]) in inventory:
                # If player already has this item, increase quantity
                inventory[str(item["id"])]["quantity"] += 1
            else:
                # Add new item to inventory
                inventory_item = {
                    "id": item["id"],
                    "name": item["name"],
                    "description": item["description"],
                    "type": item["type"],
                    "rarity": item["rarity"],
                    "effects": item["effects"],
                    "quantity": 1
                }

                # Add category and season/event info if applicable
                if "category" in item:
                    inventory_item["category"] = item["category"]
                if "season" in item:
                    inventory_item["season"] = item["season"]
                if "event" in item:
                    inventory_item["event"] = item["event"]

                inventory[str(item["id"])] = inventory_item

            # Update player data
            # Use the discounted price if available, otherwise use the original price
            price_to_deduct = item.get("discounted_price", item["price"])
            update_data = {
                "tusd": player["tusd"] - price_to_deduct,
                "inventory": json.dumps(inventory)
            }

        # Special handling for permanent attribute items
        if item["type"] == "consumable" and "permanent_attribute" in item["effects"]:
            # Check if it's a specific attribute or random
            if isinstance(item["effects"]["permanent_attribute"], dict):
                # Specific attribute
                for attr, value in item["effects"]["permanent_attribute"].items():
                    if attr in ["dexterity", "intellect", "charisma", "power_stat"]:
                        update_data[attr] = player[attr] + value
            else:
                # Random attribute
                attribute = random.choice(["dexterity", "intellect", "charisma", "power_stat"])
                update_data[attribute] = player[attribute] + item["effects"]["permanent_attribute"]

            # Remove the item from inventory since it's consumed immediately
            inventory[str(item["id"])]["quantity"] -= 1
            if inventory[str(item["id"])]["quantity"] <= 0:
                del inventory[str(item["id"])]

            update_data["inventory"] = json.dumps(inventory)

        # Special handling for technique scrolls
        techniques = player["techniques"]
        technique_learned = None

        # Regular technique scroll (random technique)
        if item["type"] == "consumable" and "learn_technique" in item["effects"]:
            # Choose a random technique
            available_techniques = [t for t in TECHNIQUES if str(t["id"]) not in techniques]
            if available_techniques:
                technique = random.choice(available_techniques)
                if str(technique["id"]) not in techniques:
                    techniques[str(technique["id"])] = {
                        "id": technique["id"],
                        "name": technique["name"],
                        "description": technique["description"],
                        "type": technique["type"],
                        "category": technique["category"],
                        "tier": technique["tier"],
                        "level": technique["level"],
                        "effects": technique["effects"]
                    }
                    technique_learned = technique
                    update_data["techniques"] = json.dumps(techniques)

                    # Remove the item from inventory since it's consumed immediately
                    inventory[str(item["id"])]["quantity"] -= 1
                    if inventory[str(item["id"])]["quantity"] <= 0:
                        del inventory[str(item["id"])]

                    update_data["inventory"] = json.dumps(inventory)
            else:
                await interaction.response.send_message(f"{interaction.user.mention}, você já conhece todas as técnicas disponíveis!")
                return

        # Advanced technique scroll (random advanced technique)
        elif item["type"] == "consumable" and "learn_advanced_technique" in item["effects"]:
            # Choose a random advanced technique
            advanced_techniques = [t for t in TECHNIQUES if t["tier"] == "advanced" and str(t["id"]) not in techniques]
            if advanced_techniques:
                technique = random.choice(advanced_techniques)
                if str(technique["id"]) not in techniques:
                    techniques[str(technique["id"])] = {
                        "id": technique["id"],
                        "name": technique["name"],
                        "description": technique["description"],
                        "type": technique["type"],
                        "category": technique["category"],
                        "tier": technique["tier"],
                        "level": technique["level"],
                        "effects": technique["effects"]
                    }
                    technique_learned = technique
                    update_data["techniques"] = json.dumps(techniques)

                    # Remove the item from inventory since it's consumed immediately
                    inventory[str(item["id"])]["quantity"] -= 1
                    if inventory[str(item["id"])]["quantity"] <= 0:
                        del inventory[str(item["id"])]

                    update_data["inventory"] = json.dumps(inventory)
            else:
                await interaction.response.send_message(f"{interaction.user.mention}, você já conhece todas as técnicas avançadas disponíveis!")
                return

        # Specific technique scroll
        elif item["type"] == "consumable" and "learn_specific_technique" in item["effects"]:
            technique_id = item["effects"]["learn_specific_technique"]
            technique = next((t for t in TECHNIQUES if t["id"] == technique_id), None)

            if technique and str(technique["id"]) not in techniques:
                techniques[str(technique["id"])] = {
                    "id": technique["id"],
                    "name": technique["name"],
                    "description": technique["description"],
                    "type": technique["type"],
                    "category": technique["category"],
                    "tier": technique["tier"],
                    "level": technique["level"],
                    "effects": technique["effects"]
                }
                technique_learned = technique
                update_data["techniques"] = json.dumps(techniques)

                # Remove the item from inventory since it's consumed immediately
                inventory[str(item["id"])]["quantity"] -= 1
                if inventory[str(item["id"])]["quantity"] <= 0:
                    del inventory[str(item["id"])]

                update_data["inventory"] = json.dumps(inventory)
            elif str(technique["id"]) in techniques:
                await interaction.response.send_message(f"{interaction.user.mention}, você já conhece a técnica {technique['name']}!")
                return
            else:
                await interaction.response.send_message(f"{interaction.user.mention}, técnica não encontrada!")
                return

        # Update player in database
        success = update_player(interaction.user.id, **update_data)

        if success:
            # Create purchase confirmation embed
            rarity = RARITIES.get(item["rarity"], RARITIES["common"])

            # Add category info to the embed
            category_info = ""
            if "category" in item:
                category_name = ITEM_CATEGORIES.get(item["category"], "")
                if category_name:
                    category_info = f"\nCategoria: {category_name}"

                    # Add seasonal or event info
                    if item["category"] == "seasonal" and "season" in item:
                        season_names = {
                            "spring": "Primavera",
                            "summer": "Verão",
                            "autumn": "Outono",
                            "winter": "Inverno"
                        }
                        season_name = season_names.get(item["season"], item["season"])
                        category_info += f" (Sazonal: {season_name})"
                    elif item["category"] == "event" and "event" in item:
                        event_name = item["event"].replace("_", " ").title()
                        category_info += f" (Evento: {event_name})"

            embed = create_basic_embed(
                title="Compra Realizada!",
                description=f"Você comprou {rarity['emoji']} **{item['name']}** por " + 
                            (f"~~{item['price']}~~ {item.get('discounted_price')} TUSD (Desconto de Clube)." if item.get('discounted_price', item['price']) < item['price'] else f"{item['price']} TUSD.") +
                            f"{category_info}\n\n"
                            f"Saldo atual: {update_data['tusd']} TUSD 💰",
                color=rarity["color"]
            )

            # Add special messages for consumed items
            if item["type"] == "consumable" and "permanent_attribute" in item["effects"]:
                attribute_names = {
                    "dexterity": "Destreza 🏃‍♂️",
                    "intellect": "Intelecto 🧠",
                    "charisma": "Carisma 💬",
                    "power_stat": "Poder ⚡"
                }

                if isinstance(item["effects"]["permanent_attribute"], dict):
                    # Specific attribute
                    attr_messages = []
                    for attr, value in item["effects"]["permanent_attribute"].items():
                        if attr in attribute_names:
                            attr_messages.append(f"{attribute_names[attr]} em +{value}")

                    if attr_messages:
                        embed.add_field(
                            name="Item Consumido!",
                            value=f"O Elixir aumentou seu(s) atributo(s) de {', '.join(attr_messages)}!",
                            inline=False
                        )
                else:
                    # Random attribute
                    embed.add_field(
                        name="Item Consumido!",
                        value=f"O Elixir aumentou seu atributo de {attribute_names[attribute]} em +{item['effects']['permanent_attribute']}!",
                        inline=False
                    )

            if technique_learned:
                # Format the technique info nicely
                tier_name = TECHNIQUE_TIERS.get(technique_learned["tier"], technique_learned["tier"].capitalize())
                category_name = TECHNIQUE_CATEGORIES.get(technique_learned["category"], technique_learned["category"].capitalize())

                embed.add_field(
                    name="Técnica Aprendida!",
                    value=f"Você aprendeu a técnica **{technique_learned['name']}**!\n"
                          f"Tipo: {technique_learned['type'].capitalize()} | Categoria: {category_name} | Nível: {tier_name}\n"
                          f"Descrição: {technique_learned['description']}",
                    inline=False
                )

            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Ocorreu um erro durante a compra. Por favor, tente novamente mais tarde.")

    @economy_group.command(name="mercado", description="Acessar o mercado de itens entre jogadores")
    async def slash_market(self, interaction: discord.Interaction):
        """Slash command version of the market command."""
        try:
            # Check if player exists
            player = get_player(interaction.user.id)
            if not player:
                await interaction.response.send_message(f"{interaction.user.mention}, você ainda não está registrado na Academia Tokugawa. Use /registro ingressar para criar seu personagem.")
                return

            # Create market embed
            embed = create_basic_embed(
                title="Mercado da Academia Tokugawa",
                description=f"Bem-vindo ao mercado de itens entre alunos! Você tem {player['tusd']} TUSD 💰\n\n"
                            f"Para vender um item, use `/economia vender <id_do_item> <preço>`\n"
                            f"Para comprar um item, use `/economia comprar_mercado <id_da_listagem>`",
                color=0x00FF00  # Green
            )

            # Add listings to embed
            if not self.market_listings:
                embed.add_field(
                    name="Nenhum item à venda",
                    value="Seja o primeiro a vender algo no mercado!",
                    inline=False
                )
            else:
                for listing_id, listing in self.market_listings.items():
                    seller = self.bot.get_user(listing["seller_id"])
                    seller_name = seller.display_name if seller else "Desconhecido"

                    rarity = RARITIES.get(listing["item_data"]["rarity"], RARITIES["common"])
                    embed.add_field(
                        name=f"{listing_id}. {rarity['emoji']} {listing['item_data']['name']} - {listing['price']} TUSD",
                        value=f"{listing['item_data']['description']}\nVendedor: {seller_name}",
                        inline=False
                    )

            await interaction.response.send_message(embed=embed)
        except discord.errors.NotFound:
            # If the interaction has expired, log it but don't try to respond
            logger.warning(f"Interaction expired for user {interaction.user.id} when using /economia mercado")
        except Exception as e:
            logger.error(f"Error in slash_market: {e}")

    @economy_group.command(name="vender", description="Vender um item no mercado")
    async def slash_sell(self, interaction: discord.Interaction, item_id: int, price: int):
        """Slash command version of the sell command."""
        try:
            # Check if player exists
            player = get_player(interaction.user.id)
            if not player:
                await interaction.response.send_message(f"{interaction.user.mention}, você ainda não está registrado na Academia Tokugawa. Use /registro ingressar para criar seu personagem.")
                return

            # Check if price is valid
            if price <= 0:
                await interaction.response.send_message(f"{interaction.user.mention}, o preço deve ser maior que zero.")
                return

            # Check if player has the item
            inventory = player["inventory"]
            if str(item_id) not in inventory:
                await interaction.response.send_message(f"{interaction.user.mention}, você não possui este item em seu inventário.")
                return

            # Get item data
            item_data = inventory[str(item_id)]

            # Create listing
            listing_id = self.next_listing_id
            self.next_listing_id += 1

            self.market_listings[listing_id] = {
                "seller_id": interaction.user.id,
                "item_id": item_id,
                "price": price,
                "item_data": item_data
            }

            # Remove item from inventory
            inventory[str(item_id)]["quantity"] -= 1
            if inventory[str(item_id)]["quantity"] <= 0:
                del inventory[str(item_id)]

            # Update player in database
            success = update_player(interaction.user.id, inventory=json.dumps(inventory))

            if success:
                # Create listing confirmation embed
                rarity = RARITIES.get(item_data["rarity"], RARITIES["common"])
                embed = create_basic_embed(
                    title="Item Colocado à Venda!",
                    description=f"Você colocou {rarity['emoji']} **{item_data['name']}** à venda por {price} TUSD.\n\n"
                                f"ID da listagem: {listing_id}",
                    color=rarity["color"]
                )

                await interaction.response.send_message(embed=embed)
            else:
                await interaction.response.send_message("Ocorreu um erro ao colocar o item à venda. Por favor, tente novamente mais tarde.")
        except discord.errors.NotFound:
            # If the interaction has expired, log it but don't try to respond
            logger.warning(f"Interaction expired for user {interaction.user.id} when using /economia vender")
        except Exception as e:
            logger.error(f"Error in slash_sell: {e}")

    @economy_group.command(name="comprar_mercado", description="Comprar um item do mercado")
    async def slash_buy_market(self, interaction: discord.Interaction, listing_id: int):
        """Slash command version of the buy_market command."""
        try:
            # Check if player exists
            player = get_player(interaction.user.id)
            if not player:
                await interaction.response.send_message(f"{interaction.user.mention}, você ainda não está registrado na Academia Tokugawa. Use /registro ingressar para criar seu personagem.")
                return

            # Check if listing exists
            if listing_id not in self.market_listings:
                await interaction.response.send_message(f"{interaction.user.mention}, listagem não encontrada. Use `/economia mercado` para ver as listagens disponíveis.")
                return

            # Get listing data
            listing = self.market_listings[listing_id]

            # Check if player is trying to buy their own item
            if listing["seller_id"] == interaction.user.id:
                await interaction.response.send_message(f"{interaction.user.mention}, você não pode comprar seu próprio item.")
                return

            # Check if player has enough TUSD
            if player["tusd"] < listing["price"]:
                await interaction.response.send_message(f"{interaction.user.mention}, você não tem TUSD suficiente para comprar este item. Preço: {listing['price']} TUSD, Seu saldo: {player['tusd']} TUSD")
                return

            # Get seller data
            seller = get_player(listing["seller_id"])
            if not seller:
                await interaction.response.send_message(f"{interaction.user.mention}, o vendedor não existe mais. A listagem será removida.")
                del self.market_listings[listing_id]
                return

            # Process the purchase
            buyer_inventory = player["inventory"]

            # Add item to buyer's inventory
            if str(listing["item_id"]) in buyer_inventory:
                # If buyer already has this item, increase quantity
                buyer_inventory[str(listing["item_id"])]["quantity"] += 1
            else:
                # Add new item to inventory
                item_data = listing["item_data"].copy()
                item_data["quantity"] = 1
                buyer_inventory[str(listing["item_id"])] = item_data

            # Update buyer data
            buyer_update = {
                "tusd": player["tusd"] - listing["price"],
                "inventory": json.dumps(buyer_inventory)
            }

            # Update seller data
            seller_update = {
                "tusd": seller["tusd"] + listing["price"]
            }

            # Update both players in database
            buyer_success = update_player(interaction.user.id, **buyer_update)
            seller_success = update_player(listing["seller_id"], **seller_update)

            if buyer_success and seller_success:
                # Remove listing
                del self.market_listings[listing_id]

                # Create purchase confirmation embed
                rarity = RARITIES.get(listing["item_data"]["rarity"], RARITIES["common"])
                embed = create_basic_embed(
                    title="Compra Realizada!",
                    description=f"Você comprou {rarity['emoji']} **{listing['item_data']['name']}** por {listing['price']} TUSD.\n\n"
                                f"Saldo atual: {buyer_update['tusd']} TUSD 💰",
                    color=rarity["color"]
                )

                await interaction.response.send_message(embed=embed)

                # Notify seller if they're online
                seller_user = self.bot.get_user(listing["seller_id"])
                if seller_user:
                    seller_embed = create_basic_embed(
                        title="Item Vendido!",
                        description=f"Seu item {rarity['emoji']} **{listing['item_data']['name']}** foi vendido por {listing['price']} TUSD.\n\n"
                                    f"Saldo atual: {seller_update['tusd']} TUSD 💰",
                        color=rarity["color"]
                    )

                    try:
                        await seller_user.send(embed=seller_embed)
                    except:
                        # Ignore if we can't DM the seller
                        pass
            else:
                await interaction.response.send_message("Ocorreu um erro durante a compra. Por favor, tente novamente mais tarde.")
        except discord.errors.NotFound:
            # If the interaction has expired, log it but don't try to respond
            logger.warning(f"Interaction expired for user {interaction.user.id} when using /economia comprar_mercado")
        except Exception as e:
            logger.error(f"Error in slash_buy_market: {e}")

    @economy_group.command(name="trocar", description="Trocar itens por recompensas")
    async def slash_exchange(self, interaction: discord.Interaction, exchange_id: int):
        """Permite trocar itens por outros itens ou moedas especiais."""
        # Check if player exists
        player = get_player(interaction.user.id)
        if not player:
            await interaction.response.send_message(f"{interaction.user.mention}, você ainda não está registrado na Academia Tokugawa. Use /registro ingressar para criar seu personagem.")
            return

        # Check cooldown (1 hour between exchanges)
        user_id = str(interaction.user.id)
        now = datetime.now().timestamp()
        if user_id in self.exchange_cooldowns and self.exchange_cooldowns[user_id] > now:
            remaining = self.exchange_cooldowns[user_id] - now
            minutes, seconds = divmod(int(remaining), 60)
            await interaction.response.send_message(f"{interaction.user.mention}, você precisa esperar {minutes}m {seconds}s para fazer outra troca.")
            return

        # Find the exchange
        exchange = next((e for e in ITEM_EXCHANGES if e["id"] == exchange_id), None)
        if not exchange:
            await interaction.response.send_message(f"{interaction.user.mention}, troca não encontrada. Use `/economia loja` para ver as trocas disponíveis.")
            return

        # Check requirements
        inventory = player["inventory"]
        requirements_met = True
        items_to_remove = []

        # Check item requirements
        if "items" in exchange["requirements"]:
            req = exchange["requirements"]["items"]
            rarity = req.get("rarity", None)
            category = req.get("category", None)
            count = req.get("count", 1)

            # Find matching items
            matching_items = []
            for item_id, item in inventory.items():
                if rarity and item.get("rarity") != rarity:
                    continue
                if category and item.get("category") != category:
                    continue

                # Add item to matching items (considering quantity)
                for _ in range(item.get("quantity", 1)):
                    matching_items.append(item_id)
                    if len(matching_items) >= count:
                        break

                if len(matching_items) >= count:
                    break

            if len(matching_items) < count:
                requirements_met = False
                await interaction.response.send_message(
                    f"{interaction.user.mention}, você não tem itens suficientes para esta troca. "
                    f"Necessário: {count} itens de raridade {rarity or 'qualquer'}"
                )
                return

            # Mark items for removal
            for item_id in matching_items[:count]:
                items_to_remove.append(item_id)

        # Check currency requirements
        if "currency" in exchange["requirements"]:
            req = exchange["requirements"]["currency"]
            currency_type = req.get("type", "TUSD")
            amount = req.get("amount", 0)

            if currency_type == "TUSD":
                if player["tusd"] < amount:
                    requirements_met = False
                    await interaction.response.send_message(
                        f"{interaction.user.mention}, você não tem TUSD suficiente para esta troca. "
                        f"Necessário: {amount} TUSD, Seu saldo: {player['tusd']} TUSD"
                    )
                    return
            else:
                alt_currencies = player.get("currencies", {})
                if alt_currencies.get(currency_type, 0) < amount:
                    requirements_met = False
                    currency_info = ALTERNATIVE_CURRENCIES.get(currency_type, {"name": currency_type})
                    await interaction.response.send_message(
                        f"{interaction.user.mention}, você não tem {currency_info['name']} suficiente para esta troca. "
                        f"Necessário: {amount} {currency_info['name']}, Seu saldo: {alt_currencies.get(currency_type, 0)} {currency_info['name']}"
                    )
                    return

        # Process the exchange if requirements are met
        if requirements_met:
            # Remove items from inventory
            for item_id in items_to_remove:
                if inventory[item_id]["quantity"] > 1:
                    inventory[item_id]["quantity"] -= 1
                else:
                    del inventory[item_id]

            # Remove currency if required
            update_data = {"inventory": json.dumps(inventory)}
            if "currency" in exchange["requirements"]:
                req = exchange["requirements"]["currency"]
                currency_type = req.get("type", "TUSD")
                amount = req.get("amount", 0)

                if currency_type == "TUSD":
                    update_data["tusd"] = player["tusd"] - amount
                else:
                    alt_currencies = player.get("currencies", {})
                    alt_currencies[currency_type] = alt_currencies.get(currency_type, 0) - amount
                    update_data["currencies"] = json.dumps(alt_currencies)

            # Process reward
            reward_message = ""

            # Item reward
            if "item_rarity" in exchange["reward"]:
                rarity = exchange["reward"]["item_rarity"]
                is_random = exchange["reward"].get("random", False)

                # Get all items of the specified rarity
                all_items = []
                for item_list in [TRAINING_ITEMS, COMBAT_ITEMS, ENERGY_ITEMS, ATTRIBUTE_ITEMS, SOCIAL_ITEMS]:
                    all_items.extend([item for item in item_list if item["rarity"] == rarity])

                for season_items in SEASONAL_ITEMS.values():
                    all_items.extend([item for item in season_items if item["rarity"] == rarity])

                for event_items in EVENT_ITEMS.values():
                    all_items.extend([item for item in event_items if item["rarity"] == rarity])

                # Choose a random item or a specific one
                if all_items:
                    if is_random:
                        reward_item = random.choice(all_items)
                    else:
                        reward_item = all_items[0]  # First item as default

                    # Add item to inventory
                    if str(reward_item["id"]) in inventory:
                        inventory[str(reward_item["id"])]["quantity"] += 1
                    else:
                        inventory_item = {
                            "id": reward_item["id"],
                            "name": reward_item["name"],
                            "description": reward_item["description"],
                            "type": reward_item["type"],
                            "rarity": reward_item["rarity"],
                            "effects": reward_item["effects"],
                            "quantity": 1
                        }

                        # Add category and season/event info if applicable
                        if "category" in reward_item:
                            inventory_item["category"] = reward_item["category"]
                        if "season" in reward_item:
                            inventory_item["season"] = reward_item["season"]
                        if "event" in reward_item:
                            inventory_item["event"] = reward_item["event"]

                        inventory[str(reward_item["id"])] = inventory_item

                    update_data["inventory"] = json.dumps(inventory)
                    reward_message = f"Você recebeu: {reward_item['name']} (Raridade: {rarity.capitalize()})"

            # Currency reward
            if "currency" in exchange["reward"]:
                req = exchange["reward"]["currency"]
                currency_type = req.get("type", "TUSD")
                amount = req.get("amount", 0)

                if currency_type == "TUSD":
                    update_data["tusd"] = player["tusd"] + amount
                    reward_message = f"Você recebeu: {amount} TUSD"
                elif currency_type == "seasonal_token":
                    # Get current season token
                    story_progress = player.get('story_progress', {})
                    bimestre = story_progress.get('bimestre_corrente', 1)
                    season = SEASONS.get(bimestre, "spring")
                    season_token = f"{season}_token"

                    alt_currencies = player.get("currencies", {})
                    alt_currencies[season_token] = alt_currencies.get(season_token, 0) + amount
                    update_data["currencies"] = json.dumps(alt_currencies)

                    currency_info = ALTERNATIVE_CURRENCIES.get(season_token, {"name": season_token})
                    reward_message = f"Você recebeu: {amount} {currency_info['name']}"
                else:
                    alt_currencies = player.get("currencies", {})
                    alt_currencies[currency_type] = alt_currencies.get(currency_type, 0) + amount
                    update_data["currencies"] = json.dumps(alt_currencies)

                    currency_info = ALTERNATIVE_CURRENCIES.get(currency_type, {"name": currency_type})
                    reward_message = f"Você recebeu: {amount} {currency_info['name']}"

            # Update player data
            update_player(interaction.user.id, update_data)

            # Set cooldown (1 hour)
            self.exchange_cooldowns[user_id] = now + 3600

            await interaction.response.send_message(
                f"{interaction.user.mention}, troca realizada com sucesso!\n{reward_message}\n"
                f"Você poderá fazer outra troca em 1 hora."
            )

    @economy_group.command(name="usar", description="Usar um item do inventário")
    async def slash_use_item(self, interaction: discord.Interaction, item_id: int):
        """Slash command version of the use_item command."""
        try:
            # Check if player exists
            player = get_player(interaction.user.id)
            if not player:
                await interaction.response.send_message(f"{interaction.user.mention}, você ainda não está registrado na Academia Tokugawa. Use /registro ingressar para criar seu personagem.")
                return

            # Check if player has the item
            inventory = player["inventory"]
            if str(item_id) not in inventory:
                await interaction.response.send_message(f"{interaction.user.mention}, você não possui este item em seu inventário.", ephemeral=True)
                return

            # Get item data
            item_data = inventory[str(item_id)]

            # Check if item is usable
            if item_data["type"] != "consumable":
                await interaction.response.send_message(f"{interaction.user.mention}, este item não pode ser usado diretamente. Itens do tipo {item_data['type']} são aplicados automaticamente.", ephemeral=True)
                return

            # Process item use
            update_data = {}
            use_message = ""

            # Handle different item effects
            if "cooldown_reduction" in item_data["effects"]:
                # Reduce cooldown for a command
                command = item_data["effects"]["cooldown_reduction"]["command"]
                amount = item_data["effects"]["cooldown_reduction"]["amount"]

                # Check if command is on cooldown
                if interaction.user.id in COOLDOWNS and command in COOLDOWNS[interaction.user.id]:
                    COOLDOWNS[interaction.user.id][command] -= amount
                    use_message = f"Você usou {item_data['name']} e reduziu o cooldown do comando /{command} em 30 minutos!"
                else:
                    await interaction.response.send_message(f"{interaction.user.mention}, este comando não está em cooldown no momento.", ephemeral=True)
                    return

            elif "club_reputation" in item_data["effects"]:
                # Increase club reputation
                if not player["club_id"]:
                    await interaction.response.send_message(f"{interaction.user.mention}, você precisa estar em um clube para usar este item.", ephemeral=True)
                    return

                # Get club data
                club = get_club(player["club_id"])
                if not club:
                    await interaction.response.send_message(f"{interaction.user.mention}, seu clube não existe mais.")
                    return

                # TODO: Implement club reputation update
                use_message = f"Você usou {item_data['name']} e aumentou sua reputação no clube {club['name']}!"

            elif "potion" in item_data["effects"]:
                # Handle potion effects
                potion_type = item_data["effects"]["potion"]["type"]
                amount = item_data["effects"]["potion"]["amount"]

                if potion_type == "training":
                    # Training potion increases experience
                    update_data["exp"] = player["exp"] + amount
                    use_message = f"Você bebeu {item_data['name']} e ganhou {amount} de experiência! Seu treinamento foi acelerado."

                elif potion_type == "attribute":
                    # Attribute potion increases a specific attribute
                    attribute = item_data["effects"]["potion"]["attribute"]
                    if attribute in ["dexterity", "intellect", "charisma", "power_stat"]:
                        update_data[attribute] = player[attribute] + amount
                        attribute_names = {
                            "dexterity": "Destreza",
                            "intellect": "Intelecto",
                            "charisma": "Carisma",
                            "power_stat": "Poder"
                        }
                        use_message = f"Você bebeu {item_data['name']} e aumentou seu atributo de {attribute_names[attribute]} em {amount} pontos!"
                    else:
                        await interaction.response.send_message(f"{interaction.user.mention}, esta poção tem um atributo inválido.", ephemeral=True)
                        return

                elif potion_type == "currency":
                    # Currency potion increases TUSD
                    update_data["tusd"] = player["tusd"] + amount
                    use_message = f"Você bebeu {item_data['name']} e ganhou {amount} TUSD! Sua carteira está mais cheia."

                elif potion_type == "health":
                    # Health potion would be used in combat (not implemented yet)
                    use_message = f"Você bebeu {item_data['name']} e se sente revigorado! Sua saúde foi restaurada."

                else:
                    await interaction.response.send_message(f"{interaction.user.mention}, este tipo de poção não é reconhecido.", ephemeral=True)
                    return

            else:
                await interaction.response.send_message(f"{interaction.user.mention}, este item não pode ser usado no momento.", ephemeral=True)
                return

            # Remove item from inventory
            inventory[str(item_id)]["quantity"] -= 1
            if inventory[str(item_id)]["quantity"] <= 0:
                del inventory[str(item_id)]

            update_data["inventory"] = json.dumps(inventory)

            # Update player in database
            success = update_player(interaction.user.id, **update_data)

            if success:
                # Create use confirmation embed
                rarity = RARITIES.get(item_data["rarity"], RARITIES["common"])
                embed = create_basic_embed(
                    title="Item Usado!",
                    description=use_message,
                    color=rarity["color"]
                )

                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message("Ocorreu um erro ao usar o item. Por favor, tente novamente mais tarde.")
        except discord.errors.NotFound:
            # If the interaction has expired, log it but don't try to respond
            logger.warning(f"Interaction expired for user {interaction.user.id} when using /economia usar")
        except Exception as e:
            logger.error(f"Error in slash_use_item: {e}")

    @economy_group.command(name="equipar", description="Equipar um acessório do inventário")
    async def slash_equip_item(self, interaction: discord.Interaction, item_id: int):
        """Slash command to equip an accessory item."""
        try:
            # Check if player exists
            player = get_player(interaction.user.id)
            if not player:
                await interaction.response.send_message(f"{interaction.user.mention}, você ainda não está registrado na Academia Tokugawa. Use /registro ingressar para criar seu personagem.")
                return

            # Check if player has the item
            inventory = player["inventory"]
            if str(item_id) not in inventory:
                await interaction.response.send_message(f"{interaction.user.mention}, você não possui este item em seu inventário.", ephemeral=True)
                return

            # Get item data
            item_data = inventory[str(item_id)]

            # Check if item is an accessory
            if item_data["type"] != "accessory":
                await interaction.response.send_message(f"{interaction.user.mention}, apenas acessórios podem ser equipados. Este item é do tipo {item_data['type']}.", ephemeral=True)
                return

            # Check if the item is already equipped
            if item_data.get("equipped", False):
                # Unequip the item
                inventory[str(item_id)]["equipped"] = False
                update_data = {"inventory": json.dumps(inventory)}
                success = update_player(interaction.user.id, **update_data)

                if success:
                    embed = create_basic_embed(
                        title="Acessório Desequipado!",
                        description=f"Você desequipou {item_data['name']}.",
                        color=RARITIES.get(item_data["rarity"], RARITIES["common"])["color"]
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                else:
                    await interaction.response.send_message("Ocorreu um erro ao desequipar o acessório. Por favor, tente novamente mais tarde.")
                return

            # Check if there's a cooldown for this accessory
            cooldown = self._check_cooldown(interaction.user.id, f"accessory_{item_id}")
            if cooldown:
                await interaction.response.send_message(f"{interaction.user.mention}, este acessório está em cooldown. Tempo restante: {cooldown}", ephemeral=True)
                return

            # Unequip any other equipped accessories of the same type
            for inv_item_id, inv_item in inventory.items():
                if inv_item["type"] == "accessory" and inv_item.get("equipped", False):
                    inventory[inv_item_id]["equipped"] = False

            # Equip the new accessory
            inventory[str(item_id)]["equipped"] = True

            # Set cooldown for this accessory (4 hours)
            self._set_cooldown(interaction.user.id, f"accessory_{item_id}", 14400)  # 4 hours in seconds

            # Update player in database
            update_data = {"inventory": json.dumps(inventory)}
            success = update_player(interaction.user.id, **update_data)

            if success:
                # Create equip confirmation embed
                rarity = RARITIES.get(item_data["rarity"], RARITIES["common"])
                embed = create_basic_embed(
                    title="Acessório Equipado!",
                    description=f"Você equipou {item_data['name']}. Os efeitos do acessório estão ativos!",
                    color=rarity["color"]
                )

                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message("Ocorreu um erro ao equipar o acessório. Por favor, tente novamente mais tarde.")
        except discord.errors.NotFound:
            # If the interaction has expired, log it but don't try to respond
            logger.warning(f"Interaction expired for user {interaction.user.id} when using /economia equipar")
        except Exception as e:
            logger.error(f"Error in slash_equip_item: {e}")

    @commands.command(name="loja")
    async def shop(self, ctx):
        """Acessar a loja da Academia Tokugawa."""
        # Check if player exists
        player = get_player(ctx.author.id)
        if not player:
            await ctx.send(f"{ctx.author.mention}, você ainda não está registrado na Academia Tokugawa. Use !ingressar para criar seu personagem.")
            return

        # Create shop embed
        embed = create_basic_embed(
            title="Loja da Academia Tokugawa",
            description=f"Bem-vindo à loja oficial da Academia! Você tem {player['tusd']} TUSD 💰\n\n"
                        f"Para comprar um item, use o comando `!comprar <id>`",
            color=0xFFD700  # Gold
        )

        # Add items to embed
        for item in SHOP_ITEMS:
            rarity = RARITIES.get(item["rarity"], RARITIES["common"])
            embed.add_field(
                name=f"{item['id']}. {rarity['emoji']} {item['name']} - {item['price']} TUSD",
                value=f"{item['description']}\nTipo: {item['type'].capitalize()}",
                inline=False
            )

        await ctx.send(embed=embed, ephemeral=True)

    @commands.command(name="comprar")
    async def buy(self, ctx, item_id: int = None):
        """Comprar um item da loja."""
        # Check if player exists
        player = get_player(ctx.author.id)
        if not player:
            await ctx.send(f"{ctx.author.mention}, você ainda não está registrado na Academia Tokugawa. Use !ingressar para criar seu personagem.")
            return

        # Check if item_id is provided
        if item_id is None:
            await ctx.send(f"{ctx.author.mention}, você precisa especificar o ID do item que deseja comprar. Use `!loja` para ver os itens disponíveis.", ephemeral=True)
            return

        # Find the item
        item = next((i for i in SHOP_ITEMS if i["id"] == item_id), None)
        if not item:
            await ctx.send(f"{ctx.author.mention}, item não encontrado. Use `!loja` para ver os itens disponíveis.", ephemeral=True)
            return

        # Check if player has enough TUSD
        if player["tusd"] < item["price"]:
            await ctx.send(f"{ctx.author.mention}, você não tem TUSD suficiente para comprar este item. Preço: {item['price']} TUSD, Seu saldo: {player['tusd']} TUSD", ephemeral=True)
            return

        # Process the purchase
        inventory = player["inventory"]

        # Add item to inventory
        if str(item["id"]) in inventory:
            # If player already has this item, increase quantity
            inventory[str(item["id"])]["quantity"] += 1
        else:
            # Add new item to inventory
            inventory[str(item["id"])] = {
                "id": item["id"],
                "name": item["name"],
                "description": item["description"],
                "type": item["type"],
                "rarity": item["rarity"],
                "effects": item["effects"],
                "quantity": 1
            }

        # Update player data
        update_data = {
            "tusd": player["tusd"] - item["price"],
            "inventory": json.dumps(inventory)
        }

        # Special handling for permanent attribute items
        if item["type"] == "consumable" and "permanent_attribute" in item["effects"]:
            # Choose a random attribute to increase
            attribute = random.choice(["dexterity", "intellect", "charisma", "power_stat"])
            update_data[attribute] = player[attribute] + item["effects"]["permanent_attribute"]

            # Remove the item from inventory since it's consumed immediately
            inventory[str(item["id"])]["quantity"] -= 1
            if inventory[str(item["id"])]["quantity"] <= 0:
                del inventory[str(item["id"])]

            update_data["inventory"] = json.dumps(inventory)

        # Special handling for technique scrolls
        if item["type"] == "consumable" and "learn_technique" in item["effects"]:
            # Choose a random technique
            technique = random.choice(TECHNIQUES)
            techniques = player["techniques"]

            if str(technique["id"]) not in techniques:
                techniques[str(technique["id"])] = technique
                update_data["techniques"] = json.dumps(techniques)

                # Remove the item from inventory since it's consumed immediately
                inventory[str(item["id"])]["quantity"] -= 1
                if inventory[str(item["id"])]["quantity"] <= 0:
                    del inventory[str(item["id"])]

                update_data["inventory"] = json.dumps(inventory)

        # Update player in database
        success = update_player(ctx.author.id, **update_data)

        if success:
            # Create purchase confirmation embed
            rarity = RARITIES.get(item["rarity"], RARITIES["common"])
            embed = create_basic_embed(
                title="Compra Realizada!",
                description=f"Você comprou {rarity['emoji']} **{item['name']}** por {item['price']} TUSD.\n\n"
                            f"Saldo atual: {update_data['tusd']} TUSD 💰",
                color=rarity["color"]
            )

            # Add special messages for consumed items
            if item["type"] == "consumable" and "permanent_attribute" in item["effects"]:
                attribute_names = {
                    "dexterity": "Destreza 🏃‍♂️",
                    "intellect": "Intelecto 🧠",
                    "charisma": "Carisma 💬",
                    "power_stat": "Poder ⚡"
                }
                embed.add_field(
                    name="Item Consumido!",
                    value=f"O Elixir aumentou seu atributo de {attribute_names[attribute]} em +{item['effects']['permanent_attribute']}!",
                    inline=False
                )

            if item["type"] == "consumable" and "learn_technique" in item["effects"] and "techniques" in update_data:
                embed.add_field(
                    name="Técnica Aprendida!",
                    value=f"Você aprendeu a técnica **{technique['name']}**!\n{technique['description']}",
                    inline=False
                )

            await ctx.send(embed=embed, ephemeral=True)
        else:
            await ctx.send("Ocorreu um erro durante a compra. Por favor, tente novamente mais tarde.")

    @commands.command(name="mercado")
    async def market(self, ctx):
        """Acessar o mercado de itens entre jogadores."""
        # Check if player exists
        player = get_player(ctx.author.id)
        if not player:
            await ctx.send(f"{ctx.author.mention}, você ainda não está registrado na Academia Tokugawa. Use !ingressar para criar seu personagem.")
            return

        # Create market embed
        embed = create_basic_embed(
            title="Mercado da Academia Tokugawa",
            description=f"Bem-vindo ao mercado de itens entre alunos! Você tem {player['tusd']} TUSD 💰\n\n"
                        f"Para vender um item, use `!vender <id_do_item> <preço>`\n"
                        f"Para comprar um item, use `!comprar_mercado <id_da_listagem>`",
            color=0x00FF00  # Green
        )

        # Add listings to embed
        if not self.market_listings:
            embed.add_field(
                name="Nenhum item à venda",
                value="Seja o primeiro a vender algo no mercado!",
                inline=False
            )
        else:
            for listing_id, listing in self.market_listings.items():
                seller = self.bot.get_user(listing["seller_id"])
                seller_name = seller.display_name if seller else "Desconhecido"

                rarity = RARITIES.get(listing["item_data"]["rarity"], RARITIES["common"])
                embed.add_field(
                    name=f"{listing_id}. {rarity['emoji']} {listing['item_data']['name']} - {listing['price']} TUSD",
                    value=f"{listing['item_data']['description']}\nVendedor: {seller_name}",
                    inline=False
                )

        await ctx.send(embed=embed, ephemeral=True)

    @commands.command(name="vender")
    async def sell(self, ctx, item_id: int = None, price: int = None):
        """Vender um item no mercado."""
        # Check if player exists
        player = get_player(ctx.author.id)
        if not player:
            await ctx.send(f"{ctx.author.mention}, você ainda não está registrado na Academia Tokugawa. Use !ingressar para criar seu personagem.", ephemeral=True)
            return

        # Check if item_id and price are provided
        if item_id is None or price is None:
            await ctx.send(f"{ctx.author.mention}, você precisa especificar o ID do item e o preço. Exemplo: `!vender 1 100`", ephemeral=True)
            return

        # Check if price is valid
        if price <= 0:
            await ctx.send(f"{ctx.author.mention}, o preço deve ser maior que zero.", ephemeral=True)
            return

        # Check if player has the item
        inventory = player["inventory"]
        if str(item_id) not in inventory:
            await ctx.send(f"{ctx.author.mention}, você não possui este item em seu inventário.", ephemeral=True)
            return

        # Get item data
        item_data = inventory[str(item_id)]

        # Create listing
        listing_id = self.next_listing_id
        self.next_listing_id += 1

        self.market_listings[listing_id] = {
            "seller_id": ctx.author.id,
            "item_id": item_id,
            "price": price,
            "item_data": item_data
        }

        # Remove item from inventory
        inventory[str(item_id)]["quantity"] -= 1
        if inventory[str(item_id)]["quantity"] <= 0:
            del inventory[str(item_id)]

        # Update player in database
        success = update_player(ctx.author.id, inventory=json.dumps(inventory))

        if success:
            # Create listing confirmation embed
            rarity = RARITIES.get(item_data["rarity"], RARITIES["common"])
            embed = create_basic_embed(
                title="Item Colocado à Venda!",
                description=f"Você colocou {rarity['emoji']} **{item_data['name']}** à venda por {price} TUSD.\n\n"
                            f"ID da listagem: {listing_id}",
                color=rarity["color"]
            )

            await ctx.send(embed=embed)
        else:
            await ctx.send("Ocorreu um erro ao colocar o item à venda. Por favor, tente novamente mais tarde.")

    @commands.command(name="comprar_mercado")
    async def buy_market(self, ctx, listing_id: int = None):
        """Comprar um item do mercado."""
        # Check if player exists
        player = get_player(ctx.author.id)
        if not player:
            await ctx.send(f"{ctx.author.mention}, você ainda não está registrado na Academia Tokugawa. Use !ingressar para criar seu personagem.", ephemeral=True)
            return

        # Check if listing_id is provided
        if listing_id is None:
            await ctx.send(f"{ctx.author.mention}, você precisa especificar o ID da listagem. Use `!mercado` para ver as listagens disponíveis.", ephemeral=True)
            return

        # Check if listing exists
        if listing_id not in self.market_listings:
            await ctx.send(f"{ctx.author.mention}, listagem não encontrada. Use `!mercado` para ver as listagens disponíveis.", ephemeral=True)
            return

        # Get listing data
        listing = self.market_listings[listing_id]

        # Check if player is trying to buy their own item
        if listing["seller_id"] == ctx.author.id:
            await ctx.send(f"{ctx.author.mention}, você não pode comprar seu próprio item.")
            return

        # Check if player has enough TUSD
        if player["tusd"] < listing["price"]:
            await ctx.send(f"{ctx.author.mention}, você não tem TUSD suficiente para comprar este item. Preço: {listing['price']} TUSD, Seu saldo: {player['tusd']} TUSD")
            return

        # Get seller data
        seller = get_player(listing["seller_id"])
        if not seller:
            await ctx.send(f"{ctx.author.mention}, o vendedor não existe mais. A listagem será removida.")
            del self.market_listings[listing_id]
            return

        # Process the purchase
        buyer_inventory = player["inventory"]

        # Add item to buyer's inventory
        if str(listing["item_id"]) in buyer_inventory:
            # If buyer already has this item, increase quantity
            buyer_inventory[str(listing["item_id"])]["quantity"] += 1
        else:
            # Add new item to inventory
            item_data = listing["item_data"].copy()
            item_data["quantity"] = 1
            buyer_inventory[str(listing["item_id"])] = item_data

        # Update buyer data
        buyer_update = {
            "tusd": player["tusd"] - listing["price"],
            "inventory": json.dumps(buyer_inventory)
        }

        # Update seller data
        seller_update = {
            "tusd": seller["tusd"] + listing["price"]
        }

        # Update both players in database
        buyer_success = update_player(ctx.author.id, **buyer_update)
        seller_success = update_player(listing["seller_id"], **seller_update)

        if buyer_success and seller_success:
            # Remove listing
            del self.market_listings[listing_id]

            # Create purchase confirmation embed
            rarity = RARITIES.get(listing["item_data"]["rarity"], RARITIES["common"])
            embed = create_basic_embed(
                title="Compra Realizada!",
                description=f"Você comprou {rarity['emoji']} **{listing['item_data']['name']}** por {listing['price']} TUSD.\n\n"
                            f"Saldo atual: {buyer_update['tusd']} TUSD 💰",
                color=rarity["color"]
            )

            await ctx.send(embed=embed, ephemeral=True)

            # Notify seller if they're online
            seller_user = self.bot.get_user(listing["seller_id"])
            if seller_user:
                seller_embed = create_basic_embed(
                    title="Item Vendido!",
                    description=f"Seu item {rarity['emoji']} **{listing['item_data']['name']}** foi vendido por {listing['price']} TUSD.\n\n"
                                f"Saldo atual: {seller_update['tusd']} TUSD 💰",
                    color=rarity["color"]
                )

                try:
                    await seller_user.send(embed=seller_embed, ephemeral=True)
                except:
                    # Ignore if we can't DM the seller
                    pass
        else:
            await ctx.send("Ocorreu um erro durante a compra. Por favor, tente novamente mais tarde.")

    @commands.command(name="equipar")
    async def equip_item(self, ctx, item_id: int = None):
        """Equipar um acessório do inventário."""
        # Check if player exists
        player = get_player(ctx.author.id)
        if not player:
            await ctx.send(f"{ctx.author.mention}, você ainda não está registrado na Academia Tokugawa. Use !ingressar para criar seu personagem.")
            return

        # Check if item_id is provided
        if item_id is None:
            await ctx.send(f"{ctx.author.mention}, você precisa especificar o ID do item que deseja equipar. Use `!inventario` para ver seus itens.", ephemeral=True)
            return

        # Check if player has the item
        inventory = player["inventory"]
        if str(item_id) not in inventory:
            await ctx.send(f"{ctx.author.mention}, você não possui este item em seu inventário.", ephemeral=True)
            return

        # Get item data
        item_data = inventory[str(item_id)]

        # Check if item is an accessory
        if item_data["type"] != "accessory":
            await ctx.send(f"{ctx.author.mention}, apenas acessórios podem ser equipados. Este item é do tipo {item_data['type']}.", ephemeral=True)
            return

        # Check if the item is already equipped
        if item_data.get("equipped", False):
            # Unequip the item
            inventory[str(item_id)]["equipped"] = False
            update_data = {"inventory": json.dumps(inventory)}
            success = update_player(ctx.author.id, **update_data)

            if success:
                embed = create_basic_embed(
                    title="Acessório Desequipado!",
                    description=f"Você desequipou {item_data['name']}.",
                    color=RARITIES.get(item_data["rarity"], RARITIES["common"])["color"]
                )
                await ctx.send(embed=embed, ephemeral=True)
            else:
                await ctx.send("Ocorreu um erro ao desequipar o acessório. Por favor, tente novamente mais tarde.")
            return

        # Check if there's a cooldown for this accessory
        cooldown = self._check_cooldown(ctx.author.id, f"accessory_{item_id}")
        if cooldown:
            await ctx.send(f"{ctx.author.mention}, este acessório está em cooldown. Tempo restante: {cooldown}")
            return

        # Unequip any other equipped accessories of the same type
        for inv_item_id, inv_item in inventory.items():
            if inv_item["type"] == "accessory" and inv_item.get("equipped", False):
                inventory[inv_item_id]["equipped"] = False

        # Equip the new accessory
        inventory[str(item_id)]["equipped"] = True

        # Set cooldown for this accessory (4 hours)
        self._set_cooldown(ctx.author.id, f"accessory_{item_id}", 14400)  # 4 hours in seconds

        # Update player in database
        update_data = {"inventory": json.dumps(inventory)}
        success = update_player(ctx.author.id, **update_data)

        if success:
            # Create equip confirmation embed
            rarity = RARITIES.get(item_data["rarity"], RARITIES["common"])
            embed = create_basic_embed(
                title="Acessório Equipado!",
                description=f"Você equipou {item_data['name']}. Os efeitos do acessório estão ativos!",
                color=rarity["color"]
            )

            await ctx.send(embed=embed, ephemeral=True)
        else:
            await ctx.send("Ocorreu um erro ao equipar o acessório. Por favor, tente novamente mais tarde.")

    @commands.command(name="usar")
    async def use_item(self, ctx, item_id: int = None):
        """Usar um item do inventário."""
        # Check if player exists
        player = get_player(ctx.author.id)
        if not player:
            await ctx.send(f"{ctx.author.mention}, você ainda não está registrado na Academia Tokugawa. Use !ingressar para criar seu personagem.")
            return

        # Check if item_id is provided
        if item_id is None:
            await ctx.send(f"{ctx.author.mention}, você precisa especificar o ID do item que deseja usar. Use `!inventario` para ver seus itens.", ephemeral=True)
            return

        # Check if player has the item
        inventory = player["inventory"]
        if str(item_id) not in inventory:
            await ctx.send(f"{ctx.author.mention}, você não possui este item em seu inventário.", ephemeral=True)
            return

        # Get item data
        item_data = inventory[str(item_id)]

        # Check if item is usable
        if item_data["type"] != "consumable":
            await ctx.send(f"{ctx.author.mention}, este item não pode ser usado diretamente. Itens do tipo {item_data['type']} são aplicados automaticamente.", ephemeral=True)
            return

        # Process item use
        update_data = {}
        use_message = ""

        # Handle different item effects
        if "cooldown_reduction" in item_data["effects"]:
            # Reduce cooldown for a command
            command = item_data["effects"]["cooldown_reduction"]["command"]
            amount = item_data["effects"]["cooldown_reduction"]["amount"]

            # Check if command is on cooldown
            if ctx.author.id in COOLDOWNS and command in COOLDOWNS[ctx.author.id]:
                COOLDOWNS[ctx.author.id][command] -= amount
                use_message = f"Você usou {item_data['name']} e reduziu o cooldown do comando !{command} em 30 minutos!"
            else:
                await ctx.send(f"{ctx.author.mention}, este comando não está em cooldown no momento.", ephemeral=True)
                return

        elif "club_reputation" in item_data["effects"]:
            # Increase club reputation
            if not player["club_id"]:
                await ctx.send(f"{ctx.author.mention}, você precisa estar em um clube para usar este item.", ephemeral=True)
                return

            # Get club data
            club = get_club(player["club_id"])
            if not club:
                await ctx.send(f"{ctx.author.mention}, seu clube não existe mais.", ephemeral=True)
                return

            # TODO: Implement club reputation update
            use_message = f"Você usou {item_data['name']} e aumentou sua reputação no clube {club['name']}!"

        elif "potion" in item_data["effects"]:
            # Handle potion effects
            potion_type = item_data["effects"]["potion"]["type"]
            amount = item_data["effects"]["potion"]["amount"]

            if potion_type == "training":
                # Training potion increases experience
                update_data["exp"] = player["exp"] + amount
                use_message = f"Você bebeu {item_data['name']} e ganhou {amount} de experiência! Seu treinamento foi acelerado."

            elif potion_type == "attribute":
                # Attribute potion increases a specific attribute
                attribute = item_data["effects"]["potion"]["attribute"]
                if attribute in ["dexterity", "intellect", "charisma", "power_stat"]:
                    update_data[attribute] = player[attribute] + amount
                    attribute_names = {
                        "dexterity": "Destreza",
                        "intellect": "Intelecto",
                        "charisma": "Carisma",
                        "power_stat": "Poder"
                    }
                    use_message = f"Você bebeu {item_data['name']} e aumentou seu atributo de {attribute_names[attribute]} em {amount} pontos!"
                else:
                    await ctx.send(f"{ctx.author.mention}, esta poção tem um atributo inválido.", ephemeral=True)
                    return

            elif potion_type == "currency":
                # Currency potion increases TUSD
                update_data["tusd"] = player["tusd"] + amount
                use_message = f"Você bebeu {item_data['name']} e ganhou {amount} TUSD! Sua carteira está mais cheia."

            elif potion_type == "health":
                # Health potion would be used in combat (not implemented yet)
                use_message = f"Você bebeu {item_data['name']} e se sente revigorado! Sua saúde foi restaurada."

            else:
                await ctx.send(f"{ctx.author.mention}, este tipo de poção não é reconhecido.", ephemeral=True)
                return

        else:
            await ctx.send(f"{ctx.author.mention}, este item não pode ser usado no momento.", ephemeral=True)
            return

        # Remove item from inventory
        inventory[str(item_id)]["quantity"] -= 1
        if inventory[str(item_id)]["quantity"] <= 0:
            del inventory[str(item_id)]

        update_data["inventory"] = json.dumps(inventory)

        # Update player in database
        success = update_player(ctx.author.id, **update_data)

        if success:
            # Create use confirmation embed
            rarity = RARITIES.get(item_data["rarity"], RARITIES["common"])
            embed = create_basic_embed(
                title="Item Usado!",
                description=use_message,
                color=rarity["color"]
            )

            await ctx.send(embed=embed, ephemeral=True)
        else:
            await ctx.send("Ocorreu um erro ao usar o item. Por favor, tente novamente mais tarde.")

async def setup(bot):
    """Add the cog to the bot."""
    cog = Economy(bot)
    await bot.add_cog(cog)
    logger.info("Economy cog loaded")

    # Add the economy_group to the bot's command tree
    try:
        bot.tree.add_command(cog.economy_group)
        logger.info(f"Added economy_group to command tree: /{cog.economy_group.name}")
    except discord.app_commands.errors.CommandAlreadyRegistered:
        logger.info(f"Economy_group already registered: /{cog.economy_group.name}")

    # Add the technique_group to the bot's command tree
    try:
        bot.tree.add_command(cog.technique_group)
        logger.info(f"Added technique_group to command tree: /{cog.technique_group.name}")
    except discord.app_commands.errors.CommandAlreadyRegistered:
        logger.info(f"Technique_group already registered: /{cog.technique_group.name}")

    # Log the slash commands that were added
    for cmd in cog.__cog_app_commands__:
        logger.info(f"Economy cog added slash command: /{cmd.name}")
