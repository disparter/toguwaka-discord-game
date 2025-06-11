"""
Events cog for Academia Tokugawa.
Handles commands related to events and tournaments.
"""

import logging
import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional

logger = logging.getLogger('tokugawa_bot.cogs.events')

class EventsCog(commands.Cog):
    """Cog for handling event-related commands."""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(
        name="eventos",
        description="Mostra informações sobre os eventos atuais"
    )
    async def show_events(self, interaction: discord.Interaction):
        """Show information about current events."""
        try:
            # Get current events
            events = await self.bot.events_manager.get_current_events()
            
            # Create embed
            embed = discord.Embed(
                title="📅 Eventos Atuais",
                color=discord.Color.blue()
            )
            
            # Add daily subject
            if events['daily']['subject']:
                subject = events['daily']['subject']
                embed.add_field(
                    name=f"{subject['emoji']} Matéria do Dia",
                    value=f"**{subject['subject']}**\n{subject['description']}",
                    inline=False
                )
            
            # Add weekly tournament
            if events['weekly']['tournament']:
                tournament = events['weekly']['tournament']
                embed.add_field(
                    name=f"{tournament['emoji']} Torneio Semanal",
                    value=f"**{tournament['name']}**\n"
                          f"{tournament['description']}\n\n"
                          f"Participantes: {events['weekly']['participants']}\n"
                          f"Prêmio: {tournament['prize']} pontos",
                    inline=False
                )
            
            # Add special event
            if events['special']['event']:
                event = events['special']['event']
                embed.add_field(
                    name=f"{event['emoji']} Evento Especial",
                    value=f"**{event['name']}**\n"
                          f"{event['description']}\n\n"
                          f"Participantes: {events['special']['participants']}\n"
                          f"Prêmio: {event['prize']} pontos",
                    inline=False
                )
            
            if not any([events['daily']['subject'], events['weekly']['tournament'], events['special']['event']]):
                embed.description = "Não há eventos ativos no momento."
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Error showing events: {e}")
            await interaction.response.send_message(
                "Ocorreu um erro ao buscar informações dos eventos. Por favor, tente novamente mais tarde.",
                ephemeral=True
            )
    
    @app_commands.command(
        name="torneio",
        description="Gerencia sua participação no torneio semanal"
    )
    @app_commands.describe(
        action="Ação a ser realizada (participar/status)"
    )
    @app_commands.choices(action=[
        app_commands.Choice(name="participar", value="join"),
        app_commands.Choice(name="status", value="status")
    ])
    async def tournament(self, interaction: discord.Interaction, action: str):
        """Manage tournament participation."""
        try:
            if action == "join":
                # Add participant
                success = await self.bot.events_manager.weekly_events.add_tournament_participant(
                    interaction.user.id,
                    interaction.user.display_name
                )
                
                if success:
                    await interaction.response.send_message(
                        "Você foi inscrito no torneio semanal! Boa sorte!",
                        ephemeral=True
                    )
                else:
                    await interaction.response.send_message(
                        "Não foi possível inscrever você no torneio. Verifique se o torneio está ativo e se você já não está participando.",
                        ephemeral=True
                    )
            
            elif action == "status":
                # Get tournament info
                events = await self.bot.events_manager.get_current_events()
                tournament = events['weekly']['tournament']
                
                if not tournament:
                    await interaction.response.send_message(
                        "Não há torneio ativo no momento.",
                        ephemeral=True
                    )
                    return
                
                # Check if user is participating
                is_participating = any(
                    p['user_id'] == interaction.user.id
                    for p in self.bot.events_manager.weekly_events.tournament_participants
                )
                
                # Create embed
                embed = discord.Embed(
                    title=f"{tournament['emoji']} Status do Torneio",
                    color=discord.Color.green() if is_participating else discord.Color.red()
                )
                
                embed.add_field(
                    name="Torneio",
                    value=tournament['name'],
                    inline=False
                )
                
                embed.add_field(
                    name="Sua Participação",
                    value="✅ Participando" if is_participating else "❌ Não participando",
                    inline=False
                )
                
                embed.add_field(
                    name="Total de Participantes",
                    value=str(events['weekly']['participants']),
                    inline=False
                )
                
                await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Error managing tournament: {e}")
            await interaction.response.send_message(
                "Ocorreu um erro ao gerenciar o torneio. Por favor, tente novamente mais tarde.",
                ephemeral=True
            )
    
    @app_commands.command(
        name="evento",
        description="Gerencia sua participação em eventos especiais"
    )
    @app_commands.describe(
        action="Ação a ser realizada (participar/status)"
    )
    @app_commands.choices(action=[
        app_commands.Choice(name="participar", value="join"),
        app_commands.Choice(name="status", value="status")
    ])
    async def special_event(self, interaction: discord.Interaction, action: str):
        """Manage special event participation."""
        try:
            if action == "join":
                # Add participant
                success = await self.bot.events_manager.special_events.add_event_participant(
                    interaction.user.id,
                    interaction.user.display_name
                )
                
                if success:
                    await interaction.response.send_message(
                        "Você foi inscrito no evento especial! Boa sorte!",
                        ephemeral=True
                    )
                else:
                    await interaction.response.send_message(
                        "Não foi possível inscrever você no evento. Verifique se o evento está ativo e se você já não está participando.",
                        ephemeral=True
                    )
            
            elif action == "status":
                # Get event info
                events = await self.bot.events_manager.get_current_events()
                event = events['special']['event']
                
                if not event:
                    await interaction.response.send_message(
                        "Não há evento especial ativo no momento.",
                        ephemeral=True
                    )
                    return
                
                # Check if user is participating
                is_participating = any(
                    p['user_id'] == interaction.user.id
                    for p in self.bot.events_manager.special_events.event_participants
                )
                
                # Create embed
                embed = discord.Embed(
                    title=f"{event['emoji']} Status do Evento Especial",
                    color=discord.Color.green() if is_participating else discord.Color.red()
                )
                
                embed.add_field(
                    name="Evento",
                    value=event['name'],
                    inline=False
                )
                
                embed.add_field(
                    name="Sua Participação",
                    value="✅ Participando" if is_participating else "❌ Não participando",
                    inline=False
                )
                
                embed.add_field(
                    name="Total de Participantes",
                    value=str(events['special']['participants']),
                    inline=False
                )
                
                await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Error managing special event: {e}")
            await interaction.response.send_message(
                "Ocorreu um erro ao gerenciar o evento. Por favor, tente novamente mais tarde.",
                ephemeral=True
            )

async def setup(bot):
    """Set up the events cog."""
    await bot.add_cog(EventsCog(bot)) 