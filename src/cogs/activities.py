import asyncio
import discord
import json
import logging
import random
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any
from discord import app_commands
from discord.ext import commands
from discord.ext import tasks

from utils.embeds import create_basic_embed, create_event_embed, create_duel_embed
from utils.game_mechanics import (
    calculate_level_from_exp
)
from utils.game_mechanics.calculators.experience_calculator import ExperienceCalculator
from utils.game_mechanics.duel.duel_calculator import DuelCalculator
from utils.game_mechanics.duel.duel_narrator import DuelNarrator
from utils.game_mechanics.events.random_event import RandomEvent
from utils.game_mechanics.events.training_event import TrainingEvent
from utils.persistence import db_provider

logger = logging.getLogger('tokugawa_bot')

# Cooldown tracking
COOLDOWNS = {
    # user_id: {command_name: expiry_timestamp}
}

# Cooldown durations in seconds
COOLDOWN_DURATIONS = {
    "treinar": 3600,  # 1 hour
    "explorar": 3600,  # 1 hour
    "duelar": 1800,  # 30 minutes
    "evento": 86400  # 24 hours
}


class Activities(commands.Cog):
    """Cog for player activities and interactions."""

    def __init__(self, bot):
        self.bot = bot
        self.active_duels = {}  # {challenger_id: opponent_id}
        self.clear_cooldowns.start()

    def cog_unload(self):
        self.clear_cooldowns.cancel()

    @tasks.loop(minutes=5)
    async def clear_cooldowns(self):
        """Clear expired cooldowns."""
        try:
            await self.clear_expired_cooldowns()
        except Exception as e:
            logger.error(f"Error clearing cooldowns: {e}")

    @clear_cooldowns.before_loop
    async def before_clear_cooldowns(self):
        """Wait for the bot to be ready before clearing cooldowns."""
        await self.bot.wait_until_ready()

    # Group for activity commands
    activity_group = app_commands.Group(name="atividade", description="Comandos de atividades da Academia Tokugawa")

    @activity_group.command(name="treinar", description="Treinar para ganhar experiência e melhorar atributos")
    async def slash_train(self, interaction: discord.Interaction):
        """Slash command version of the train command."""
        try:
            # Check if player exists
            player = await db_provider.get_player(interaction.user.id)
            if not player:
                await interaction.response.send_message(
                    f"{interaction.user.mention}, você ainda não está registrado na Academia Tokugawa. Use /registro ingressar para criar seu personagem.",
                    ephemeral=True)
                return

            # Check cooldown
            cooldown = await self._check_cooldown(interaction.user.id, "treinar")
            if cooldown:
                await interaction.response.send_message(
                    f"{interaction.user.mention}, você precisa descansar antes de treinar novamente. Tempo restante: {cooldown}",
                    ephemeral=True)
                return

            # Create a random training event using the new SOLID architecture
            training_event = TrainingEvent.create_random_training_event()
            training_result = training_event.trigger(player)

            # Get the outcome, experience and attribute gains from the event
            outcome = training_event.get_description()
            exp_gain = training_result["exp_gain"]
            attribute_gain = training_result.get("attribute_gain",
                                                 random.choice(["dexterity", "intellect", "charisma", "power_stat"]))

            # Check if player has equipped accessories that boost experience
            inventory = player.get('inventory', {})
            if isinstance(inventory, str):
                try:
                    inventory = json.loads(inventory)
                except Exception:
                    inventory = {}
            if not isinstance(inventory, dict):
                inventory = {}

            accessory_boost_applied = False
            accessory_name = ""
            original_exp = exp_gain

            for item_id, item in inventory.items():
                if item["type"] == "accessory" and item.get("equipped", False) and "exp_boost" in item["effects"]:
                    # Apply experience boost from accessory
                    exp_boost = item["effects"]["exp_boost"]
                    exp_gain = int(exp_gain * exp_boost)
                    accessory_boost_applied = True
                    accessory_name = item["name"]
                    logger.info(
                        f"Player {player.get('name', 'Unknown')} gained {exp_gain} exp (boosted from {original_exp}) due to equipped accessory {item['name']}")

            # Update player data using the new ExperienceCalculator
            new_exp = player.get("exp", 0) + exp_gain
            new_level = ExperienceCalculator.calculate_level(new_exp)
            level_up = new_level > player.get("level", 1)

            # Prepare update data
            update_data = {
                "exp": new_exp,
                attribute_gain: player.get(attribute_gain, 5) + 1,  # Increase the chosen attribute
                "tusd": player.get("tusd", 0) + 10  # Add TUSD reward for training
            }

            if level_up:
                update_data["level"] = new_level
                # Full HP recovery on level up
                update_data["hp"] = player.get("max_hp", 100)
                # Bonus TUSD for level up
                update_data["tusd"] = player.get("tusd", 0) + (
                            new_level * 50) + 10  # Add base TUSD reward plus level up bonus

            # Apply HP loss for training (5-15% of max HP)
            if "hp" in player and "max_hp" in player:
                hp_loss = random.randint(5, 15)
                hp_loss_amount = int(player["max_hp"] * (hp_loss / 100))
                current_hp = player.get("hp", player["max_hp"])
                update_data["hp"] = max(1, current_hp - hp_loss_amount)

            # Update player in database
            success = await db_provider.update_player(interaction.user.id, **update_data)

            if success:
                # Set cooldown
                await self._set_cooldown(interaction.user.id, "treinar")

                # Create embed for training result
                embed = create_basic_embed(
                    title="Treinamento Concluído!",
                    description=outcome,
                    color=0x00FF00
                )

                # Add experience gain
                if accessory_boost_applied:
                    embed.add_field(
                        name="Experiência Ganha",
                        value=f"+{exp_gain} EXP (Bônus de {accessory_name}: +{exp_gain - original_exp} EXP)",
                        inline=True
                    )
                else:
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

                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(
                    "Ocorreu um erro durante o treinamento. Por favor, tente novamente mais tarde.", ephemeral=True)
        except discord.errors.NotFound:
            # If the interaction has expired, log it but don't try to respond
            logger.warning(f"Interaction expired for user {interaction.user.id} when using /atividade treinar")
        except Exception as e:
            logger.error(f"Error in slash_train: {e}", exc_info=True)
            try:
                await interaction.response.send_message(
                    "Ocorreu um erro durante o treinamento. Por favor, tente novamente mais tarde.", ephemeral=True)
            except discord.errors.NotFound:
                pass

    @activity_group.command(name="explorar", description="Explorar a academia em busca de eventos aleatórios")
    async def slash_explore(self, interaction: discord.Interaction):
        """Slash command version of the explore command."""
        try:
            # Check if player exists
            player = await db_provider.get_player(interaction.user.id)
            if not player:
                await interaction.response.send_message(
                    f"{interaction.user.mention}, você ainda não está registrado na Academia Tokugawa. Use /registro ingressar para criar seu personagem.",
                    ephemeral=True)
                return

            # Garantir que o inventário é um dicionário
            inventory = player.get('inventory', {})
            if isinstance(inventory, str):
                try:
                    inventory = json.loads(inventory)
                except Exception:
                    inventory = {}
            if not isinstance(inventory, dict):
                inventory = {}
            player['inventory'] = inventory

            # Check cooldown
            cooldowns = await db_provider.get_cooldowns(str(interaction.user.id))
            for cooldown in cooldowns:
                if cooldown['SK'] == 'COOLDOWN#explore':
                    expiry = datetime.fromisoformat(cooldown['expiry'])
                    if datetime.now() < expiry:
                        remaining = expiry - datetime.now()
                        await interaction.response.send_message(
                            f"{interaction.user.mention}, você precisa esperar {int(remaining.total_seconds() / 60)} minutos antes de explorar novamente.",
                            ephemeral=True
                        )
                        return

            # Create a random event using the enhanced RandomEvent class
            random_event = RandomEvent.create_random_event()

            # Trigger the event for the player
            event_result = random_event.trigger(player)

            # Process event effects
            update_data = {}

            # Experience change
            if "exp_change" in event_result:
                update_data["exp"] = player.get("exp", 0) + event_result["exp_change"]

            # TUSD change
            if "tusd_change" in event_result:
                update_data["tusd"] = max(0, player.get("tusd", 0) + event_result[
                    "tusd_change"])  # Ensure TUSD doesn't go below 0

            # Primary attribute change
            if "attribute_change" in event_result:
                attribute = event_result["attribute_change"]
                value = event_result["attribute_value"]
                current_value = player.get(attribute, 5)  # Default to 5 if not found
                update_data[attribute] = max(1, min(10, current_value + value))  # Keep between 1 and 10

            # Secondary attribute change (usually negative)
            if "secondary_attribute_change" in event_result:
                attribute = event_result["secondary_attribute_change"]
                value = event_result["secondary_attribute_value"]
                current_value = player.get(attribute, 5)  # Default to 5 if not found
                update_data[attribute] = max(1, min(10, current_value + value))  # Keep between 1 and 10

            # All attributes boost
            if "all_attributes_change" in event_result:
                value = event_result["all_attributes_change"]
                for attr in ["dexterity", "intellect", "charisma", "power_stat"]:
                    current_value = player.get(attr, 5)  # Default to 5 if not found
                    update_data[attr] = max(1, min(10, current_value + value))  # Keep between 1 and 10

            # Check for level up
            if "exp" in update_data:
                new_level = calculate_level_from_exp(update_data["exp"])
                if new_level > player.get("level", 1):
                    update_data["level"] = new_level
                    # Full HP recovery on level up
                    update_data["hp"] = player.get("max_hp", 100)
                    # Bonus TUSD for level up
                    if "tusd" in update_data:
                        update_data["tusd"] += new_level * 50
                    else:
                        update_data["tusd"] = player.get("tusd", 0) + (new_level * 50)

            # Apply HP loss for training (5-15% of max HP)
            if "hp" in player and "max_hp" in player:
                hp_loss = random.randint(5, 15)
                hp_loss_amount = int(player["max_hp"] * (hp_loss / 100))
                current_hp = player.get("hp", player["max_hp"])
                update_data["hp"] = max(1, current_hp - hp_loss_amount)

            # Handle item rewards
            if "item_reward" in event_result:
                logger.info(f"Player {player.get('name', 'Unknown')} received item: {event_result['item_reward']}")
                # Add item to inventory
                item_id = f"item_{datetime.now().timestamp()}"
                inventory[item_id] = event_result['item_reward']
                update_data['inventory'] = json.dumps(inventory)

            # Update player in database
            success = await db_provider.update_player(interaction.user.id, **update_data)

            if success:
                # Set cooldown
                await db_provider.store_cooldown(
                    str(interaction.user.id),
                    'explore',
                    datetime.now() + timedelta(minutes=30)
                )

                # Create embed for event
                embed = create_event_embed(event_result)

                # Add level up message if applicable
                if "level" in update_data:
                    embed.add_field(
                        name="Nível Aumentado!",
                        value=f"Você subiu para o nível {update_data['level']}!\n+{update_data['level'] * 50} TUSD",
                        inline=False
                    )

                await interaction.response.send_message(embed=embed)
            else:
                await interaction.response.send_message(
                    "Ocorreu um erro durante a exploração. Por favor, tente novamente mais tarde.")
        except discord.errors.NotFound:
            # If the interaction has expired, log it but don't try to respond
            logger.warning(f"Interaction expired for user {interaction.user.id} when using /atividade explorar")
        except Exception as e:
            logger.error(f"Error in slash_explore: {e}", exc_info=True)
            try:
                await interaction.response.send_message(
                    "Ocorreu um erro durante a exploração. Por favor, tente novamente mais tarde.")
            except discord.errors.NotFound:
                pass

    async def handle_duel(self, interaction: discord.Interaction, opponent: discord.Member,
                          duel_type: str = "physical"):
        """Handle duel logic for both slash_duel and slash_bet_duel commands."""
        try:
            # Check if opponent is specified
            if not opponent:
                await interaction.response.send_message(
                    f"{interaction.user.mention}, você precisa mencionar um oponente para duelar.")
                return False

            # Check if player is trying to duel themselves
            if opponent.id == interaction.user.id:
                await interaction.response.send_message(
                    f"{interaction.user.mention}, você não pode duelar consigo mesmo!")
                return False

            # Check if player exists
            challenger = await db_provider.get_player(interaction.user.id)
            if not challenger:
                await interaction.response.send_message(
                    f"{interaction.user.mention}, você ainda não está registrado na Academia Tokugawa. Use /registro ingressar para criar seu personagem.")
                return False

            # Check if opponent exists
            opponent_player = await db_provider.get_player(opponent.id)
            if not opponent_player:
                await interaction.response.send_message(f"{opponent.mention} não está registrado na Academia Tokugawa.")
                return False

            # Validate duel type
            valid_types = ["physical", "mental", "strategic", "social", "elemental"]
            if duel_type.lower() not in valid_types:
                duel_type = "physical"  # Default to physical
            else:
                duel_type = duel_type.lower()

            # Create duel challenge embed
            duel_names = {
                "physical": "Físico",
                "mental": "Mental",
                "strategic": "Estratégico",
                "social": "Social",
                "elemental": "Elemental"
            }

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
                    await button_interaction.response.send_message(
                        "Apenas o oponente desafiado pode aceitar ou recusar.", ephemeral=True)
                    return

                # Disable buttons
                for child in view.children:
                    child.disabled = True
                await button_interaction.message.edit(view=view)

                # Mark duel as active
                self.active_duels[interaction.user.id] = opponent.id

                # Calculate duel outcome using the new DuelCalculator
                calculator = DuelCalculator()
                duel_result = calculator.calculate_outcome(challenger, opponent_player, duel_type)

                # Generate narration using the new DuelNarrator
                narration = DuelNarrator.generate_narration(duel_result)
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
                    # Full HP recovery on level up
                    winner_update["hp"] = player["max_hp"]
                    # Add level up bonus
                    winner_update["tusd"] += new_level * 50

                # Check for bonus rewards
                if "bonus_rewards" in duel_result and duel_result["bonus_rewards"] and "item" in duel_result[
                    "bonus_rewards"]:
                    # Get winner's inventory
                    winner_player = await db_provider.get_player(winner_id)
                    if winner_player and "inventory" in winner_player:
                        inventory = winner_player["inventory"]

                        # Get bonus item details
                        bonus_item = duel_result["bonus_rewards"]
                        item_id = bonus_item["item"]

                        # Check if item already exists in inventory
                        if str(item_id) in inventory:
                            # Increment quantity
                            inventory[str(item_id)]["quantity"] += 1
                        else:
                            # Add new item to inventory
                            inventory_item = {
                                "id": item_id,
                                "name": bonus_item["item_name"],
                                "description": bonus_item["item_description"],
                                "quantity": 1,
                                "type": "consumable",
                                "rarity": "uncommon",
                                "category": "duel_reward"
                            }
                            inventory[str(item_id)] = inventory_item

                        # Add inventory to winner update
                        winner_update["inventory"] = json.dumps(inventory)

                # Update loser (half exp, no TUSD, and HP loss)
                loser_update = {
                    "exp": duel_result["loser"]["exp"] + (duel_result["exp_reward"] // 2)
                }

                # Apply HP loss to loser if HP system is available
                if 'hp' in duel_result["loser"] and 'max_hp' in duel_result["loser"]:
                    current_hp = duel_result["loser"]["hp"]
                    hp_loss = duel_result.get("hp_loss", 10)  # Default to 10 if not specified
                    new_hp = max(1, current_hp - hp_loss)  # Ensure HP doesn't go below 1
                    loser_update["hp"] = new_hp

                # Check for level up
                new_level = calculate_level_from_exp(loser_update["exp"])
                if new_level > duel_result["loser"]["level"]:
                    loser_update["level"] = new_level

                # Update players in database
                winner_success = await db_provider.update_player(winner_id, **winner_update)
                loser_success = await db_provider.update_player(loser_id, **loser_update)

                if winner_success and loser_success:
                    # Set cooldown for challenger
                    await self._set_cooldown(interaction.user.id, "duelar")

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

                    # Dispatch an event for the duel completion
                    self.bot.dispatch("duel_complete", duel_result)
                else:
                    await button_interaction.response.send_message(
                        "Ocorreu um erro durante o duelo. Por favor, tente novamente mais tarde.")

                # Remove active duel
                if interaction.user.id in self.active_duels:
                    del self.active_duels[interaction.user.id]

            async def decline_callback(button_interaction):
                if button_interaction.user.id != opponent.id:
                    await button_interaction.response.send_message(
                        "Apenas o oponente desafiado pode aceitar ou recusar.", ephemeral=True)
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
                try:
                    # Disable buttons
                    for child in view.children:
                        child.disabled = True
                    
                    # Try to edit the message first
                    try:
                        await message.edit(view=view)
                    except discord.NotFound:
                        logger.warning(f"Message not found when handling duel timeout for user {interaction.user.id}")
                    except discord.HTTPException as e:
                        logger.error(f"Failed to edit message during duel timeout: {e}")
                    
                    # Try to send timeout message
                    try:
                        await channel.send(f"{opponent.mention} não respondeu ao desafio a tempo.")
                    except discord.HTTPException as e:
                        logger.error(f"Failed to send timeout message: {e}")
                    
                    # Clean up active duel if it exists
                    if interaction.user.id in self.active_duels:
                        del self.active_duels[interaction.user.id]
                        
                except Exception as e:
                    logger.error(f"Error in duel timeout handler: {e}")

            view.on_timeout = on_timeout
            return True

        except discord.errors.NotFound:
            # If the interaction has expired, log it but don't try to respond
            logger.warning(f"Interaction expired for user {interaction.user.id} when using duel")
            return False
        except Exception as e:
            logger.error(f"Error in handle_duel: {e}")
            return False

    @activity_group.command(name="duelar", description="Desafiar outro jogador para um duelo")
    @app_commands.choices(duel_type=[
        app_commands.Choice(name="Físico", value="physical"),
        app_commands.Choice(name="Mental", value="mental"),
        app_commands.Choice(name="Estratégico", value="strategic"),
        app_commands.Choice(name="Social", value="social"),
        app_commands.Choice(name="Elemental", value="elemental")
    ])
    async def slash_duel(self, interaction: discord.Interaction, opponent: discord.Member, duel_type: str = "physical"):
        """Slash command version of the duel command."""
        try:
            # Check cooldown
            cooldown = await self._check_cooldown(interaction.user.id, "duelar")
            if cooldown:
                await interaction.response.send_message(
                    f"{interaction.user.mention}, você precisa descansar antes de duelar novamente. Tempo restante: {cooldown}")
                return

            # Check if player is already in a duel
            if interaction.user.id in self.active_duels or opponent.id in self.active_duels.values():
                await interaction.response.send_message(
                    f"{interaction.user.mention}, você ou seu oponente já está em um duelo!")
                return

            # Send initial response
            await interaction.response.send_message(f"Desafio enviado para {opponent.mention}!")

            # Handle the duel logic
            await self.handle_duel(interaction, opponent, duel_type)

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
            player = db_provider.get_player(interaction.user.id)
            if not player:
                await interaction.response.send_message(
                    f"{interaction.user.mention}, você ainda não está registrado na Academia Tokugawa. Use /registro ingressar para criar seu personagem.")
                return

            # Check cooldown
            cooldown = await self._check_cooldown(interaction.user.id, "evento")
            if cooldown:
                await interaction.response.send_message(
                    f"{interaction.user.mention}, você precisa esperar antes de participar de outro evento. Tempo restante: {cooldown}")
                return

            # Create a random event using the new SOLID architecture
            random_event = RandomEvent.create_random_event()
            event_result = random_event.trigger(player)

            # Process the event result
            update_data = {}

            # Experience change
            if "exp_change" in event_result:
                exp_change = event_result["exp_change"]
                new_exp = player["exp"] + exp_change
                update_data["exp"] = new_exp

                # Check for level up
                new_level = ExperienceCalculator.calculate_level(new_exp)
                if new_level > player["level"]:
                    update_data["level"] = new_level
                    # Full HP recovery on level up
                    update_data["hp"] = player["max_hp"]
                    # Bonus TUSD for level up
                    update_data["tusd"] = player.get("tusd", 0) + (new_level * 50)

            # TUSD change
            if "tusd_change" in event_result and "tusd" not in update_data:
                tusd_change = event_result["tusd_change"]
                update_data["tusd"] = player.get("tusd", 0) + tusd_change

            # Attribute change
            if "attribute_change" in event_result:
                attribute = event_result["attribute_change"]
                value = event_result.get("attribute_value", 1)
                update_data[attribute] = player.get(attribute, 0) + value

            # Update player in database
            success = db_provider.update_player(interaction.user.id, **update_data)

            if success:
                # Set cooldown
                await self._set_cooldown(interaction.user.id, "evento")

                # Create embed for event result
                embed = create_event_embed(
                    title=random_event.get_title(),
                    description=random_event.get_description(),
                    event_type=random_event.get_type()
                )

                # Add fields for changes
                if "exp_change" in event_result:
                    embed.add_field(
                        name="Experiência",
                        value=f"{'+' if event_result['exp_change'] >= 0 else ''}{event_result['exp_change']} EXP",
                        inline=True
                    )

                if "tusd_change" in event_result:
                    embed.add_field(
                        name="TUSD",
                        value=f"{'+' if event_result['tusd_change'] >= 0 else ''}{event_result['tusd_change']} TUSD",
                        inline=True
                    )

                if "attribute_change" in event_result:
                    attribute_names = {
                        "dexterity": "Destreza",
                        "intellect": "Intelecto",
                        "charisma": "Carisma",
                        "power_stat": "Poder"
                    }
                    attribute_name = attribute_names.get(event_result["attribute_change"],
                                                         event_result["attribute_change"])
                    embed.add_field(
                        name=attribute_name,
                        value=f"+{event_result.get('attribute_value', 1)}",
                        inline=True
                    )

                if "item_reward" in event_result:
                    embed.add_field(
                        name="Item",
                        value=f"Você recebeu: {event_result['item_reward']}",
                        inline=False
                    )

                await interaction.response.send_message(embed=embed)

                # If the event triggers a duel, start it
                if event_result.get("trigger_duel", False):
                    # This would be implemented in a future update
                    await interaction.followup.send(
                        "Um duelo foi desencadeado pelo evento! Esta funcionalidade será implementada em breve.")
            else:
                await interaction.response.send_message(
                    "Ocorreu um erro ao processar o evento. Por favor, tente novamente mais tarde.")
        except discord.errors.NotFound:
            # If the interaction has expired, log it but don't try to respond
            logger.warning(f"Interaction expired for user {interaction.user.id} when using /atividade evento")
        except Exception as e:
            logger.error(f"Error in slash_event: {e}")

    async def _check_cooldown(self, user_id, command):
        """Check if a command is on cooldown for a user."""
        try:
            # Get cooldown directly for this user and command
            cooldown = await db_provider.get_cooldown(str(user_id), command)

            if cooldown:
                if datetime.now() < cooldown:
                    remaining = cooldown - datetime.now()
                    minutes = int(remaining.total_seconds() // 60)
                    seconds = int(remaining.total_seconds() % 60)
                    return f"{minutes}m {seconds}s"
            return None
        except Exception as e:
            logger.error(f"Error checking cooldown: {e}")
            return None

    async def _set_cooldown(self, user_id, command, custom_duration=None):
        """Set a cooldown for a command for a user."""
        try:
            duration = custom_duration or COOLDOWN_DURATIONS.get(command, 3600)
            expiry = datetime.now() + timedelta(seconds=duration)
            await db_provider.store_cooldown(str(user_id), command, expiry)
        except Exception as e:
            logger.error(f"Error setting cooldown: {e}")

    @commands.command(name="treinar")
    async def train(self, ctx):
        """Treinar para ganhar experiência e melhorar atributos."""
        try:
            # Check if player exists
            player = await db_provider.get_player(ctx.author.id)
            if not player:
                await ctx.send(
                    f"{ctx.author.mention}, você ainda não está registrado na Academia Tokugawa. Use !ingressar para criar seu personagem.")
                return

            # Check cooldown
            cooldown = await self._check_cooldown(ctx.author.id, "treinar")
            if cooldown:
                await ctx.send(
                    f"{ctx.author.mention}, você precisa descansar antes de treinar novamente. Tempo restante: {cooldown}")
                return

            # Create a random training event using the new SOLID architecture
            training_event = TrainingEvent.create_random_training_event()
            training_result = training_event.trigger(player)

            # Get the outcome, experience and attribute gains from the event
            outcome = training_event.get_description()
            exp_gain = training_result["exp_gain"]
            attribute_gain = training_result.get("attribute_gain",
                                                 random.choice(["dexterity", "intellect", "charisma", "power_stat"]))

            # Check if player has equipped accessories that boost experience
            inventory = player.get('inventory', {})
            if isinstance(inventory, str):
                try:
                    inventory = json.loads(inventory)
                except Exception:
                    inventory = {}
            if not isinstance(inventory, dict):
                inventory = {}

            accessory_boost_applied = False
            accessory_name = ""
            original_exp = exp_gain

            for item_id, item in inventory.items():
                if item["type"] == "accessory" and item.get("equipped", False) and "exp_boost" in item["effects"]:
                    # Apply experience boost from accessory
                    exp_boost = item["effects"]["exp_boost"]
                    exp_gain = int(exp_gain * exp_boost)
                    accessory_boost_applied = True
                    accessory_name = item["name"]
                    logger.info(
                        f"Player {player.get('name', 'Unknown')} gained {exp_gain} exp (boosted from {original_exp}) due to equipped accessory {item['name']}")

            # Update player data using the new ExperienceCalculator
            new_exp = player.get("exp", 0) + exp_gain
            new_level = ExperienceCalculator.calculate_level(new_exp)
            level_up = new_level > player.get("level", 1)

            # Prepare update data
            update_data = {
                "exp": new_exp,
                attribute_gain: player.get(attribute_gain, 5) + 1,  # Increase the chosen attribute
                "tusd": player.get("tusd", 0) + 10  # Add TUSD reward for training
            }

            if level_up:
                update_data["level"] = new_level
                # Full HP recovery on level up
                update_data["hp"] = player.get("max_hp", 100)
                # Bonus TUSD for level up
                update_data["tusd"] = player.get("tusd", 0) + (
                            new_level * 50) + 10  # Add base TUSD reward plus level up bonus

            # Apply HP loss for training (5-15% of max HP)
            if "hp" in player and "max_hp" in player:
                hp_loss = random.randint(5, 15)
                hp_loss_percentage = Decimal(hp_loss) / Decimal(100)
                hp_loss_amount = int(player["max_hp"] * hp_loss_percentage)
                current_hp = player.get("hp", player["max_hp"])
                update_data["hp"] = max(1, current_hp - hp_loss_amount)

            # Update player in database
            success = await db_provider.update_player(ctx.author.id, **update_data)

            if success:
                # Set cooldown
                await self._set_cooldown(ctx.author.id, "treinar")

                # Create embed for training result
                embed = create_basic_embed(
                    title="Treinamento Concluído!",
                    description=outcome,
                    color=0x00FF00
                )

                # Add experience gain
                if accessory_boost_applied:
                    embed.add_field(
                        name="Experiência Ganha",
                        value=f"+{exp_gain} EXP (Bônus de {accessory_name}: +{exp_gain - original_exp} EXP)",
                        inline=True
                    )
                else:
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
        except Exception as e:
            logger.error(f"Error in train command: {e}", exc_info=True)
            await ctx.send("Ocorreu um erro durante o treinamento. Por favor, tente novamente mais tarde.")

    @commands.command(name="explorar")
    async def explore(self, ctx):
        """Explorar a academia em busca de eventos aleatórios."""
        try:
            # Check if player exists
            player = await db_provider.get_player(ctx.author.id)
            if not player:
                await ctx.send(
                    f"{ctx.author.mention}, você ainda não está registrado na Academia Tokugawa. Use !ingressar para criar seu personagem.")
                return

            # LOG: Mostrar dados do player e inventário
            logger.info(f"[EXPLORAR] Player lido: {player}")

            # Garantir que o inventário é um dicionário
            inventory = player.get('inventory', {})
            if isinstance(inventory, str):
                try:
                    inventory = json.loads(inventory)
                except Exception:
                    inventory = {}
            if not isinstance(inventory, dict):
                inventory = {}
            player['inventory'] = inventory

            # Check cooldown
            cooldown = await self._check_cooldown(ctx.author.id, "explorar")
            if cooldown:
                await ctx.send(
                    f"{ctx.author.mention}, você precisa descansar antes de explorar novamente. Tempo restante: {cooldown}")
                return

            # Create a random event using the enhanced RandomEvent class
            random_event = RandomEvent.create_random_event()

            # Trigger the event for the player
            event_result = random_event.trigger(player)

            # Process event effects
            update_data = {}

            # Experience change
            if "exp_change" in event_result:
                update_data["exp"] = player.get("exp", 0) + event_result["exp_change"]

            # TUSD change
            if "tusd_change" in event_result:
                update_data["tusd"] = max(0, player.get("tusd", 0) + event_result[
                    "tusd_change"])  # Ensure TUSD doesn't go below 0

            # Attribute changes
            if "attribute_changes" in event_result:
                for attr, change in event_result["attribute_changes"].items():
                    current_value = player.get(attr, 5)  # Default to 5 if not found
                    update_data[attr] = max(1, min(10, current_value + change))  # Keep between 1 and 10

            # Handle item rewards
            if "item_reward" in event_result:
                logger.info(f"Player {player.get('name', 'Unknown')} received item: {event_result['item_reward']}")
                # Add item to inventory
                item_id = f"item_{datetime.now().timestamp()}"
                inventory[item_id] = event_result['item_reward']
                update_data['inventory'] = json.dumps(inventory)

            # Update player in database
            success = await db_provider.update_player(ctx.author.id, **update_data)

            if success:
                # Set cooldown
                await self._set_cooldown(ctx.author.id, "explorar")

                # Create embed for event
                embed = create_event_embed(event_result)

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
        except Exception as e:
            logger.error(f"Error in explore command: {e}", exc_info=True)
            await ctx.send("Ocorreu um erro durante a exploração. Por favor, tente novamente mais tarde.")

    @commands.command(name="duelar")
    async def duel(self, ctx, opponent: discord.Member = None, duel_type: str = "physical"):
        """Desafiar outro jogador para um duelo."""
        # Check if opponent is specified
        if not opponent:
            await ctx.send(
                f"{ctx.author.mention}, você precisa mencionar um oponente para duelar. Exemplo: !duelar @usuário")
            return

        # Check if player is trying to duel themselves
        if opponent.id == ctx.author.id:
            await ctx.send(f"{ctx.author.mention}, você não pode duelar consigo mesmo!")
            return

        # Check if player exists
        challenger = await db_provider.get_player(ctx.author.id)
        if not challenger:
            await ctx.send(
                f"{ctx.author.mention}, você ainda não está registrado na Academia Tokugawa. Use !ingressar para criar seu personagem.")
            return

        # Check if opponent exists
        opponent_player = await db_provider.get_player(opponent.id)
        if not opponent_player:
            await ctx.send(f"{opponent.mention} não está registrado na Academia Tokugawa.")
            return

        # Check cooldown
        cooldown = await self._check_cooldown(ctx.author.id, "duelar")
        if cooldown:
            await ctx.send(
                f"{ctx.author.mention}, você precisa descansar antes de duelar novamente. Tempo restante: {cooldown}")
            return

        # Check if player is already in a duel
        if ctx.author.id in self.active_duels or opponent.id in self.active_duels.values():
            await ctx.send(f"{ctx.author.mention}, você ou seu oponente já está em um duelo!")
            return

        # Validate duel type
        valid_types = ["physical", "mental", "strategic", "social", "elemental"]
        if duel_type.lower() not in valid_types:
            duel_type = "physical"  # Default to physical
        else:
            duel_type = duel_type.lower()

        # Create duel challenge embed
        duel_names = {
            "physical": "Físico",
            "mental": "Mental",
            "strategic": "Estratégico",
            "social": "Social",
            "elemental": "Elemental"
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
            return m.author.id == opponent.id and m.channel == ctx.channel and m.content.lower() in ["sim", "não",
                                                                                                     "nao", "yes", "no"]

        try:
            # Wait for opponent's response
            response = await self.bot.wait_for('message', check=check, timeout=60.0)

            # Process response
            if response.content.lower() in ["sim", "yes"]:
                # Calculate duel outcome using the new DuelCalculator
                calculator = DuelCalculator()
                duel_result = calculator.calculate_outcome(challenger, opponent_player, duel_type)

                # Generate narration using the new DuelNarrator
                narration = DuelNarrator.generate_narration(duel_result)
                duel_result["narration"] = narration

                # Update winner and loser
                winner_id = duel_result["winner"]["user_id"]
                loser_id = duel_result["loser"]["user_id"]

                # Update winner
                winner_update = {
                    "exp": duel_result["winner"]["exp"] + duel_result["exp_reward"],
                    "tusd": duel_result["winner"]["tusd"] + duel_result["tusd_reward"]
                }

                # Check for level up using the new ExperienceCalculator
                new_level = ExperienceCalculator.calculate_level(winner_update["exp"])
                if new_level > duel_result["winner"]["level"]:
                    winner_update["level"] = new_level
                    # Full HP recovery on level up
                    winner_update["hp"] = player["max_hp"]
                    # Add level up bonus
                    winner_update["tusd"] += new_level * 50

                # Check for bonus rewards
                if "bonus_rewards" in duel_result and duel_result["bonus_rewards"] and "item" in duel_result[
                    "bonus_rewards"]:
                    # Get winner's inventory
                    winner_player = await db_provider.get_player(winner_id)
                    if winner_player and "inventory" in winner_player:
                        inventory = winner_player["inventory"]

                        # Get bonus item details
                        bonus_item = duel_result["bonus_rewards"]
                        item_id = bonus_item["item"]

                        # Check if item already exists in inventory
                        if str(item_id) in inventory:
                            # Increment quantity
                            inventory[str(item_id)]["quantity"] += 1
                        else:
                            # Add new item to inventory
                            inventory_item = {
                                "id": item_id,
                                "name": bonus_item["item_name"],
                                "description": bonus_item["item_description"],
                                "quantity": 1,
                                "type": "consumable",
                                "rarity": "uncommon",
                                "category": "duel_reward"
                            }
                            inventory[str(item_id)] = inventory_item

                        # Add inventory to winner update
                        winner_update["inventory"] = json.dumps(inventory)

                # Update loser (half exp, no TUSD)
                loser_update = {
                    "exp": duel_result["loser"]["exp"] + (duel_result["exp_reward"] // 2)
                }

                # Check for level up using the new ExperienceCalculator
                new_level = ExperienceCalculator.calculate_level(loser_update["exp"])
                if new_level > duel_result["loser"]["level"]:
                    loser_update["level"] = new_level

                # Update players in database
                winner_success = await db_provider.update_player(winner_id, **winner_update)
                loser_success = await db_provider.update_player(loser_id, **loser_update)

                if winner_success and loser_success:
                    # Set cooldown for challenger
                    await self._set_cooldown(ctx.author.id, "duelar")

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

    async def clear_expired_cooldowns(self):
        """Clear all expired cooldowns from the database."""
        try:
            cleared = await db_provider.clear_expired_cooldowns()
            if cleared > 0:
                logger.info(f"Cleared {cleared} expired cooldowns")
        except Exception as e:
            logger.error(f"Error clearing cooldowns: {e}")


async def setup(bot):
    """Add the cog to the bot."""
    from utils.command_registrar import CommandRegistrar

    # Create and add the cog
    cog = Activities(bot)
    await bot.add_cog(cog)
    logger.info("Activities cog loaded")

    # Register commands using the CommandRegistrar
    await CommandRegistrar.register_commands(bot, cog)
