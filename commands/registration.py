import discord
from discord.ext import commands
from discord import app_commands
import logging
from src.utils.persistence.db_provider import get_all_clubs, update_player
from src.utils.normalization import normalize_club_name

logger = logging.getLogger('tokugawa_bot')

class RegistrationCommands(commands.Cog):
    """Commands for player registration and club selection."""

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="selecionar", description="Selecione um clube para se afiliar")
    async def select_club(self, ctx: commands.Context, clube: str):
        """Select a club to join."""
        try:
            # Get available clubs
            clubs = await get_all_clubs()
            
            if not clubs:
                await ctx.send(
                    "❌ Não há clubes disponíveis no momento.",
                    ephemeral=True
                )
                return
            
            # Normalize the selected club name
            normalized_selected = normalize_club_name(clube)
            
            # Find the matching club
            matching_club = None
            for club in clubs:
                normalized_name = normalize_club_name(club['name'])
                if normalized_name == normalized_selected:
                    matching_club = club
                    break
            
            if not matching_club:
                await ctx.send(
                    "❌ Clube não encontrado. Use /clubes para ver a lista de clubes disponíveis.",
                    ephemeral=True
                )
                return
            
            # Update user's club
            success = await update_player(ctx.author.id, club=matching_club['name'])
            if not success:
                await ctx.send(
                    "❌ Erro ao selecionar clube. Tente novamente mais tarde.",
                    ephemeral=True
                )
                return
            
            await ctx.send(
                "✅ Clube selecionado com sucesso!",
                ephemeral=True
            )
            
        except Exception as e:
            logger.error(f"Error in select_club: {e}")
            await ctx.send(
                "❌ Erro ao selecionar clube. Tente novamente mais tarde.",
                ephemeral=True
            )

async def setup(bot):
    """Add the cog to the bot."""
    await bot.add_cog(RegistrationCommands(bot)) 