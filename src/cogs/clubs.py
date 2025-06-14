import discord
import logging
from typing import Any
from discord import app_commands
from discord.ext import commands

from story_mode.club_rivalry_system import ClubSystem
from utils.command_registrar import CommandRegistrar
from utils.embeds import create_basic_embed, create_club_embed
from utils.persistence.db_provider import db_provider

logger = logging.getLogger('tokugawa_bot')


class Clubs(commands.Cog):
    """Cog for club-related commands."""

    def __init__(self, bot):
        self.bot = bot
        self.club_system = ClubSystem()

    # Group for club commands
    club_group = app_commands.Group(name="clube", description="Comandos de clubes da Academia Tokugawa")

    @club_group.command(name="teste",
                        description="Comando de teste para verificar se os comandos estão sendo sincronizados")
    async def slash_test(self, interaction: discord.Interaction):
        """Test command to verify that commands are being synced."""
        try:
            await interaction.response.send_message(
                "Teste bem-sucedido! Os comandos estão sendo sincronizados corretamente.")
        except discord.errors.NotFound:
            # If the interaction has expired, log it but don't try to respond
            logger.warning(f"Interaction expired for user {interaction.user.id} when using /clube teste")
        except Exception as e:
            logger.error(f"Error in slash_test: {e}")

    @club_group.command(name="info", description="Exibe informações sobre o clube do jogador")
    async def slash_club(self, interaction: discord.Interaction):
        """Slash command version of the club command."""
        try:
            # Check if player exists
            player = await db_provider.get_player(interaction.user.id)
            if not player:
                await interaction.response.send_message(
                    f"{interaction.user.mention}, você ainda não está registrado na Academia Tokugawa. Use !ingressar para criar seu personagem.",
                    ephemeral=True)
                return

            # Check if player is in a club
            if not player['club_id']:
                await interaction.response.send_message(
                    f"{interaction.user.mention}, você não está afiliado a nenhum clube. Use !ingressar para criar um novo personagem e escolher um clube.",
                    ephemeral=True)
                return

            # Get club data
            club = await db_provider.get_club(player['club_id'])
            if not club:
                await interaction.response.send_message(
                    f"{interaction.user.mention}, não foi possível encontrar informações sobre seu clube. Por favor, contate um administrador.",
                    ephemeral=True)
                return

            # Get club members
            members = await db_provider.get_club_members(player['club_id'])
            npcs = await db_provider.get_relevant_npcs(player['club_id'])

            # Create club embed
            embed = await create_club_embed(club)

            # Add members to embed
            member_list = "\n".join(
                [f"- {m['name']} (Nível {m['level']})" for m in members]) if members else "Nenhum membro encontrado."
            embed.add_field(name="📜 Jogadores", value=member_list, inline=False)

            # Add NPCs to embed
            npc_list = "\n".join(
                [f"- {n['name']} ({n['role']})" for n in npcs]) if npcs else "Nenhum NPC relevante identificado."
            embed.add_field(name="🤖 NPCs Relevantes", value=npc_list, inline=False)

            # Send the embed with ephemeral=True to make it visible only to the user
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except discord.errors.NotFound:
            # If the interaction has expired, log it but don't try to respond
            logger.warning(f"Interaction expired for user {interaction.user.id} when using /clube info")
        except Exception as e:
            logger.error(f"Error in slash_club: {e}")

    @club_group.command(name="lista", description="Exibe a lista de todos os clubes disponíveis")
    async def slash_all_clubs(self, interaction: discord.Interaction):
        """Slash command version of the all_clubs command."""
        try:
            # Get all clubs
            clubs = await db_provider.get_all_clubs()

            # Create embed
            embed = create_basic_embed(
                title="Clubes da Academia Tokugawa",
                description="Aqui estão todos os clubes disponíveis na academia:",
                color=0x1E90FF
            )

            # Add each club to the embed
            for club in clubs:
                embed.add_field(
                    name=f"{club['PK'].split('#')[1]}. {club['name']}",
                    value=f"{club['descricao']}\n"
                          f"**Membros:** {club.get('members_count', 0)} 👥\n"
                          f"**Reputação:** {club.get('reputacao', 0)} 🏆",
                    inline=False
                )

            await interaction.response.send_message(embed=embed)
        except discord.errors.NotFound:
            # If the interaction has expired, log it but don't try to respond
            logger.warning(f"Interaction expired for user {interaction.user.id} when using /clube lista")
        except Exception as e:
            logger.error(f"Error in slash_all_clubs: {e}")

    @commands.command(name="clube")
    async def club(self, ctx):
        """Exibe informações sobre o clube do jogador."""
        # Check if player exists
        player = await db_provider.get_player(ctx.author.id)
        if not player:
            await ctx.send(
                f"{ctx.author.mention}, você ainda não está registrado na Academia Tokugawa. Use !ingressar para criar seu personagem.")
            return

        # Check if player is in a club
        if not player['club_id']:
            await ctx.send(
                f"{ctx.author.mention}, você não está afiliado a nenhum clube. Use !ingressar para criar um novo personagem e escolher um clube.")
            return

        # Get club data
        club = await db_provider.get_club(player['club_id'])
        if not club:
            await ctx.send(
                f"{ctx.author.mention}, não foi possível encontrar informações sobre seu clube. Por favor, contate um administrador.")
            return

        # Create and send club embed
        embed = await create_club_embed(club)
        await ctx.send(embed=embed)

    @commands.command(name="clubes")
    async def all_clubs(self, ctx):
        """Exibe a lista de todos os clubes disponíveis."""
        embed = create_basic_embed(
            title="Clubes da Academia Tokugawa",
            description="Aqui estão todos os clubes disponíveis na academia:",
            color=0x1E90FF
        )

        for club_name in self.club_system.CLUBS.values():
            embed.add_field(
                name=club_name,
                value=f"O {club_name} é um dos clubes mais prestigiados da Academia Tokugawa.",
                inline=False
            )

        await ctx.send(embed=embed)

    @app_commands.command(name="info", description="Mostra informações sobre um clube")
    async def slash_club_info(self, interaction: discord.Interaction, clube: str):
        """Mostra informações sobre um clube."""
        try:
            await interaction.response.defer(ephemeral=True)
        except discord.errors.NotFound:
            logger.error("A interação expirou antes que pudesse ser processada.")
            return

        # Get club data
        club = await db_provider.get_club(clube)
        if not club:
            await interaction.followup.send(f"Clube '{clube}' não encontrado.", ephemeral=True)
            return

        # Create embed
        embed = await create_club_embed(club)

        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="listar", description="Lista todos os clubes disponíveis")
    async def slash_list_clubs(self, interaction: discord.Interaction):
        """Lista todos os clubes disponíveis."""
        try:
            await interaction.response.defer(ephemeral=True)
        except discord.errors.NotFound:
            logger.error("A interação expirou antes que pudesse ser processada.")
            return

        # Get all clubs
        clubs = await db_provider.get_all_clubs()
        if not clubs:
            await interaction.followup.send("Não há clubes disponíveis no momento.", ephemeral=True)
            return

        # Create embeds for each club
        embeds = []
        for club in clubs:
            embed = await create_club_embed(club)
            embeds.append(embed)

        # Send embeds
        for embed in embeds:
            await interaction.followup.send(embed=embed, ephemeral=True)


async def setup(bot):
    """Add the cog to the bot."""

    # Create and add the cog
    cog = Clubs(bot)
    await bot.add_cog(cog)
    logger.info("Clubs cog loaded")

    # Register commands using the CommandRegistrar
    await CommandRegistrar.register_commands(bot, cog)
