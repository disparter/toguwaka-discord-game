import discord
from datetime import datetime
from utils.game_mechanics import STRENGTH_LEVELS, RARITIES, calculate_exp_progress, calculate_hp_factor
import json
from utils.persistence.db_provider import db_provider
from utils.club_perks import get_club_perk_description
from typing import Dict, Optional, Any

def create_basic_embed(title, description=None, color=0x1E90FF):
    """Create a basic embed with the Academia Tokugawa theme."""
    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        timestamp=datetime.utcnow()
    )
    embed.set_footer(text="Academia Tokugawa", icon_url="https://i.imgur.com/example.png")
    return embed

def create_player_embed(player: Dict[str, Any], club: Optional[Dict[str, Any]] = None) -> discord.Embed:
    """Create an embed for player status."""
    # Get player's name and level
    name = player.get('name', 'No Name')
    level = player.get('level', 1)
    exp = player.get('exp', 0)
    tusd = player.get('tusd', 0)
    hp = player.get('hp', 100)
    max_hp = player.get('max_hp', 100)
    dexterity = player.get('dexterity', 10)
    intellect = player.get('intellect', 10)
    charisma = player.get('charisma', 10)
    power_stat = player.get('power_stat', 10)
    reputation = player.get('reputation', 0)
    strength_level = player.get('strength_level', 1)
    power = player.get('power', 'no_power')

    # Calculate HP factor and regeneration
    hp_factor = calculate_hp_factor(hp, max_hp)
    regeneration = player.get('regeneration', 0)
    regeneration_text = f"🔄 +{regeneration}/hora" if regeneration > 0 else ""

    # Calculate debuff percentage
    debuff_percentage = int((1 - hp_factor) * 100) if hp_factor < 1 else 0
    debuff_text = f"⚠️ -{debuff_percentage}% atributos" if debuff_percentage > 0 else ""

    # Get club color if available
    color = 0x1E90FF  # Default color
    if club and isinstance(club, dict) and 'club_id' in club:
        color = club_colors.get(club['club_id'], 0x1E90FF)

    # Create embed
    embed = discord.Embed(
        title=f"{name} - Nível {level}",
        description=f"**Experiência:** {exp}\n**TUSD:** {tusd} 💰",
        color=color
    )

    # Add stats with HP factor and regeneration info
    hp_text = f"**HP:** {hp}/{max_hp} ❤️"
    if regeneration > 0:
        hp_text += f" {regeneration_text}"
    if debuff_percentage > 0:
        hp_text += f"\n{debuff_text}"

    embed.add_field(
        name="Atributos",
        value=(
            f"{hp_text}\n"
            f"**Destreza:** {dexterity} 🏃‍♂️\n"
            f"**Intelecto:** {intellect} 🧠\n"
            f"**Carisma:** {charisma} 💬\n"
            f"**Poder:** {power_stat} ⚡\n"
            f"**Reputação:** {reputation} 🌟\n"
            f"**Nível de Força:** {strength_level} 💪"
        ),
        inline=True
    )

    # Add club info if available
    if club and isinstance(club, dict):
        club_name = club.get('name', 'Sem Clube')
        club_description = club.get('description', 'Sem descrição')
        embed.add_field(
            name="Clube",
            value=f"**{club_name}**\n{club_description}",
            inline=True
        )

    # Add power info
    if power != 'no_power':
        embed.add_field(
            name="Poder",
            value=f"**{power}**",
            inline=True
        )

    return embed

