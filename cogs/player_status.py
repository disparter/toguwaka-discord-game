import discord
from discord.ext import commands
from discord import app_commands
import logging
from utils.database import get_player, get_club, get_top_players
from utils.embeds import create_player_embed, create_inventory_embed, create_leaderboard_embed

logger = logging.getLogger('tokugawa_bot')

class PlayerStatus(commands.Cog):
    """Cog for player status commands."""

    def __init__(self, bot):
        self.bot = bot

    # Group for player status commands
    status_group = app_commands.Group(name="status", description="Comandos de status da Academia Tokugawa")

    @status_group.command(name="status", description="Exibe o status do jogador")
    async def slash_status(self, interaction: discord.Interaction, member: discord.Member = None):
        """Slash command version of the status command."""
        try:
            # If no member is specified, use the command author
            target = member or interaction.user

            # Get player data
            player = get_player(target.id)
            if not player:
                if target == interaction.user:
                    await interaction.response.send_message(f"{interaction.user.mention}, você ainda não está registrado na Academia Tokugawa. Use !ingressar para criar seu personagem.")
                else:
                    await interaction.response.send_message(f"{target.display_name} não está registrado na Academia Tokugawa.")
                return

            # Get club data
            club = None
            if player['club_id']:
                club = get_club(player['club_id'])

            # Create and send player embed
            embed = create_player_embed(player, club)
            await interaction.response.send_message(embed=embed)
        except discord.errors.NotFound:
            # If the interaction has expired, log it but don't try to respond
            logger.warning(f"Interaction expired for user {interaction.user.id} when using /status status")
        except Exception as e:
            logger.error(f"Error in slash_status: {e}")

    @status_group.command(name="inventario", description="Exibe o inventário do jogador")
    async def slash_inventory(self, interaction: discord.Interaction):
        """Slash command version of the inventory command."""
        try:
            # Get player data
            player = get_player(interaction.user.id)
            if not player:
                await interaction.response.send_message(f"{interaction.user.mention}, você ainda não está registrado na Academia Tokugawa. Use !ingressar para criar seu personagem.")
                return

            # Create and send inventory embed
            embed = create_inventory_embed(player)
            await interaction.response.send_message(embed=embed)
        except discord.errors.NotFound:
            # If the interaction has expired, log it but don't try to respond
            logger.warning(f"Interaction expired for user {interaction.user.id} when using /status inventario")
        except Exception as e:
            logger.error(f"Error in slash_inventory: {e}")

    @status_group.command(name="top", description="Exibe o ranking dos melhores alunos")
    async def slash_leaderboard(self, interaction: discord.Interaction, limit: int = 10):
        """Slash command version of the leaderboard command."""
        try:
            # Limit the number of players to show
            if limit < 1:
                limit = 1
            elif limit > 25:
                limit = 25

            # Get top players
            top_players = get_top_players(limit)

            # Create and send leaderboard embed
            embed = create_leaderboard_embed(top_players)
            await interaction.response.send_message(embed=embed)
        except discord.errors.NotFound:
            # If the interaction has expired, log it but don't try to respond
            logger.warning(f"Interaction expired for user {interaction.user.id} when using /status top")
        except Exception as e:
            logger.error(f"Error in slash_leaderboard: {e}")

    @commands.command(name="status")
    async def status(self, ctx, member: discord.Member = None):
        """Exibe o status do jogador."""
        # If no member is specified, use the command author
        target = member or ctx.author

        # Get player data
        player = get_player(target.id)
        if not player:
            if target == ctx.author:
                await ctx.send(f"{ctx.author.mention}, você ainda não está registrado na Academia Tokugawa. Use !ingressar para criar seu personagem.")
            else:
                await ctx.send(f"{target.display_name} não está registrado na Academia Tokugawa.")
            return

        # Get club data
        club = None
        if player['club_id']:
            club = get_club(player['club_id'])

        # Create and send player embed
        embed = create_player_embed(player, club)
        await ctx.send(embed=embed)

    @commands.command(name="inventario")
    async def inventory(self, ctx):
        """Exibe o inventário do jogador."""
        # Get player data
        player = get_player(ctx.author.id)
        if not player:
            await ctx.send(f"{ctx.author.mention}, você ainda não está registrado na Academia Tokugawa. Use !ingressar para criar seu personagem.")
            return

        # Create and send inventory embed
        embed = create_inventory_embed(player)
        await ctx.send(embed=embed)

    @commands.command(name="top")
    async def leaderboard(self, ctx, limit: int = 10):
        """Exibe o ranking dos melhores alunos da Academia Tokugawa."""
        # Limit the number of players to show
        if limit < 1:
            limit = 1
        elif limit > 25:
            limit = 25

        # Get top players
        top_players = get_top_players(limit)

        # Create and send leaderboard embed
        embed = create_leaderboard_embed(top_players)
        await ctx.send(embed=embed)

    @commands.command(name="perfil")
    async def profile(self, ctx, member: discord.Member = None):
        """Alias para o comando status."""
        await self.status(ctx, member)

async def setup(bot):
    """Add the cog to the bot."""
    cog = PlayerStatus(bot)
    await bot.add_cog(cog)
    logger.info("PlayerStatus cog loaded")

    # Add the status_group to the bot's command tree
    try:
        bot.tree.add_command(cog.status_group)
        logger.info(f"Added status_group to command tree: /{cog.status_group.name}")
    except discord.app_commands.errors.CommandAlreadyRegistered:
        logger.info(f"Status_group already registered: /{cog.status_group.name}")

    # Log the slash commands that were added
    for cmd in cog.__cog_app_commands__:
        logger.info(f"PlayerStatus cog added slash command: /{cmd.name}")
