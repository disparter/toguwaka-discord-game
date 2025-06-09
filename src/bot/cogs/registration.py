import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import logging
import random
from src.utils.persistence.db_provider import get_player, create_player, get_all_clubs
from src.utils.embeds import create_basic_embed, create_player_embed
from src.utils.game_mechanics import STRENGTH_LEVELS
from src.utils.command_registrar import CommandRegistrar
from story_mode.club_system import ClubSystem

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
            player = await get_player(interaction.user.id)
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
        player = await get_player(ctx.author.id)
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
                            "1. Fraco - Poderes básicos e limitados\n" +
                            "2. Moderado - Poderes com algumas limitações\n" +
                            "3. Forte - Poderes significativos\n" +
                            "4. Muito Forte - Poderes excepcionais\n" +
                            "5. Extremamente Forte - Poderes raros e poderosos\n\n" +
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
            success = await create_player(
                ctx.author.id,
                character_name,
                power=character_power,
                strength_level=strength_level,
                club_id=selected_club['club_id']
            )

            if success:
                # Get the created player and their club
                player = await get_player(ctx.author.id)

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

async def setup(bot):
    """Add the cog to the bot."""
    from src.utils.command_registrar import CommandRegistrar

    # Create and add the cog
    cog = Registration(bot)
    await bot.add_cog(cog)
    logger.info("Registration cog loaded")

    # Register commands using the CommandRegistrar
    await CommandRegistrar.register_commands(bot, cog)

    # Add the registration_group to the bot's command tree
    try:
        bot.tree.add_command(cog.registration_group)
        logger.info(f"Added registration_group to command tree: /{cog.registration_group.name}")
    except discord.app_commands.errors.CommandAlreadyRegistered:
        logger.info(f"Registration_group already registered: /{cog.registration_group.name}")

    # Add the slash_register command directly to the bot's command tree
    @bot.tree.command(name="registrar", description="Iniciar o processo de registro na Academia Tokugawa")
    async def direct_slash_register(interaction: discord.Interaction):
        """Direct slash command for registration."""
        try:
            # Check if player already exists
            from src.utils.persistence.db_provider import get_player
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
            logger.warning(f"Interaction expired for user {interaction.user.id} when using /registrar")
        except Exception as e:
            logger.error(f"Error in direct_slash_register: {e}")

    # Log the slash commands that were added
    for cmd in cog.__cog_app_commands__:
        logger.info(f"Registration cog added slash command: /{cmd.name}")

    # Log the direct slash command that was added
    logger.info(f"Added direct slash command: /registrar")
