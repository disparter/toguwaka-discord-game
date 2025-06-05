import discord
from discord.ext import commands
from discord import app_commands
import logging
import random
import asyncio
from datetime import datetime, timedelta
from utils.database import get_player, update_player, get_club
from utils.embeds import create_basic_embed, create_event_embed, create_duel_embed
from utils.game_mechanics import (
    get_random_training_outcome, get_random_event, 
    calculate_duel_outcome, generate_duel_narration,
    calculate_level_from_exp
)

logger = logging.getLogger('tokugawa_bot')

# Cooldown tracking
COOLDOWNS = {
    # user_id: {command_name: expiry_timestamp}
}

# Cooldown durations in seconds
COOLDOWN_DURATIONS = {
    "treinar": 3600,  # 1 hour
    "explorar": 3600,  # 1 hour
    "duelar": 1800,   # 30 minutes
    "evento": 86400   # 24 hours
}

class Activities(commands.Cog):
    """Cog for player activities and interactions."""

    def __init__(self, bot):
        self.bot = bot
        self.active_duels = {}  # {challenger_id: opponent_id}

    # Group for activity commands
    activity_group = app_commands.Group(name="atividade", description="Comandos de atividades da Academia Tokugawa")

    @activity_group.command(name="treinar", description="Treinar para ganhar experiência e melhorar atributos")
    async def slash_train(self, interaction: discord.Interaction):
        """Slash command version of the train command."""
        try:
            # Check if player exists
            player = get_player(interaction.user.id)
            if not player:
                await interaction.response.send_message(f"{interaction.user.mention}, você ainda não está registrado na Academia Tokugawa. Use /registro ingressar para criar seu personagem.")
                return

            # Check cooldown
            cooldown = self._check_cooldown(interaction.user.id, "treinar")
            if cooldown:
                await interaction.response.send_message(f"{interaction.user.mention}, você precisa descansar antes de treinar novamente. Tempo restante: {cooldown}")
                return

            # Get a random training outcome
            outcome = get_random_training_outcome()

            # Calculate experience and attribute gains
            exp_gain = random.randint(10, 30)
            attribute_gain = random.choice(["dexterity", "intellect", "charisma", "power_stat"])

            # Update player data
            new_exp = player["exp"] + exp_gain
            new_level = calculate_level_from_exp(new_exp)
            level_up = new_level > player["level"]

            # Prepare update data
            update_data = {
                "exp": new_exp,
                attribute_gain: player[attribute_gain] + 1  # Increase the chosen attribute
            }

            if level_up:
                update_data["level"] = new_level
                # Bonus TUSD for level up
                update_data["tusd"] = player["tusd"] + (new_level * 50)

            # Update player in database
            success = update_player(interaction.user.id, **update_data)

            if success:
                # Set cooldown
                self._set_cooldown(interaction.user.id, "treinar")

                # Create embed for training result
                embed = create_basic_embed(
                    title="Treinamento Concluído!",
                    description=outcome,
                    color=0x00FF00
                )

                # Add experience gain
                embed.add_field(
                    name="Experiência Ganha",
                    value=f"+{exp_gain} EXP",
                    inline=True
                )

                # Add attribute gain
                attribute_names = {
                    "dexterity": "Destreza 🏃‍♂️",
                    "intellect": "Intelecto 🧠",
                    "charisma": "Carisma 💬",
                    "power_stat": "Poder ⚡"
                }
                embed.add_field(
                    name="Atributo Melhorado",
                    value=f"{attribute_names[attribute_gain]} +1",
                    inline=True
                )

                # Add level up message if applicable
                if level_up:
                    embed.add_field(
                        name="Nível Aumentado!",
                        value=f"Você subiu para o nível {new_level}!\n+{new_level * 50} TUSD",
                        inline=False
                    )

                await interaction.response.send_message(embed=embed)
            else:
                await interaction.response.send_message("Ocorreu um erro durante o treinamento. Por favor, tente novamente mais tarde.")
        except discord.errors.NotFound:
            # If the interaction has expired, log it but don't try to respond
            logger.warning(f"Interaction expired for user {interaction.user.id} when using /atividade treinar")
        except Exception as e:
            logger.error(f"Error in slash_train: {e}")

    @activity_group.command(name="explorar", description="Explorar a academia em busca de eventos aleatórios")
    async def slash_explore(self, interaction: discord.Interaction):
        """Slash command version of the explore command."""
        try:
            # Check if player exists
            player = get_player(interaction.user.id)
            if not player:
                await interaction.response.send_message(f"{interaction.user.mention}, você ainda não está registrado na Academia Tokugawa. Use /registro ingressar para criar seu personagem.")
                return

            # Check cooldown
            cooldown = self._check_cooldown(interaction.user.id, "explorar")
            if cooldown:
                await interaction.response.send_message(f"{interaction.user.mention}, você precisa descansar antes de explorar novamente. Tempo restante: {cooldown}")
                return

            # Get a random event
            event = get_random_event()

            # Process event effects
            update_data = {}

            for key, value in event["effect"].items():
                if key == "exp":
                    update_data["exp"] = player["exp"] + value
                elif key == "tusd":
                    update_data["tusd"] = max(0, player["tusd"] + value)  # Ensure TUSD doesn't go below 0
                elif key == "attribute" and value == "random":
                    # Randomly increase an attribute
                    attribute = random.choice(["dexterity", "intellect", "charisma", "power_stat"])
                    update_data[attribute] = player[attribute] + 1
                    event["effect"][key] = attribute  # Update the event effect for display

            # Check for level up
            if "exp" in update_data:
                new_level = calculate_level_from_exp(update_data["exp"])
                if new_level > player["level"]:
                    update_data["level"] = new_level
                    # Bonus TUSD for level up
                    if "tusd" in update_data:
                        update_data["tusd"] += new_level * 50
                    else:
                        update_data["tusd"] = player["tusd"] + (new_level * 50)

            # Update player in database
            success = update_player(interaction.user.id, **update_data)

            if success:
                # Set cooldown
                self._set_cooldown(interaction.user.id, "explorar")

                # Create embed for event
                embed = create_event_embed(event)

                # Add level up message if applicable
                if "level" in update_data:
                    embed.add_field(
                        name="Nível Aumentado!",
                        value=f"Você subiu para o nível {update_data['level']}!\n+{update_data['level'] * 50} TUSD",
                        inline=False
                    )

                await interaction.response.send_message(embed=embed)
            else:
                await interaction.response.send_message("Ocorreu um erro durante a exploração. Por favor, tente novamente mais tarde.")
        except discord.errors.NotFound:
            # If the interaction has expired, log it but don't try to respond
            logger.warning(f"Interaction expired for user {interaction.user.id} when using /atividade explorar")
        except Exception as e:
            logger.error(f"Error in slash_explore: {e}")

    @activity_group.command(name="duelar", description="Desafiar outro jogador para um duelo")
    async def slash_duel(self, interaction: discord.Interaction, opponent: discord.Member, duel_type: str = "physical"):
        """Slash command version of the duel command."""
        try:
            # Check if opponent is specified
            if not opponent:
                await interaction.response.send_message(f"{interaction.user.mention}, você precisa mencionar um oponente para duelar.")
                return

            # Check if player is trying to duel themselves
            if opponent.id == interaction.user.id:
                await interaction.response.send_message(f"{interaction.user.mention}, você não pode duelar consigo mesmo!")
                return

            # Check if player exists
            challenger = get_player(interaction.user.id)
            if not challenger:
                await interaction.response.send_message(f"{interaction.user.mention}, você ainda não está registrado na Academia Tokugawa. Use /registro ingressar para criar seu personagem.")
                return

            # Check if opponent exists
            opponent_player = get_player(opponent.id)
            if not opponent_player:
                await interaction.response.send_message(f"{opponent.mention} não está registrado na Academia Tokugawa.")
                return

            # Check cooldown
            cooldown = self._check_cooldown(interaction.user.id, "duelar")
            if cooldown:
                await interaction.response.send_message(f"{interaction.user.mention}, você precisa descansar antes de duelar novamente. Tempo restante: {cooldown}")
                return

            # Check if player is already in a duel
            if interaction.user.id in self.active_duels or opponent.id in self.active_duels.values():
                await interaction.response.send_message(f"{interaction.user.mention}, você ou seu oponente já está em um duelo!")
                return

            # Validate duel type
            valid_types = ["physical", "mental", "strategic", "social"]
            if duel_type.lower() not in valid_types:
                duel_type = "physical"  # Default to physical
            else:
                duel_type = duel_type.lower()

            # Create duel challenge embed
            duel_names = {
                "physical": "Físico",
                "mental": "Mental",
                "strategic": "Estratégico",
                "social": "Social"
            }

            # Send initial response
            await interaction.response.send_message(f"Desafio enviado para {opponent.mention}!")

            # Create challenge embed
            challenge_embed = create_basic_embed(
                title="Desafio de Duelo!",
                description=f"{interaction.user.mention} desafiou {opponent.mention} para um duelo **{duel_names[duel_type]}**!\n\n"
                            f"{opponent.mention}, você aceita o desafio? Clique nos botões abaixo para responder.",
                color=0xFF0000
            )

            # Create buttons for accepting or declining
            view = discord.ui.View(timeout=60)

            async def accept_callback(button_interaction):
                if button_interaction.user.id != opponent.id:
                    await button_interaction.response.send_message("Apenas o oponente desafiado pode aceitar ou recusar.", ephemeral=True)
                    return

                # Disable buttons
                for child in view.children:
                    child.disabled = True
                await button_interaction.message.edit(view=view)

                # Mark duel as active
                self.active_duels[interaction.user.id] = opponent.id

                # Calculate duel outcome
                duel_result = calculate_duel_outcome(challenger, opponent_player, duel_type)

                # Generate narration
                narration = generate_duel_narration(duel_result)
                duel_result["narration"] = narration

                # Update winner and loser
                winner_id = duel_result["winner"]["user_id"]
                loser_id = duel_result["loser"]["user_id"]

                # Update winner
                winner_update = {
                    "exp": duel_result["winner"]["exp"] + duel_result["exp_reward"],
                    "tusd": duel_result["winner"]["tusd"] + duel_result["tusd_reward"]
                }

                # Check for level up
                new_level = calculate_level_from_exp(winner_update["exp"])
                if new_level > duel_result["winner"]["level"]:
                    winner_update["level"] = new_level
                    # Add level up bonus
                    winner_update["tusd"] += new_level * 50

                # Update loser (half exp, no TUSD)
                loser_update = {
                    "exp": duel_result["loser"]["exp"] + (duel_result["exp_reward"] // 2)
                }

                # Check for level up
                new_level = calculate_level_from_exp(loser_update["exp"])
                if new_level > duel_result["loser"]["level"]:
                    loser_update["level"] = new_level

                # Update players in database
                winner_success = update_player(winner_id, **winner_update)
                loser_success = update_player(loser_id, **loser_update)

                if winner_success and loser_success:
                    # Set cooldown for challenger
                    self._set_cooldown(interaction.user.id, "duelar")

                    # Create duel result embed
                    embed = create_duel_embed(duel_result)

                    # Add level up messages if applicable
                    if "level" in winner_update:
                        embed.add_field(
                            name=f"{duel_result['winner']['name']} Subiu de Nível!",
                            value=f"Novo nível: {winner_update['level']}",
                            inline=False
                        )

                    if "level" in loser_update:
                        embed.add_field(
                            name=f"{duel_result['loser']['name']} Subiu de Nível!",
                            value=f"Novo nível: {loser_update['level']}",
                            inline=False
                        )

                    await button_interaction.response.send_message(embed=embed)
                else:
                    await button_interaction.response.send_message("Ocorreu um erro durante o duelo. Por favor, tente novamente mais tarde.")

                # Remove active duel
                if interaction.user.id in self.active_duels:
                    del self.active_duels[interaction.user.id]

            async def decline_callback(button_interaction):
                if button_interaction.user.id != opponent.id:
                    await button_interaction.response.send_message("Apenas o oponente desafiado pode aceitar ou recusar.", ephemeral=True)
                    return

                # Disable buttons
                for child in view.children:
                    child.disabled = True
                await button_interaction.message.edit(view=view)

                await button_interaction.response.send_message(f"{opponent.mention} recusou o desafio de duelo.")

            # Add buttons to view
            accept_button = discord.ui.Button(label="Aceitar", style=discord.ButtonStyle.green)
            decline_button = discord.ui.Button(label="Recusar", style=discord.ButtonStyle.red)
            accept_button.callback = accept_callback
            decline_button.callback = decline_callback
            view.add_item(accept_button)
            view.add_item(decline_button)

            # Send challenge with buttons
            channel = interaction.channel
            message = await channel.send(embed=challenge_embed, view=view)

            # Set timeout handler
            async def on_timeout():
                # Disable buttons
                for child in view.children:
                    child.disabled = True
                try:
                    await message.edit(view=view)
                    await channel.send(f"{opponent.mention} não respondeu ao desafio a tempo.")
                except:
                    pass

            view.on_timeout = on_timeout

        except discord.errors.NotFound:
            # If the interaction has expired, log it but don't try to respond
            logger.warning(f"Interaction expired for user {interaction.user.id} when using /atividade duelar")
        except Exception as e:
            logger.error(f"Error in slash_duel: {e}")

    @activity_group.command(name="evento", description="Participar do evento atual da academia")
    async def slash_event(self, interaction: discord.Interaction):
        """Slash command version of the event command."""
        try:
            # Check if player exists
            player = get_player(interaction.user.id)
            if not player:
                await interaction.response.send_message(f"{interaction.user.mention}, você ainda não está registrado na Academia Tokugawa. Use /registro ingressar para criar seu personagem.")
                return

            # This is a placeholder for future weekly events
            await interaction.response.send_message("Não há eventos ativos no momento. Fique atento para futuros eventos na Academia Tokugawa!")
        except discord.errors.NotFound:
            # If the interaction has expired, log it but don't try to respond
            logger.warning(f"Interaction expired for user {interaction.user.id} when using /atividade evento")
        except Exception as e:
            logger.error(f"Error in slash_event: {e}")

    def _check_cooldown(self, user_id, command):
        """Check if a command is on cooldown for a user."""
        now = datetime.now().timestamp()

        # Initialize user cooldowns if not exists
        if user_id not in COOLDOWNS:
            COOLDOWNS[user_id] = {}

        # Check if command is on cooldown
        if command in COOLDOWNS[user_id] and COOLDOWNS[user_id][command] > now:
            # Calculate remaining time
            remaining = COOLDOWNS[user_id][command] - now
            minutes, seconds = divmod(int(remaining), 60)
            hours, minutes = divmod(minutes, 60)

            if hours > 0:
                time_str = f"{hours}h {minutes}m {seconds}s"
            elif minutes > 0:
                time_str = f"{minutes}m {seconds}s"
            else:
                time_str = f"{seconds}s"

            return time_str

        return None

    def _set_cooldown(self, user_id, command):
        """Set a cooldown for a command for a user."""
        if user_id not in COOLDOWNS:
            COOLDOWNS[user_id] = {}

        duration = COOLDOWN_DURATIONS.get(command, 3600)  # Default 1 hour
        expiry_time = datetime.now().timestamp() + duration
        COOLDOWNS[user_id][command] = expiry_time

        # Store cooldown in database
        try:
            from utils.database import store_cooldown
            store_cooldown(user_id, command, expiry_time)
        except Exception as e:
            logger.error(f"Error storing cooldown in database: {e}")

    @commands.command(name="treinar")
    async def train(self, ctx):
        """Treinar para ganhar experiência e melhorar atributos."""
        # Check if player exists
        player = get_player(ctx.author.id)
        if not player:
            await ctx.send(f"{ctx.author.mention}, você ainda não está registrado na Academia Tokugawa. Use !ingressar para criar seu personagem.")
            return

        # Check cooldown
        cooldown = self._check_cooldown(ctx.author.id, "treinar")
        if cooldown:
            await ctx.send(f"{ctx.author.mention}, você precisa descansar antes de treinar novamente. Tempo restante: {cooldown}")
            return

        # Get a random training outcome
        outcome = get_random_training_outcome()

        # Calculate experience and attribute gains
        exp_gain = random.randint(10, 30)
        attribute_gain = random.choice(["dexterity", "intellect", "charisma", "power_stat"])

        # Update player data
        new_exp = player["exp"] + exp_gain
        new_level = calculate_level_from_exp(new_exp)
        level_up = new_level > player["level"]

        # Prepare update data
        update_data = {
            "exp": new_exp,
            attribute_gain: player[attribute_gain] + 1  # Increase the chosen attribute
        }

        if level_up:
            update_data["level"] = new_level
            # Bonus TUSD for level up
            update_data["tusd"] = player["tusd"] + (new_level * 50)

        # Update player in database
        success = update_player(ctx.author.id, **update_data)

        if success:
            # Set cooldown
            self._set_cooldown(ctx.author.id, "treinar")

            # Create embed for training result
            embed = create_basic_embed(
                title="Treinamento Concluído!",
                description=outcome,
                color=0x00FF00
            )

            # Add experience gain
            embed.add_field(
                name="Experiência Ganha",
                value=f"+{exp_gain} EXP",
                inline=True
            )

            # Add attribute gain
            attribute_names = {
                "dexterity": "Destreza 🏃‍♂️",
                "intellect": "Intelecto 🧠",
                "charisma": "Carisma 💬",
                "power_stat": "Poder ⚡"
            }
            embed.add_field(
                name="Atributo Melhorado",
                value=f"{attribute_names[attribute_gain]} +1",
                inline=True
            )

            # Add level up message if applicable
            if level_up:
                embed.add_field(
                    name="Nível Aumentado!",
                    value=f"Você subiu para o nível {new_level}!\n+{new_level * 50} TUSD",
                    inline=False
                )

            await ctx.send(embed=embed)
        else:
            await ctx.send("Ocorreu um erro durante o treinamento. Por favor, tente novamente mais tarde.")

    @commands.command(name="explorar")
    async def explore(self, ctx):
        """Explorar a academia em busca de eventos aleatórios."""
        # Check if player exists
        player = get_player(ctx.author.id)
        if not player:
            await ctx.send(f"{ctx.author.mention}, você ainda não está registrado na Academia Tokugawa. Use !ingressar para criar seu personagem.")
            return

        # Check cooldown
        cooldown = self._check_cooldown(ctx.author.id, "explorar")
        if cooldown:
            await ctx.send(f"{ctx.author.mention}, você precisa descansar antes de explorar novamente. Tempo restante: {cooldown}")
            return

        # Get a random event
        event = get_random_event()

        # Process event effects
        update_data = {}

        for key, value in event["effect"].items():
            if key == "exp":
                update_data["exp"] = player["exp"] + value
            elif key == "tusd":
                update_data["tusd"] = max(0, player["tusd"] + value)  # Ensure TUSD doesn't go below 0
            elif key == "attribute" and value == "random":
                # Randomly increase an attribute
                attribute = random.choice(["dexterity", "intellect", "charisma", "power_stat"])
                update_data[attribute] = player[attribute] + 1
                event["effect"][key] = attribute  # Update the event effect for display

        # Check for level up
        if "exp" in update_data:
            new_level = calculate_level_from_exp(update_data["exp"])
            if new_level > player["level"]:
                update_data["level"] = new_level
                # Bonus TUSD for level up
                if "tusd" in update_data:
                    update_data["tusd"] += new_level * 50
                else:
                    update_data["tusd"] = player["tusd"] + (new_level * 50)

        # Update player in database
        success = update_player(ctx.author.id, **update_data)

        if success:
            # Set cooldown
            self._set_cooldown(ctx.author.id, "explorar")

            # Create embed for event
            embed = create_event_embed(event)

            # Add level up message if applicable
            if "level" in update_data:
                embed.add_field(
                    name="Nível Aumentado!",
                    value=f"Você subiu para o nível {update_data['level']}!\n+{update_data['level'] * 50} TUSD",
                    inline=False
                )

            await ctx.send(embed=embed)
        else:
            await ctx.send("Ocorreu um erro durante a exploração. Por favor, tente novamente mais tarde.")

    @commands.command(name="duelar")
    async def duel(self, ctx, opponent: discord.Member = None, duel_type: str = "physical"):
        """Desafiar outro jogador para um duelo."""
        # Check if opponent is specified
        if not opponent:
            await ctx.send(f"{ctx.author.mention}, você precisa mencionar um oponente para duelar. Exemplo: !duelar @usuário")
            return

        # Check if player is trying to duel themselves
        if opponent.id == ctx.author.id:
            await ctx.send(f"{ctx.author.mention}, você não pode duelar consigo mesmo!")
            return

        # Check if player exists
        challenger = get_player(ctx.author.id)
        if not challenger:
            await ctx.send(f"{ctx.author.mention}, você ainda não está registrado na Academia Tokugawa. Use !ingressar para criar seu personagem.")
            return

        # Check if opponent exists
        opponent_player = get_player(opponent.id)
        if not opponent_player:
            await ctx.send(f"{opponent.mention} não está registrado na Academia Tokugawa.")
            return

        # Check cooldown
        cooldown = self._check_cooldown(ctx.author.id, "duelar")
        if cooldown:
            await ctx.send(f"{ctx.author.mention}, você precisa descansar antes de duelar novamente. Tempo restante: {cooldown}")
            return

        # Check if player is already in a duel
        if ctx.author.id in self.active_duels or opponent.id in self.active_duels.values():
            await ctx.send(f"{ctx.author.mention}, você ou seu oponente já está em um duelo!")
            return

        # Validate duel type
        valid_types = ["physical", "mental", "strategic", "social"]
        if duel_type.lower() not in valid_types:
            duel_type = "physical"  # Default to physical
        else:
            duel_type = duel_type.lower()

        # Create duel challenge embed
        duel_names = {
            "physical": "Físico",
            "mental": "Mental",
            "strategic": "Estratégico",
            "social": "Social"
        }

        challenge_embed = create_basic_embed(
            title="Desafio de Duelo!",
            description=f"{ctx.author.mention} desafiou {opponent.mention} para um duelo **{duel_names[duel_type]}**!\n\n"
                        f"{opponent.mention}, você aceita o desafio? Responda com 'sim' ou 'não' em 60 segundos.",
            color=0xFF0000
        )
        await ctx.send(embed=challenge_embed)

        # Mark duel as active
        self.active_duels[ctx.author.id] = opponent.id

        def check(m):
            return m.author.id == opponent.id and m.channel == ctx.channel and m.content.lower() in ["sim", "não", "nao", "yes", "no"]

        try:
            # Wait for opponent's response
            response = await self.bot.wait_for('message', check=check, timeout=60.0)

            # Process response
            if response.content.lower() in ["sim", "yes"]:
                # Calculate duel outcome
                duel_result = calculate_duel_outcome(challenger, opponent_player, duel_type)

                # Generate narration
                narration = generate_duel_narration(duel_result)
                duel_result["narration"] = narration

                # Update winner and loser
                winner_id = duel_result["winner"]["user_id"]
                loser_id = duel_result["loser"]["user_id"]

                # Update winner
                winner_update = {
                    "exp": duel_result["winner"]["exp"] + duel_result["exp_reward"],
                    "tusd": duel_result["winner"]["tusd"] + duel_result["tusd_reward"]
                }

                # Check for level up
                new_level = calculate_level_from_exp(winner_update["exp"])
                if new_level > duel_result["winner"]["level"]:
                    winner_update["level"] = new_level
                    # Add level up bonus
                    winner_update["tusd"] += new_level * 50

                # Update loser (half exp, no TUSD)
                loser_update = {
                    "exp": duel_result["loser"]["exp"] + (duel_result["exp_reward"] // 2)
                }

                # Check for level up
                new_level = calculate_level_from_exp(loser_update["exp"])
                if new_level > duel_result["loser"]["level"]:
                    loser_update["level"] = new_level

                # Update players in database
                winner_success = update_player(winner_id, **winner_update)
                loser_success = update_player(loser_id, **loser_update)

                if winner_success and loser_success:
                    # Set cooldown for challenger
                    self._set_cooldown(ctx.author.id, "duelar")

                    # Create duel result embed
                    embed = create_duel_embed(duel_result)

                    # Add level up messages if applicable
                    if "level" in winner_update:
                        embed.add_field(
                            name=f"{duel_result['winner']['name']} Subiu de Nível!",
                            value=f"Novo nível: {winner_update['level']}",
                            inline=False
                        )

                    if "level" in loser_update:
                        embed.add_field(
                            name=f"{duel_result['loser']['name']} Subiu de Nível!",
                            value=f"Novo nível: {loser_update['level']}",
                            inline=False
                        )

                    await ctx.send(embed=embed)
                else:
                    await ctx.send("Ocorreu um erro durante o duelo. Por favor, tente novamente mais tarde.")
            else:
                await ctx.send(f"{opponent.mention} recusou o desafio de duelo.")

        except asyncio.TimeoutError:
            await ctx.send(f"{opponent.mention} não respondeu ao desafio a tempo.")

        finally:
            # Remove active duel
            if ctx.author.id in self.active_duels:
                del self.active_duels[ctx.author.id]

    @commands.command(name="evento")
    async def event(self, ctx):
        """Participar do evento atual da academia."""
        # This is a placeholder for future weekly events
        await ctx.send("Não há eventos ativos no momento. Fique atento para futuros eventos na Academia Tokugawa!")

async def setup(bot):
    """Add the cog to the bot."""
    from utils.command_registrar import CommandRegistrar

    # Create and add the cog
    cog = Activities(bot)
    await bot.add_cog(cog)
    logger.info("Activities cog loaded")

    # Register commands using the CommandRegistrar
    await CommandRegistrar.register_commands(bot, cog)
