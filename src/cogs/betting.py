"""
Betting cog for the Academia Tokugawa Discord bot.
This cog provides commands for betting on duels and other events.
"""

import discord
import logging
from discord import app_commands
from discord.ext import commands
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from utils.command_registrar import CommandRegistrar
from utils.embeds import create_basic_embed
from utils.persistence import db_provider
from utils.ranking_formatter import RankingFormatter
from events.events_manager import EventsManager

logger = logging.getLogger('tokugawa_bot')


class BettingCog(commands.Cog):
    """Cog for betting on duels and other events."""

    def __init__(self, bot):
        self.bot = bot
        self.active_bets = {}  # {bet_id: {challenger_id, opponent_id, amount, participants: {user_id: choice}}}
        self.bet_counter = 1
        self.ranking_formatter = RankingFormatter()
        self.events_manager = EventsManager(bot)

    # Group for betting commands
    betting_group = app_commands.Group(name="aposta", description="Comandos de apostas da Academia Tokugawa")

    @betting_group.command(name="duelar", description="Desafiar outro jogador para um duelo com apostas")
    async def slash_bet_duel(self, interaction: discord.Interaction, opponent: discord.Member, amount: int,
                             duel_type: str = "physical"):
        """Slash command for betting duel."""
        try:
            # Check if opponent is specified
            if not opponent:
                await interaction.response.send_message(
                    f"{interaction.user.mention}, você precisa mencionar um oponente para duelar.")
                return

            # Check if player is trying to duel themselves
            if opponent.id == interaction.user.id:
                await interaction.response.send_message(
                    f"{interaction.user.mention}, você não pode duelar consigo mesmo!")
                return

            # Check if player exists
            challenger = await db_provider.get_player(interaction.user.id)
            if not challenger:
                await interaction.response.send_message(
                    f"{interaction.user.mention}, você ainda não está registrado na Academia Tokugawa. Use /registro ingressar para criar seu personagem.")
                return

            # Check if opponent exists
            opponent_player = await db_provider.get_player(opponent.id)
            if not opponent_player:
                await interaction.response.send_message(f"{opponent.mention} não está registrado na Academia Tokugawa.")
                return

            # Check if amount is valid
            if amount <= 0:
                await interaction.response.send_message(
                    f"{interaction.user.mention}, o valor da aposta deve ser maior que zero.")
                return

            # Check if player has enough TUSD
            if challenger["tusd"] < amount:
                await interaction.response.send_message(
                    f"{interaction.user.mention}, você não tem TUSD suficiente para essa aposta. Seu saldo: {challenger['tusd']} TUSD")
                return

            # Check if player is already in a duel
            activities_cog = self.bot.get_cog('Activities')
            if activities_cog and (
                    interaction.user.id in activities_cog.active_duels or opponent.id in activities_cog.active_duels.values()):
                await interaction.response.send_message(
                    f"{interaction.user.mention}, você ou seu oponente já está em um duelo!")
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

            # Send initial response
            await interaction.response.send_message(f"Desafio de duelo com apostas enviado para {opponent.mention}!")

            # Create challenge embed
            challenge_embed = create_basic_embed(
                title="Desafio de Duelo com Apostas!",
                description=f"{interaction.user.mention} desafiou {opponent.mention} para um duelo **{duel_names[duel_type]}** com aposta de **{amount} TUSD**!\n\n"
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

                # Check if opponent has enough TUSD
                if opponent_player["tusd"] < amount:
                    await button_interaction.response.send_message(
                        f"{opponent.mention}, você não tem TUSD suficiente para essa aposta. Seu saldo: {opponent_player['tusd']} TUSD",
                        ephemeral=True)
                    return

                # Disable buttons
                for child in view.children:
                    child.disabled = True
                await button_interaction.message.edit(view=view)

                # Create a bet ID
                bet_id = self.bet_counter
                self.bet_counter += 1

                # Store bet information
                self.active_bets[bet_id] = {
                    "challenger_id": interaction.user.id,
                    "opponent_id": opponent.id,
                    "amount": amount,
                    "duel_type": duel_type,
                    "participants": {
                        interaction.user.id: "challenger",
                        opponent.id: "opponent"
                    }
                }

                # Deduct TUSD from both players
                challenger["tusd"] -= amount
                opponent_player["tusd"] -= amount
                await db_provider.update_player(interaction.user.id, challenger)
                await db_provider.update_player(opponent.id, opponent_player)

                # Start the duel
                if activities_cog:
                    # Mark duel as active in Activities cog
                    activities_cog.active_duels[interaction.user.id] = opponent.id

                    # Use the existing duel functionality
                    # Instead of trying to access _callback directly, which causes errors
                    # We'll call the method directly with the proper parameters
                    await activities_cog.handle_duel(interaction, opponent, duel_type)

                    # Add a callback to handle the duel result
                    self.bot.add_listener(self.on_duel_complete, "on_duel_complete")
                else:
                    await button_interaction.response.send_message(
                        "Erro ao iniciar o duelo. O módulo de atividades não está disponível.")
                    # Refund the TUSD
                    challenger["tusd"] += amount
                    opponent_player["tusd"] += amount
                    await db_provider.update_player(interaction.user.id, challenger)
                    await db_provider.update_player(opponent.id, opponent_player)

            async def decline_callback(button_interaction):
                if button_interaction.user.id != opponent.id:
                    await button_interaction.response.send_message(
                        "Apenas o oponente desafiado pode aceitar ou recusar.", ephemeral=True)
                    return

                # Disable buttons
                for child in view.children:
                    child.disabled = True
                await button_interaction.message.edit(view=view)

                await button_interaction.response.send_message(
                    f"{opponent.mention} recusou o desafio de duelo com apostas.")

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
            logger.warning(f"Interaction expired for user {interaction.user.id} when using /aposta duelar")
        except Exception as e:
            logger.error(f"Error in slash_bet_duel: {e}")

    @betting_group.command(name="evento", description="Apostar em um evento atual")
    async def slash_bet_event(self, interaction: discord.Interaction, event_id: str, choice: str, amount: int):
        """Slash command for betting on events."""
        try:
            # Check if player exists
            player = await db_provider.get_player(interaction.user.id)
            if not player:
                await interaction.response.send_message(
                    f"{interaction.user.mention}, você ainda não está registrado na Academia Tokugawa. Use /registro ingressar para criar seu personagem.")
                return

            # Check if amount is valid
            if amount <= 0:
                await interaction.response.send_message(
                    f"{interaction.user.mention}, o valor da aposta deve ser maior que zero.")
                return

            # Check if player has enough TUSD
            if player["tusd"] < amount:
                await interaction.response.send_message(
                    f"{interaction.user.mention}, você não tem TUSD suficiente para essa aposta. Seu saldo: {player['tusd']} TUSD")
                return

            # Get the event
            scheduled_events_cog = self.bot.get_cog('ScheduledEvents')
            if not scheduled_events_cog:
                await interaction.response.send_message(
                    "Erro ao processar a aposta. O módulo de eventos não está disponível.")
                return

            # This is a placeholder for future event betting functionality
            await interaction.response.send_message("Apostas em eventos serão implementadas em breve!")

        except discord.errors.NotFound:
            # If the interaction has expired, log it but don't try to respond
            logger.warning(f"Interaction expired for user {interaction.user.id} when using /aposta evento")
        except Exception as e:
            logger.error(f"Error in slash_bet_event: {e}")

    async def on_duel_complete(self, duel_result):
        """Handle duel completion and distribute winnings."""
        # Find the bet for this duel
        bet_id = None
        for bid, bet in self.active_bets.items():
            if (bet["challenger_id"] == duel_result["winner_id"] and bet["opponent_id"] == duel_result["loser_id"]) or \
                    (bet["challenger_id"] == duel_result["loser_id"] and bet["opponent_id"] == duel_result[
                        "winner_id"]):
                bet_id = bid
                break

        if bet_id:
            await self._handle_bet_result(bet_id, duel_result["winner_id"], duel_result["loser_id"])
            del self.active_bets[bet_id]

    async def _handle_bet_result(self, bet_id, winner_id, loser_id):
        """Handle the result of a bet and distribute winnings."""
        bet = self.active_bets.get(bet_id)
        if not bet:
            return

        # Calculate winnings (total pot)
        winnings = bet["amount"] * 2  # Both players put in the same amount

        # Get player data
        winner = await db_provider.get_player(winner_id)
        loser = await db_provider.get_player(loser_id)
        if not winner or not loser:
            return

        # Update winner's TUSD
        winner["tusd"] += winnings
        await db_provider.update_player(winner_id, winner)

        # Log the result
        logger.info(f"Bet {bet_id} completed. Winner: {winner_id}, Winnings: {winnings} TUSD")

    @commands.command(name="apostar")
    async def bet(self, ctx, opponent: discord.Member = None, amount: int = None, duel_type: str = "physical"):
        """Command for betting on duels."""
        if not opponent or not amount:
            await ctx.send(f"{ctx.author.mention}, uso correto: !apostar @oponente <valor> [tipo_de_duelo]")
            return

        # Convert to slash command
        interaction = await self.bot._get_context(ctx.message)
        await self.slash_bet_duel(interaction, opponent, amount, duel_type)

    @app_commands.command(name="apostar", description="Aposte em um duelo ou evento")
    async def slash_bet(self, interaction: discord.Interaction, tipo: str, id: str, valor: int):
        """Place a bet on a duel or event."""
        try:
            # Check if user has enough money
            player_data = await db_provider.get_player(str(interaction.user.id))
            if not player_data:
                await interaction.response.send_message("Você precisa criar um personagem primeiro!", ephemeral=True)
                return
            
            if player_data.get('money', 0) < valor:
                await interaction.response.send_message("Você não tem dinheiro suficiente para fazer essa aposta!", ephemeral=True)
                return
            
            # Handle different bet types
            if tipo.lower() == "duelo":
                # Get duel data
                duel_data = await db_provider.get_duel(id)
                if not duel_data:
                    await interaction.response.send_message("Duelo não encontrado!", ephemeral=True)
                    return
                
                # Check if duel is still open for bets
                if datetime.fromisoformat(duel_data['end_time']) < datetime.now():
                    await interaction.response.send_message("Este duelo já está fechado para apostas!", ephemeral=True)
                    return
                
                # Place bet
                success = await db_provider.place_bet(
                    user_id=str(interaction.user.id),
                    bet_type="duel",
                    target_id=id,
                    amount=valor
                )
                
                if success:
                    await interaction.response.send_message(f"Aposta de {valor} moedas realizada com sucesso!", ephemeral=True)
                else:
                    await interaction.response.send_message("Erro ao realizar aposta. Tente novamente mais tarde.", ephemeral=True)
            
            elif tipo.lower() == "evento":
                # Get event data
                event_data = await db_provider.get_event(id)
                if not event_data:
                    await interaction.response.send_message("Evento não encontrado!", ephemeral=True)
                    return
                
                # Check if event is still open for bets
                if datetime.fromisoformat(event_data['end_time']) < datetime.now():
                    await interaction.response.send_message("Este evento já está fechado para apostas!", ephemeral=True)
                    return
                
                # Place bet
                success = await db_provider.place_bet(
                    user_id=str(interaction.user.id),
                    bet_type="event",
                    target_id=id,
                    amount=valor
                )
                
                if success:
                    await interaction.response.send_message(f"Aposta de {valor} moedas realizada com sucesso!", ephemeral=True)
                else:
                    await interaction.response.send_message("Erro ao realizar aposta. Tente novamente mais tarde.", ephemeral=True)
            
            else:
                await interaction.response.send_message("Tipo de aposta inválido! Use 'duelo' ou 'evento'.", ephemeral=True)
        
        except Exception as e:
            logger.error(f"Error in slash_bet: {e}")
            await interaction.response.send_message("Ocorreu um erro ao processar sua aposta. Por favor, tente novamente mais tarde.", ephemeral=True)
    
    @app_commands.command(name="apostas", description="Veja suas apostas ativas")
    async def slash_my_bets(self, interaction: discord.Interaction):
        """Show active bets."""
        try:
            # Get user's active bets
            bets = await db_provider.get_active_bets(str(interaction.user.id))
            if not bets:
                await interaction.response.send_message("Você não tem apostas ativas!", ephemeral=True)
                return
            
            # Create embed
            embed = discord.Embed(
                title="🎲 Suas Apostas Ativas",
                color=discord.Color.blue()
            )
            
            for bet in bets:
                if bet['type'] == 'duel':
                    duel_data = await db_provider.get_duel(bet['target_id'])
                    if duel_data:
                        embed.add_field(
                            name=f"Duelo: {duel_data['name']}",
                            value=f"Valor: {bet['amount']} moedas\nStatus: {duel_data['status']}",
                            inline=False
                        )
                elif bet['type'] == 'event':
                    event_data = await db_provider.get_event(bet['target_id'])
                    if event_data:
                        embed.add_field(
                            name=f"Evento: {event_data['name']}",
                            value=f"Valor: {bet['amount']} moedas\nStatus: {event_data['status']}",
                            inline=False
                        )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
        
        except Exception as e:
            logger.error(f"Error in slash_my_bets: {e}")
            await interaction.response.send_message("Ocorreu um erro ao buscar suas apostas. Por favor, tente novamente mais tarde.", ephemeral=True)
    
    @app_commands.command(name="ranking_apostas", description="Veja o ranking de apostadores")
    async def slash_betting_ranking(self, interaction: discord.Interaction):
        """Show betting ranking."""
        try:
            # Get betting ranking
            ranking = await db_provider.get_betting_ranking()
            if not ranking:
                await interaction.response.send_message("Não há dados de apostas disponíveis!", ephemeral=True)
                return
            
            # Create embed
            embed = discord.Embed(
                title="🏆 Ranking de Apostadores",
                color=discord.Color.gold()
            )
            
            for i, player in enumerate(ranking[:10], 1):
                embed.add_field(
                    name=f"{i}. {player['name']}",
                    value=f"Ganhos: {player['total_winnings']} moedas\nApostas: {player['total_bets']}",
                    inline=False
                )
            
            await interaction.response.send_message(embed=embed)
        
        except Exception as e:
            logger.error(f"Error in slash_betting_ranking: {e}")
            await interaction.response.send_message("Ocorreu um erro ao buscar o ranking. Por favor, tente novamente mais tarde.", ephemeral=True)
    
    async def handle_duel_completion(self, duel_id: str, winner_id: str):
        """Handle duel completion and pay out bets."""
        try:
            # Get duel data
            duel_data = await db_provider.get_duel(duel_id)
            if not duel_data:
                logger.error(f"Duel {duel_id} not found")
                return
            
            # Get all bets for this duel
            bets = await db_provider.get_bets_for_target(duel_id)
            if not bets:
                logger.info(f"No bets found for duel {duel_id}")
                return
            
            # Calculate total pot and winning bets
            total_pot = sum(bet['amount'] for bet in bets)
            winning_bets = [bet for bet in bets if bet['user_id'] == winner_id]
            
            if not winning_bets:
                logger.info(f"No winning bets for duel {duel_id}")
                return
            
            # Calculate winnings per bet
            winnings_per_bet = total_pot / len(winning_bets)
            
            # Pay out winners
            for bet in winning_bets:
                await db_provider.update_player_money(
                    bet['user_id'],
                    winnings_per_bet
                )
                
                # Notify winner
                user = self.bot.get_user(int(bet['user_id']))
                if user:
                    try:
                        await user.send(f"Você ganhou {winnings_per_bet} moedas na aposta do duelo {duel_data['name']}!")
                    except:
                        logger.error(f"Could not send DM to user {bet['user_id']}")
            
            # Mark bets as completed
            await db_provider.complete_bets_for_target(duel_id)
            
            logger.info(f"Successfully paid out bets for duel {duel_id}")
        
        except Exception as e:
            logger.error(f"Error handling duel completion: {e}")
    
    async def handle_event_completion(self, event_id: str, winners: list):
        """Handle event completion and pay out bets."""
        try:
            # Get event data
            event_data = await db_provider.get_event(event_id)
            if not event_data:
                logger.error(f"Event {event_id} not found")
                return
            
            # Get all bets for this event
            bets = await db_provider.get_bets_for_target(event_id)
            if not bets:
                logger.info(f"No bets found for event {event_id}")
                return
            
            # Calculate total pot and winning bets
            total_pot = sum(bet['amount'] for bet in bets)
            winning_bets = [bet for bet in bets if bet['user_id'] in winners]
            
            if not winning_bets:
                logger.info(f"No winning bets for event {event_id}")
                return
            
            # Calculate winnings per bet
            winnings_per_bet = total_pot / len(winning_bets)
            
            # Pay out winners
            for bet in winning_bets:
                await db_provider.update_player_money(
                    bet['user_id'],
                    winnings_per_bet
                )
                
                # Notify winner
                user = self.bot.get_user(int(bet['user_id']))
                if user:
                    try:
                        await user.send(f"Você ganhou {winnings_per_bet} moedas na aposta do evento {event_data['name']}!")
                    except:
                        logger.error(f"Could not send DM to user {bet['user_id']}")
            
            # Mark bets as completed
            await db_provider.complete_bets_for_target(event_id)
            
            logger.info(f"Successfully paid out bets for event {event_id}")
        
        except Exception as e:
            logger.error(f"Error handling event completion: {e}")


async def setup(bot):
    """Add the cog to the bot."""
    # Create and add the cog
    cog = BettingCog(bot)
    await bot.add_cog(cog)
    logger.info("Betting cog loaded")

    # Register commands using the CommandRegistrar
    await CommandRegistrar.register_commands(bot, cog)
