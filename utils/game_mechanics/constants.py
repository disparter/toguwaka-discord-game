"""
Constants used throughout the game mechanics.
Extracted from the original game_mechanics.py to follow the Single Responsibility Principle.
"""
import math

# HP factor constants
HP_FACTOR_THRESHOLD = 0.5  # Below 50% HP, attributes start to be affected
HP_FACTOR_MIN = 0.7  # At 0% HP, attributes would be at 70% (though players can't reach 0 HP)

# Experience required for each level
# Formula: base_exp * (level ^ 1.5)
BASE_EXP = 100
EXP_LEVELS = {level: math.floor(BASE_EXP * (level ** 1.5)) for level in range(1, 51)}

# Strength level stars (1-5)
STRENGTH_LEVELS = {
    1: "⭐",
    2: "⭐⭐",
    3: "⭐⭐⭐",
    4: "⭐⭐⭐⭐",
    5: "⭐⭐⭐⭐⭐"
}

# Item rarities
RARITIES = {
    "common": {"color": 0x808080, "emoji": "🔘", "multiplier": 1.0},
    "uncommon": {"color": 0x00FF00, "emoji": "🟢", "multiplier": 1.5},
    "rare": {"color": 0x0000FF, "emoji": "🔵", "multiplier": 2.0},
    "epic": {"color": 0x800080, "emoji": "🟣", "multiplier": 3.0},
    "legendary": {"color": 0xFFA500, "emoji": "🟠", "multiplier": 5.0}
}

# Training outcomes
TRAINING_OUTCOMES = [
    "Você treinou intensamente e sentiu seu poder crescer!",
    "Seu treinamento foi produtivo, mas você sabe que pode melhorar.",
    "Você encontrou um novo método de treinamento que potencializa seu poder!",
    "Seu mentor ficou impressionado com seu progresso no treinamento!",
    "Você superou seus limites durante o treino de hoje!",
    "O treinamento foi exaustivo, mas valeu a pena pelo crescimento obtido."
]

# Random events
RANDOM_EVENTS = [
    {
        "title": "Festival dos Poderes",
        "description": "Você foi convidado para o Festival dos Poderes! Ganhe experiência extra por participar.",
        "type": "positive",
        "effect": {"exp": 50, "tusd": 20}
    },
    {
        "title": "Sabotagem no Clube",
        "description": "Seu clube foi sabotado por rivais! Você precisa ajudar na recuperação.",
        "type": "negative",
        "effect": {"exp": 30, "tusd": -10}
    },
    {
        "title": "Mentor Surpresa",
        "description": "Um mentor misterioso ofereceu treinamento especial para você!",
        "type": "positive",
        "effect": {"exp": 100, "attribute": "random"}
    },
    {
        "title": "Desafio Surpresa",
        "description": "Um estudante desconhecido desafiou você para um duelo amistoso!",
        "type": "neutral",
        "effect": {"exp": 40, "duel": True}
    },
    {
        "title": "Artefato Misterioso",
        "description": "Você encontrou um artefato misterioso que aumenta temporariamente seu poder!",
        "type": "positive",
        "effect": {"item": "random"}
    }
]