import discord
from typing import List
from discord.ext import commands
from discord import app_commands
import logging
import re
from utils.db import get_clubs, update_user_club

logger = logging.getLogger('tokugawa_bot')

def normalize_club_name(name: str) -> str:
    """Normalize club name for comparison by removing accents, converting to lowercase, and replacing special characters with spaces."""
    import unicodedata
    # Remove accents
    name = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('ASCII')
    # Replace hyphens and special characters with spaces
    name = re.sub(r'[^a-zA-Z0-9 ]', ' ', name)
    # Convert to lowercase and remove extra spaces
    return ' '.join(name.lower().split())

class Registration(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def club_selection_autocomplete(self, interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
        """Provide club name suggestions for autocomplete."""
        try:
            # Get available clubs
            clubs = await get_clubs()
            if not clubs:
                return []
            
            # Normalize the current input
            normalized_current = normalize_club_name(current)
            
            # Filter and sort clubs based on the current input
            choices = []
            for club in clubs:
                normalized_name = normalize_club_name(club['name'])
                if normalized_current in normalized_name:
                    choices.append(app_commands.Choice(
                        name=club['name'],
                        value=club['name']
                    ))
                
            # Sort choices by name
            choices.sort(key=lambda x: x.name)
            
            # Return top 25 choices (Discord's limit)
            return choices[:25]
        except Exception as e:
            logger.error(f"Error in club_selection_autocomplete: {e}")
            return []

    @commands.hybrid_command(name="selecionar", description="Selecione um clube para se afiliar")
    @app_commands.autocomplete(clube=club_selection_autocomplete)
    async def select_club(self, ctx: commands.Context, clube: str):
        """Select a club to join."""
        try:
            user_id = str(ctx.author.id)
            logger.info(f"User {user_id} selected club: {clube}")
            
            # Get available clubs
            logger.info("Attempting to get clubs from database")
            clubs = await get_clubs()
            logger.info(f"Retrieved clubs from database: {clubs}")
            
            if not clubs:
                logger.error("No clubs retrieved from database")
                await ctx.send(
                    "❌ Erro ao recuperar clubes. Por favor, tente novamente mais tarde.",
                    ephemeral=True
                )
                return
            
            # Normalize the selected club name
            normalized_selected = normalize_club_name(clube)
            logger.info(f"Normalized selected club: {normalized_selected}")
            
            # Get available club names (normalized)
            available_club_names = [normalize_club_name(club['name']) for club in clubs]
            logger.info(f"Available club names (normalized): {available_club_names}")
            
            # Find the matching club
            matching_club = None
            for club in clubs:
                normalized_name = normalize_club_name(club['name'])
                logger.info(f"Checking club: {club['name']} (normalized: {normalized_name})")
                if normalized_name == normalized_selected:
                    matching_club = club
                    logger.info(f"Found matching club: {club['name']}")
                    break
            
            if not matching_club:
                logger.warning(f"Invalid club selection: {clube}")
                await ctx.send(
                    "❌ Clube inválido. Por favor, selecione um dos clubes disponíveis.",
                    ephemeral=True
                )
                return
            
            # Update user's club
            logger.info(f"Attempting to update user {user_id} to club {matching_club['name']}")
            success = await update_user_club(user_id, matching_club['name'])
            if not success:
                logger.error(f"Failed to update user {user_id} to club {matching_club['name']}")
                await ctx.send(
                    "❌ Erro ao atualizar seu clube. Por favor, tente novamente.",
                    ephemeral=True
                )
                return
            
            logger.info(f"Successfully updated user {user_id} to club {matching_club['name']}")
            await ctx.send(
                f"✅ Clube atualizado com sucesso! Você agora é membro do {matching_club['name']}.",
                ephemeral=True
            )
            
        except Exception as e:
            logger.error(f"Error in select_club: {e}")
            await ctx.send(
                "❌ Ocorreu um erro ao processar sua seleção. Por favor, tente novamente.",
                ephemeral=True
            )

    async def handle_club_selection(self, interaction: discord.Interaction, user_id: int, selected_club: str) -> bool:
        """Handle club selection with normalized comparison."""
        try:
            # Get available clubs
            clubs = await get_clubs()
            logger.info(f"Retrieved clubs from database: {clubs}")
            
            if not clubs:
                logger.error("No clubs retrieved from database")
                await interaction.response.send_message(
                    "❌ Erro ao recuperar clubes. Por favor, tente novamente mais tarde.",
                    ephemeral=True
                )
                return False
            
            # Normalize the selected club name
            normalized_selected = normalize_club_name(selected_club)
            logger.info(f"Normalized selected club: {normalized_selected}")
            
            # Get available club names (normalized)
            available_club_names = [normalize_club_name(club['name']) for club in clubs]
            logger.info(f"Available club names (normalized): {available_club_names}")
            
            # Find the matching club
            matching_club = None
            for club in clubs:
                normalized_name = normalize_club_name(club['name'])
                logger.info(f"Checking club: {club['name']} (normalized: {normalized_name})")
                if normalized_name == normalized_selected:
                    matching_club = club
                    logger.info(f"Found matching club: {club['name']}")
                    break
            
            if not matching_club:
                logger.warning(f"Invalid club selection: {selected_club}")
                await interaction.response.send_message(
                    "❌ Clube inválido. Por favor, selecione um dos clubes disponíveis.",
                    ephemeral=True
                )
                return False
            
            # Update user's club
            logger.info(f"Attempting to update user {user_id} to club {matching_club['name']}")
            success = await update_user_club(user_id, matching_club['name'])
            if not success:
                logger.error(f"Failed to update user {user_id} to club {matching_club['name']}")
                await interaction.response.send_message(
                    "❌ Erro ao atualizar seu clube. Por favor, tente novamente.",
                    ephemeral=True
                )
                return False
            
            logger.info(f"Successfully updated user {user_id} to club {matching_club['name']}")
            await interaction.response.send_message(
                f"✅ Clube atualizado com sucesso! Você agora é membro do {matching_club['name']}.",
                ephemeral=True
            )
            return True
            
        except Exception as e:
            logger.error(f"Error in handle_club_selection: {e}")
            await interaction.response.send_message(
                "❌ Ocorreu um erro ao processar sua seleção. Por favor, tente novamente.",
                ephemeral=True
            )
            return False

# @club_selection.error
# def club_selection_error(...):
#     pass 