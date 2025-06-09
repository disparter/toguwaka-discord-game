import discord
from typing import List
from discord.ext import commands
from discord import app_commands
import logging
import re
from utils.json_utils import dumps as json_dumps
import asyncio
import os
from datetime import datetime
from typing import Dict, Any, Optional, Union
import random

from utils.db_provider import get_all_clubs, update_player, get_player, get_club
from utils.embeds import create_basic_embed, create_event_embed
from utils.game_mechanics import calculate_level_from_exp
from utils.club_system import ClubSystem
from utils.normalization import normalize_club_name

logger = logging.getLogger('tokugawa_bot')

class Registration(commands.Cog):
    """Cog for player registration and character creation."""

    def __init__(self, bot):
        self.bot = bot
        self.club_system = ClubSystem()

    # Group for registration commands
    registration_group = app_commands.Group(name="registro", description="Comandos de registro da Academia Tokugawa")

    @registration_group.command(name="ingressar", description="Iniciar o processo de registro na Academia Tokugawa")
    async def slash_register(self, interaction: discord.Interaction):
        """Slash command version of the register command."""
        try:
            # Check if player already exists
            player = get_player(interaction.user.id)
            if player:
                await interaction.response.send_message(f"{interaction.user.mention}, você já está registrado na Academia Tokugawa!")
                return

            # For slash commands, we'll use a simplified registration process
            await interaction.response.send_message(
                "Para iniciar o processo de registro completo, use o comando de texto `!ingressar`.\n"
                "O processo de registro interativo requer múltiplas etapas que funcionam melhor com comandos de texto."
            )
        except discord.errors.NotFound:
            # If the interaction has expired, log it but don't try to respond
            logger.warning(f"Interaction expired for user {interaction.user.id} when using /registro ingressar")
        except Exception as e:
            logger.error(f"Error in slash_register: {e}")

    @commands.command(name="ingressar")
    async def register(self, ctx):
        """Iniciar o processo de registro na Academia Tokugawa."""
        logger.info(f"Register command called by user {ctx.author.id} ({ctx.author.name})")
        
        # Check if player already exists
        player = get_player(ctx.author.id)
        logger.info(f"Player lookup result for {ctx.author.id}: {player}")
        
        if player:
            logger.info(f"Player {ctx.author.id} already registered")
            await ctx.send(f"{ctx.author.mention}, você já está registrado na Academia Tokugawa!")
            return

        # Start registration process
        logger.info(f"Starting registration process for user {ctx.author.id}")
        welcome_embed = create_basic_embed(
            title="Bem-vindo à Academia Tokugawa!",
            description="Você está prestes a ingressar na mais prestigiada academia para estudantes com superpoderes!\n\n"
                        "Vamos criar seu personagem. Responda às perguntas a seguir para começar sua jornada.",
            color=0x1E90FF
        )
        await ctx.send(embed=welcome_embed)

        # Get character name
        await ctx.send("**Qual é o seu nome?** (Responda no chat)")

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            # Get character name
            name_msg = await self.bot.wait_for('message', check=check, timeout=60.0)
            character_name = name_msg.content.strip()

            # Get character power
            await ctx.send("**Qual é o seu superpoder?** (Descreva brevemente sua habilidade)")
            power_msg = await self.bot.wait_for('message', check=check, timeout=60.0)
            character_power = power_msg.content.strip()

            # Get strength level
            strength_embed = create_basic_embed(
                title="Nível de Força",
                description="Escolha o nível de força do seu poder (1-5):\n\n" +
                            "1. Fraco - Poderes básicos e limitados - ⭐\n" +
                            "2. Moderado - Poderes com algumas limitações - ⭐⭐\n" +
                            "3. Forte - Poderes significativos - ⭐⭐⭐\n" +
                            "4. Muito Forte - Poderes excepcionais - ⭐⭐⭐⭐\n" +
                            "5. Extremamente Forte - Poderes raros e poderosos - ⭐⭐⭐⭐⭐\n\n" +
                            "Digite o número correspondente ao nível escolhido:",
                color=0x1E90FF
            )
            await ctx.send(embed=strength_embed)

            valid_strength = False
            strength_level = None

            while not valid_strength:
                strength_msg = await self.bot.wait_for('message', check=check, timeout=60.0)
                try:
                    strength_level = int(strength_msg.content.strip())
                    if 1 <= strength_level <= 5:
                        valid_strength = True
                    else:
                        await ctx.send("Por favor, digite um número de 1 a 5.")
                except ValueError:
                    await ctx.send("Por favor, digite um número válido de 1 a 5.")

            # Get club choice
            clubs = []
            for club_id, club_name in self.club_system.CLUBS.items():
                clubs.append({
                    'club_id': club_id,
                    'name': club_name,
                    'description': f"O {club_name} é um dos clubes mais prestigiados da Academia Tokugawa."
                })

            clubs_embed = create_basic_embed(
                title="Escolha de Clube",
                description="Escolha um clube para se afiliar:\n\n" + 
                            "\n".join([f"{i+1}. **{club['name']}** - {club['description']}" for i, club in enumerate(clubs)]) +
                            "\n\nDigite o número do clube escolhido:",
                color=0x1E90FF
            )
            await ctx.send(embed=clubs_embed)

            valid_club = False
            while not valid_club:
                club_msg = await self.bot.wait_for('message', check=check, timeout=60.0)
                try:
                    club_index = int(club_msg.content.strip()) - 1
                    if 0 <= club_index < len(clubs):
                        valid_club = True
                        selected_club = clubs[club_index]
                        logger.info(f"User {ctx.author.id} selected club: {selected_club['name']} (ID: {selected_club['club_id']})")
                    else:
                        logger.warning(f"Invalid club index: {club_index + 1}")
                        await ctx.send("Por favor, escolha um número válido da lista.")
                except ValueError:
                    logger.warning(f"Invalid club selection: {club_msg.content}")
                    await ctx.send("Por favor, digite apenas o número do clube escolhido.")

            # Create the player
            success = create_player(
                ctx.author.id,
                character_name,
                power=character_power,
                strength_level=strength_level,
                club_id=selected_club['club_id']
            )

            if success:
                # Get the created player and their club
                player = get_player(ctx.author.id)

                # Send welcome message
                welcome_msg = create_basic_embed(
                    title="Registro Concluído!",
                    description=f"Bem-vindo à Academia Tokugawa, {character_name}!\n\n"
                                f"Você agora é oficialmente um estudante com o poder de **{character_power}** "
                                f"({STRENGTH_LEVELS[strength_level]}).\n\n"
                                f"Você se juntou ao **{selected_club['name']}**.\n\n"
                                f"Use o comando `!status` para ver seu perfil e `!ajuda` para ver todos os comandos disponíveis.",
                    color=0x00FF00
                )
                await ctx.send(embed=welcome_msg)

                # Send player embed
                player_embed = create_player_embed(player, selected_club)
                await ctx.send(embed=player_embed)
            else:
                await ctx.send("Ocorreu um erro durante o registro. Por favor, tente novamente mais tarde.")

        except asyncio.TimeoutError:
            await ctx.send("Tempo esgotado. Por favor, tente novamente com o comando !ingressar.")

    @commands.command(name="ajuda")
    async def help_command(self, ctx):
        """Exibe informações de ajuda sobre os comandos do jogo."""
        help_embed = create_basic_embed(
            title="Ajuda da Academia Tokugawa",
            description="Aqui estão os comandos disponíveis:",
            color=0x1E90FF
        )

        # Registration commands
        help_embed.add_field(
            name="Comandos de Registro",
            value="**!ingressar** - Crie seu personagem e ingresse na Academia Tokugawa",
            inline=False
        )

        # Status commands
        help_embed.add_field(
            name="Comandos de Status",
            value="**!status** - Veja seu perfil e estatísticas\n"
                  "**!inventario** - Veja seus itens e técnicas\n"
                  "**!top** - Veja o ranking dos melhores alunos",
            inline=False
        )

        # Activity commands
        help_embed.add_field(
            name="Comandos de Atividades",
            value="**!treinar** - Treine para ganhar experiência\n"
                  "**!duelar @usuário** - Desafie outro aluno para um duelo\n"
                  "**!explorar** - Explore a academia em busca de eventos\n"
                  "**!evento** - Participe do evento atual",
            inline=False
        )

        # Club commands
        help_embed.add_field(
            name="Comandos de Clube",
            value="**!clube** - Veja informações sobre seu clube\n"
                  "**!clubes** - Veja a lista de todos os clubes",
            inline=False
        )

        # Economy commands
        help_embed.add_field(
            name="Comandos de Economia",
            value="**!loja** - Acesse a loja da academia\n"
                  "**!mercado** - Acesse o mercado de itens entre jogadores",
            inline=False
        )

        await ctx.send(embed=help_embed)

    async def club_selection_autocomplete(self, interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
        """Provide club name suggestions for autocomplete."""
        try:
            # Get available clubs
            clubs = await get_all_clubs()
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
            clubs = await get_all_clubs()
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
            success = await update_player(user_id, club=matching_club['name'])
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
            clubs = await get_all_clubs()
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
            success = await update_player(user_id, club=matching_club['name'])
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