async def create_club_embed(club):
    """Create an embed displaying club information."""
    # Determine color based on club
    club_colors = {
        1: 0xFF0000,  # Clube das Chamas - Red
        2: 0x800080,  # Ilusionistas Mentais - Purple
        3: 0xFFD700,  # Conselho Político - Gold
        4: 0x00FF00,  # Elementalistas - Green
        5: 0x808080   # Clube de Combate - Gray
    }
    color = club_colors.get(club['club_id'], 0x1E90FF)

    # Create embed
    embed = discord.Embed(
        title=club['name'],
        description=club['description'],
        color=color,
        timestamp=datetime.utcnow()
    )

    # Get club leader from NPCs
    club_leader_name = club.get('leader_name', 'Nenhum')
    if club.get('club_id'):
        # Get NPCs for this club
        npcs = await db_provider.get_relevant_npcs(club['club_id'])
        # Find the leader
        for npc in npcs:
            if npc.get('role') == 'Líder':
                club_leader_name = npc.get('name')
                break

    # Add club stats
    embed.add_field(
        name="Estatísticas",
        value=f"**Membros:** {club['members_count']} 👥\n"
              f"**Reputação:** {club['reputation']} 🏆\n"
              f"**Líder:** {club_leader_name}",
        inline=True
    )

    # Add club perks
    club_id = club.get('club_id')
    if club_id:
        perk_description = get_club_perk_description(club_id)
        embed.add_field(
            name="Bônus de Clube",
            value=perk_description,
            inline=True
        )

    # Add footer
    embed.set_footer(text="Academia Tokugawa", icon_url="https://i.imgur.com/example.png")

    return embed

def create_duel_embed(duel_result):
    """Create an embed displaying duel results."""
    winner = duel_result["winner"]
    loser = duel_result["loser"]

    # Determine color based on duel type
    duel_colors = {
        "physical": 0xFF0000,  # Red
        "mental": 0x800080,    # Purple
        "strategic": 0x008000, # Green
        "social": 0xFFD700,    # Gold
        "elemental": 0x00FFFF  # Cyan
    }
    color = duel_colors.get(duel_result["duel_type"], 0x1E90FF)

    # Create embed
    embed = discord.Embed(
        title=f"Resultado do Duelo: {duel_result['duel_type'].capitalize()}",
        description=duel_result["narration"],
        color=color,
        timestamp=datetime.utcnow()
    )

    # Add winner and loser info
    embed.add_field(
        name="Vencedor",
        value=f"**{winner['name']}**\nNível {winner['level']}\nGanhou {duel_result['exp_reward']} EXP e {duel_result['tusd_reward']} TUSD",
        inline=True
    )

    embed.add_field(
        name="Perdedor",
        value=f"**{loser['name']}**\nNível {loser['level']}\nGanhou {duel_result['exp_reward']//2} EXP",
        inline=True
    )

    # Add club perks info if any were applied
    if "club_perks_applied" in duel_result and duel_result["club_perks_applied"]:
        perks_text = []
        for club, perk_description in duel_result["club_perks_applied"].items():
            club_names = {
                "clube_das_chamas": "🔥 Clube das Chamas",
                "ilusionistas_mentais": "🧠 Ilusionistas Mentais",
                "elementalistas": "🌪️ Elementalistas",
                "clube_de_combate": "⚔️ Clube de Combate"
            }
            club_name = club_names.get(club, club)
            perks_text.append(f"**{club_name}**: {perk_description}")

        embed.add_field(
            name="Bônus de Clube Aplicados",
            value="\n".join(perks_text),
            inline=False
        )

    # Add bonus rewards info if any were awarded
    if "bonus_rewards" in duel_result and duel_result["bonus_rewards"]:
        bonus_rewards = duel_result["bonus_rewards"]
        if "item" in bonus_rewards:
            embed.add_field(
                name="🎁 Recompensa Bônus",
                value=f"**{bonus_rewards['item_name']}**\n{bonus_rewards['item_description']}",
                inline=False
            )

    # Add footer
    embed.set_footer(text="Academia Tokugawa", icon_url="https://i.imgur.com/example.png")

    return embed

