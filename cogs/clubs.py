import discord
from discord.ext import commands
from discord import app_commands
import logging
from utils.database import get_player, get_club, get_all_clubs
from utils.embeds import create_basic_embed, create_club_embed

logger = logging.getLogger('tokugawa_bot')

class Clubs(commands.Cog):
    """Cog for club-related commands."""

    def __init__(self, bot):
        self.bot = bot

    # Group for club commands
    club_group = app_commands.Group(name="clube", description="Comandos de clubes da Academia Tokugawa")

    @club_group.command(name="teste", description="Comando de teste para verificar se os comandos estão sendo sincronizados")
    async def slash_test(self, interaction: discord.Interaction):
        """Test command to verify that commands are being synced."""
        try:
            await interaction.response.send_message("Teste bem-sucedido! Os comandos estão sendo sincronizados corretamente.")
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
            player = get_player(interaction.user.id)
            if not player:
                await interaction.response.send_message(f"{interaction.user.mention}, você ainda não está registrado na Academia Tokugawa. Use !ingressar para criar seu personagem.")
                return

            # Check if player is in a club
            if not player['club_id']:
                await interaction.response.send_message(f"{interaction.user.mention}, você não está afiliado a nenhum clube. Use !ingressar para criar um novo personagem e escolher um clube.")
                return

            # Get club data
            club = get_club(player['club_id'])
            if not club:
                await interaction.response.send_message(f"{interaction.user.mention}, não foi possível encontrar informações sobre seu clube. Por favor, contate um administrador.")
                return

            # Create and send club embed
            embed = create_club_embed(club)
            await interaction.response.send_message(embed=embed)
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
            clubs = get_all_clubs()

            # Create embed
            embed = create_basic_embed(
                title="Clubes da Academia Tokugawa",
                description="Aqui estão todos os clubes disponíveis na academia:",
                color=0x1E90FF
            )

            # Add each club to the embed
            for club in clubs:
                embed.add_field(
                    name=f"{club['club_id']}. {club['name']}",
                    value=f"{club['description']}\n"
                          f"**Membros:** {club['members_count']} 👥\n"
                          f"**Reputação:** {club['reputation']} 🏆",
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
        player = get_player(ctx.author.id)
        if not player:
            await ctx.send(f"{ctx.author.mention}, você ainda não está registrado na Academia Tokugawa. Use !ingressar para criar seu personagem.")
            return

        # Check if player is in a club
        if not player['club_id']:
            await ctx.send(f"{ctx.author.mention}, você não está afiliado a nenhum clube. Use !ingressar para criar um novo personagem e escolher um clube.")
            return

        # Get club data
        club = get_club(player['club_id'])
        if not club:
            await ctx.send(f"{ctx.author.mention}, não foi possível encontrar informações sobre seu clube. Por favor, contate um administrador.")
            return

        # Create and send club embed
        embed = create_club_embed(club)
        await ctx.send(embed=embed)

    @commands.command(name="clubes")
    async def all_clubs(self, ctx):
        """Exibe a lista de todos os clubes disponíveis."""
        # Get all clubs
        clubs = get_all_clubs()

        # Create embed
        embed = create_basic_embed(
            title="Clubes da Academia Tokugawa",
            description="Aqui estão todos os clubes disponíveis na academia:",
            color=0x1E90FF
        )

        # Add each club to the embed
        for club in clubs:
            embed.add_field(
                name=f"{club['club_id']}. {club['name']}",
                value=f"{club['description']}\n"
                      f"**Membros:** {club['members_count']} 👥\n"
                      f"**Reputação:** {club['reputation']} 🏆",
                inline=False
            )

        await ctx.send(embed=embed)

async def setup(bot):
    """Add the cog to the bot."""
    cog = Clubs(bot)
    await bot.add_cog(cog)
    logger.info("Clubs cog loaded")

    # Add the club_group to the bot's command tree
    try:
        bot.tree.add_command(cog.club_group)
        logger.info(f"Added club_group to command tree: /{cog.club_group.name}")
    except discord.app_commands.errors.CommandAlreadyRegistered:
        logger.info(f"Club_group already registered: /{cog.club_group.name}")

    # Add a direct test command to the bot's command tree
    @bot.tree.command(name="teste_direto", description="Comando de teste direto para verificar se os comandos estão sendo sincronizados")
    async def direct_test(interaction: discord.Interaction):
        """Direct test command to verify that commands are being synced."""
        try:
            await interaction.response.send_message("Teste direto bem-sucedido! Os comandos estão sendo sincronizados corretamente.")
        except discord.errors.NotFound:
            # If the interaction has expired, log it but don't try to respond
            logger.warning(f"Interaction expired for user {interaction.user.id} when using /teste_direto")
        except Exception as e:
            logger.error(f"Error in direct_test: {e}")

    # Log the slash commands that were added
    for cmd in cog.__cog_app_commands__:
        logger.info(f"Clubs cog added slash command: /{cmd.name}")

    # Log the direct test command that was added
    logger.info(f"Added direct test command: /teste_direto")
