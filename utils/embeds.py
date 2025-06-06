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
        color = club_colors.get(club['club_id'], 0x1E90FF)

    # Create embed
    embed = discord.Embed(
        title=f"Perfil de {player['name']}",
        description=f"**Poder:** {player['power']}\n**Nível de Força:** {STRENGTH_LEVELS.get(player['strength_level'], 'Desconhecido')}",
        color=color,
        timestamp=datetime.utcnow()
    )

    # Add club information if available
    if club:
        embed.add_field(
            name="Clube",
            value=f"**{club['name']}**\n{club['description']}",
            inline=False
        )

    # Add attributes
    embed.add_field(
        name="Atributos",
        value=f"**Destreza:** {player['dexterity']} 🏃\n"
              f"**Intelecto:** {player['intellect']} 🧠\n"
              f"**Carisma:** {player['charisma']} 💫\n"
              f"**Poder:** {player['power_stat']} 💪",
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
    # Import club perks module
    from utils.club_perks import get_club_perk_description

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

    # Add club stats
    embed.add_field(
        name="Estatísticas",
        value=f"**Membros:** {club['members_count']} 👥\n"
              f"**Reputação:** {club['reputation']} 🏆\n"
              f"**Líder:** {club.get('leader_name', 'Nenhum')}",
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
        "social": 0xFFD700     # Gold
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
            item_type = item['type'].capitalize()
            equipped_text = " [EQUIPADO]" if item.get('equipped', False) else ""
            items_text.append(f"{rarity['emoji']} **{item['name']}**{equipped_text} (ID: {item_id}, Tipo: {item_type}) - {item['description']}")

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