def create_event_embed(event):
    """Create an embed displaying an event."""
    # Determine color based on event type
    event_colors = {
        "positive": 0x00FF00,  # Green
        "negative": 0xFF0000,  # Red
        "neutral": 0xFFFF00    # Yellow
    }
    color = event_colors.get(event["type"], 0x1E90FF)

    # Rarity colors (override event type color for rare+ events)
    rarity_colors = {
        "rare": 0x0000FF,      # Blue
        "epic": 0x800080,      # Purple
        "legendary": 0xFFA500  # Orange
    }

    # If event has rarity, use it for color for rare+ events
    if "rarity" in event and event["rarity"] in rarity_colors:
        color = rarity_colors[event["rarity"]]

    # Rarity emoji
    rarity_emoji = {
        "common": "🔘",
        "uncommon": "🟢",
        "rare": "🔵",
        "epic": "🟣",
        "legendary": "🟠"
    }

    # Category emoji
    category_emoji = {
        "social": "👥",
        "training": "💪",
        "combat": "⚔️",
        "discovery": "🔍",
        "club": "🏛️",
        "special": "✨",
        "general": "📜"
    }

    # Create title with rarity and category if available
    title = event["title"]
    if "rarity" in event and "category" in event:
        emoji_rarity = rarity_emoji.get(event["rarity"], "")
        emoji_category = category_emoji.get(event["category"], "")
        title = f"{emoji_rarity} {title} {emoji_category}"

    # Create embed
    embed = discord.Embed(
        title=title,
        description=event["description"],
        color=color,
        timestamp=datetime.utcnow()
    )

    # Add category and rarity if available
    if "category" in event or "rarity" in event:
        category_text = event.get("category", "").capitalize() if "category" in event else ""
        rarity_text = event.get("rarity", "").capitalize() if "rarity" in event else ""

        if category_text and rarity_text:
            info_text = f"**Categoria:** {category_text} | **Raridade:** {rarity_text}"
        elif category_text:
            info_text = f"**Categoria:** {category_text}"
        else:
            info_text = f"**Raridade:** {rarity_text}"

        embed.add_field(
            name="Informações",
            value=info_text,
            inline=False
        )

    # Add effects from the event object directly
    effects = []

    # Experience change
    if "exp_change" in event:
        effects.append(f"**Experiência:** {'+' if event['exp_change'] > 0 else ''}{event['exp_change']} EXP")

    # TUSD change
    if "tusd_change" in event:
        effects.append(f"**TUSD:** {'+' if event['tusd_change'] > 0 else ''}{event['tusd_change']} 💰")

    # Primary attribute change
    if "attribute_change" in event:
        attribute_names = {
            "dexterity": "Destreza 🏃‍♂️",
            "intellect": "Intelecto 🧠",
            "charisma": "Carisma 💬",
            "power_stat": "Poder ⚡"
        }
        attr_name = attribute_names.get(event["attribute_change"], event["attribute_change"])
        value = event["attribute_value"]
        effects.append(f"**{attr_name}:** {'+' if value > 0 else ''}{value}")

    # Secondary attribute change (usually negative)
    if "secondary_attribute_change" in event:
        attribute_names = {
            "dexterity": "Destreza 🏃‍♂️",
            "intellect": "Intelecto 🧠",
            "charisma": "Carisma 💬",
            "power_stat": "Poder ⚡"
        }
        attr_name = attribute_names.get(event["secondary_attribute_change"], event["secondary_attribute_change"])
        value = event["secondary_attribute_value"]
        effects.append(f"**{attr_name}:** {'+' if value > 0 else ''}{value}")

    # All attributes boost
    if "all_attributes_change" in event:
        value = event["all_attributes_change"]
        effects.append(f"**Todos os Atributos:** {'+' if value > 0 else ''}{value}")

    # Item reward
    if "item_reward" in event:
        item_text = event["item_reward"]
        if "item_rarity" in event:
            rarity_emoji_item = rarity_emoji.get(event["item_rarity"], "")
            item_text = f"{rarity_emoji_item} {item_text}"
        effects.append(f"**Item:** {item_text}")

    # Duel trigger
    if "trigger_duel" in event and event["trigger_duel"]:
        effects.append("**Duelo:** Desafio para um duelo!")

    # If no effects were added from the event object, try to extract from the effect dictionary
    if not effects and "effect" in event:
        for key, value in event["effect"].items():
            if key == "exp":
                effects.append(f"**Experiência:** {'+' if value > 0 else ''}{value} EXP")
            elif key == "tusd":
                effects.append(f"**TUSD:** {'+' if value > 0 else ''}{value} 💰")
            elif key == "attribute":
                if value == "random":
                    effects.append("**Atributo Bônus:** Aleatório +1")
                else:
                    effects.append(f"**Atributo Bônus:** {value}")
            elif key == "duel" and value:
                effects.append("**Duelo:** Desafio para um duelo!")
            elif key == "item":
                if value == "random":
                    effects.append("**Item:** Item aleatório")
                else:
                    effects.append(f"**Item:** Item {value}")
            elif key in ["dexterity", "intellect", "charisma", "power_stat"]:
                attribute_names = {
                    "dexterity": "Destreza 🏃‍♂️",
                    "intellect": "Intelecto 🧠",
                    "charisma": "Carisma 💬",
                    "power_stat": "Poder ⚡"
                }
                attr_name = attribute_names.get(key, key)
                effects.append(f"**{attr_name}:** {'+' if value > 0 else ''}{value}")
            elif key == "all_attributes" and value:
                effects.append(f"**Todos os Atributos:** +{value}")

    if effects:
        embed.add_field(
            name="Efeitos",
            value="\n".join(effects),
            inline=False
        )

    # Add footer
    embed.set_footer(text="Academia Tokugawa", icon_url="https://i.imgur.com/example.png")

    return embed

