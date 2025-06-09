import discord
from datetime import datetime
import random
from src.utils.persistence.db_provider import get_player, get_club, get_top_players, get_top_players_by_reputation
from src.utils.embeds import create_basic_embed

class RankingFormatter:
    """Class for formatting ranking and news messages for the Academia Tokugawa Discord bot."""

    @staticmethod
    def format_diario(daily_players):
        """Format daily ranking embed with improved visuals.
        
        Args:
            daily_players (list): List of player dictionaries with daily progress
            
        Returns:
            discord.Embed: Formatted embed for daily ranking
        """
        if not daily_players:
            return create_basic_embed(
                title="🎓 Conselho Estudantil da Tokugawa · 📅 Ranking Diário",
                description="Nenhuma atividade registrada hoje.",
                color=0x00FF00  # Green
            )
        
        # Sort players by exp gained
        daily_players.sort(key=lambda x: x.get('exp_gained', 0), reverse=True)
        top_daily = daily_players[:5]
        
        # Create ranking text with improved formatting
        ranking_text = "🏆 __Rankings do Dia:__\n──────────────\n"
        
        for i, player in enumerate(top_daily, 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            club_name = player.get('club_name', 'Sem clube')
            
            ranking_text += f"{medal} **{player.get('name', 'Unknown')}** | {club_name} | Total: {player.get('exp_gained', 0)} pts\n"
        
        ranking_text += "──────────────\n\n"
        
        # Create embed with themed color
        embed = create_basic_embed(
            title="🎓 Conselho Estudantil da Tokugawa · 📅 Ranking Diário",
            description=ranking_text,
            color=0x00FF00  # Green
        )
        
        # Add reactions hint at the bottom
        embed.add_field(
            name="",
            value="🔁 Reaja com 🔁 para ver rankings anteriores.",
            inline=False
        )
        
        return embed

    @staticmethod
    def format_geral(overall_players):
        """Format overall ranking embed with improved visuals.
        
        Args:
            overall_players (list): List of player dictionaries with overall stats
            
        Returns:
            discord.Embed: Formatted embed for overall ranking
        """
        if not overall_players:
            return create_basic_embed(
                title="🎓 Conselho Estudantil da Tokugawa · 📊 Ranking Geral",
                description="Nenhum estudante registrado.",
                color=0xFFD700  # Gold
            )
        
        # Create ranking text with improved formatting
        ranking_text = "🏆 __Rankings Gerais:__\n──────────────\n"
        
        for i, player in enumerate(overall_players[:5], 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            club_name = player.get('club_name', 'Sem clube')
            
            ranking_text += f"{medal} **{player.get('name', 'Unknown')}** | {club_name} | Nível: {player.get('level', 1)}\n"
        
        ranking_text += "──────────────\n\n"
        
        # Create embed with themed color
        embed = create_basic_embed(
            title="🎓 Conselho Estudantil da Tokugawa · 📊 Ranking Geral",
            description=ranking_text,
            color=0xFFD700  # Gold
        )
        
        # Add reactions hint at the bottom
        embed.add_field(
            name="",
            value="🔁 Reaja com 🔁 para ver rankings completos.",
            inline=False
        )
        
        return embed

    @staticmethod
    def format_reputacao(reputation_players):
        """Format reputation ranking embed with improved visuals.
        
        Args:
            reputation_players (list): List of player dictionaries with reputation stats
            
        Returns:
            discord.Embed: Formatted embed for reputation ranking
        """
        if not reputation_players:
            return create_basic_embed(
                title="🎓 Conselho Estudantil da Tokugawa · ⭐ Ranking de Reputação",
                description="Nenhum estudante com reputação registrada.",
                color=0xFFA500  # Orange
            )
        
        # Sort players by reputation
        reputation_players.sort(key=lambda x: x.get('reputation', 0), reverse=True)
        top_reputation = reputation_players[:5]
        
        # Create ranking text with improved formatting
        ranking_text = "🌟 __Reputação Atual:__\n──────────────\n"
        
        for i, player in enumerate(top_reputation, 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            club_name = player.get('club_name', 'Sem clube')
            
            ranking_text += f"{medal} **{player.get('name', 'Unknown')}**: {player.get('reputation', 0)} pts\n"
        
        ranking_text += "──────────────\n\n"
        
        # Create embed with themed color
        embed = create_basic_embed(
            title="🎓 Conselho Estudantil da Tokugawa · ⭐ Ranking de Reputação",
            description=ranking_text,
            color=0xFFA500  # Orange
        )
        
        return embed

    @staticmethod
    def format_noticias(featured_club=None, buff_description=None, news_items=None):
        """Format news embed with improved visuals.
        
        Args:
            featured_club (dict, optional): Featured club data
            buff_description (str, optional): Description of the club buff
            news_items (list, optional): List of news items
            
        Returns:
            discord.Embed: Formatted embed for news
        """
        # Default news items if none provided
        if news_items is None:
            news_items = [
                "☀️ Hoje é um dia tranquilo na Academia Tokugawa."
            ]
        
        # Determine color based on featured club
        color = 0x4169E1  # Default Royal Blue
        
        if featured_club:
            # Club colors
            club_colors = {
                1: 0xFF0000,  # Clube das Chamas - Red
                2: 0x800080,  # Ilusionistas Mentais - Purple
                3: 0xFFD700,  # Conselho Político - Gold
                4: 0x00FF00,  # Elementalistas - Green
                5: 0x808080   # Clube de Combate - Gray
            }
            color = club_colors.get(featured_club['club_id'], 0x4169E1)
        
        # Create news text with improved formatting
        news_text = "📢 __Notícias do Conselho:__\n"
        
        # Add featured club news if available
        if featured_club and buff_description:
            news_text += f"🎉 Clube **{featured_club['name']}** foi destaque hoje!\n"
            news_text += f"🎖️ Bônus ativo: {buff_description}\n"
            news_text += f"📚 Reitor concedeu benção especial ao clube.\n\n"
        
        # Add other news items
        for item in news_items:
            if item.startswith("•"):
                item = item[2:]  # Remove bullet if already present
            
            # Skip if it's about the featured club (already handled above)
            if featured_club and featured_club['name'] in item and "destaque" in item:
                continue
                
            news_text += f"• {item}\n"
        
        # Create embed with themed color
        embed = create_basic_embed(
            title="🎓 Conselho Estudantil da Tokugawa · 📰 Notícias",
            description=news_text,
            color=color
        )
        
        # Add view rewards button hint if there's a buff
        if featured_club and buff_description:
            embed.add_field(
                name="",
                value="💎 Clique em 'Ver Recompensas' para detalhes do bônus",
                inline=False
            )
        
        return embed

    @staticmethod
    def create_daily_summary(daily_players, reputation_players, featured_club=None, buff_description=None, news_items=None):
        """Create a comprehensive daily summary embed combining rankings and news.
        
        Args:
            daily_players (list): List of player dictionaries with daily progress
            reputation_players (list): List of player dictionaries with reputation stats
            featured_club (dict, optional): Featured club data
            buff_description (str, optional): Description of the club buff
            news_items (list, optional): List of news items
            
        Returns:
            discord.Embed: Formatted embed for daily summary
        """
        # Determine color based on featured club
        color = 0x1E90FF  # Default Blue
        
        if featured_club:
            # Club colors
            club_colors = {
                1: 0xFF0000,  # Clube das Chamas - Red
                2: 0x800080,  # Ilusionistas Mentais - Purple
                3: 0xFFD700,  # Conselho Político - Gold
                4: 0x00FF00,  # Elementalistas - Green
                5: 0x808080   # Clube de Combate - Gray
            }
            color = club_colors.get(featured_club['club_id'], 0x1E90FF)
        
        # Create embed
        embed = discord.Embed(
            title="🎓 Conselho Estudantil da Tokugawa · 📅 " + datetime.now().strftime("%A"),
            color=color,
            timestamp=datetime.utcnow()
        )
        
        # Add daily ranking
        if daily_players:
            daily_players.sort(key=lambda x: x['exp_gained'], reverse=True)
            top_daily = daily_players[:2]  # Show only top 2 in summary
            
            ranking_text = ""
            for i, player in enumerate(top_daily, 1):
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                club = get_club(player['club_id']) if player.get('club_id') else None
                club_name = club['name'] if club else "Sem clube"
                
                ranking_text += f"{medal} **{player['name']}** | {club_name} | Total: {player['exp_gained']} pts\n"
            
            embed.add_field(
                name="🏆 Rankings do Dia:",
                value=ranking_text or "Nenhuma atividade registrada hoje.",
                inline=False
            )
        
        # Add reputation ranking
        if reputation_players:
            reputation_players.sort(key=lambda x: x['reputation'], reverse=True)
            top_reputation = reputation_players[:2]  # Show only top 2 in summary
            
            reputation_text = ""
            for i, player in enumerate(top_reputation, 1):
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                reputation_text += f"{medal} **{player['name']}**: {player['reputation']} pts\n"
            
            embed.add_field(
                name="🌟 Reputação Atual:",
                value=reputation_text or "Nenhum estudante com reputação registrada.",
                inline=False
            )
        
        # Add news
        news_text = ""
        
        # Add featured club news if available
        if featured_club and buff_description:
            news_text += f"🎉 Clube **{featured_club['name']}** foi destaque hoje!\n"
            news_text += f"🎖️ Bônus ativo: {buff_description}\n"
            news_text += f"📚 Reitor concedeu benção especial ao clube.\n"
        
        # Add one random news item
        if news_items:
            random_news = random.choice(news_items)
            if random_news.startswith("•"):
                random_news = random_news[2:]  # Remove bullet if already present
            
            # Skip if it's about the featured club (already handled above)
            if not (featured_club and featured_club['name'] in random_news and "destaque" in random_news):
                news_text += f"\n• {random_news}"
        
        if news_text:
            embed.add_field(
                name="📢 Notícias do Conselho:",
                value=news_text,
                inline=False
            )
        
        # Add footer with reactions hint
        embed.set_footer(text="Academia Tokugawa | 🔁 Reaja para ver rankings anteriores", icon_url="https://i.imgur.com/example.png")
        
        return embed

class ClubEffectEngine:
    """Class for centralizing the application of club effects and buffs."""
    
    @staticmethod
    def format_buff_description(buff_type, buff_value):
        """Format a buff description string.
        
        Args:
            buff_type (str): Type of buff ('exp', 'tusd', 'attribute')
            buff_value (int): Value of the buff (percentage)
            
        Returns:
            str: Formatted buff description
        """
        if buff_type == 'exp':
            return f"+{buff_value}% de EXP em treinamentos"
        elif buff_type == 'tusd':
            return f"+{buff_value}% de TUSD em atividades"
        elif buff_type == 'attribute':
            return f"+{buff_value}% de chance de aumentar atributos"
        else:
            return f"+{buff_value}% de bônus"
    
    @staticmethod
    def apply_club_buff(player, action_type, base_value):
        """Apply club buffs to a value based on player's club and action type.
        
        Args:
            player (dict): Player data
            action_type (str): Type of action ('exp', 'tusd', 'attribute')
            base_value (int/float): Base value before buff
            
        Returns:
            tuple: (buffed_value, buff_description or None)
        """
        from cogs.scheduled_events import CLUB_BUFFS
        
        # If player has no club, return base value
        if not player.get('club_id'):
            return base_value, None
        
        # Check if player's club has an active buff
        club_id = player['club_id']
        if club_id in CLUB_BUFFS:
            buff = CLUB_BUFFS[club_id]
            
            # Check if buff is for the right action type and not expired
            if buff['type'] == action_type and buff['expires'] > datetime.now():
                # Apply buff
                buffed_value = base_value * (1 + buff['value'] / 100)
                buff_description = ClubEffectEngine.format_buff_description(buff['type'], buff['value'])
                return buffed_value, buff_description
        
        # No applicable buff found
        return base_value, None