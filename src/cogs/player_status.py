import discord
import json
import logging
from typing import Any
from discord import app_commands
from discord.ext import commands

from utils.embeds import create_player_embed, create_inventory_embed, create_leaderboard_embed
from utils.persistence.db_provider import db_provider

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
            player = await db_provider.get_player(target.id)
            if not player:
                if target == interaction.user:
                    await interaction.response.send_message(
                        f"{interaction.user.mention}, você ainda não está registrado na Academia Tokugawa. Use !ingressar para criar seu personagem.")
                else:
                    await interaction.response.send_message(
                        f"{target.display_name} não está registrado na Academia Tokugawa.")
                return

            # Get club data
            club = None
            if player['club_id']:
                club = await db_provider.get_club(str(player['club_id']))

            # Create and send player embed
            embed = create_player_embed(player, club)
            await interaction.response.send_message(embed=embed, ephemeral=True)
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
            player = await db_provider.get_player(interaction.user.id)
            if not player:
                await interaction.response.send_message(
                    f"{interaction.user.mention}, você ainda não está registrado na Academia Tokugawa. Use !ingressar para criar seu personagem.")
                return

            # Buscar inventário na tabela Inventario
            inventory = await db_provider.get_player_inventory(interaction.user.id)
            player['inventory'] = inventory

            # Create inventory embed
            embed = create_inventory_embed(player)

            # Create view with buttons for consumable items
            view = discord.ui.View(timeout=60)

            # Check if player has consumable items
            has_consumables = False
            for item_id, item in inventory.items():
                if item.get('type') == 'consumable':
                    has_consumables = True
                    # Create button for each consumable item
                    button = discord.ui.Button(
                        label=f"Usar {item.get('name', item_id)}",
                        custom_id=f"use_{item_id}",
                        style=discord.ButtonStyle.primary
                    )

                    # Define callback for button
                    async def button_callback(button_interaction, item_id=item_id):
                        if button_interaction.user.id != interaction.user.id:
                            await button_interaction.response.send_message("Este não é o seu inventário!",
                                                                           ephemeral=True)
                            return

                        # Call the use_item command from economy cog
                        economy_cog = self.bot.get_cog('Economy')
                        if economy_cog:
                            await economy_cog.slash_use_item(button_interaction, int(item_id))
                        else:
                            await button_interaction.response.send_message(
                                "Erro ao usar o item. Tente usar o comando `/economia usar` diretamente.",
                                ephemeral=True)

                    button.callback = button_callback
                    view.add_item(button)

            # Add a note about using items if there are consumables
            if has_consumables:
                embed.add_field(
                    name="Usar Itens",
                    value="Clique nos botões abaixo para usar itens consumíveis ou use o comando `/economia usar <id>`.",
                    inline=False
                )

            # Send the embed with or without buttons
            if has_consumables:
                await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            else:
                await interaction.response.send_message(embed=embed, ephemeral=True)

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
            top_players = await db_provider.get_top_players(limit)

            # Create and send leaderboard embed
            embed = await create_leaderboard_embed(top_players)
            await interaction.response.send_message(embed=embed, ephemeral=True)
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
        player = await db_provider.get_player(target.id)
        if not player:
            if target == ctx.author:
                await ctx.send(
                    f"{ctx.author.mention}, você ainda não está registrado na Academia Tokugawa. Use !ingressar para criar seu personagem.")
            else:
                await ctx.send(f"{target.display_name} não está registrado na Academia Tokugawa.")
            return

        # LOG: Mostrar dados do player e inventário
        logger.info(f"[STATUS] Player lido: {player}")
        logger.info(f"[STATUS] Inventário lido: {player.get('inventory')}")

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

        # Get club data
        club = None
        if player['club_id']:
            club = await db_provider.get_club(str(player['club_id']))

        # Create and send player embed
        embed = create_player_embed(player, club)
        await ctx.send(embed=embed, ephemeral=True)

    @commands.command(name="inventario")
    async def inventory(self, ctx):
        """Exibe o inventário do jogador."""
        # Get player data
        player = await db_provider.get_player(ctx.author.id)
        if not player:
            await ctx.send(
                f"{ctx.author.mention}, você ainda não está registrado na Academia Tokugawa. Use !ingressar para criar seu personagem.")
            return

        # Buscar inventário na tabela Inventario
        inventory = await db_provider.get_player_inventory(ctx.author.id)
        player['inventory'] = inventory

        # Create inventory embed
        embed = create_inventory_embed(player)

        # Check if player has consumable items
        has_consumables = False
        for item_id, item in inventory.items():
            if item.get('type') == 'consumable':
                has_consumables = True
                break

        # Add a note about using items if there are consumables
        if has_consumables:
            embed.add_field(
                name="Usar Itens",
                value="Use o comando `!usar <id>` para usar itens consumíveis.",
                inline=False
            )

        # Send the embed
        await ctx.send(embed=embed, ephemeral=True)

    @commands.command(name="top")
    async def leaderboard(self, ctx, limit: int = 10):
        """Exibe o ranking dos melhores alunos da Academia Tokugawa."""
        # Limit the number of players to show
        if limit < 1:
            limit = 1
        elif limit > 25:
            limit = 25

        # Get top players
        top_players = await db_provider.get_top_players(limit)

        # Create and send leaderboard embed
        embed = await create_leaderboard_embed(top_players)
        await ctx.send(embed=embed, ephemeral=True)

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
