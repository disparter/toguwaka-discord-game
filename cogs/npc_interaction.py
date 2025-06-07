import discord
from discord.ext import commands
from discord import app_commands
import logging
import os
from typing import Dict, List, Any, Optional, Union

from utils.database import get_player, update_player
from utils.embeds import create_basic_embed
from story_mode.story_mode import StoryMode

logger = logging.getLogger('tokugawa_bot')

class NPCInteractionCog(commands.Cog):
    """
    A cog that handles interactions with NPCs in the game.
    """
    def __init__(self, bot):
        self.bot = bot
        self.story_mode = StoryMode()
        logger.info("NPCInteractionCog initialized")

    def cog_load(self):
        """Called when the cog is loaded."""
        logger.info("NPCInteractionCog loaded")

    @app_commands.command(name="falar", description="Falar com um personagem do jogo")
    @app_commands.describe(
        personagem="Nome do personagem com quem deseja falar",
        assunto="Assunto sobre o qual deseja falar (opcional)"
    )
    async def slash_talk_to_npc(self, interaction: discord.Interaction, personagem: str, assunto: str = None):
        """
        Slash command to talk to an NPC.
        """
        try:
            await interaction.response.defer(ephemeral=True)
        except discord.errors.NotFound:
            logger.error("A interação expirou antes que pudesse ser processada.")
            return

        user_id = interaction.user.id
        player_data = get_player(user_id)

        if not player_data:
            await interaction.followup.send("Você precisa criar um personagem primeiro! Use /registrar", ephemeral=True)
            return

        # Get the NPC
        npc = self.story_mode.npc_manager.get_npc_by_name(personagem)

        if not npc:
            await interaction.followup.send(f"Personagem '{personagem}' não encontrado.", ephemeral=True)
            return

        # Get the dialogue based on the subject
        dialogue_id = assunto if assunto else "greeting"
        dialogue = npc.get_dialogue(dialogue_id, player_data)

        # Create embed for the dialogue
        embed = create_basic_embed(
            title=f"{npc.get_name()}",
            description=dialogue.get("text", "..."),
            color=discord.Color.blue()
        )

        # Check if this is the director and if we need to show the welcome.gif
        if npc.get_name().lower() in ["diretor", "diretor sombrio"]:
            # Check if the player has already seen the welcome.gif
            story_progress = player_data.get("story_progress", {})
            seen_gifs = story_progress.get("seen_gifs", {})

            if "welcome" not in seen_gifs:
                # Player hasn't seen the welcome.gif yet, show it
                gif_path = "assets/gifs/welcome.gif"

                # Check if the gif exists
                if os.path.exists(gif_path):
                    # Send the gif
                    await interaction.followup.send(file=discord.File(gif_path), ephemeral=False)

                    # Record that the player has seen the gif
                    if "seen_gifs" not in story_progress:
                        story_progress["seen_gifs"] = {}

                    story_progress["seen_gifs"]["welcome"] = True
                    player_data["story_progress"] = story_progress

                    # Add the gif to the player's image registry
                    if "image_registry" not in story_progress:
                        story_progress["image_registry"] = {}

                    story_progress["image_registry"]["welcome.gif"] = {
                        "path": gif_path,
                        "description": "Mensagem de boas-vindas do Diretor",
                        "seen_at": discord.utils.utcnow().isoformat()
                    }

                    player_data["story_progress"] = story_progress

                    # Update player data in database
                    update_player(user_id, story_progress=player_data["story_progress"])
                else:
                    logger.error(f"Welcome gif not found at {gif_path}")

        # Send the dialogue
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="registros", description="Ver imagens registradas durante o jogo")
    @app_commands.describe(
        id="ID da imagem que deseja ver (opcional)"
    )
    async def slash_view_registry(self, interaction: discord.Interaction, id: str = None):
        """
        Slash command to view registered images.
        """
        try:
            await interaction.response.defer(ephemeral=True)
        except discord.errors.NotFound:
            logger.error("A interação expirou antes que pudesse ser processada.")
            return

        user_id = interaction.user.id
        player_data = get_player(user_id)

        if not player_data:
            await interaction.followup.send("Você precisa criar um personagem primeiro! Use /registrar", ephemeral=True)
            return

        story_progress = player_data.get("story_progress", {})
        image_registry = story_progress.get("image_registry", {})

        if not image_registry:
            await interaction.followup.send("Você ainda não tem imagens registradas.", ephemeral=True)
            return

        # Always show the list of available images first
        embed = create_basic_embed(
            title="Seus Registros",
            description="Imagens que você desbloqueou durante o jogo.",
            color=discord.Color.blue()
        )

        for image_id, image_data in image_registry.items():
            embed.add_field(
                name=image_id,
                value=image_data.get("description", "Sem descrição disponível."),
                inline=False
            )

        # If an ID is provided, show that specific image after showing the list
        if id and id in image_registry:
            embed.set_footer(text=f"Mostrando registro: {id}")
            await interaction.followup.send(embed=embed, ephemeral=True)

            image_data = image_registry[id]
            image_path = image_data.get("path")

            if os.path.exists(image_path):
                detail_embed = create_basic_embed(
                    title=f"Registro: {id}",
                    description=image_data.get("description", "Sem descrição disponível."),
                    color=discord.Color.blue()
                )

                await interaction.followup.send(embed=detail_embed, file=discord.File(image_path), ephemeral=True)
            else:
                await interaction.followup.send(f"Imagem não encontrada para o registro '{id}'.", ephemeral=True)
        else:
            embed.set_footer(text="Use /registros [id] para ver uma imagem específica.")
            await interaction.followup.send(embed=embed, ephemeral=True)

async def setup(bot):
    """
    Setup function for the cog.
    """
    from utils.command_registrar import CommandRegistrar

    # Create and add the cog
    cog = NPCInteractionCog(bot)
    await bot.add_cog(cog)
    logger.info("NPCInteractionCog setup complete")

    # Register commands using the CommandRegistrar
    await CommandRegistrar.register_commands(bot, cog)