def create_inventory_embed(player):
    """Create an embed displaying a player's inventory."""
    embed = discord.Embed(
        title="Inventário",
        color=0x1E90FF,
        timestamp=datetime.utcnow()
    )

    # Garantir que o inventário é um dicionário
    inventory = player.get('inventory', {})
    if isinstance(inventory, str):
        try:
            inventory = json.loads(inventory)
        except Exception:
            inventory = {}
    if not isinstance(inventory, dict):
        inventory = {}

    # Add items if any
    if inventory:
        items_text = []
        for item_id, item in inventory.items():
            items_text.append(f"🔹 **{item['name']}** - {item['description']}")

        embed.add_field(
            name="Itens",
            value="\n".join(items_text) if items_text else "Nenhum item no inventário.",
            inline=False
        )
    else:
        embed.add_field(
            name="Itens",
            value="Nenhum item no inventário.",
            inline=False
        )

    # Add techniques if any
    if player.get('techniques'):
        techniques_text = []
        for tech_id, tech in player['techniques'].items():
            techniques_text.append(f"⚡ **{tech['name']}** - {tech['description']}")

        embed.add_field(
            name="Técnicas",
            value="\n".join(techniques_text) if techniques_text else "Nenhuma técnica aprendida.",
            inline=False
        )
    else:
        embed.add_field(
            name="Técnicas",
            value="Nenhuma técnica aprendida.",
            inline=False
        )

    # Add footer
    embed.set_footer(text="Academia Tokugawa", icon_url="https://i.imgur.com/example.png")

    return embed

def create_progress_bar(percentage, length=10):
    """Create a text-based progress bar."""
    filled = int(percentage / 100 * length)
    bar = "█" * filled + "░" * (length - filled)
    return bar

