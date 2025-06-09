import discord
from discord.ext import commands
from discord import app_commands
import logging
from utils.database import get_player, get_club, get_all_clubs, update_player
from utils.embeds import create_basic_embed, create_club_embed
from story_mode.club_system import ClubSystem

logger = logging.getLogger('tokugawa_bot')

class Clubs(commands.Cog):
    """Cog for club-related commands."""

    def __init__(self, bot):
        self.bot = bot
        self.club_system = ClubSystem()

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
                await interaction.response.send_message(f"{interaction.user.mention}, você ainda não está registrado na Academia Tokugawa. Use !ingressar para criar seu personagem.", ephemeral=True)
                return

            # Check if player is in a club
            if not player['club_id']:
                await interaction.response.send_message(f"{interaction.user.mention}, você não está afiliado a nenhum clube. Use !ingressar para criar um novo personagem e escolher um clube.", ephemeral=True)
                return

            # Get club data
            club = get_club(player['club_id'])
            if not club:
                await interaction.response.send_message(f"{interaction.user.mention}, não foi possível encontrar informações sobre seu clube. Por favor, contate um administrador.", ephemeral=True)
                return

            # Get club members
            from utils.database import get_club_members, get_relevant_npcs
            members = get_club_members(player['club_id'])
            npcs = get_relevant_npcs(player['club_id'])

            # Create club embed
            embed = create_club_embed(club)

            # Add members to embed
            member_list = "\n".join([f"- {m['name']} (Nível {m['level']})" for m in members]) if members else "Nenhum membro encontrado."
            embed.add_field(name="📜 Jogadores", value=member_list, inline=False)

            # Add NPCs to embed
            npc_list = "\n".join([f"- {n['name']} ({n['role']})" for n in npcs]) if npcs else "Nenhum NPC relevante identificado."
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

    @commands.command(name="ingressar")
    async def join_club(self, ctx, *, club_choice: str):
        """Ingressa em um clube da academia."""
        # Get player data
        player = get_player(ctx.author.id)
        if not player:
            await ctx.send("Você precisa se registrar primeiro! Use o comando `!registrar`.")
            return

        # Check if player is already in a club
        if player.get('club'):
            await ctx.send(f"Você já é membro do clube {player['club']}!")
            return

        # Convert club_choice to index (1-based to 0-based)
        try:
            club_index = int(club_choice) - 1
            if club_index < 0 or club_index >= len(self.club_system.CLUBS):
                await ctx.send("Por favor, escolha um número válido da lista.")
                return
        except ValueError:
            await ctx.send("Por favor, digite apenas o número do clube escolhido.")
            return

        # Get club name from index
        club_name = list(self.club_system.CLUBS.values())[club_index]
        
        # Join club using ClubSystem
        if self.club_system.join_club(player, club_index + 1):  # Convert back to 1-based for club_id
            # Update player's club
            update_player(ctx.author.id, club=club_name)
            
            # Create embed
            embed = create_basic_embed(
                title="Ingresso no Clube",
                description=f"Bem-vindo ao clube {club_name}!",
                color=0x00FF00
            )
            embed.add_field(
                name="Mensagem",
                value=f"Você agora é um membro oficial do clube {club_name}!",
                inline=False
            )
            
            await ctx.send(embed=embed)
        else:
            await ctx.send("Ocorreu um erro ao ingressar no clube. Tente novamente mais tarde.")

async def setup(bot):
    """Add the cog to the bot."""
    from utils.command_registrar import CommandRegistrar

    # Create and add the cog
    cog = Clubs(bot)
    await bot.add_cog(cog)
    logger.info("Clubs cog loaded")

    # Register commands using the CommandRegistrar
    await CommandRegistrar.register_commands(bot, cog)
