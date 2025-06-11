import discord
import logging
import os
from datetime import datetime
from discord import app_commands
from discord.ext import commands
from typing import Dict, Any, Optional
import json

from story_mode.club_system import ClubSystem
from story_mode.consequences import DynamicConsequencesSystem
from story_mode.relationship_system import RelationshipSystem
from story_mode.story_mode import StoryMode
from story_mode.image_manager import ImageManager
from story_mode.progress import DefaultStoryProgressManager
from utils.embeds import create_basic_embed, create_event_embed
from utils.json_utils import dumps as json_dumps
from utils.persistence import db_provider
from utils.persistence.dynamodb_story import get_story_progress, update_story_progress
from utils.config import STORY_MODE_DIR

logger = logging.getLogger('tokugawa_bot')


class StoryModeCog(commands.Cog):
    """
    A cog that implements the story mode using the new SOLID architecture.
    This cog serves as an adapter between the Discord bot and the StoryMode system.
    """

    def __init__(self, bot):
        self.bot = bot
        self.story_mode = StoryMode(STORY_MODE_DIR)
        self.progress_manager = DefaultStoryProgressManager()
        self.active_sessions = {}  # user_id -> session_data
        self.club_system = ClubSystem()
        self.consequences_system = DynamicConsequencesSystem()
        self.relationship_system = RelationshipSystem()
        self.image_manager = ImageManager()

        logger.info("StoryModeCog initialized")

    def cog_load(self):
        """Called when the cog is loaded."""
        logger.info("StoryModeCog loaded")

    async def _load_chapter(self, chapter_id: str) -> Optional[Dict[str, Any]]:
        """
        Load chapter data from JSON file.
        """
        try:
            chapter_file = os.path.join(STORY_MODE_DIR, "chapters", f"{chapter_id}.json")
            if not os.path.exists(chapter_file):
                logger.error(f"Chapter file not found: {chapter_file}")
                return None
            
            with open(chapter_file, 'r', encoding='utf-8') as f:
                chapter_data = json.load(f)
            
            return chapter_data
        except Exception as e:
            logger.error(f"Error loading chapter {chapter_id}: {e}")
            return None

    @commands.command(name="start_story")
    async def start_story(self, ctx):
        """
        Start the story mode.
        """
        try:
            # Get player data
            player_data = {"user_id": str(ctx.author.id)}
            
            # Initialize story progress
            player_data = await self.progress_manager.initialize_story_progress(player_data)
            
            # Get current chapter
            current_chapter = await self.progress_manager.get_current_chapter(player_data)
            if not current_chapter:
                # Start with first chapter
                current_chapter = "chapter_1"
                player_data = await self.progress_manager.set_current_chapter(player_data, current_chapter)
            
            # Load chapter data
            chapter_data = await self._load_chapter(current_chapter)
            if not chapter_data:
                await ctx.send("Error: Could not load chapter data.")
                return
            
            # Get first scene
            first_scene = chapter_data.get("scenes", [{}])[0]
            scene_text = first_scene.get("text", "No text available.")
            choices = first_scene.get("choices", [])
            
            # Send scene text
            await ctx.send(scene_text)
            
            # Send choices if any
            if choices:
                choice_text = "Your choices:\n"
                for i, choice in enumerate(choices, 1):
                    choice_text += f"{i}. {choice['text']}\n"
                await ctx.send(choice_text)
            
        except Exception as e:
            logger.error(f"Error in start_story: {e}")
            await ctx.send("An error occurred while starting the story.")
    
    @commands.command(name="continue_story")
    async def continue_story(self, ctx):
        """
        Continue the story from where you left off.
        """
        try:
            # Get player data
            player_data = {"user_id": str(ctx.author.id)}
            
            # Get current chapter
            current_chapter = await self.progress_manager.get_current_chapter(player_data)
            if not current_chapter:
                await ctx.send("You haven't started the story yet. Use !start_story to begin.")
                return
            
            # Load chapter data
            chapter_data = await self._load_chapter(current_chapter)
            if not chapter_data:
                await ctx.send("Error: Could not load chapter data.")
                return
            
            # Get current scene
            current_scene = chapter_data.get("scenes", [{}])[0]  # For now, just get first scene
            scene_text = current_scene.get("text", "No text available.")
            choices = current_scene.get("choices", [])
            
            # Send scene text
            await ctx.send(scene_text)
            
            # Send choices if any
            if choices:
                choice_text = "Your choices:\n"
                for i, choice in enumerate(choices, 1):
                    choice_text += f"{i}. {choice['text']}\n"
                await ctx.send(choice_text)
            
        except Exception as e:
            logger.error(f"Error in continue_story: {e}")
            await ctx.send("An error occurred while continuing the story.")
    
    @commands.command(name="story_progress")
    async def story_progress(self, ctx):
        """
        Show your story progress.
        """
        try:
            # Get player data
            player_data = {"user_id": str(ctx.author.id)}
            
            # Get story progress
            progress = await get_story_progress(player_data["user_id"])
            if not progress:
                await ctx.send("You haven't started the story yet. Use !start_story to begin.")
                return
            
            # Format progress message
            message = "Your Story Progress:\n"
            message += f"Current Chapter: {progress.get('current_chapter', 'None')}\n"
            message += f"Completed Chapters: {', '.join(progress.get('completed_chapters', []))}\n"
            message += f"Hierarchy Tier: {progress.get('hierarchy_tier', 1)}\n"
            message += f"Hierarchy Points: {progress.get('hierarchy_points', 0)}"
            
            await ctx.send(message)
            
        except Exception as e:
            logger.error(f"Error in story_progress: {e}")
            await ctx.send("An error occurred while retrieving your story progress.")

    @app_commands.command(name="historia", description="Inicia ou continua o modo história")
    async def slash_start_story(self, interaction: discord.Interaction):
        """
        Slash command to start or continue the story mode.
        """
        try:
            await interaction.response.defer(ephemeral=True)
        except discord.errors.NotFound:
            logger.warning(f"Interaction expired for user {interaction.user.id} when using /historia")
            return  # Let the command tree error handler handle this

        user_id = interaction.user.id
        player_data = await db_provider.get_player(user_id)

        if not player_data:
            await interaction.followup.send("Você precisa criar um personagem primeiro! Use /registrar", ephemeral=True)
            return

        # Ensure player_data is a dictionary
        if isinstance(player_data, str):
            try:
                player_data = json.loads(player_data)
            except json.JSONDecodeError:
                logger.error(f"Invalid player data format for user {user_id}: {player_data}")
                await interaction.followup.send("Erro interno: dados do jogador inválidos. Por favor, contate um administrador.", ephemeral=True)
                return

        # Start or continue the story
        result = await self.story_mode.start_story(player_data)
        logger.info(
            f"start_story result: user_id={result.get('user_id')}, "
            f"current_chapter={result.get('story_progress', {}).get('current_chapter')}, "
            f"completed_chapters={result.get('story_progress', {}).get('completed_chapters')}"
        )
        logger.debug(f"Full start_story result: {json.dumps(result, default=str)[:1000]}")  # Truncate if needed
        logger.debug(f"start_story result type: {type(result)}")
        logger.debug(f"chapter_data type: {type(result.get('chapter_data'))}")
        logger.debug(f"chapter_data content: {result.get('chapter_data')}")

        if "error" in result:
            await interaction.followup.send(f"Erro ao iniciar o modo história: {result['error']}", ephemeral=True)
            return

        if "player_data" not in result or "chapter_data" not in result:
            await interaction.followup.send(
                "Erro interno: dados do modo história ausentes. Por favor, contate um administrador.", ephemeral=True)
            logger.error(f"start_story returned incomplete result: {result}")
            return

        # Update player data in database
        update_data = {"story_progress": json_dumps(result["player_data"]["story_progress"])}

        # Also update club_id if it's in the player data
        if "club_id" in result["player_data"]:
            update_data["club_id"] = result["player_data"]["club_id"]

        await db_provider.update_player(user_id, **update_data)

        # Store session data
        self.active_sessions[user_id] = {
            "channel_id": interaction.channel_id,
            "last_activity": datetime.now()
        }

        # Send chapter information
        chapter_data = result["chapter_data"]
        if isinstance(chapter_data, dict) and "chapter_data" in chapter_data:
            chapter_data = chapter_data["chapter_data"]

        # Handle StoryChapter object or dictionary
        if hasattr(chapter_data, 'get_title') and hasattr(chapter_data, 'get_description'):
            # It's a StoryChapter object
            title = chapter_data.get_title()
            description = chapter_data.get_description()
        else:
            # It's a dictionary
            title = chapter_data['title']
            description = chapter_data['description']

        embed = create_basic_embed(
            title=f"Capítulo: {title}",
            description=description,
            color=discord.Color.blue()
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

        # Send first dialogue or choices
        await self._send_dialogue_or_choices(interaction, chapter_data, player_data)

        # Check for available events
        if "available_events" in result and result["available_events"]:
            await self._notify_about_events(interaction.channel, user_id, result["available_events"])

    @app_commands.command(name="status_historia", description="Mostra o status atual do seu progresso no modo história")
    async def slash_story_status(self, interaction: discord.Interaction):
        """
        Slash command to show the current status of the player's story progress.
        """
        try:
            await interaction.response.defer(ephemeral=True)
        except discord.errors.NotFound:
            logger.warning(f"Interaction expired for user {interaction.user.id} when using /status_historia")
            return  # Let the command tree error handler handle this

        user_id = interaction.user.id
        player_data = await db_provider.get_player(user_id)

        if not player_data:
            await interaction.followup.send("Você precisa criar um personagem primeiro! Use /registrar", ephemeral=True)
            return

        # Get story status
        status = await self.story_mode.get_story_status(player_data)

        # Create embed
        embed = create_basic_embed(
            title="Status do Modo História",
            description=f"Status atual do seu progresso no modo história.",
            color=discord.Color.blue()
        )

        # Add current chapter
        if status["current_chapter"]:
            embed.add_field(
                name="Capítulo Atual",
                value=f"{status['current_chapter']['title']}\n{status['current_chapter']['description']}",
                inline=False
            )
        else:
            embed.add_field(
                name="Capítulo Atual",
                value="Nenhum capítulo em andamento.",
                inline=False
            )

        # Add hierarchy information
        hierarchy_tier = status["hierarchy"]["tier"]
        hierarchy_points = status["hierarchy"]["points"]
        embed.add_field(
            name="Hierarquia",
            value=f"Nível: {hierarchy_tier} ({self._get_hierarchy_name(hierarchy_tier)})\nPontos: {hierarchy_points}",
            inline=True
        )

        # Add completed chapters
        completed_chapters = len(status["completed_chapters"])
        completed_challenge_chapters = len(status["completed_challenge_chapters"])
        embed.add_field(
            name="Capítulos Completados",
            value=f"Capítulos Principais: {completed_chapters}\nCapítulos Desafio: {completed_challenge_chapters}",
            inline=True
        )

        # Add discovered secrets
        discovered_secrets = len(status["discovered_secrets"])
        embed.add_field(
            name="Segredos Descobertos",
            value=f"{discovered_secrets} segredos",
            inline=True
        )

        # Add special items
        if status["special_items"]:
            embed.add_field(
                name="Itens Especiais",
                value="\n".join(status["special_items"]),
                inline=False
            )

        # Add relationships
        if status["relationships"]:
            relationships_text = ""
            for rel in status["relationships"][:5]:  # Show top 5
                relationships_text += f"{rel['npc']}: {rel['affinity']} ({rel['level']})\n"

            embed.add_field(
                name="Relacionamentos",
                value=relationships_text,
                inline=False
            )

        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="relacionamento", description="Mostra ou altera seu relacionamento com um personagem")
    @app_commands.describe(
        personagem="Nome do personagem",
        afinidade="Quantidade de pontos de afinidade para adicionar (opcional)"
    )
    async def slash_relacionamento(self, interaction: discord.Interaction, personagem: str = None,
                                   afinidade: int = None):
        """
        Slash command to show or change the player's relationship with an NPC.
        """
        try:
            await interaction.response.defer(ephemeral=True)
        except discord.errors.NotFound:
            logger.warning(f"Interaction expired for user {interaction.user.id} when using /relacionamento")
            return  # Let the command tree error handler handle this

        user_id = interaction.user.id
        player_data = await db_provider.get_player(user_id)

        if not player_data:
            await interaction.followup.send("Você precisa criar um personagem primeiro! Use /registrar", ephemeral=True)
            return

        # If no character specified, show all relationships
        if not personagem:
            status = await self.story_mode.get_story_status(player_data)

            if not status["relationships"]:
                await interaction.followup.send("Você ainda não tem relacionamentos com personagens.", ephemeral=True)
                return

            embed = create_basic_embed(
                title="Seus Relacionamentos",
                description="Seu nível de afinidade com os personagens do jogo.",
                color=discord.Color.purple()
            )

            for rel in status["relationships"]:
                embed.add_field(
                    name=f"{rel['npc']} ({rel['level']})",
                    value=f"Afinidade: {rel['affinity']}",
                    inline=True
                )

            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        # If affinity specified, update relationship
        if afinidade is not None:
            # Only allow admins to change affinity
            if not await self._is_admin(interaction.user):
                await interaction.followup.send("Apenas administradores podem alterar afinidade diretamente.",
                                                ephemeral=True)
                return

            result = await self.story_mode.update_affinity(player_data, personagem, afinidade)

            if "error" in result:
                await interaction.followup.send(f"Erro ao atualizar afinidade: {result['error']}", ephemeral=True)
                return

            # Update player data in database
            update_data = {"story_progress": json_dumps(result["player_data"]["story_progress"])}

            # Also update club_id if it's in the player data
            if "club_id" in result["player_data"]:
                update_data["club_id"] = result["player_data"]["club_id"]

            await db_provider.update_player(user_id, **update_data)

            affinity_result = result["affinity_result"]

            embed = create_basic_embed(
                title=f"Afinidade Atualizada: {affinity_result['npc']}",
                description=f"Sua afinidade com {affinity_result['npc']} foi atualizada.",
                color=discord.Color.green()
            )

            embed.add_field(
                name="Nova Afinidade",
                value=f"{affinity_result['affinity']} ({affinity_result['level']})",
                inline=False
            )

            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        # If character specified but no affinity, show relationship with that character
        status = await self.story_mode.get_story_status(player_data)

        relationship = None
        for rel in status["relationships"]:
            if rel["npc"].lower() == personagem.lower():
                relationship = rel
                break

        if not relationship:
            await interaction.followup.send(f"Você ainda não tem um relacionamento com {personagem}.", ephemeral=True)
            return

        embed = create_basic_embed(
            title=f"Relacionamento com {relationship['npc']}",
            description=f"Seu nível de afinidade com {relationship['npc']}.",
            color=discord.Color.purple()
        )

        embed.add_field(
            name="Afinidade",
            value=f"{relationship['affinity']} ({relationship['level']})",
            inline=False
        )

        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="evento", description="Participa de um evento disponível")
    @app_commands.describe(
        evento_id="ID do evento para participar"
    )
    async def slash_participate_event(self, interaction: discord.Interaction, evento_id: str = None):
        """
        Slash command to participate in an available event.
        """
        try:
            await interaction.response.defer(ephemeral=True)
        except discord.errors.NotFound:
            logger.warning(f"Interaction expired for user {interaction.user.id} when using /evento")
            return  # Let the command tree error handler handle this

        user_id = interaction.user.id
        player_data = await db_provider.get_player(user_id)

        if not player_data:
            try:
                await interaction.followup.send("Você precisa criar um personagem primeiro! Use /registrar",
                                                ephemeral=True)
            except discord.errors.NotFound:
                logger.error("A interação expirou antes que a resposta pudesse ser enviada.")
            except Exception as e:
                logger.error(f"Erro ao enviar resposta: {e}")
            return

        # If no event ID specified, show available events
        if not evento_id:
            result = await self.story_mode.start_story(player_data)

            if "error" in result:
                try:
                    await interaction.followup.send(f"Erro ao verificar eventos disponíveis: {result['error']}",
                                                    ephemeral=True)
                except discord.errors.NotFound:
                    logger.error("A interação expirou antes que a resposta pudesse ser enviada.")
                except Exception as e:
                    logger.error(f"Erro ao enviar resposta: {e}")
                return

            if "available_events" not in result or not result["available_events"]:
                try:
                    await interaction.followup.send("Não há eventos disponíveis para você no momento.", ephemeral=True)
                except discord.errors.NotFound:
                    logger.error("A interação expirou antes que a resposta pudesse ser enviada.")
                except Exception as e:
                    logger.error(f"Erro ao enviar resposta: {e}")
                return

            embed = create_basic_embed(
                title="Eventos Disponíveis",
                description="Eventos que você pode participar agora.",
                color=discord.Color.gold()
            )

            for event in result["available_events"]:
                embed.add_field(
                    name=event["name"],
                    value=f"ID: {event['id']}\n{event['description']}",
                    inline=False
                )

            embed.set_footer(text="Use /evento [evento_id] para participar de um evento.")

            try:
                await interaction.followup.send(embed=embed, ephemeral=True)
            except discord.errors.NotFound:
                logger.error("A interação expirou antes que a resposta pudesse ser enviada.")
            except Exception as e:
                logger.error(f"Erro ao enviar resposta: {e}")
            return

        # Trigger the event
        result = await self.story_mode.trigger_event(player_data, evento_id)

        if "error" in result:
            try:
                await interaction.followup.send(f"Erro ao participar do evento: {result['error']}", ephemeral=True)
            except discord.errors.NotFound:
                logger.error("A interação expirou antes que a resposta pudesse ser enviada.")
            except Exception as e:
                logger.error(f"Erro ao enviar resposta: {e}")
            return

        # Update player data in database
        update_data = {"story_progress": json_dumps(result["player_data"]["story_progress"])}

        # Also update club_id if it's in the player data
        if "club_id" in result["player_data"]:
            update_data["club_id"] = result["player_data"]["club_id"]

        await db_provider.update_player(user_id, **update_data)

        event_result = result["event_result"]

        # Create embed for event result
        embed = create_event_embed({
            "title": f"Evento: {event_result['name']}",
            "description": event_result['description'],
            "type": "neutral",  # Considerar tipo real do evento aqui
            "effect": event_result["rewards"]  # Rewards equivale a "effect" nos dicionários
        })

        try:
            await interaction.followup.send(embed=embed, ephemeral=True)
        except discord.errors.NotFound:
            logger.error("A interação expirou antes que a resposta pudesse ser enviada.")
        except Exception as e:
            logger.error(f"Erro ao enviar resposta: {e}")

    async def _send_dialogue_or_choices(self, ctx_or_interaction, chapter_data, player_data):
        """Send current dialogue or choices to the channel."""
        try:
            # Handle both Context and Interaction objects
            is_interaction = isinstance(ctx_or_interaction, discord.Interaction)
            user_id = ctx_or_interaction.user.id if is_interaction else ctx_or_interaction.author.id
            send_message = ctx_or_interaction.followup.send if is_interaction else ctx_or_interaction.send
            
            # Get current dialogue index
            story_progress = player_data.get("story_progress", {})
            current_dialogue_index = story_progress.get("current_dialogue_index", 0)
            
            # Handle StoryChapter object
            if hasattr(chapter_data, 'get_available_choices'):
                # Get available choices from the StoryChapter object
                available_choices = chapter_data.get_available_choices(player_data)
                
                if available_choices:
                    # Create choice buttons
                    view = discord.ui.View()
                    for i, choice in enumerate(available_choices):
                        button = discord.ui.Button(
                            label=choice.get("text", f"Opção {i+1}"),
                            custom_id=f"choice_{i}",
                            style=discord.ButtonStyle.primary
                        )
                        button.callback = self._create_choice_callback(user_id, i)
                        view.add_item(button)
                    
                    await send_message("Escolha uma opção:", view=view)
                else:
                    # If no choices available, show continue button
                    view = discord.ui.View()
                    continue_button = discord.ui.Button(
                        label="Continuar",
                        custom_id="continue",
                        style=discord.ButtonStyle.primary
                    )
                    continue_button.callback = self._create_continue_callback(user_id)
                    view.add_item(continue_button)
                    await send_message("Pressione continuar para seguir:", view=view)
            else:
                # Handle dictionary format
                dialogues = chapter_data.get("dialogues", [])
                
                if current_dialogue_index < len(dialogues):
                    current_dialogue = dialogues[current_dialogue_index]
                    await send_message(current_dialogue.get("text", ""))
                    
                    story_progress["current_dialogue_index"] = current_dialogue_index + 1
                    await db_provider.update_player(user_id, {"story_progress": story_progress})
                    
                    if current_dialogue_index + 1 < len(dialogues):
                        await self._send_dialogue_or_choices(ctx_or_interaction, chapter_data, player_data)
                    else:
                        await self._show_choices(ctx_or_interaction, chapter_data, player_data)
                else:
                    await self._show_choices(ctx_or_interaction, chapter_data, player_data)
                    
        except Exception as e:
            logger.error(f"Error in _send_dialogue_or_choices: {str(e)}")
            await send_message("Ocorreu um erro ao processar o diálogo. Por favor, tente novamente.")

    def _create_choice_callback(self, user_id: int, choice_index: int):
        """
        Creates a callback function for a choice button.
        """

        async def choice_callback(interaction: discord.Interaction):
            # Check if the user who clicked is the same as the user who started the story
            if interaction.user.id != user_id:
                await interaction.response.send_message("Esta não é a sua história!", ephemeral=True)
                return

            try:
                await interaction.response.defer(ephemeral=True)
            except discord.errors.NotFound:
                logger.error("A interação expirou antes que pudesse ser processada.")
                return

            # Get player data
            player_data = await db_provider.get_player(user_id)

            if not player_data:
                await interaction.followup.send("Erro: Dados do jogador não encontrados.", ephemeral=True)
                return

            # Process the choice
            result = await self.story_mode.process_choice(player_data, choice_index)

            if "error" in result:
                await interaction.followup.send(f"Erro ao processar escolha: {result['error']}", ephemeral=True)
                return

            # Update player data in database
            update_data = {"story_progress": json_dumps(result["player_data"]["story_progress"])}

            # Also update club_id if it's in the player data
            if "club_id" in result["player_data"]:
                update_data["club_id"] = result["player_data"]["club_id"]

            await db_provider.update_player(user_id, **update_data)

            # Send next dialogue or choices
            await self._send_dialogue_or_choices(interaction.channel, result["chapter_data"], result["player_data"])

            # Check for available events
            if "available_events" in result and result["available_events"]:
                await self._notify_about_events(interaction.channel, user_id, result["available_events"])

            # Check if chapter is complete
            if "chapter_complete" in result and result["chapter_complete"]:
                if "story_complete" in result and result["story_complete"]:
                    embed = create_basic_embed(
                        title="História Concluída",
                        description="Parabéns! Você concluiu a história principal do jogo.",
                        color=discord.Color.gold()
                    )
                    await interaction.channel.send(embed=embed)
                elif "next_chapter_id" in result:
                    embed = create_basic_embed(
                        title="Capítulo Concluído",
                        description=f"Você concluiu este capítulo da história. O próximo capítulo está disponível.",
                        color=discord.Color.green()
                    )
                    await interaction.channel.send(embed=embed)

        return choice_callback

    def _create_continue_callback(self, user_id: int):
        """
        Creates a callback function for a continue button.
        """

        async def continue_callback(interaction: discord.Interaction):
            # Check if the user who clicked is the same as the user who started the story
            if interaction.user.id != user_id:
                await interaction.response.send_message("Esta não é a sua história!", ephemeral=True)
                return

            try:
                await interaction.response.defer(ephemeral=True)
            except discord.errors.NotFound:
                logger.error("A interação expirou antes que pudesse ser processada.")
                return

            # Get player data
            player_data = await db_provider.get_player(user_id)

            if not player_data:
                await interaction.followup.send("Erro: Dados do jogador não encontrados.", ephemeral=True)
                return

            # Process the choice (continue is equivalent to choice 0)
            result = await self.story_mode.process_choice(player_data, 0)

            if "error" in result:
                await interaction.followup.send(f"Erro ao continuar: {result['error']}", ephemeral=True)
                return

            # Update player data in database
            update_data = {"story_progress": json_dumps(result["player_data"]["story_progress"])}

            # Also update club_id if it's in the player data
            if "club_id" in result["player_data"]:
                update_data["club_id"] = result["player_data"]["club_id"]

            await db_provider.update_player(user_id, **update_data)

            # Send next dialogue or choices
            await self._send_dialogue_or_choices(interaction, result["chapter_data"], result["player_data"])

            # Check for available events
            if "available_events" in result and result["available_events"]:
                await self._notify_about_events(interaction.channel, user_id, result["available_events"])

            # Check if chapter is complete
            if "chapter_complete" in result and result["chapter_complete"]:
                if "story_complete" in result and result["story_complete"]:
                    embed = create_basic_embed(
                        title="História Concluída",
                        description="Parabéns! Você concluiu a história principal do jogo.",
                        color=discord.Color.gold()
                    )
                    await interaction.followup.send(embed=embed)
                elif "next_chapter_id" in result:
                    embed = create_basic_embed(
                        title="Capítulo Concluído",
                        description=f"Você concluiu este capítulo da história. O próximo capítulo está disponível.",
                        color=discord.Color.green()
                    )
                    await interaction.followup.send(embed=embed)

        return continue_callback

    async def _notify_about_events(self, channel, user_id: int, available_events):
        """
        Notifies the user about available events.
        """
        embed = create_basic_embed(
            title="Eventos Disponíveis",
            description="Há eventos disponíveis para você participar!",
            color=discord.Color.gold()
        )

        for event in available_events:
            embed.add_field(
                name=event["name"],
                value=f"ID: {event['id']}\n{event['description']}",
                inline=False
            )

        embed.set_footer(text="Use /evento [evento_id] para participar de um evento.")

        # Get the member object for the user
        guild = self.bot.get_guild(self.bot.config.get("guild_id"))
        if guild:
            member = guild.get_member(user_id)
            if member:
                try:
                    # Send a direct message to the user instead of posting in the channel
                    await member.send(embed=embed)
                    return
                except discord.errors.Forbidden:
                    # If the user has DMs disabled, fall back to an ephemeral message in the channel
                    pass

        # If we couldn't send a DM or get the member, store the message for later delivery
        # when the user interacts with the bot
        if not hasattr(self, 'pending_event_notifications'):
            self.pending_event_notifications = {}

        self.pending_event_notifications[user_id] = {
            'embed': embed,
            'timestamp': datetime.now()
        }

        # Send a private notification that only mentions the user
        await channel.send(f"<@{user_id}>, você tem novas notificações! Use `/evento` para verificar.", delete_after=60)

    def _get_hierarchy_name(self, tier: int) -> str:
        """
        Returns the name of a hierarchy tier.
        """
        hierarchy_names = {
            5: "Rei/Rainha",
            4: "Jack/Ás",
            3: "Elite",
            2: "Médio-Alto",
            1: "Médio",
            0: "Baixo"
        }

        return hierarchy_names.get(tier, "Desconhecido")

    async def _is_admin(self, user: discord.User) -> bool:
        """
        Checks if a user is an admin.
        """
        # Get the guild
        guild = self.bot.get_guild(self.bot.config.get("guild_id"))

        if not guild:
            return False

        # Get the member
        member = guild.get_member(user.id)

        if not member:
            return False

        # Check if the member has the admin role
        admin_role_id = self.bot.config.get("admin_role_id")

        if not admin_role_id:
            return False

        admin_role = guild.get_role(admin_role_id)

        if not admin_role:
            return False

        return admin_role in member.roles

    @commands.command(name="alianca")
    async def form_alliance(self, ctx, *, club_name: str):
        """Forma uma aliança com outro clube."""
        # Get player data
        player = await db_provider.get_player(ctx.author.id)
        if not player:
            await ctx.send("Você precisa se registrar primeiro! Use o comando `!registrar`.")
            return

        # Check if player is in a club
        if not player.get('club'):
            await ctx.send("Você precisa estar em um clube para formar alianças!")
            return

        # Find target club
        target_club_id = None
        for club_id, name in self.club_system.CLUBS.items():
            if name.lower() == club_name.lower():
                target_club_id = club_id
                break

        if not target_club_id:
            await ctx.send(f"Clube '{club_name}' não encontrado. Use `!clubes` para ver a lista de clubes disponíveis.")
            return

        # Form alliance
        result = self.club_system.form_alliance(player, target_club_id)
        if "error" in result:
            await ctx.send(result["error"])
            return

        # Create embed
        embed = create_basic_embed(
            title="Aliança Formada!",
            description=f"Seu clube formou uma aliança com o clube {club_name}!",
            color=0x00FF00
        )

        # Add alliance information
        embed.add_field(
            name="Detalhes da Aliança",
            value=result["message"],
            inline=False
        )

        await ctx.send(embed=embed)

    @commands.command(name="rivalidade")
    async def declare_rivalry(self, ctx, *, club_name: str):
        """Declara rivalidade com outro clube."""
        # Get player data
        player = await db_provider.get_player(ctx.author.id)
        if not player:
            await ctx.send("Você precisa se registrar primeiro! Use o comando `!registrar`.")
            return

        # Check if player is in a club
        if not player.get('club'):
            await ctx.send("Você precisa estar em um clube para declarar rivalidades!")
            return

        # Find target club
        target_club_id = None
        for club_id, name in self.club_system.CLUBS.items():
            if name.lower() == club_name.lower():
                target_club_id = club_id
                break

        if not target_club_id:
            await ctx.send(f"Clube '{club_name}' não encontrado. Use `!clubes` para ver a lista de clubes disponíveis.")
            return

        # Declare rivalry
        result = self.club_system.declare_rivalry(player, target_club_id)
        if "error" in result:
            await ctx.send(result["error"])
            return

        # Create embed
        embed = create_basic_embed(
            title="Rivalidade Declarada!",
            description=f"Seu clube declarou rivalidade com o clube {club_name}!",
            color=0xFF0000
        )

        # Add rivalry information
        embed.add_field(
            name="Detalhes da Rivalidade",
            value=result["message"],
            inline=False
        )

        await ctx.send(embed=embed)

    async def _show_choices(self, ctx_or_interaction, chapter_data, player_data):
        """Show available choices to the player."""
        try:
            # Handle both Context and Interaction objects
            is_interaction = isinstance(ctx_or_interaction, discord.Interaction)
            user_id = ctx_or_interaction.user.id if is_interaction else ctx_or_interaction.author.id
            send_message = ctx_or_interaction.followup.send if is_interaction else ctx_or_interaction.send

            # Get available choices
            if hasattr(chapter_data, 'get_available_choices'):
                choices = chapter_data.get_available_choices(player_data)
            else:
                choices = chapter_data.get("choices", [])

            if choices:
                # Create choice buttons
                view = discord.ui.View()
                for i, choice in enumerate(choices):
                    button = discord.ui.Button(
                        label=choice.get("text", f"Opção {i+1}"),
                        custom_id=f"choice_{i}",
                        style=discord.ButtonStyle.primary
                    )
                    button.callback = self._create_choice_callback(user_id, i)
                    view.add_item(button)
                
                await send_message("Escolha uma opção:", view=view)
            else:
                # If no choices available, show continue button
                view = discord.ui.View()
                continue_button = discord.ui.Button(
                    label="Continuar",
                    custom_id="continue",
                    style=discord.ButtonStyle.primary
                )
                continue_button.callback = self._create_continue_callback(user_id)
                view.add_item(continue_button)
                await send_message("Pressione continuar para seguir:", view=view)

        except Exception as e:
            logger.error(f"Error in _show_choices: {str(e)}")
            await send_message("Ocorreu um erro ao mostrar as opções. Por favor, tente novamente.")


async def setup(bot):
    """
    Setup function for the cog.
    """
    from utils.command_registrar import CommandRegistrar

    # Create and add the cog
    cog = StoryModeCog(bot)
    await bot.add_cog(cog)
    logger.info("StoryModeCog setup complete")

    # Register commands using the CommandRegistrar
    await CommandRegistrar.register_commands(bot, cog)
