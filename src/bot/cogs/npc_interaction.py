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

        # Initialize story progress if needed
        if "story_progress" not in player_data:
            player_data["story_progress"] = {}

        # Initialize NPC interaction history if needed
        if "npc_interactions" not in player_data["story_progress"]:
            player_data["story_progress"]["npc_interactions"] = {}

        # Get or initialize interaction history with this NPC
        npc_name = npc.get_name()
        if npc_name not in player_data["story_progress"]["npc_interactions"]:
            player_data["story_progress"]["npc_interactions"][npc_name] = {
                "total_interactions": 0,
                "last_interaction": None,
                "topics_discussed": {},
                "repeated_greetings": 0
            }

        npc_interactions = player_data["story_progress"]["npc_interactions"][npc_name]

        # Get the dialogue based on the subject
        dialogue_id = assunto if assunto else "greeting"

        # Check for repetitive interactions
        if dialogue_id == "greeting":
            npc_interactions["repeated_greetings"] += 1

            # If player has greeted the NPC too many times without discussing other topics,
            # the NPC will suggest something more meaningful
            if npc_interactions["repeated_greetings"] > 3 and len(npc_interactions["topics_discussed"]) < 2:
                # Override the dialogue to suggest more meaningful interaction
                dialogue = {
                    "text": f"Já nos cumprimentamos várias vezes. Que tal conversarmos sobre algo mais específico? "
                            f"Você pode me perguntar sobre '{', '.join(list(npc.dialogues.keys())[:3])}'."
                }

                # Small affinity penalty for repetitive greetings
                result = self.story_mode.update_affinity(player_data, npc_name, -1)
                player_data = result["player_data"]

                embed = create_basic_embed(
                    title=f"{npc.get_name()}",
                    description=dialogue.get("text", "..."),
                    color=discord.Color.gold()  # Different color to highlight this is a special response
                )

                # Update interaction history
                npc_interactions["total_interactions"] += 1
                npc_interactions["last_interaction"] = dialogue_id
                player_data["story_progress"]["npc_interactions"][npc_name] = npc_interactions

                # Update player data in database
                update_player(user_id, story_progress=player_data["story_progress"])

                await interaction.followup.send(embed=embed, ephemeral=True)
                return

        # Track topic discussion
        if dialogue_id != "greeting":
            if dialogue_id not in npc_interactions["topics_discussed"]:
                npc_interactions["topics_discussed"][dialogue_id] = 0

                # Small affinity bonus for discussing new topics
                result = self.story_mode.update_affinity(player_data, npc_name, 2)
                player_data = result["player_data"]

            npc_interactions["topics_discussed"][dialogue_id] += 1

            # If a topic has been discussed too many times, the NPC will provide new insights
            if npc_interactions["topics_discussed"][dialogue_id] > 3:
                # Get current affinity level to determine if the NPC shares more
                affinity_level = npc.get_affinity_level(player_data)

                if affinity_level in ["close", "trusted"]:
                    # For close/trusted relationships, provide deeper insights on repeated topics
                    dialogue = {
                        "text": f"Já conversamos bastante sobre isso. Deixe-me compartilhar algo mais profundo... "
                                f"Na verdade, há aspectos sobre {dialogue_id} que poucos conhecem. "
                                f"Como somos próximos, posso te contar que..."
                    }
                else:
                    # For other relationships, suggest new topics
                    other_topics = [topic for topic in npc.dialogues.keys() 
                                   if topic != dialogue_id and topic != "greeting" 
                                   and topic not in npc_interactions["topics_discussed"]]

                    if other_topics:
                        dialogue = {
                            "text": f"Já falamos bastante sobre {dialogue_id}. "
                                    f"Talvez queira me perguntar sobre '{', '.join(other_topics[:2])}'?"
                        }
                    else:
                        # Get the standard dialogue if no other topics available
                        dialogue = npc.get_dialogue(dialogue_id, player_data)
            else:
                # Get the standard dialogue for this topic
                dialogue = npc.get_dialogue(dialogue_id, player_data)
        else:
            # Get the standard greeting dialogue
            dialogue = npc.get_dialogue(dialogue_id, player_data)

        # Update interaction history
        npc_interactions["total_interactions"] += 1
        npc_interactions["last_interaction"] = dialogue_id
        player_data["story_progress"]["npc_interactions"][npc_name] = npc_interactions

        # Update player data in database
        update_player(user_id, story_progress=player_data["story_progress"])

        # Create embed for the dialogue
        # Get current affinity level for the footer
        affinity_level = npc.get_affinity_level(player_data)
        affinity_value = npc.get_affinity(player_data)

        # Determine color based on affinity level
        color = discord.Color.blue()
        if affinity_level == "trusted":
            color = discord.Color.purple()
        elif affinity_level == "close":
            color = discord.Color.green()
        elif affinity_level == "friendly":
            color = discord.Color.teal()
        elif affinity_level == "unfriendly":
            color = discord.Color.orange()
        elif affinity_level == "hostile":
            color = discord.Color.red()

        embed = create_basic_embed(
            title=f"{npc.get_name()}",
            description=dialogue.get("text", "..."),
            color=color
        )

        # Add footer with relationship status
        embed.set_footer(text=f"Relacionamento: {affinity_level.capitalize()} (Afinidade: {affinity_value})")

        # Check if this is the director and if we need to show the welcome image
        if npc_name == "Diretor":
            # Check if the player has already seen the welcome image
            story_progress = player_data.get("story_progress", {})
            seen_images = story_progress.get("seen_images", {})
            
            if "welcome" not in seen_images:
                # Player hasn't seen the welcome image yet, show it
                image_path = "assets/images/welcome.png"
                
                # Check if the image exists
                if os.path.exists(image_path):
                    # Send the image
                    await interaction.followup.send(file=discord.File(image_path), ephemeral=False)
                    
                    # Record that the player has seen the image
                    if "seen_images" not in story_progress:
                        story_progress["seen_images"] = {}
                    
                    story_progress["seen_images"]["welcome"] = True
                    
                    # Add the image to the player's image registry
                    if "image_registry" not in story_progress:
                        story_progress["image_registry"] = {}
                    
                    story_progress["image_registry"]["welcome.png"] = {
                        "path": image_path,
                        "description": "Imagem de boas-vindas do Diretor",
                        "seen_at": discord.utils.utcnow().isoformat()
                    }
                    
                    # Update player data
                    update_player(user_id, story_progress=story_progress)
                else:
                    logger.error(f"Welcome image not found at {image_path}")

        # Check if this is Professor Quantum and if we need to show the professor_quantum_intro image
        elif npc_name == "Professor Quantum":
            # Check if the player has already seen the professor_quantum_intro image
            story_progress = player_data.get("story_progress", {})
            seen_images = story_progress.get("seen_images", {})
            
            if "professor_quantum_intro" not in seen_images:
                # Player hasn't seen the professor_quantum_intro image yet, show it
                image_path = "assets/images/professor_quantum_intro.png"
                
                # Check if the image exists
                if os.path.exists(image_path):
                    # Send the image
                    await interaction.followup.send(file=discord.File(image_path), ephemeral=False)
                    
                    # Record that the player has seen the image
                    if "seen_images" not in story_progress:
                        story_progress["seen_images"] = {}
                    
                    story_progress["seen_images"]["professor_quantum_intro"] = True
                    
                    # Add the image to the player's image registry
                    if "image_registry" not in story_progress:
                        story_progress["image_registry"] = {}
                    
                    story_progress["image_registry"]["professor_quantum_intro.png"] = {
                        "path": image_path,
                        "description": "Introdução do Professor Quantum",
                        "seen_at": discord.utils.utcnow().isoformat()
                    }
                    
                    # Update player data
                    update_player(user_id, story_progress=story_progress)
                else:
                    logger.error(f"Professor Quantum intro image not found at {image_path}")

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
