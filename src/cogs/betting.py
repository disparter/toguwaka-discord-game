"""
Betting cog for Academia Tokugawa.
Handles all betting-related commands and functionality.
"""

import logging
import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from utils.persistence.db_provider import db_provider
from utils.logging_config import get_logger

logger = get_logger('tokugawa_bot.betting')

class BettingCog(commands.Cog):
    """Cog for handling betting functionality."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @app_commands.command(name="apostar", description="Aposte em um duelo ou evento")
    async def slash_bet(self, interaction: discord.Interaction, tipo: str, id: str, valor: int):
        """Place a bet on a duel or event."""
        try:
            # Check if user has enough funds
            player = await db_provider.get_player(str(interaction.user.id))
            if not player or player.get('coins', 0) < valor:
                await interaction.response.send_message("Você não tem moedas suficientes para fazer esta aposta.", ephemeral=True)
                return
            
            # Get duel or event data
            if tipo.lower() == 'duelo':
                duel = await db_provider.get_event(id)
                if not duel or duel.get('type') != 'duel':
                    await interaction.response.send_message("Duelo não encontrado.", ephemeral=True)
                    return
            else:
                event = await db_provider.get_event(id)
                if not event:
                    await interaction.response.send_message("Evento não encontrado.", ephemeral=True)
                    return
            
            # Place bet
            bet_data = {
                'user_id': str(interaction.user.id),
                'type': tipo,
                'target_id': id,
                'amount': valor,
                'timestamp': datetime.now().isoformat()
            }
            
            await db_provider.store_event(
                f"BET#{interaction.user.id}#{id}",
                f"Aposta de {interaction.user.name}",
                f"Aposta de {valor} moedas em {tipo} {id}",
                'bet',
                str(interaction.channel_id),
                None,
                datetime.now(),
                datetime.now() + timedelta(days=7),
                [str(interaction.user.id)],
                bet_data
            )
            
            # Deduct coins
            player['coins'] -= valor
            await db_provider.update_player(str(interaction.user.id), **player)
            
            await interaction.response.send_message(f"Aposta de {valor} moedas realizada com sucesso!", ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error in slash_bet: {e}")
            await interaction.response.send_message("Ocorreu um erro ao processar sua aposta. Por favor, tente novamente.", ephemeral=True)
    
    @app_commands.command(name="minhas_apostas", description="Veja suas apostas ativas")
    async def slash_my_bets(self, interaction: discord.Interaction):
        """Show active bets for the user."""
        try:
            # Get user's bets
            bets = await db_provider.get_all_events()
            user_bets = [bet for bet in bets if bet.get('type') == 'bet' and str(interaction.user.id) in bet.get('participants', [])]
            
            if not user_bets:
                await interaction.response.send_message("Você não tem apostas ativas.", ephemeral=True)
                return
            
            # Create embed
            embed = discord.Embed(
                title="Suas Apostas Ativas",
                color=discord.Color.blue()
            )
            
            for bet in user_bets:
                bet_data = bet.get('data', {})
                embed.add_field(
                    name=f"Aposta em {bet_data.get('type', 'Desconhecido')} {bet_data.get('target_id', 'N/A')}",
                    value=f"Valor: {bet_data.get('amount', 0)} moedas",
                    inline=False
                )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error in slash_my_bets: {e}")
            await interaction.response.send_message("Ocorreu um erro ao buscar suas apostas. Por favor, tente novamente.", ephemeral=True)
    
    @app_commands.command(name="ranking_apostas", description="Veja o ranking de apostadores")
    async def slash_betting_ranking(self, interaction: discord.Interaction):
        """Show betting ranking."""
        try:
            # Get all bets
            bets = await db_provider.get_all_events()
            betting_stats = {}
            
            for bet in bets:
                if bet.get('type') == 'bet':
                    user_id = bet.get('participants', [None])[0]
                    if user_id:
                        if user_id not in betting_stats:
                            betting_stats[user_id] = {'total_bets': 0, 'total_amount': 0}
                        betting_stats[user_id]['total_bets'] += 1
                        betting_stats[user_id]['total_amount'] += bet.get('data', {}).get('amount', 0)
            
            # Sort by total amount
            sorted_stats = sorted(betting_stats.items(), key=lambda x: x[1]['total_amount'], reverse=True)
            
            # Create embed
            embed = discord.Embed(
                title="Ranking de Apostadores",
                color=discord.Color.gold()
            )
            
            for i, (user_id, stats) in enumerate(sorted_stats[:10], 1):
                user = await self.bot.fetch_user(int(user_id))
                embed.add_field(
                    name=f"{i}. {user.name}",
                    value=f"Total apostado: {stats['total_amount']} moedas\nApostas: {stats['total_bets']}",
                    inline=False
                )
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in slash_betting_ranking: {e}")
            await interaction.response.send_message("Ocorreu um erro ao buscar o ranking. Por favor, tente novamente.", ephemeral=True)
    
    async def handle_duel_completion(self, duel_id: str, winner_id: str):
        """Handle duel completion and distribute winnings."""
        try:
            # Get all bets for this duel
            bets = await db_provider.get_all_events()
            duel_bets = [bet for bet in bets if bet.get('type') == 'bet' and bet.get('data', {}).get('target_id') == duel_id]
            
            total_pot = sum(bet.get('data', {}).get('amount', 0) for bet in duel_bets)
            winning_bets = [bet for bet in duel_bets if bet.get('data', {}).get('user_id') == winner_id]
            
            if winning_bets:
                # Calculate winnings
                winning_amount = total_pot // len(winning_bets)
                
                # Distribute winnings
                for bet in winning_bets:
                    user_id = bet.get('data', {}).get('user_id')
                    player = await db_provider.get_player(user_id)
                    if player:
                        player['coins'] = player.get('coins', 0) + winning_amount
                        await db_provider.update_player(user_id, **player)
                        
                        # Notify user
                        try:
                            user = await self.bot.fetch_user(int(user_id))
                            await user.send(f"Você ganhou {winning_amount} moedas na aposta do duelo {duel_id}!")
                        except:
                            pass
            
            # Mark bets as completed
            for bet in duel_bets:
                bet['completed'] = True
                await db_provider.store_event(
                    bet['PK'].split('#')[1],
                    bet['name'],
                    bet['description'],
                    bet['type'],
                    bet['channel_id'],
                    bet['message_id'],
                    datetime.fromisoformat(bet['start_time']),
                    datetime.fromisoformat(bet['end_time']),
                    bet['participants'],
                    bet['data'],
                    True
                )
            
        except Exception as e:
            logger.error(f"Error in handle_duel_completion: {e}")
    
    async def handle_event_completion(self, event_id: str, winners: list):
        """Handle event completion and distribute winnings."""
        try:
            # Get all bets for this event
            bets = await db_provider.get_all_events()
            event_bets = [bet for bet in bets if bet.get('type') == 'bet' and bet.get('data', {}).get('target_id') == event_id]
            
            total_pot = sum(bet.get('data', {}).get('amount', 0) for bet in event_bets)
            winning_bets = [bet for bet in event_bets if bet.get('data', {}).get('user_id') in winners]
            
            if winning_bets:
                # Calculate winnings
                winning_amount = total_pot // len(winning_bets)
                
                # Distribute winnings
                for bet in winning_bets:
                    user_id = bet.get('data', {}).get('user_id')
                    player = await db_provider.get_player(user_id)
                    if player:
                        player['coins'] = player.get('coins', 0) + winning_amount
                        await db_provider.update_player(user_id, **player)
                        
                        # Notify user
                        try:
                            user = await self.bot.fetch_user(int(user_id))
                            await user.send(f"Você ganhou {winning_amount} moedas na aposta do evento {event_id}!")
                        except:
                            pass
            
            # Mark bets as completed
            for bet in event_bets:
                bet['completed'] = True
                await db_provider.store_event(
                    bet['PK'].split('#')[1],
                    bet['name'],
                    bet['description'],
                    bet['type'],
                    bet['channel_id'],
                    bet['message_id'],
                    datetime.fromisoformat(bet['start_time']),
                    datetime.fromisoformat(bet['end_time']),
                    bet['participants'],
                    bet['data'],
                    True
                )
            
        except Exception as e:
            logger.error(f"Error in handle_event_completion: {e}")

async def setup(bot: commands.Bot):
    """Set up the betting cog."""
    await bot.add_cog(BettingCog(bot))
