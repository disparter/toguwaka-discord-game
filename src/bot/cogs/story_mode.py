import discord
from discord.ext import commands
from discord import app_commands
import logging
from utils.json_utils import dumps as json_dumps
import asyncio
import os
from datetime import datetime
from typing import Dict, List, Any, Optional, Union

from utils.database import get_player, update_player, get_club, get_all_clubs
from utils.embeds import create_basic_embed, create_event_embed
from utils.game_mechanics import calculate_level_from_exp

from story_mode.story_mode import StoryMode
from story_mode.club_system import ClubSystem

logger = logging.getLogger('tokugawa_bot')

class StoryModeCog(commands.Cog):
    """
    A cog that implements the story mode using the new SOLID architecture.
    This cog serves as an adapter between the Discord bot and the StoryMode system.
    """
    def __init__(self, bot):
        self.bot = bot
        self.story_mode = StoryMode()
        self.active_sessions = {}  # user_id -> session_data
        self.club_system = ClubSystem()

        logger.info("StoryModeCog initialized")

    def cog_load(self):
        """Called when the cog is loaded."""
        logger.info("StoryModeCog loaded")

    @commands.command(name="historia")
    async def start_story(self, ctx):
        """
        Regular command to start or continue the story mode.
        """
        user_id = ctx.author.id
        player_data = get_player(user_id)

        if not player_data:
            await ctx.send("Você precisa criar um personagem primeiro! Use /registrar")
            return

        # Start or continue the story
        result = self.story_mode.start_story(player_data)
        logger.info(f"start_story result: {result}")

        if "error" in result:
            await ctx.send(f"Erro ao iniciar o modo história: {result['error']}")
            return

        if "player_data" not in result or "chapter_data" not in result:
            await ctx.send("Erro interno: dados do modo história ausentes. Por favor, contate um administrador.")
            logger.error(f"start_story returned incomplete result: {result}")
            return

        # Update player data in database
        update_data = {"story_progress": json_dumps(result["player_data"]["story_progress"])}

        # Also update club_id if it's in the player data
        if "club_id" in result["player_data"]:
            update_data["club_id"] = result["player_data"]["club_id"]

        update_player(user_id, **update_data)

        # Store session data
        self.active_sessions[user_id] = {
            "channel_id": ctx.channel.id,
            "last_activity": datetime.now()
        }

        # Send chapter information
        chapter_data = result["chapter_data"]
        embed = create_basic_embed(
            title=f"Capítulo: {chapter_data['title']}",
            description=chapter_data['description'],
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

        # Send first dialogue or choices
        await self._send_dialogue_or_choices(ctx.channel, user_id, result)

        # Check for available events
        if "available_events" in result and result["available_events"]:
            await self._notify_about_events(ctx.channel, user_id, result["available_events"])

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
        player_data = get_player(user_id)

        if not player_data:
            await interaction.followup.send("Você precisa criar um personagem primeiro! Use /registrar", ephemeral=True)
            return

        # Start or continue the story
        result = self.story_mode.start_story(player_data)
        logger.info(f"start_story result: {result}")

        if "error" in result:
            await interaction.followup.send(f"Erro ao iniciar o modo história: {result['error']}", ephemeral=True)
            return

        if "player_data" not in result or "chapter_data" not in result:
            await interaction.followup.send("Erro interno: dados do modo história ausentes. Por favor, contate um administrador.", ephemeral=True)
            logger.error(f"start_story returned incomplete result: {result}")
            return

        # Update player data in database
        update_data = {"story_progress": json_dumps(result["player_data"]["story_progress"])}

        # Also update club_id if it's in the player data
        if "club_id" in result["player_data"]:
            update_data["club_id"] = result["player_data"]["club_id"]

        update_player(user_id, **update_data)

        # Store session data
        self.active_sessions[user_id] = {
            "channel_id": interaction.channel_id,
            "last_activity": datetime.now()
        }

        # Send chapter information
        chapter_data = result["chapter_data"]
        embed = create_basic_embed(
            title=f"Capítulo: {chapter_data['title']}",
            description=chapter_data['description'],
            color=discord.Color.blue()
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

        # Send first dialogue or choices
        await self._send_dialogue_or_choices(interaction.channel, user_id, result)

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
        player_data = get_player(user_id)

        if not player_data:
            await interaction.followup.send("Você precisa criar um personagem primeiro! Use /registrar", ephemeral=True)
            return

        # Get story status
        status = self.story_mode.get_story_status(player_data)

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
    async def slash_relacionamento(self, interaction: discord.Interaction, personagem: str = None, afinidade: int = None):
        """
        Slash command to show or change the player's relationship with an NPC.
        """
        try:
            await interaction.response.defer(ephemeral=True)
        except discord.errors.NotFound:
            logger.warning(f"Interaction expired for user {interaction.user.id} when using /relacionamento")
            return  # Let the command tree error handler handle this

        user_id = interaction.user.id
        player_data = get_player(user_id)

        if not player_data:
            await interaction.followup.send("Você precisa criar um personagem primeiro! Use /registrar", ephemeral=True)
            return

        # If no character specified, show all relationships
        if not personagem:
            status = self.story_mode.get_story_status(player_data)

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
                await interaction.followup.send("Apenas administradores podem alterar afinidade diretamente.", ephemeral=True)
                return

            result = self.story_mode.update_affinity(player_data, personagem, afinidade)

            if "error" in result:
                await interaction.followup.send(f"Erro ao atualizar afinidade: {result['error']}", ephemeral=True)
                return

            # Update player data in database
            update_data = {"story_progress": json_dumps(result["player_data"]["story_progress"])}

            # Also update club_id if it's in the player data
            if "club_id" in result["player_data"]:
                update_data["club_id"] = result["player_data"]["club_id"]

            update_player(user_id, **update_data)

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
        status = self.story_mode.get_story_status(player_data)

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
        player_data = get_player(user_id)

        if not player_data:
            try:
                await interaction.followup.send("Você precisa criar um personagem primeiro! Use /registrar", ephemeral=True)
            except discord.errors.NotFound:
                logger.error("A interação expirou antes que a resposta pudesse ser enviada.")
            except Exception as e:
                logger.error(f"Erro ao enviar resposta: {e}")
            return

        # If no event ID specified, show available events
        if not evento_id:
            result = self.story_mode.start_story(player_data)

            if "error" in result:
                try:
                    await interaction.followup.send(f"Erro ao verificar eventos disponíveis: {result['error']}", ephemeral=True)
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
        result = self.story_mode.trigger_event(player_data, evento_id)

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

        update_player(user_id, **update_data)

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

    async def _send_dialogue_or_choices(self, channel, user_id: int, result: Dict[str, Any]):
        """
        Sends the current dialogue or choices to the channel.
        """
        chapter_data = result["chapter_data"]

        # Check if this is a challenge that has already been completed or failed
        if "already_completed" in chapter_data and chapter_data["already_completed"]:
            embed = create_basic_embed(
                title="Desafio Já Completado",
                description="Você já completou este desafio com sucesso. Não é possível refazê-lo.",
                color=discord.Color.gold()
            )
            await channel.send(embed=embed, ephemeral=True)
            return

        if "already_failed" in chapter_data and chapter_data["already_failed"]:
            embed = create_basic_embed(
                title="Desafio Já Tentado",
                description="Você já falhou neste desafio. Não é possível tentá-lo novamente.",
                color=discord.Color.red()
            )
            await channel.send(embed=embed, ephemeral=True)
            return

        # Check if a path is blocked due to previous failures
        if "path_blocked" in result and result["path_blocked"]:
            embed = create_basic_embed(
                title="Caminho Bloqueado",
                description="Devido a falhas anteriores, este caminho da história está bloqueado para você.",
                color=discord.Color.red()
            )
            await channel.send(embed=embed, ephemeral=True)
            return

        # Check if a challenge was just completed successfully
        if "challenge_success" in result and result["challenge_success"]:
            embed = create_basic_embed(
                title="Desafio Completado",
                description="Parabéns! Você completou o desafio com sucesso e recebeu recompensas.",
                color=discord.Color.green()
            )
            await channel.send(embed=embed, ephemeral=True)

        # Check if a challenge was just failed
        if "challenge_failure" in result and result["challenge_failure"]:
            embed = create_basic_embed(
                title="Desafio Falhou",
                description="Você falhou no desafio. Isso terá consequências para sua jornada.",
                color=discord.Color.red()
            )
            await channel.send(embed=embed, ephemeral=True)

        # If there's a current dialogue, send it
        if "current_dialogue" in chapter_data and chapter_data["current_dialogue"]:
            dialogue = chapter_data["current_dialogue"]

            # Format the dialogue
            npc_name = dialogue.get("npc", "Narrador")
            text = dialogue.get("text", "...")

            # Replace placeholders in the text with player-specific information
            player_data = get_player(user_id)
            if player_data:
                text = text.format(
                    player_name=player_data["name"],
                    player_level=player_data["level"],
                    player_element=player_data.get("element", "desconhecido")
                )

            # Create embed for the dialogue
            embed = create_basic_embed(
                title=npc_name,
                description=text,
                color=discord.Color.blue()
            )

            # Add character intro images for first interactions
            if "image" in dialogue and dialogue["image"]:
                image_filename = dialogue["image"]
                image_path = f"assets/images/{image_filename}"
                if os.path.exists(image_path):
                    try:
                        # Check file size
                        file_size = os.path.getsize(image_path)
                        if file_size <= 8 * 1024 * 1024:  # 8MB limit
                            embed.set_image(url=f"attachment://{image_filename}")
                            file = discord.File(image_path, filename=image_filename)
                            await channel.send(embed=embed, file=file, ephemeral=True)
                        else:
                            logger.warning(f"Image file {image_filename} is too large ({file_size/1024/1024:.2f}MB) and couldn't be sent")
                            await channel.send(embed=embed, ephemeral=True)
                    except Exception as e:
                        logger.error(f"Error sending image {image_filename}: {str(e)}")
                        await channel.send(embed=embed, ephemeral=True)
                else:
                    logger.warning(f"Image file {image_filename} not found at {image_path}")
                    await channel.send(embed=embed, ephemeral=True)
            else:
                await channel.send(embed=embed, ephemeral=True)

            # If the dialogue has choices, add buttons for those choices
            if "choices" in dialogue and dialogue["choices"]:
                view = discord.ui.View(timeout=300)

                for i, choice in enumerate(dialogue["choices"]):
                    # Ensure button label is not longer than 80 characters (Discord's limit)
                    label = choice["text"]
                    if len(label) > 80:
                        label = label[:77] + "..."

                    button = discord.ui.Button(
                        style=discord.ButtonStyle.primary,
                        label=label,
                        custom_id=f"choice_{i}"
                    )
                    button.callback = self._create_choice_callback(user_id, i)
                    view.add_item(button)

                # Send choices as ephemeral
                if file:
                    message = await channel.send(file=file, embed=embed, view=view, ephemeral=True)
                else:
                    message = await channel.send(embed=embed, view=view, ephemeral=True)
                return

            # If there are choices in the chapter data but not in the dialogue, check if we should show them
            elif "choices" in chapter_data and chapter_data["choices"]:
                # This is a story event with choices
                view = discord.ui.View(timeout=300)

                for i, choice in enumerate(chapter_data["choices"]):
                    # Ensure button label is not longer than 80 characters (Discord's limit)
                    label = choice["text"]
                    if len(label) > 80:
                        label = label[:77] + "..."

                    button = discord.ui.Button(
                        style=discord.ButtonStyle.primary,
                        label=label,
                        custom_id=f"choice_{i}"
                    )
                    button.callback = self._create_choice_callback(user_id, i)
                    view.add_item(button)

                # Send choices as ephemeral
                if file:
                    message = await channel.send(file=file, embed=embed, view=view, ephemeral=True)
                else:
                    message = await channel.send(embed=embed, view=view, ephemeral=True)
                return
            else:
                # If no choices, add a "Continue" button
                view = discord.ui.View(timeout=300)
                # "Continuar" is short enough, but adding the check for consistency
                label = "Continuar"
                if len(label) > 80:
                    label = label[:77] + "..."

                button = discord.ui.Button(
                    style=discord.ButtonStyle.primary,
                    label=label,
                    custom_id="continue"
                )
                button.callback = self._create_continue_callback(user_id)
                view.add_item(button)

                # Send continue button as ephemeral
                if file:
                    message = await channel.send(file=file, embed=embed, view=view, ephemeral=True)
                else:
                    message = await channel.send(embed=embed, view=view, ephemeral=True)
                return

        # If there are choices but no current dialogue, send the choices
        if "choices" in chapter_data and chapter_data["choices"]:
            # Check if this is a challenge chapter
            challenge_type = chapter_data.get("challenge_type")
            if challenge_type:
                title = f"Desafio: {challenge_type.capitalize()}"
                description = "Escolha como enfrentar este desafio:"
                color = discord.Color.gold()
            else:
                title = "Escolha uma opção"
                description = "O que você deseja fazer?"
                color = discord.Color.blue()

            embed = create_basic_embed(
                title=title,
                description=description,
                color=color
            )

            view = discord.ui.View(timeout=300)

            for i, choice in enumerate(chapter_data["choices"]):
                # Ensure button label is not longer than 80 characters (Discord's limit)
                label = choice["text"]
                if len(label) > 80:
                    label = label[:77] + "..."

                button = discord.ui.Button(
                    style=discord.ButtonStyle.primary,
                    label=label,
                    custom_id=f"choice_{i}"
                )
                button.callback = self._create_choice_callback(user_id, i)
                view.add_item(button)

            # Send choices as ephemeral
            message = await channel.send(embed=embed, view=view, ephemeral=True)
            return

        # If no dialogue or choices, the chapter is complete
        if "chapter_complete" in result and result["chapter_complete"]:
            if "story_complete" in result and result["story_complete"]:
                title = "História Concluída"
                description = "Parabéns! Você concluiu a história principal do jogo."
                color = discord.Color.gold()
            else:
                title = "Capítulo Concluído"
                description = "Você concluiu este capítulo da história."
                color = discord.Color.green()
        else:
            title = "Capítulo Concluído"
            description = "Você concluiu este capítulo da história."
            color = discord.Color.green()

        embed = create_basic_embed(
            title=title,
            description=description,
            color=color
        )

        # Send chapter completion message as ephemeral
        await channel.send(embed=embed, ephemeral=True)

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
            player_data = get_player(user_id)

            if not player_data:
                await interaction.followup.send("Erro: Dados do jogador não encontrados.", ephemeral=True)
                return

            # Process the choice
            result = self.story_mode.process_choice(player_data, choice_index)

            if "error" in result:
                await interaction.followup.send(f"Erro ao processar escolha: {result['error']}", ephemeral=True)
                return

            # Update player data in database
            update_data = {"story_progress": json_dumps(result["player_data"]["story_progress"])}

            # Also update club_id if it's in the player data
            if "club_id" in result["player_data"]:
                update_data["club_id"] = result["player_data"]["club_id"]

            update_player(user_id, **update_data)

            # Send next dialogue or choices
            await self._send_dialogue_or_choices(interaction.channel, user_id, result)

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
                    await interaction.channel.send(embed=embed, ephemeral=True)
                elif "next_chapter_id" in result:
                    embed = create_basic_embed(
                        title="Capítulo Concluído",
                        description=f"Você concluiu este capítulo da história. O próximo capítulo está disponível.",
                        color=discord.Color.green()
                    )
                    await interaction.channel.send(embed=embed, ephemeral=True)

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
            player_data = get_player(user_id)

            if not player_data:
                await interaction.followup.send("Erro: Dados do jogador não encontrados.", ephemeral=True)
                return

            # Process the choice (continue is equivalent to choice 0)
            result = self.story_mode.process_choice(player_data, 0)

            if "error" in result:
                await interaction.followup.send(f"Erro ao continuar: {result['error']}", ephemeral=True)
                return

            # Update player data in database
            update_data = {"story_progress": json_dumps(result["player_data"]["story_progress"])}

            # Also update club_id if it's in the player data
            if "club_id" in result["player_data"]:
                update_data["club_id"] = result["player_data"]["club_id"]

            update_player(user_id, **update_data)

            # Send next dialogue or choices
            await self._send_dialogue_or_choices(interaction.channel, user_id, result)

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

        return continue_callback

    async def _notify_about_events(self, channel, user_id: int, available_events: List[Dict[str, Any]]):
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

    @commands.command(name="clube")
    async def club_info(self, ctx):
        """Exibe informações sobre o clube atual do jogador."""
        # Get player data
        player = get_player(ctx.author.id)
        if not player:
            await ctx.send("Você precisa se registrar primeiro! Use o comando `!registrar`.")
            return

        # Get club info
        club_info = self.club_system.get_club_info(player)
        if "error" in club_info:
            await ctx.send("Você não está em nenhum clube. Use `!ingressar` para entrar em um clube.")
            return

        # Create embed
        embed = create_basic_embed(
            title=f"Informações do Clube: {club_info['name']}",
            description=f"Líder: {club_info['leader']}",
            color=0x1E90FF
        )

        # Add rank information
        embed.add_field(
            name="Rank",
            value=f"{club_info['rank_name']} (Nível {club_info['rank']})",
            inline=False
        )

        # Add experience information
        embed.add_field(
            name="Experiência",
            value=f"{club_info['experience']}/{club_info['experience_needed']} EXP",
            inline=False
        )

        # Add rivalries information
        rivalries = self.club_system._get_rivalries_info(player)
        if rivalries:
            rivalries_text = "\n".join([f"- {r['name']}: {r['affinity']}" for r in rivalries])
            embed.add_field(
                name="Rivalidades",
                value=rivalries_text,
                inline=False
            )

        # Add alliances information
        alliances = self.club_system._get_alliances_info(player)
        if alliances:
            alliances_text = "\n".join([f"- {a['name']}: {a['affinity']}" for a in alliances])
            embed.add_field(
                name="Alianças",
                value=alliances_text,
                inline=False
            )

        await ctx.send(embed=embed)

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
