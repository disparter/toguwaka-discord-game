import random
import math
import logging

logger = logging.getLogger('tokugawa_bot')

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

def calculate_exp_for_level(level):
    """Calculate experience required for a specific level."""
    if level in EXP_LEVELS:
        return EXP_LEVELS[level]
    return math.floor(BASE_EXP * (level ** 1.5))

def calculate_level_from_exp(exp):
    """Calculate level based on total experience."""
    level = 1
    while level < 50 and exp >= calculate_exp_for_level(level + 1):
        level += 1
    return level

def calculate_exp_progress(exp, level):
    """Calculate progress to next level as percentage."""
    current_level_exp = calculate_exp_for_level(level)
    next_level_exp = calculate_exp_for_level(level + 1)
    exp_needed = next_level_exp - current_level_exp
    exp_gained = exp - current_level_exp
    return min(100, max(0, int((exp_gained / exp_needed) * 100)))

def get_random_training_outcome():
    """Get a random training outcome message."""
    return random.choice(TRAINING_OUTCOMES)

def get_random_event():
    """Get a random event."""
    return random.choice(RANDOM_EVENTS)

def calculate_duel_outcome(challenger, opponent, duel_type):
    """Calculate the outcome of a duel between two players."""
    # Different duel types emphasize different attributes
    attribute_weights = {
        "physical": {"dexterity": 0.6, "power_stat": 0.3, "intellect": 0.05, "charisma": 0.05},
        "mental": {"intellect": 0.6, "charisma": 0.2, "dexterity": 0.1, "power_stat": 0.1},
        "strategic": {"intellect": 0.4, "dexterity": 0.3, "power_stat": 0.2, "charisma": 0.1},
        "social": {"charisma": 0.7, "intellect": 0.2, "dexterity": 0.05, "power_stat": 0.05}
    }

    # Default to physical if invalid type
    weights = attribute_weights.get(duel_type, attribute_weights["physical"])

    # Apply HP factor to attributes if available
    challenger_attributes = challenger.copy()
    opponent_attributes = opponent.copy()

    # Apply HP factor to challenger if HP data is available
    if 'hp' in challenger and 'max_hp' in challenger:
        hp_factor = calculate_hp_factor(challenger['hp'], challenger['max_hp'])
        for attr in ['dexterity', 'power_stat', 'intellect', 'charisma']:
            if attr in challenger_attributes:
                challenger_attributes[attr] = challenger_attributes[attr] * hp_factor

    # Apply HP factor to opponent if HP data is available
    if 'hp' in opponent and 'max_hp' in opponent:
        hp_factor = calculate_hp_factor(opponent['hp'], opponent['max_hp'])
        for attr in ['dexterity', 'power_stat', 'intellect', 'charisma']:
            if attr in opponent_attributes:
                opponent_attributes[attr] = opponent_attributes[attr] * hp_factor

    # Calculate weighted scores
    challenger_score = sum(challenger_attributes[attr] * weight for attr, weight in weights.items())
    opponent_score = sum(opponent_attributes[attr] * weight for attr, weight in weights.items())

    # Add randomness factor (±20%)
    challenger_score *= random.uniform(0.8, 1.2)
    opponent_score *= random.uniform(0.8, 1.2)

    # Determine winner
    if challenger_score > opponent_score:
        winner = challenger
        loser = opponent
        win_margin = challenger_score - opponent_score
    else:
        winner = opponent
        loser = challenger
        win_margin = opponent_score - challenger_score

    # Calculate rewards based on margin and level difference
    level_diff = abs(winner["level"] - loser["level"])
    exp_reward = int(30 + (win_margin / 5) + (level_diff * 5))
    tusd_reward = int(10 + (win_margin / 10) + (level_diff * 2))

    # Calculate HP loss for the loser based on win margin
    # Higher win margins cause more HP loss
    hp_loss = min(30, max(5, int(win_margin / 3)))

    return {
        "winner": winner,
        "loser": loser,
        "exp_reward": exp_reward,
        "tusd_reward": tusd_reward,
        "duel_type": duel_type,
        "win_margin": win_margin,
        "hp_loss": hp_loss
    }

def calculate_hp_factor(current_hp, max_hp):
    """Calculate the factor that affects player attributes based on HP.

    When HP is above the threshold (default 50%), there's no effect (factor = 1.0).
    When HP is below the threshold, attributes are reduced linearly down to the minimum factor.

    Args:
        current_hp (int): Player's current HP
        max_hp (int): Player's maximum HP

    Returns:
        float: Factor to multiply attributes by (between HP_FACTOR_MIN and 1.0)
    """
    # Ensure we don't divide by zero
    if max_hp <= 0:
        return 1.0

    # Calculate HP percentage
    hp_percentage = current_hp / max_hp

    # If HP is above the threshold, no effect
    if hp_percentage >= HP_FACTOR_THRESHOLD:
        return 1.0

    # Calculate factor based on how far below threshold the HP is
    # Map hp_percentage from [0, HP_FACTOR_THRESHOLD] to [HP_FACTOR_MIN, 1.0]
    factor = HP_FACTOR_MIN + (1.0 - HP_FACTOR_MIN) * (hp_percentage / HP_FACTOR_THRESHOLD)

    return factor

def generate_duel_narration(duel_result):
    """Generate a narrative description of a duel."""
    winner = duel_result["winner"]
    loser = duel_result["loser"]
    duel_type = duel_result["duel_type"]

    # Intro based on duel type
    intros = {
        "physical": [
            f"Uma batalha física intensa entre {winner['name']} e {loser['name']} começou!",
            f"O ginásio da Academia Tokugawa tremeu com o confronto entre {winner['name']} e {loser['name']}!"
        ],
        "mental": [
            f"Um duelo de mentes brilhantes entre {winner['name']} e {loser['name']} teve início!",
            f"A tensão era palpável enquanto {winner['name']} e {loser['name']} se enfrentavam em um desafio mental!"
        ],
        "strategic": [
            f"Um jogo de estratégia e tática começou entre {winner['name']} e {loser['name']}!",
            f"Como um jogo de xadrez, {winner['name']} e {loser['name']} planejavam cada movimento cuidadosamente!"
        ],
        "social": [
            f"O debate entre {winner['name']} e {loser['name']} atraiu uma multidão de espectadores!",
            f"A influência social estava em jogo enquanto {winner['name']} e {loser['name']} mediam forças!"
        ]
    }

    # Middle part based on margin
    if duel_result["win_margin"] > 20:
        middles = [
            f"{winner['name']} demonstrou clara superioridade durante todo o duelo.",
            f"A vitória de {winner['name']} nunca esteve em dúvida, dominando o confronto."
        ]
    else:
        middles = [
            f"Foi uma disputa acirrada, com ambos os lados mostrando grande habilidade.",
            f"{winner['name']} e {loser['name']} estavam muito equilibrados, mas no final a vitória pendeu para um lado."
        ]

    # Conclusion
    conclusions = [
        f"No final, {winner['name']} emergiu vitorioso, conquistando {duel_result['exp_reward']} de experiência e {duel_result['tusd_reward']} TUSD!",
        f"A vitória foi de {winner['name']}, que ganhou {duel_result['exp_reward']} de experiência e {duel_result['tusd_reward']} TUSD pelo seu desempenho!"
    ]

    # Combine parts
    narration = f"{random.choice(intros.get(duel_type, intros['physical']))}\n\n"
    narration += f"{random.choice(middles)}\n\n"
    narration += f"{random.choice(conclusions)}"

    return narration