async def create_leaderboard_embed(players, title="Ranking da Academia Tokugawa"):
    """Create an embed displaying a leaderboard of players."""
    embed = discord.Embed(
        title=title,
        color=0xFFD700,  # Gold
        timestamp=datetime.utcnow()
    )

    if not players:
        embed.description = "Nenhum jogador encontrado."
        return embed

    # Import here to avoid circular imports
    from utils.persistence.db_provider import db_provider

    # Create leaderboard text
    leaderboard_text = ""
    for i, player in enumerate(players, 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."

        # Get club name based on club_id
        club_name = 'Sem clube'
        if player.get('club_id'):
            # Try to get club name from player data first
            if player.get('club_name'):
                club_name = player.get('club_name')
            # Otherwise fetch it from the database
            else:
                # Use the async method directly from db_provider
                club = await db_provider.get_club(str(player.get('club_id')))
                if club and club.get('name'):
                    club_name = club.get('name')

        leaderboard_text += f"{medal} **{player.get('name', 'Desconhecido')}** | {club_name} | Nível: {player.get('level', 1)}\n"

    embed.description = leaderboard_text

    # Add footer
    embed.set_footer(text="Academia Tokugawa", icon_url="https://i.imgur.com/example.png")

    return embed

def create_db_event_embed(event, show_participants=True):
    """Create an embed displaying an event from the database.

    Args:
        event (dict): Event data from the database
        show_participants (bool): Whether to show participants list

    Returns:
        discord.Embed: The created embed
    """
    # Determine if event is active or completed
    is_completed = event.get('completed', False)

    # Set color based on event status
    if is_completed:
        color = 0x808080  # Gray for completed events
    else:
        # Use different colors based on event type
        event_colors = {
            "tournament": 0xFFD700,  # Gold
            "turf_wars": 0xFF4500,   # Orange-Red
            "quiz": 0x1E90FF,        # Dodger Blue
            "duel": 0xFF0000,        # Red
            "minion": 0x800080,      # Purple
            "villain": 0x000000,     # Black
            "item": 0x008000,        # Green
        }
        color = event_colors.get(event.get('type', ''), 0x1E90FF)  # Default blue

    # Format times
    start_time = event.get('start_time', '')
    end_time = event.get('end_time', '')

    # Try to parse ISO format strings to datetime objects
    try:
        if isinstance(start_time, str):
            start_time = datetime.fromisoformat(start_time)
        if isinstance(end_time, str):
            end_time = datetime.fromisoformat(end_time)
    except (ValueError, TypeError):
        # If parsing fails, use the original values
        pass

    # Create embed
    embed = discord.Embed(
        title=event.get('name', 'Evento'),
        description=event.get('description', 'Sem descrição disponível.'),
        color=color,
        timestamp=datetime.utcnow()
    )

    # Add event details
    embed.add_field(
        name="Tipo",
        value=event.get('type', 'Desconhecido').capitalize(),
        inline=True
    )

    embed.add_field(
        name="Status",
        value="Concluído" if is_completed else "Ativo",
        inline=True
    )

    # Format and add times
    if start_time:
        if isinstance(start_time, datetime):
            start_str = start_time.strftime("%d/%m/%Y %H:%M")
        else:
            start_str = start_time
        embed.add_field(
            name="Início",
            value=start_str,
            inline=True
        )

    if end_time:
        if isinstance(end_time, datetime):
            end_str = end_time.strftime("%d/%m/%Y %H:%M")
        else:
            end_str = end_time
        embed.add_field(
            name="Término",
            value=end_str,
            inline=True
        )

    # Add participants if requested and available
    if show_participants and event.get('participants'):
        participants = event.get('participants', [])
        if participants:
            # Limit to first 10 participants if there are many
            if len(participants) > 10:
                participants_text = "\n".join([f"<@{p}>" for p in participants[:10]]) + f"\n... e mais {len(participants) - 10} participantes"
            else:
                participants_text = "\n".join([f"<@{p}>" for p in participants])

            embed.add_field(
                name=f"Participantes ({len(participants)})",
                value=participants_text,
                inline=False
            )

    # Add additional data if available
    data = event.get('data', {})
    if data and isinstance(data, dict):
        # Extract and display relevant data based on event type
        if event.get('type') == 'tournament':
            if 'winner' in data:
                embed.add_field(
                    name="Vencedor",
                    value=f"<@{data['winner']}>",
                    inline=True
                )
        elif event.get('type') == 'turf_wars':
            if 'teams' in data:
                teams_text = []
                for team_name, team_data in data['teams'].items():
                    score = team_data.get('score', 0)
                    teams_text.append(f"**{team_name}**: {score} pontos")
                if teams_text:
                    embed.add_field(
                        name="Times",
                        value="\n".join(teams_text),
                        inline=False
                    )

    # Add footer
    embed.set_footer(text="Academia Tokugawa", icon_url="https://i.imgur.com/example.png")

    return embed
