import discord
from datetime import datetime
from utils.game_mechanics import STRENGTH_LEVELS, RARITIES, calculate_exp_progress

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

def create_player_embed(player, club=None):
    """Create an embed displaying player information."""
    # Determine color based on club
    color = 0x1E90FF
    if club:
        # Each club could have its own color
        club_colors = {
            1: 0xFF0000,  # Clube das Chamas - Red
            2: 0x800080,  # Ilusionistas Mentais - Purple
            3: 0xFFD700,  # Conselho Político - Gold
            4: 0x00FF00,  # Elementalistas - Green
            5: 0x808080   # Clube de Combate - Gray
        }
        color = club_colors.get(club.get('club_id', 0), 0x1E90FF)
    
    # Create embed
    embed = discord.Embed(
        title=f"{player['name']} - Nível {player['level']}",
        description=f"**Poder:** {player['power']} {STRENGTH_LEVELS[player['strength_level']]}\n"
                    f"**Clube:** {club['name'] if club else 'Nenhum'}\n"
                    f"**TUSD:** {player['tusd']} 💰",
        color=color,
        timestamp=datetime.utcnow()
    )
    
    # Add attributes
    embed.add_field(
        name="Atributos",
        value=f"**Destreza:** {player['dexterity']} 🏃‍♂️\n"
              f"**Intelecto:** {player['intellect']} 🧠\n"
              f"**Carisma:** {player['charisma']} 💬\n"
              f"**Poder:** {player['power_stat']} ⚡",
        inline=True
    )
    
    # Add experience progress
    exp_progress = calculate_exp_progress(player['exp'], player['level'])
    progress_bar = create_progress_bar(exp_progress)
    embed.add_field(
        name="Experiência",
        value=f"{progress_bar} {exp_progress}%\n"
              f"EXP: {player['exp']}",
        inline=True
    )
    
    # Add footer
    embed.set_footer(text="Academia Tokugawa", icon_url="https://i.imgur.com/example.png")
    
    return embed

def create_club_embed(club):
    """Create an embed displaying club information."""
    # Determine color based on club
    club_colors = {
        1: 0xFF0000,  # Clube das Chamas - Red
        2: 0x800080,  # Ilusionistas Mentais - Purple
        3: 0xFFD700,  # Conselho Político - Gold
        4: 0x00FF00,  # Elementalistas - Green
        5: 0x808080   # Clube de Combate - Gray
    }
    color = club_colors.get(club.get('club_id', 0), 0x1E90FF)
    
    # Create embed
    embed = discord.Embed(
        title=club['name'],
        description=club['description'],
        color=color,
        timestamp=datetime.utcnow()
    )
    
    # Add club stats
    embed.add_field(
        name="Estatísticas",
        value=f"**Membros:** {club['members_count']} 👥\n"
              f"**Reputação:** {club['reputation']} 🏆\n"
              f"**Líder:** {club.get('leader_name', 'Nenhum')}",
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
        "strategic": 0x0000FF, # Blue
        "social": 0xFFD700     # Gold
    }
    color = duel_colors.get(duel_result["duel_type"], 0x1E90FF)
    
    # Create embed
    embed = discord.Embed(
        title=f"Resultado do Duelo: {duel_result['duel_type'].capitalize()}",
        description=duel_result.get("narration", ""),
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
    
    # Create embed
    embed = discord.Embed(
        title=event["title"],
        description=event["description"],
        color=color,
        timestamp=datetime.utcnow()
    )
    
    # Add effects if any
    effects = []
    for key, value in event["effect"].items():
        if key == "exp":
            effects.append(f"**Experiência:** {'+' if value > 0 else ''}{value} EXP")
        elif key == "tusd":
            effects.append(f"**TUSD:** {'+' if value > 0 else ''}{value} 💰")
        elif key == "attribute":
            effects.append(f"**Atributo Bônus:** {value}")
        elif key == "duel":
            effects.append("**Duelo:** Desafio para um duelo!")
        elif key == "item":
            effects.append("**Item:** Recebeu um item especial!")
    
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
    """Create an embed displaying player inventory."""
    embed = discord.Embed(
        title=f"Inventário de {player['name']}",
        description=f"TUSD: {player['tusd']} 💰",
        color=0x1E90FF,
        timestamp=datetime.utcnow()
    )
    
    # Add items if any
    if player['inventory']:
        items_text = []
        for item_id, item in player['inventory'].items():
            rarity = RARITIES.get(item['rarity'], RARITIES['common'])
            items_text.append(f"{rarity['emoji']} **{item['name']}** - {item['description']}")
        
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
    if player['techniques']:
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

def create_leaderboard_embed(players, title="Ranking da Academia Tokugawa"):
    """Create an embed displaying a leaderboard of players."""
    embed = discord.Embed(
        title=title,
        color=0xFFD700,  # Gold
        timestamp=datetime.utcnow()
    )
    
    if not players:
        embed.description = "Nenhum jogador encontrado."
        return embed
    
    # Create leaderboard text
    leaderboard_text = ""
    for i, player in enumerate(players, 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        club_name = player.get('club_name', 'Sem clube')
        leaderboard_text += f"{medal} **{player['name']}** (Nível {player['level']}) - {club_name}\n"
    
    embed.description = leaderboard_text
    
    # Add footer
    embed.set_footer(text="Academia Tokugawa", icon_url="https://i.imgur.com/example.png")
    
    return embed