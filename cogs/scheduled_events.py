import discord
from discord.ext import commands, tasks
from discord import app_commands
import logging
import random
import asyncio
import json
import sqlite3
from datetime import datetime, timedelta, time
import pytz
from utils.database import get_player, update_player, get_club, get_all_clubs, get_top_players
from utils.embeds import create_basic_embed, create_event_embed, create_duel_embed, create_leaderboard_embed
from utils.game_mechanics import calculate_level_from_exp

logger = logging.getLogger('tokugawa_bot')

# Dictionary to store active events
ACTIVE_EVENTS = {
    # 'event_type': {
    #     'channel_id': channel_id,
    #     'message_id': message_id,
    #     'start_time': datetime,
    #     'end_time': datetime,
    #     'participants': [],
    #     'data': {}  # Additional event-specific data
    # }
}

# Dictionary to store Turf Wars teams
TURF_WARS_TEAMS = {
    # 'team_name': {
    #     'members': {
    #         'monarch': {'user_id': user_id, 'name': name},
    #         'queen': {'user_id': user_id, 'name': name},
    #         'jack': {'user_id': user_id, 'name': name},
    #         'healer': {'user_id': user_id, 'name': name}
    #     },
    #     'score': 0
    # }
}

# Dictionary to store player activity for intelligent timing
PLAYER_ACTIVITY = {
    # 'hour': {
    #     'count': 0,
    #     'last_updated': datetime
    # }
}

# Dictionary to store daily and weekly player progress
PLAYER_PROGRESS = {
    # 'daily': {
    #     user_id: {'exp_gained': 0, 'duels_won': 0, 'events_completed': 0}
    # },
    # 'weekly': {
    #     user_id: {'exp_gained': 0, 'duels_won': 0, 'events_completed': 0}
    # }
}

# Dictionary to store club reputation buffs
CLUB_BUFFS = {
    # club_id: {
    #     'type': 'exp',  # or 'tusd', 'attribute', etc.
    #     'value': 10,  # percentage or flat value
    #     'expires': datetime
    # }
}

class ScheduledEvents(commands.Cog):
    """Cog for scheduled and automated events."""

    def __init__(self, bot):
        self.bot = bot
        self.tournament_channel_id = None
        self.announcement_channel_id = None

        # Start the background tasks
        self.check_scheduled_events.start()
        self.daily_reset.start()
        self.weekly_reset.start()

        # Initialize player progress dictionaries
        PLAYER_PROGRESS['daily'] = {}
        PLAYER_PROGRESS['weekly'] = {}

        logger.info("ScheduledEvents cog initialized")

    def cog_unload(self):
        """Clean up when cog is unloaded."""
        self.check_scheduled_events.cancel()
        self.daily_reset.cancel()
        self.weekly_reset.cancel()

    @tasks.loop(minutes=1)
    async def check_scheduled_events(self):
        """Check for scheduled events every minute."""
        try:
            now = datetime.now()

            # Update player activity for the current hour
            current_hour = now.hour
            if current_hour not in PLAYER_ACTIVITY:
                PLAYER_ACTIVITY[current_hour] = {'count': 0, 'last_updated': now}

            # Check for Wednesday tournament (18:00)
            if now.weekday() == 2 and now.hour == 18 and now.minute == 0:
                await self.start_wednesday_tournament()

            # Check for Sunday Turf Wars (14:00)
            if now.weekday() == 6 and now.hour == 14 and now.minute == 0:
                await self.start_turf_wars()

            # Check for daily morning announcements (8:00)
            if now.hour == 8 and now.minute == 0:
                await self.send_daily_announcements()

            # Check for random events based on player activity
            await self.check_random_events()

            # Clean up expired events
            await self.cleanup_expired_events()

        except Exception as e:
            logger.error(f"Error in check_scheduled_events: {e}")

    @tasks.loop(time=time(hour=0, minute=0))  # Run at midnight
    async def daily_reset(self):
        """Reset daily player progress and generate new buffs."""
        try:
            # Reset daily player progress
            PLAYER_PROGRESS['daily'] = {}

            # Generate new club buffs
            await self.generate_club_buffs()

            logger.info("Daily reset completed")
        except Exception as e:
            logger.error(f"Error in daily_reset: {e}")

    async def generate_club_buffs(self):
        """Generate random buffs for clubs based on reputation."""
        try:
            # Clear expired buffs
            expired_buffs = []
            now = datetime.now()
            for club_id, buff in CLUB_BUFFS.items():
                if buff['expires'] < now:
                    expired_buffs.append(club_id)

            for club_id in expired_buffs:
                CLUB_BUFFS.pop(club_id, None)

            # Get all clubs
            clubs = get_all_clubs()

            # Select clubs for buffs based on reputation
            if clubs:
                # Create weighted list based on reputation
                weighted_clubs = []
                for club in clubs:
                    # Add club to weighted list based on reputation
                    weight = max(1, club['reputation'] // 20)
                    weighted_clubs.extend([club] * weight)

                # Select 1-2 clubs for buffs
                if weighted_clubs:
                    num_buffs = min(2, len(weighted_clubs))
                    selected_clubs = random.sample(weighted_clubs, num_buffs)

                    # Ensure we don't select the same club twice
                    unique_clubs = []
                    seen_club_ids = set()
                    for club in selected_clubs:
                        if club['club_id'] not in seen_club_ids:
                            unique_clubs.append(club)
                            seen_club_ids.add(club['club_id'])

                    # Create buffs for selected clubs
                    for club in unique_clubs:
                        buff_types = ['exp', 'tusd', 'attribute']
                        buff_type = random.choice(buff_types)
                        buff_value = random.randint(5, 15)  # 5-15% bonus

                        CLUB_BUFFS[club['club_id']] = {
                            'type': buff_type,
                            'value': buff_value,
                            'expires': datetime.now() + timedelta(days=1)
                        }

                        logger.info(f"Generated {buff_type} buff of {buff_value}% for club {club['name']}")

            logger.info(f"Club buffs generated. Active buffs: {len(CLUB_BUFFS)}")
        except Exception as e:
            logger.error(f"Error generating club buffs: {e}")

    @tasks.loop(time=time(hour=0, minute=0))  # Run at midnight on Monday
    async def weekly_reset(self):
        """Reset weekly player progress."""
        try:
            # Only reset on Monday
            if datetime.now().weekday() == 0:
                PLAYER_PROGRESS['weekly'] = {}
                logger.info("Weekly reset completed")
        except Exception as e:
            logger.error(f"Error in weekly_reset: {e}")

    @check_scheduled_events.before_loop
    @daily_reset.before_loop
    @weekly_reset.before_loop
    async def before_tasks(self):
        """Wait until the bot is ready before starting tasks."""
        await self.bot.wait_until_ready()

    async def start_wednesday_tournament(self):
        """Start the Wednesday tournament event."""
        try:
            if not self.tournament_channel_id:
                # Try to find a general or announcements channel
                for guild in self.bot.guilds:
                    general_channel = discord.utils.get(guild.text_channels, name="geral") or \
                                     discord.utils.get(guild.text_channels, name="general") or \
                                     discord.utils.get(guild.text_channels, name="anúncios") or \
                                     discord.utils.get(guild.text_channels, name="announcements")
                    if general_channel:
                        self.tournament_channel_id = general_channel.id
                        break

            if not self.tournament_channel_id:
                logger.error("No tournament channel set and couldn't find a suitable channel")
                return

            channel = self.bot.get_channel(self.tournament_channel_id)
            if not channel:
                logger.error(f"Could not find tournament channel with ID {self.tournament_channel_id}")
                return

            # Create tournament embed
            embed = create_basic_embed(
                title="🏆 Torneio Semanal da Academia Tokugawa 🏆",
                description=(
                    "O Conselho Estudantil está organizando um torneio semanal!\n\n"
                    "**Regras:**\n"
                    "- Inscrições abertas por 30 minutos\n"
                    "- Combates eliminatórios entre os participantes\n"
                    "- O vencedor receberá EXP, TUSD e um troféu colecionável!\n\n"
                    "Para participar, reaja a esta mensagem com 🏆"
                ),
                color=0xFFD700  # Gold
            )

            # Send the announcement
            message = await channel.send(
                content="@everyone O Torneio Semanal da Academia Tokugawa está começando!",
                embed=embed
            )

            # Add reaction for signup
            await message.add_reaction("🏆")

            # Store event data
            ACTIVE_EVENTS['wednesday_tournament'] = {
                'channel_id': channel.id,
                'message_id': message.id,
                'start_time': datetime.now(),
                'end_time': datetime.now() + timedelta(minutes=30),
                'participants': [],
                'data': {'signup_phase': True, 'matches': []}
            }

            # Schedule tournament start after 30 minutes
            self.bot.loop.create_task(self.run_tournament_after_signup())

            logger.info("Wednesday tournament announced")
        except Exception as e:
            logger.error(f"Error starting Wednesday tournament: {e}")

    async def run_tournament_after_signup(self):
        """Run the tournament after the signup period ends."""
        try:
            # Wait for 30 minutes
            await asyncio.sleep(30 * 60)

            # Get tournament data
            tournament = ACTIVE_EVENTS.get('wednesday_tournament')
            if not tournament:
                logger.error("Tournament data not found")
                return

            channel = self.bot.get_channel(tournament['channel_id'])
            if not channel:
                logger.error(f"Could not find tournament channel with ID {tournament['channel_id']}")
                return

            # Get the message with reactions
            try:
                message = await channel.fetch_message(tournament['message_id'])
                reaction = discord.utils.get(message.reactions, emoji="🏆")

                # Get participants
                participants = []
                async for user in reaction.users():
                    if not user.bot:
                        player = get_player(user.id)
                        if player:
                            participants.append({
                                'user_id': user.id,
                                'name': player['name'],
                                'level': player['level'],
                                'eliminated': False
                            })

                tournament['participants'] = participants
                tournament['data']['signup_phase'] = False

                # Check if we have enough participants
                if len(participants) < 2:
                    await channel.send("Não há participantes suficientes para o torneio. Evento cancelado.")
                    ACTIVE_EVENTS.pop('wednesday_tournament', None)
                    return

                # Announce participants
                participant_list = "\n".join([f"- {p['name']} (Nível {p['level']})" for p in participants])
                await channel.send(
                    embed=create_basic_embed(
                        title="Participantes do Torneio",
                        description=f"**{len(participants)}** estudantes participarão do torneio:\n\n{participant_list}",
                        color=0xFFD700
                    )
                )

                # Run tournament rounds
                await self.run_tournament_rounds(channel, tournament)

            except discord.NotFound:
                logger.error(f"Tournament message with ID {tournament['message_id']} not found")
                ACTIVE_EVENTS.pop('wednesday_tournament', None)

        except Exception as e:
            logger.error(f"Error running tournament after signup: {e}")

    async def run_tournament_rounds(self, channel, tournament):
        """Run the tournament rounds."""
        try:
            participants = tournament['participants']

            # Shuffle participants
            random.shuffle(participants)

            # Calculate number of rounds needed
            import math
            num_rounds = math.ceil(math.log2(len(participants)))

            await channel.send(
                embed=create_basic_embed(
                    title="Torneio Iniciado!",
                    description=f"O torneio terá {num_rounds} rodadas de combates eliminatórios.",
                    color=0xFFD700
                )
            )

            # Run each round
            for round_num in range(1, num_rounds + 1):
                await channel.send(f"**Rodada {round_num}**")

                # Create matches for this round
                active_participants = [p for p in participants if not p['eliminated']]
                matches = []

                # If odd number of participants, one gets a bye
                if len(active_participants) % 2 != 0 and len(active_participants) > 1:
                    bye_participant = random.choice(active_participants)
                    active_participants.remove(bye_participant)
                    await channel.send(f"{bye_participant['name']} recebeu um bye nesta rodada!")

                # Create matches
                for i in range(0, len(active_participants), 2):
                    if i + 1 < len(active_participants):
                        matches.append((active_participants[i], active_participants[i + 1]))

                # Run matches
                for match_num, (player1, player2) in enumerate(matches, 1):
                    await channel.send(f"**Combate {match_num}:** {player1['name']} vs {player2['name']}")

                    # Simulate combat (random winner for simplicity)
                    p1 = get_player(player1['user_id'])
                    p2 = get_player(player2['user_id'])

                    if not p1 or not p2:
                        logger.error(f"Could not find player data for match {match_num}")
                        continue

                    # Determine winner (random with level weighting)
                    p1_weight = p1['level'] * random.uniform(0.8, 1.2)
                    p2_weight = p2['level'] * random.uniform(0.8, 1.2)

                    if p1_weight > p2_weight:
                        winner, loser = player1, player2
                        winner_full, loser_full = p1, p2
                    else:
                        winner, loser = player2, player1
                        winner_full, loser_full = p2, p1

                    # Mark loser as eliminated
                    for p in participants:
                        if p['user_id'] == loser['user_id']:
                            p['eliminated'] = True

                    # Calculate rewards
                    exp_reward = 30 + (winner_full['level'] * 2)
                    tusd_reward = 20 + winner_full['level']

                    # Update winner's stats
                    update_player(
                        winner['user_id'],
                        exp=winner_full['exp'] + exp_reward,
                        tusd=winner_full['tusd'] + tusd_reward
                    )

                    # Update loser's stats (consolation prize)
                    update_player(
                        loser['user_id'],
                        exp=loser_full['exp'] + (exp_reward // 2)
                    )

                    # Track progress for rankings
                    if winner['user_id'] not in PLAYER_PROGRESS['daily']:
                        PLAYER_PROGRESS['daily'][winner['user_id']] = {'exp_gained': 0, 'duels_won': 0, 'events_completed': 0}
                    if winner['user_id'] not in PLAYER_PROGRESS['weekly']:
                        PLAYER_PROGRESS['weekly'][winner['user_id']] = {'exp_gained': 0, 'duels_won': 0, 'events_completed': 0}

                    PLAYER_PROGRESS['daily'][winner['user_id']]['exp_gained'] += exp_reward
                    PLAYER_PROGRESS['daily'][winner['user_id']]['duels_won'] += 1
                    PLAYER_PROGRESS['weekly'][winner['user_id']]['exp_gained'] += exp_reward
                    PLAYER_PROGRESS['weekly'][winner['user_id']]['duels_won'] += 1

                    # Announce result
                    await channel.send(
                        embed=create_basic_embed(
                            title=f"Resultado: {winner['name']} venceu!",
                            description=(
                                f"{winner['name']} derrotou {loser['name']} e avança para a próxima rodada!\n\n"
                                f"**Recompensas:**\n"
                                f"{winner['name']}: +{exp_reward} EXP, +{tusd_reward} TUSD\n"
                                f"{loser['name']}: +{exp_reward // 2} EXP (prêmio de consolação)"
                            ),
                            color=0xFFD700
                        )
                    )

                    # Add a small delay between matches
                    await asyncio.sleep(2)

                # Check if we have a winner
                active_participants = [p for p in participants if not p['eliminated']]
                if len(active_participants) == 1:
                    # We have a tournament winner
                    winner = active_participants[0]
                    winner_full = get_player(winner['user_id'])

                    # Special final reward
                    final_exp_reward = 100 + (winner_full['level'] * 5)
                    final_tusd_reward = 50 + (winner_full['level'] * 2)

                    # Update winner's inventory with trophy
                    trophy = {
                        "name": "Troféu do Torneio Semanal",
                        "description": f"Conquistado em {datetime.now().strftime('%d/%m/%Y')}",
                        "type": "collectible",
                        "rarity": "rare",
                        "effects": {}
                    }

                    # Add trophy to inventory
                    inventory = winner_full.get('inventory', {})
                    trophy_id = f"trophy_{datetime.now().strftime('%Y%m%d')}"
                    inventory[trophy_id] = trophy

                    # Update player
                    update_player(
                        winner['user_id'],
                        exp=winner_full['exp'] + final_exp_reward,
                        tusd=winner_full['tusd'] + final_tusd_reward,
                        inventory=json.dumps(inventory)
                    )

                    # Track progress for rankings
                    PLAYER_PROGRESS['daily'][winner['user_id']]['exp_gained'] += final_exp_reward
                    PLAYER_PROGRESS['daily'][winner['user_id']]['events_completed'] += 1
                    PLAYER_PROGRESS['weekly'][winner['user_id']]['exp_gained'] += final_exp_reward
                    PLAYER_PROGRESS['weekly'][winner['user_id']]['events_completed'] += 1

                    # Announce tournament winner
                    await channel.send(
                        embed=create_basic_embed(
                            title="🏆 Campeão do Torneio! 🏆",
                            description=(
                                f"**{winner['name']}** é o grande campeão do Torneio Semanal da Academia Tokugawa!\n\n"
                                f"**Recompensa Final:**\n"
                                f"- +{final_exp_reward} EXP\n"
                                f"- +{final_tusd_reward} TUSD\n"
                                f"- Troféu Colecionável: {trophy['name']}"
                            ),
                            color=0xFFD700
                        )
                    )

                    # End tournament
                    ACTIVE_EVENTS.pop('wednesday_tournament', None)
                    break

                # Add delay between rounds
                await asyncio.sleep(5)

        except Exception as e:
            logger.error(f"Error running tournament rounds: {e}")

    async def start_turf_wars(self):
        """Start the Sunday Turf Wars event."""
        try:
            if not self.tournament_channel_id:
                # Try to find a general or announcements channel
                for guild in self.bot.guilds:
                    general_channel = discord.utils.get(guild.text_channels, name="geral") or \
                                     discord.utils.get(guild.text_channels, name="general") or \
                                     discord.utils.get(guild.text_channels, name="anúncios") or \
                                     discord.utils.get(guild.text_channels, name="announcements")
                    if general_channel:
                        self.tournament_channel_id = general_channel.id
                        break

            if not self.tournament_channel_id:
                logger.error("No tournament channel set and couldn't find a suitable channel")
                return

            channel = self.bot.get_channel(self.tournament_channel_id)
            if not channel:
                logger.error(f"Could not find tournament channel with ID {self.tournament_channel_id}")
                return

            # Reset teams
            TURF_WARS_TEAMS.clear()

            # Create Turf Wars embed
            embed = create_basic_embed(
                title="⚔️ Turf Wars Dominical ⚔️",
                description=(
                    "As Turf Wars começaram! Formem times de 4 jogadores para competir pelo domínio da Academia!\n\n"
                    "**Regras:**\n"
                    "- Cada time deve ter 4 membros com papéis específicos:\n"
                    "  • **Monarca** - Líder estratégico que decide quem luta em cada batalha\n"
                    "  • **Rainha** - Principal força defensiva\n"
                    "  • **Valete** - Dano secundário e adaptável\n"
                    "  • **Healer** - Suporte que pode curar um membro por batalha\n\n"
                    "- Inscrições abertas até às 14:30\n"
                    "- Batalhas começam às 14:30 e terminam às 16:00\n\n"
                    "Para criar um time, use o comando `/turfwars criar [nome_do_time]`\n"
                    "Para entrar em um time, use `/turfwars entrar [nome_do_time] [papel]`"
                ),
                color=0xFF5733  # Orange-red
            )

            # Send the announcement
            message = await channel.send(
                content="@everyone As Turf Wars Dominicais estão começando!",
                embed=embed
            )

            # Store event data
            ACTIVE_EVENTS['turf_wars'] = {
                'channel_id': channel.id,
                'message_id': message.id,
                'start_time': datetime.now(),
                'end_time': datetime.now() + timedelta(minutes=150),  # 2.5 hours total
                'participants': [],
                'data': {
                    'signup_phase': True,
                    'battle_phase': False,
                    'teams': {}
                }
            }

            # Schedule battle phase start after 30 minutes
            self.bot.loop.create_task(self.start_turf_wars_battles())

            logger.info("Sunday Turf Wars announced")
        except Exception as e:
            logger.error(f"Error starting Sunday Turf Wars: {e}")

    async def start_turf_wars_battles(self):
        """Start the battle phase of Turf Wars after signup period."""
        try:
            # Wait for 30 minutes
            await asyncio.sleep(30 * 60)

            # Get Turf Wars data
            turf_wars = ACTIVE_EVENTS.get('turf_wars')
            if not turf_wars:
                logger.error("Turf Wars data not found")
                return

            channel = self.bot.get_channel(turf_wars['channel_id'])
            if not channel:
                logger.error(f"Could not find Turf Wars channel with ID {turf_wars['channel_id']}")
                return

            # Update event status
            turf_wars['data']['signup_phase'] = False
            turf_wars['data']['battle_phase'] = True

            # Get teams
            teams = list(TURF_WARS_TEAMS.items())

            # Check if we have enough teams
            if len(teams) < 2:
                await channel.send("Não há times suficientes para as Turf Wars. Evento cancelado.")
                ACTIVE_EVENTS.pop('turf_wars', None)
                return

            # Announce teams
            team_list = ""
            for team_name, team_data in teams:
                members = team_data['members']
                team_list += f"**Time {team_name}**\n"
                for role, member in members.items():
                    if member:
                        team_list += f"- {role.capitalize()}: {member['name']}\n"
                team_list += "\n"

            await channel.send(
                embed=create_basic_embed(
                    title="Times das Turf Wars",
                    description=f"**{len(teams)}** times participarão das Turf Wars:\n\n{team_list}",
                    color=0xFF5733
                )
            )

            # Run Turf Wars battles
            await self.run_turf_wars_battles(channel, turf_wars)

        except Exception as e:
            logger.error(f"Error starting Turf Wars battles: {e}")

    async def run_turf_wars_battles(self, channel, turf_wars):
        """Run the Turf Wars battles."""
        try:
            teams = list(TURF_WARS_TEAMS.items())

            await channel.send(
                embed=create_basic_embed(
                    title="⚔️ Fase de Batalhas das Turf Wars ⚔️",
                    description=(
                        "As batalhas das Turf Wars começaram!\n\n"
                        "Cada time enfrentará os outros em uma série de duelos 1v1.\n"
                        "O Monarca de cada time decidirá quem lutará em cada batalha."
                    ),
                    color=0xFF5733
                )
            )

            # Create all possible team matchups
            import itertools
            matchups = list(itertools.combinations(teams, 2))

            # Shuffle matchups for variety
            random.shuffle(matchups)

            # Run each matchup
            for (team1_name, team1_data), (team2_name, team2_data) in matchups:
                await channel.send(
                    embed=create_basic_embed(
                        title=f"🏆 {team1_name} vs {team2_name} 🏆",
                        description=f"Preparem-se para a batalha entre os times {team1_name} e {team2_name}!",
                        color=0xFF5733
                    )
                )

                # Get monarchs
                monarch1 = team1_data['members'].get('monarch')
                monarch2 = team2_data['members'].get('monarch')

                if not monarch1 or not monarch2:
                    await channel.send("Um dos times não tem um Monarca! Esta batalha será cancelada.")
                    continue

                # Simulate monarch decisions
                # For simplicity, we'll just randomly select team members for each battle
                team1_fighters = [member for role, member in team1_data['members'].items() if member]
                team2_fighters = [member for role, member in team2_data['members'].items() if member]

                if not team1_fighters or not team2_fighters:
                    await channel.send("Um dos times não tem lutadores! Esta batalha será cancelada.")
                    continue

                # Determine number of battles (minimum of team sizes)
                num_battles = min(len(team1_fighters), len(team2_fighters))

                # Track team scores for this matchup
                team1_score = 0
                team2_score = 0

                # Run battles
                for battle_num in range(1, num_battles + 1):
                    # Monarchs select fighters
                    fighter1 = random.choice(team1_fighters)
                    fighter2 = random.choice(team2_fighters)

                    await channel.send(
                        embed=create_basic_embed(
                            title=f"Batalha {battle_num}",
                            description=(
                                f"O Monarca de {team1_name} escolheu **{fighter1['name']}**!\n"
                                f"O Monarca de {team2_name} escolheu **{fighter2['name']}**!"
                            ),
                            color=0xFF5733
                        )
                    )

                    # Simulate battle
                    p1 = get_player(fighter1['user_id'])
                    p2 = get_player(fighter2['user_id'])

                    if not p1 or not p2:
                        await channel.send("Dados de jogador não encontrados! Esta batalha será cancelada.")
                        continue

                    # Determine winner (random with level weighting)
                    p1_weight = p1['level'] * random.uniform(0.8, 1.2)
                    p2_weight = p2['level'] * random.uniform(0.8, 1.2)

                    # Apply role bonuses
                    for role, member in team1_data['members'].items():
                        if member and member['user_id'] == fighter1['user_id']:
                            if role == 'queen':
                                p1_weight *= 1.2  # Queen gets combat bonus
                            elif role == 'jack':
                                p1_weight *= 1.1  # Jack gets smaller combat bonus

                    for role, member in team2_data['members'].items():
                        if member and member['user_id'] == fighter2['user_id']:
                            if role == 'queen':
                                p2_weight *= 1.2  # Queen gets combat bonus
                            elif role == 'jack':
                                p2_weight *= 1.1  # Jack gets smaller combat bonus

                    # Determine winner
                    if p1_weight > p2_weight:
                        winner, loser = fighter1, fighter2
                        winner_team, loser_team = team1_name, team2_name
                        team1_score += 1
                    else:
                        winner, loser = fighter2, fighter1
                        winner_team, loser_team = team2_name, team1_name
                        team2_score += 1

                    # Calculate rewards
                    exp_reward = 20 + (battle_num * 5)

                    # Update winner's stats
                    winner_full = get_player(winner['user_id'])
                    update_player(
                        winner['user_id'],
                        exp=winner_full['exp'] + exp_reward
                    )

                    # Track progress for rankings
                    if winner['user_id'] not in PLAYER_PROGRESS['daily']:
                        PLAYER_PROGRESS['daily'][winner['user_id']] = {'exp_gained': 0, 'duels_won': 0, 'events_completed': 0}
                    if winner['user_id'] not in PLAYER_PROGRESS['weekly']:
                        PLAYER_PROGRESS['weekly'][winner['user_id']] = {'exp_gained': 0, 'duels_won': 0, 'events_completed': 0}

                    PLAYER_PROGRESS['daily'][winner['user_id']]['exp_gained'] += exp_reward
                    PLAYER_PROGRESS['daily'][winner['user_id']]['duels_won'] += 1
                    PLAYER_PROGRESS['weekly'][winner['user_id']]['exp_gained'] += exp_reward
                    PLAYER_PROGRESS['weekly'][winner['user_id']]['duels_won'] += 1

                    # Announce result
                    await channel.send(
                        embed=create_basic_embed(
                            title=f"{winner['name']} venceu pelo time {winner_team}!",
                            description=(
                                f"**{winner['name']}** derrotou **{loser['name']}** e marca um ponto para o time {winner_team}!\n\n"
                                f"**Recompensa:**\n"
                                f"{winner['name']}: +{exp_reward} EXP"
                            ),
                            color=0xFF5733
                        )
                    )

                    # Add a small delay between battles
                    await asyncio.sleep(2)

                # Announce matchup result
                if team1_score > team2_score:
                    winner_team, loser_team = team1_name, team2_name
                    winner_score, loser_score = team1_score, team2_score
                else:
                    winner_team, loser_team = team2_name, team1_name
                    winner_score, loser_score = team2_score, team1_score

                await channel.send(
                    embed=create_basic_embed(
                        title=f"Resultado: {winner_team} venceu!",
                        description=(
                            f"O time **{winner_team}** venceu o confronto contra **{loser_team}** por {winner_score} a {loser_score}!\n\n"
                            f"Cada membro do time {winner_team} recebe +10 EXP bônus!"
                        ),
                        color=0xFF5733
                    )
                )

                # Award team bonus
                if winner_team == team1_name:
                    for role, member in team1_data['members'].items():
                        if member:
                            player = get_player(member['user_id'])
                            if player:
                                update_player(member['user_id'], exp=player['exp'] + 10)
                    TURF_WARS_TEAMS[team1_name]['score'] += 1
                else:
                    for role, member in team2_data['members'].items():
                        if member:
                            player = get_player(member['user_id'])
                            if player:
                                update_player(member['user_id'], exp=player['exp'] + 10)
                    TURF_WARS_TEAMS[team2_name]['score'] += 1

                # Add delay between matchups
                await asyncio.sleep(5)

            # Determine overall winner
            teams_sorted = sorted(TURF_WARS_TEAMS.items(), key=lambda x: x[1]['score'], reverse=True)
            overall_winner = teams_sorted[0][0]

            # Calculate club reputation bonus
            # Find which club has the most members in the winning team
            club_counts = {}
            for role, member in TURF_WARS_TEAMS[overall_winner]['members'].items():
                if member:
                    player = get_player(member['user_id'])
                    if player and player.get('club_id'):
                        club_id = player['club_id']
                        club_counts[club_id] = club_counts.get(club_id, 0) + 1

            winning_club_id = max(club_counts.items(), key=lambda x: x[1])[0] if club_counts else None

            # Award final rewards
            for role, member in TURF_WARS_TEAMS[overall_winner]['members'].items():
                if member:
                    player = get_player(member['user_id'])
                    if player:
                        # Award XP based on role
                        role_multipliers = {
                            'monarch': 1.5,
                            'queen': 1.3,
                            'jack': 1.2,
                            'healer': 1.1
                        }
                        multiplier = role_multipliers.get(role, 1.0)
                        exp_reward = int(50 * multiplier)
                        tusd_reward = int(25 * multiplier)

                        update_player(
                            member['user_id'],
                            exp=player['exp'] + exp_reward,
                            tusd=player['tusd'] + tusd_reward
                        )

                        # Track progress for rankings
                        if member['user_id'] not in PLAYER_PROGRESS['daily']:
                            PLAYER_PROGRESS['daily'][member['user_id']] = {'exp_gained': 0, 'duels_won': 0, 'events_completed': 0}
                        if member['user_id'] not in PLAYER_PROGRESS['weekly']:
                            PLAYER_PROGRESS['weekly'][member['user_id']] = {'exp_gained': 0, 'duels_won': 0, 'events_completed': 0}

                        PLAYER_PROGRESS['daily'][member['user_id']]['exp_gained'] += exp_reward
                        PLAYER_PROGRESS['daily'][member['user_id']]['events_completed'] += 1
                        PLAYER_PROGRESS['weekly'][member['user_id']]['exp_gained'] += exp_reward
                        PLAYER_PROGRESS['weekly'][member['user_id']]['events_completed'] += 1

            # Increase winning club reputation if applicable
            if winning_club_id:
                club = get_club(winning_club_id)
                if club:
                    # Update club reputation
                    conn = sqlite3.connect('data/tokugawa.db')
                    cursor = conn.cursor()
                    cursor.execute(
                        "UPDATE clubs SET reputation = reputation + 50 WHERE club_id = ?",
                        (winning_club_id,)
                    )
                    conn.commit()
                    conn.close()

                    # Add buff for winning club
                    CLUB_BUFFS[winning_club_id] = {
                        'type': 'exp',
                        'value': 10,  # 10% EXP bonus
                        'expires': datetime.now() + timedelta(days=1)
                    }

            # Announce overall winner
            await channel.send(
                embed=create_basic_embed(
                    title="🏆 Campeão das Turf Wars! 🏆",
                    description=(
                        f"O time **{overall_winner}** é o grande campeão das Turf Wars Dominicais!\n\n"
                        f"**Recompensas:**\n"
                        f"- Cada membro recebeu EXP e TUSD bônus\n"
                        f"- O time dominará a Academia por esta semana!\n"
                        + (f"- O clube {get_club(winning_club_id)['name']} ganhou +50 de Reputação e terá +10% de EXP por 24 horas!" if winning_club_id else "")
                    ),
                    color=0xFF5733
                )
            )

            # End Turf Wars
            ACTIVE_EVENTS.pop('turf_wars', None)

        except Exception as e:
            logger.error(f"Error running Turf Wars battles: {e}")

    async def send_daily_announcements(self):
        """Send daily announcements, rankings, and news."""
        try:
            if not self.announcement_channel_id:
                # Try to find a general or announcements channel
                for guild in self.bot.guilds:
                    general_channel = discord.utils.get(guild.text_channels, name="geral") or \
                                     discord.utils.get(guild.text_channels, name="general") or \
                                     discord.utils.get(guild.text_channels, name="anúncios") or \
                                     discord.utils.get(guild.text_channels, name="announcements")
                    if general_channel:
                        self.announcement_channel_id = general_channel.id
                        break

            if not self.announcement_channel_id:
                logger.error("No announcement channel set and couldn't find a suitable channel")
                return

            channel = self.bot.get_channel(self.announcement_channel_id)
            if not channel:
                logger.error(f"Could not find announcement channel with ID {self.announcement_channel_id}")
                return

            # Get daily rankings
            daily_players = []
            for user_id, progress in PLAYER_PROGRESS['daily'].items():
                player = get_player(user_id)
                if player:
                    daily_players.append({
                        'user_id': user_id,
                        'name': player['name'],
                        'level': player['level'],
                        'club_id': player.get('club_id'),
                        'exp_gained': progress['exp_gained'],
                        'duels_won': progress['duels_won'],
                        'events_completed': progress['events_completed']
                    })

            # Sort by exp gained
            daily_players.sort(key=lambda x: x['exp_gained'], reverse=True)

            # Get top 5 players
            top_daily = daily_players[:5]

            # Create daily ranking embed
            if top_daily:
                ranking_text = ""
                for i, player in enumerate(top_daily, 1):
                    medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                    club = get_club(player['club_id']) if player.get('club_id') else None
                    club_name = club['name'] if club else "Sem clube"
                    ranking_text += f"{medal} **{player['name']}** (Nível {player['level']}) - {club_name}\n"
                    ranking_text += f"   EXP: +{player['exp_gained']} | Duelos: {player['duels_won']} | Eventos: {player['events_completed']}\n\n"

                daily_embed = create_basic_embed(
                    title="📊 Ranking Diário da Academia Tokugawa 📊",
                    description=ranking_text or "Nenhuma atividade registrada ontem.",
                    color=0x00FF00  # Green
                )
            else:
                daily_embed = create_basic_embed(
                    title="📊 Ranking Diário da Academia Tokugawa 📊",
                    description="Nenhuma atividade registrada ontem.",
                    color=0x00FF00  # Green
                )

            # Generate daily news
            news_embed = await self.generate_daily_news()

            # Send morning message
            greeting_messages = [
                "Bom dia, estudantes da Academia Tokugawa! Preparem-se para mais um dia épico!",
                "Amanheceu na Academia Tokugawa! Que desafios nos aguardam hoje?",
                "O sol nasce sobre a Academia Tokugawa! Quem se destacará hoje?",
                "Despertem, futuros heróis da Academia Tokugawa! Um novo dia de aventuras começa!",
                "O Conselho Estudantil saúda todos os estudantes nesta bela manhã!"
            ]

            await channel.send(
                content=random.choice(greeting_messages),
                embeds=[daily_embed, news_embed]
            )

            logger.info("Daily announcements sent")
        except Exception as e:
            logger.error(f"Error sending daily announcements: {e}")

    async def generate_daily_news(self):
        """Generate daily news and buffs."""
        try:
            # Get all clubs
            clubs = get_all_clubs()

            # Select a random club for today's buff
            if clubs:
                # Prioritize clubs with higher reputation
                weighted_clubs = []
                for club in clubs:
                    # Add club to weighted list based on reputation
                    weight = max(1, club['reputation'] // 20)
                    weighted_clubs.extend([club] * weight)

                if weighted_clubs:
                    featured_club = random.choice(weighted_clubs)

                    # Create a buff for this club
                    buff_types = ['exp', 'tusd', 'attribute']
                    buff_type = random.choice(buff_types)
                    buff_value = random.randint(5, 15)  # 5-15% bonus

                    CLUB_BUFFS[featured_club['club_id']] = {
                        'type': buff_type,
                        'value': buff_value,
                        'expires': datetime.now() + timedelta(days=1)
                    }

                    buff_description = ""
                    if buff_type == 'exp':
                        buff_description = f"+{buff_value}% de EXP em treinamentos"
                    elif buff_type == 'tusd':
                        buff_description = f"+{buff_value}% de TUSD em atividades"
                    elif buff_type == 'attribute':
                        buff_description = f"+{buff_value}% de chance de aumentar atributos"

                    # Generate news content
                    news_items = [
                        f"O clube **{featured_club['name']}** ganhou destaque hoje! Todos os membros recebem {buff_description}.",
                        f"O reitor da academia enviou sua benção aos **{featured_club['name']}** por sua performance incrível!",
                        f"Hoje é o dia do **{featured_club['name']}**! Todos os membros recebem {buff_description}.",
                        f"Os **{featured_club['name']}** demonstraram grande valor e recebem {buff_description} hoje!"
                    ]
                else:
                    news_items = [
                        "Nenhum clube se destacou o suficiente para receber bônus hoje.",
                        "O Conselho Estudantil está avaliando o desempenho dos clubes para futuros benefícios.",
                        "Hoje é um dia tranquilo na Academia Tokugawa."
                    ]
            else:
                news_items = [
                    "Nenhum clube ativo foi encontrado na Academia Tokugawa.",
                    "O Conselho Estudantil está recrutando novos membros para os clubes!",
                    "Hoje é um dia tranquilo na Academia Tokugawa."
                ]

            # Add random news items
            random_news = [
                "Um novo Vilão misterioso foi avistado próximo à Academia! Fiquem alertas!",
                "O Festival dos Poderes está se aproximando! Preparem-se para demonstrar suas habilidades!",
                "Rumores indicam que um artefato poderoso foi descoberto na biblioteca da Academia.",
                "O Conselho Estudantil anunciou melhorias nas instalações de treinamento!",
                "Uma competição de talentos será realizada em breve! Comecem a praticar!",
                "Visitantes de uma academia rival foram vistos observando nossos estudantes.",
                "Uma nova técnica secreta foi descoberta por um dos professores!",
                "O diretor da Academia está planejando um anúncio importante para esta semana."
            ]

            # Add 1-2 random news items
            for _ in range(random.randint(1, 2)):
                news_items.append(random.choice(random_news))
                random_news.remove(news_items[-1])  # Prevent duplicates

            # Create news embed
            news_text = "\n\n".join([f"• {item}" for item in news_items])

            news_embed = create_basic_embed(
                title="📰 Notícias do Conselho Estudantil 📰",
                description=news_text,
                color=0x4169E1  # Royal Blue
            )

            return news_embed
        except Exception as e:
            logger.error(f"Error generating daily news: {e}")
            return create_basic_embed(
                title="📰 Notícias do Conselho Estudantil 📰",
                description="O Conselho Estudantil está ocupado hoje. Notícias serão divulgadas em breve.",
                color=0x4169E1
            )

    async def check_random_events(self):
        """Check if a random event should be triggered."""
        try:
            # Only trigger random events if we have active players
            now = datetime.now()
            current_hour = now.hour

            # Update player activity for the current hour
            if current_hour not in PLAYER_ACTIVITY:
                PLAYER_ACTIVITY[current_hour] = {'count': 0, 'last_updated': now}

            # Get active guilds
            active_guilds = self.bot.guilds
            if not active_guilds:
                return

            # Determine if we should trigger an event based on activity
            # Higher chance during peak hours
            base_chance = 0.05  # 5% base chance per minute

            # Adjust chance based on hour (higher during evening, lower during night)
            hour_multiplier = 1.0
            if 17 <= current_hour <= 22:  # Evening hours
                hour_multiplier = 2.0
            elif 23 <= current_hour or current_hour <= 6:  # Night hours
                hour_multiplier = 0.5

            # Adjust chance based on recent activity
            activity_count = PLAYER_ACTIVITY.get(current_hour, {}).get('count', 0)
            activity_multiplier = min(3.0, max(0.5, 1.0 + (activity_count / 10)))

            final_chance = base_chance * hour_multiplier * activity_multiplier

            # Roll for event
            if random.random() < final_chance:
                # Choose a random event type
                event_types = ['minion', 'villain', 'collectible']
                weights = [0.6, 0.3, 0.1]  # 60% minion, 30% villain, 10% collectible
                event_type = random.choices(event_types, weights=weights, k=1)[0]

                # Choose a random guild and channel
                guild = random.choice(active_guilds)

                # Find suitable channels (text channels that are not announcement channels)
                suitable_channels = [
                    channel for channel in guild.text_channels
                    if channel.permissions_for(guild.me).send_messages
                    and not any(name in channel.name for name in ['anúncio', 'announcement', 'rule', 'regra', 'bem-vindo', 'welcome'])
                ]

                if not suitable_channels:
                    return

                channel = random.choice(suitable_channels)

                # Trigger the appropriate event
                if event_type == 'minion':
                    await self.trigger_minion_event(channel)
                elif event_type == 'villain':
                    await self.trigger_villain_event(channel)
                elif event_type == 'collectible':
                    await self.trigger_collectible_event(channel)

        except Exception as e:
            logger.error(f"Error checking random events: {e}")

    async def trigger_minion_event(self, channel):
        """Trigger a random minion appearance event."""
        try:
            # Create minion event
            minion_types = ['Slime', 'Goblin', 'Esqueleto', 'Zumbi', 'Fantasma', 'Kobold', 'Imp']
            minion_name = random.choice(minion_types)

            # Create event embed
            embed = create_basic_embed(
                title=f"⚠️ Um {minion_name} apareceu! ⚠️",
                description=(
                    f"Um {minion_name} invadiu a Academia Tokugawa!\n\n"
                    f"Seja o primeiro a derrotá-lo usando o comando `/minion atacar` para ganhar recompensas!"
                ),
                color=0xFF0000  # Red
            )

            # Send the announcement
            message = await channel.send(embed=embed)

            # Store event data
            event_id = f"minion_{datetime.now().timestamp()}"
            ACTIVE_EVENTS[event_id] = {
                'channel_id': channel.id,
                'message_id': message.id,
                'start_time': datetime.now(),
                'end_time': datetime.now() + timedelta(minutes=5),  # 5 minute duration
                'participants': [],
                'data': {
                    'type': 'minion',
                    'name': minion_name,
                    'defeated': False,
                    'exp_reward': random.randint(10, 30),
                    'tusd_reward': random.randint(5, 15)
                }
            }

            logger.info(f"Triggered minion event in channel {channel.name}")
        except Exception as e:
            logger.error(f"Error triggering minion event: {e}")

    async def trigger_villain_event(self, channel):
        """Trigger a random villain invasion event."""
        try:
            # Create villain event
            villain_types = [
                'Lorde das Sombras', 'Mestre do Caos', 'Imperador do Gelo', 
                'Rainha das Chamas', 'Senhor dos Pesadelos', 'Caçador de Almas'
            ]
            villain_name = random.choice(villain_types)

            # Determine villain strength based on server activity
            base_strength = 100
            activity_count = sum(data.get('count', 0) for hour, data in PLAYER_ACTIVITY.items())
            villain_strength = base_strength + (activity_count * 10)

            # Create event embed
            embed = create_basic_embed(
                title=f"🔥 ALERTA: {villain_name} está invadindo a Academia! 🔥",
                description=(
                    f"O temível **{villain_name}** está invadindo a Academia Tokugawa!\n\n"
                    f"Força do Vilão: {villain_strength} HP\n\n"
                    f"Todos os estudantes devem se unir para derrotá-lo! Use o comando `/vilao atacar` para combater esta ameaça!\n\n"
                    f"Quanto mais estudantes participarem, maiores serão as recompensas para todos!"
                ),
                color=0x800080  # Purple
            )

            # Send the announcement
            message = await channel.send(
                content="@everyone Uma ameaça foi detectada na Academia Tokugawa! Todos os estudantes são convocados!",
                embed=embed
            )

            # Store event data
            event_id = f"villain_{datetime.now().timestamp()}"
            ACTIVE_EVENTS[event_id] = {
                'channel_id': channel.id,
                'message_id': message.id,
                'start_time': datetime.now(),
                'end_time': datetime.now() + timedelta(minutes=30),  # 30 minute duration
                'participants': [],
                'data': {
                    'type': 'villain',
                    'name': villain_name,
                    'strength': villain_strength,
                    'current_hp': villain_strength,
                    'defeated': False,
                    'base_exp_reward': 50,
                    'base_tusd_reward': 25
                }
            }

            logger.info(f"Triggered villain event in channel {channel.name}")
        except Exception as e:
            logger.error(f"Error triggering villain event: {e}")

    async def trigger_collectible_event(self, channel):
        """Trigger a random collectible item appearance event."""
        try:
            # Create collectible event
            collectible_types = [
                'Pergaminho Antigo', 'Cristal Misterioso', 'Amuleto Encantado', 
                'Poção Brilhante', 'Fragmento de Artefato', 'Livro de Feitiços'
            ]
            collectible_name = random.choice(collectible_types)

            # Determine rarity
            rarities = ['common', 'uncommon', 'rare', 'epic', 'legendary']
            weights = [0.4, 0.3, 0.2, 0.08, 0.02]  # 40% common, 2% legendary
            rarity = random.choices(rarities, weights=weights, k=1)[0]

            # Rarity colors
            rarity_colors = {
                'common': 0x808080,
                'uncommon': 0x00FF00,
                'rare': 0x0000FF,
                'epic': 0x800080,
                'legendary': 0xFFA500
            }

            # Create event embed
            embed = create_basic_embed(
                title=f"✨ Um {collectible_name} apareceu! ✨",
                description=(
                    f"Um {rarity} **{collectible_name}** foi avistado na Academia Tokugawa!\n\n"
                    f"Seja o primeiro a coletá-lo usando o comando `/item coletar` para adicioná-lo ao seu inventário!"
                ),
                color=rarity_colors.get(rarity, 0x1E90FF)
            )

            # Send the announcement
            message = await channel.send(embed=embed)

            # Store event data
            event_id = f"collectible_{datetime.now().timestamp()}"
            ACTIVE_EVENTS[event_id] = {
                'channel_id': channel.id,
                'message_id': message.id,
                'start_time': datetime.now(),
                'end_time': datetime.now() + timedelta(minutes=5),  # 5 minute duration
                'participants': [],
                'data': {
                    'type': 'collectible',
                    'name': collectible_name,
                    'rarity': rarity,
                    'collected': False,
                    'item': {
                        'name': collectible_name,
                        'description': f"Um {rarity} item coletado durante um evento especial.",
                        'type': 'collectible',
                        'rarity': rarity,
                        'effects': {}
                    }
                }
            }

            logger.info(f"Triggered collectible event in channel {channel.name}")
        except Exception as e:
            logger.error(f"Error triggering collectible event: {e}")

    async def cleanup_expired_events(self):
        """Clean up expired events."""
        try:
            now = datetime.now()
            expired_events = []

            for event_id, event_data in ACTIVE_EVENTS.items():
                if event_data['end_time'] < now:
                    expired_events.append(event_id)

                    # Handle specific event cleanup
                    if 'villain' in event_id and not event_data['data'].get('defeated', False):
                        # Villain escaped
                        try:
                            channel = self.bot.get_channel(event_data['channel_id'])
                            if channel:
                                await channel.send(
                                    embed=create_basic_embed(
                                        title=f"{event_data['data']['name']} escapou!",
                                        description=(
                                            f"O vilão **{event_data['data']['name']}** escapou da Academia Tokugawa!\n\n"
                                            f"Os estudantes não conseguiram derrotá-lo a tempo."
                                        ),
                                        color=0x808080  # Gray
                                    )
                                )
                        except Exception as e:
                            logger.error(f"Error sending villain escape message: {e}")

            # Remove expired events
            for event_id in expired_events:
                ACTIVE_EVENTS.pop(event_id, None)

        except Exception as e:
            logger.error(f"Error cleaning up expired events: {e}")

    @app_commands.command(name="configurar", description="Configurar canais para eventos e anúncios")
    @app_commands.default_permissions(administrator=True)
    async def slash_configure(self, interaction: discord.Interaction, canal_torneios: discord.TextChannel = None, canal_anuncios: discord.TextChannel = None):
        """Configure channels for tournaments and announcements."""
        try:
            if not interaction.user.guild_permissions.administrator:
                await interaction.response.send_message("Você precisa ser administrador para usar este comando.", ephemeral=True)
                return

            if canal_torneios:
                self.tournament_channel_id = canal_torneios.id

            if canal_anuncios:
                self.announcement_channel_id = canal_anuncios.id

            response = "Configurações atualizadas:\n"
            if canal_torneios:
                response += f"- Canal de torneios: {canal_torneios.mention}\n"
            if canal_anuncios:
                response += f"- Canal de anúncios: {canal_anuncios.mention}\n"

            await interaction.response.send_message(response, ephemeral=True)
            logger.info(f"Channels configured by {interaction.user.name}")
        except Exception as e:
            logger.error(f"Error in slash_configure: {e}")
            await interaction.response.send_message("Ocorreu um erro ao configurar os canais.", ephemeral=True)

    @app_commands.command(name="minion", description="Interagir com minions que aparecem na Academia")
    @app_commands.describe(acao="Ação a ser realizada com o minion")
    @app_commands.choices(acao=[
        app_commands.Choice(name="atacar", value="attack")
    ])
    async def slash_minion(self, interaction: discord.Interaction, acao: str):
        """Interact with minions that appear in the Academy."""
        try:
            # Check if player exists
            player = get_player(interaction.user.id)
            if not player:
                await interaction.response.send_message(f"{interaction.user.mention}, você ainda não está registrado na Academia Tokugawa. Use /registro ingressar para criar seu personagem.", ephemeral=True)
                return

            # Find active minion event in this channel
            active_minion = None
            active_event_id = None

            for event_id, event_data in ACTIVE_EVENTS.items():
                if ('minion' in event_id and 
                    event_data['channel_id'] == interaction.channel.id and 
                    not event_data['data'].get('defeated', False)):
                    active_minion = event_data
                    active_event_id = event_id
                    break

            if not active_minion:
                await interaction.response.send_message("Não há minions ativos neste canal no momento.", ephemeral=True)
                return

            # Handle attack action
            if acao == "attack":
                # Mark minion as defeated
                active_minion['data']['defeated'] = True
                active_minion['participants'].append(interaction.user.id)

                # Calculate rewards
                exp_reward = active_minion['data']['exp_reward']
                tusd_reward = active_minion['data']['tusd_reward']

                # Apply club buffs if any
                if player.get('club_id') and player['club_id'] in CLUB_BUFFS:
                    buff = CLUB_BUFFS[player['club_id']]
                    if buff['type'] == 'exp':
                        exp_reward = int(exp_reward * (1 + buff['value'] / 100))
                    elif buff['type'] == 'tusd':
                        tusd_reward = int(tusd_reward * (1 + buff['value'] / 100))

                # Update player stats
                update_player(
                    interaction.user.id,
                    exp=player['exp'] + exp_reward,
                    tusd=player['tusd'] + tusd_reward
                )

                # Track progress for rankings
                if interaction.user.id not in PLAYER_PROGRESS['daily']:
                    PLAYER_PROGRESS['daily'][interaction.user.id] = {'exp_gained': 0, 'duels_won': 0, 'events_completed': 0}
                if interaction.user.id not in PLAYER_PROGRESS['weekly']:
                    PLAYER_PROGRESS['weekly'][interaction.user.id] = {'exp_gained': 0, 'duels_won': 0, 'events_completed': 0}

                PLAYER_PROGRESS['daily'][interaction.user.id]['exp_gained'] += exp_reward
                PLAYER_PROGRESS['daily'][interaction.user.id]['events_completed'] += 1
                PLAYER_PROGRESS['weekly'][interaction.user.id]['exp_gained'] += exp_reward
                PLAYER_PROGRESS['weekly'][interaction.user.id]['events_completed'] += 1

                # Send success message
                await interaction.response.send_message(
                    embed=create_basic_embed(
                        title=f"{player['name']} derrotou o {active_minion['data']['name']}!",
                        description=(
                            f"Com um golpe preciso, {player['name']} derrotou o {active_minion['data']['name']}!\n\n"
                            f"**Recompensas:**\n"
                            f"- +{exp_reward} EXP\n"
                            f"- +{tusd_reward} TUSD"
                        ),
                        color=0x00FF00  # Green
                    )
                )

                # Remove the event
                ACTIVE_EVENTS.pop(active_event_id, None)

                # Update player activity
                current_hour = datetime.now().hour
                if current_hour in PLAYER_ACTIVITY:
                    PLAYER_ACTIVITY[current_hour]['count'] += 1
                else:
                    PLAYER_ACTIVITY[current_hour] = {'count': 1, 'last_updated': datetime.now()}

                logger.info(f"Player {player['name']} defeated minion {active_minion['data']['name']}")

        except Exception as e:
            logger.error(f"Error in slash_minion: {e}")
            await interaction.response.send_message("Ocorreu um erro ao interagir com o minion.", ephemeral=True)

    @app_commands.command(name="vilao", description="Combater vilões que invadem a Academia")
    @app_commands.describe(acao="Ação a ser realizada contra o vilão")
    @app_commands.choices(acao=[
        app_commands.Choice(name="atacar", value="attack")
    ])
    async def slash_villain(self, interaction: discord.Interaction, acao: str):
        """Combat villains that invade the Academy."""
        try:
            # Check if player exists
            player = get_player(interaction.user.id)
            if not player:
                await interaction.response.send_message(f"{interaction.user.mention}, você ainda não está registrado na Academia Tokugawa. Use /registro ingressar para criar seu personagem.", ephemeral=True)
                return

            # Find active villain event in this channel
            active_villain = None
            active_event_id = None

            for event_id, event_data in ACTIVE_EVENTS.items():
                if ('villain' in event_id and 
                    event_data['channel_id'] == interaction.channel.id and 
                    not event_data['data'].get('defeated', False)):
                    active_villain = event_data
                    active_event_id = event_id
                    break

            if not active_villain:
                await interaction.response.send_message("Não há vilões ativos neste canal no momento.", ephemeral=True)
                return

            # Check if player already participated
            if interaction.user.id in active_villain['participants']:
                await interaction.response.send_message("Você já atacou este vilão. Aguarde outros estudantes se juntarem à batalha!", ephemeral=True)
                return

            # Handle attack action
            if acao == "attack":
                # Calculate damage based on player level and attributes
                base_damage = 10 + player['level'] * 2
                attribute_bonus = (player['power_stat'] * 0.5) + (player['dexterity'] * 0.3)
                total_damage = int(base_damage + attribute_bonus)

                # Apply club buffs if any
                if player.get('club_id') and player['club_id'] in CLUB_BUFFS:
                    buff = CLUB_BUFFS[player['club_id']]
                    if buff['type'] == 'attribute':
                        total_damage = int(total_damage * (1 + buff['value'] / 100))

                # Add randomness
                total_damage = int(total_damage * random.uniform(0.8, 1.2))

                # Update villain HP
                active_villain['data']['current_hp'] -= total_damage
                active_villain['participants'].append(interaction.user.id)

                # Check if villain is defeated
                if active_villain['data']['current_hp'] <= 0:
                    active_villain['data']['defeated'] = True

                    # Calculate rewards based on participation
                    num_participants = len(active_villain['participants'])
                    base_exp = active_villain['data']['base_exp_reward']
                    base_tusd = active_villain['data']['base_tusd_reward']

                    # More participants = more rewards for everyone
                    participation_bonus = min(3.0, 1.0 + (num_participants * 0.1))  # Cap at 3x bonus

                    exp_reward = int(base_exp * participation_bonus)
                    tusd_reward = int(base_tusd * participation_bonus)

                    # Award all participants
                    participant_names = []
                    for user_id in active_villain['participants']:
                        p = get_player(user_id)
                        if p:
                            # Apply club buffs if any
                            p_exp_reward = exp_reward
                            p_tusd_reward = tusd_reward

                            if p.get('club_id') and p['club_id'] in CLUB_BUFFS:
                                buff = CLUB_BUFFS[p['club_id']]
                                if buff['type'] == 'exp':
                                    p_exp_reward = int(p_exp_reward * (1 + buff['value'] / 100))
                                elif buff['type'] == 'tusd':
                                    p_tusd_reward = int(p_tusd_reward * (1 + buff['value'] / 100))

                            # Update player
                            update_player(
                                user_id,
                                exp=p['exp'] + p_exp_reward,
                                tusd=p['tusd'] + p_tusd_reward
                            )

                            # Track progress for rankings
                            if user_id not in PLAYER_PROGRESS['daily']:
                                PLAYER_PROGRESS['daily'][user_id] = {'exp_gained': 0, 'duels_won': 0, 'events_completed': 0}
                            if user_id not in PLAYER_PROGRESS['weekly']:
                                PLAYER_PROGRESS['weekly'][user_id] = {'exp_gained': 0, 'duels_won': 0, 'events_completed': 0}

                            PLAYER_PROGRESS['daily'][user_id]['exp_gained'] += p_exp_reward
                            PLAYER_PROGRESS['daily'][user_id]['events_completed'] += 1
                            PLAYER_PROGRESS['weekly'][user_id]['exp_gained'] += p_exp_reward
                            PLAYER_PROGRESS['weekly'][user_id]['events_completed'] += 1

                            participant_names.append(p['name'])

                    # Send victory message
                    await interaction.response.send_message(
                        embed=create_basic_embed(
                            title=f"Vilão Derrotado! {active_villain['data']['name']} foi vencido!",
                            description=(
                                f"Graças aos esforços combinados de {num_participants} estudantes, o vilão **{active_villain['data']['name']}** foi derrotado!\n\n"
                                f"**Participantes:** {', '.join(participant_names)}\n\n"
                                f"**Recompensas para cada participante:**\n"
                                f"- +{exp_reward} EXP\n"
                                f"- +{tusd_reward} TUSD\n\n"
                                f"A Academia Tokugawa está segura... por enquanto."
                            ),
                            color=0x00FF00  # Green
                        )
                    )

                    # Remove the event
                    ACTIVE_EVENTS.pop(active_event_id, None)
                else:
                    # Villain still active, update status
                    hp_percentage = max(0, min(100, int((active_villain['data']['current_hp'] / active_villain['data']['strength']) * 100)))
                    hp_bar = "█" * (hp_percentage // 10) + "░" * (10 - (hp_percentage // 10))

                    await interaction.response.send_message(
                        embed=create_basic_embed(
                            title=f"{player['name']} atacou {active_villain['data']['name']}!",
                            description=(
                                f"{player['name']} causou **{total_damage}** de dano ao vilão!\n\n"
                                f"**HP do Vilão:** {active_villain['data']['current_hp']}/{active_villain['data']['strength']} ({hp_percentage}%)\n"
                                f"{hp_bar}\n\n"
                                f"Mais {max(1, active_villain['data']['current_hp'] // total_damage)} ataques como esse serão necessários para derrotá-lo!\n"
                                f"Convoque mais estudantes para ajudar!"
                            ),
                            color=0xFFA500  # Orange
                        )
                    )

                # Update player activity
                current_hour = datetime.now().hour
                if current_hour in PLAYER_ACTIVITY:
                    PLAYER_ACTIVITY[current_hour]['count'] += 1
                else:
                    PLAYER_ACTIVITY[current_hour] = {'count': 1, 'last_updated': datetime.now()}

                logger.info(f"Player {player['name']} attacked villain {active_villain['data']['name']} for {total_damage} damage")

        except Exception as e:
            logger.error(f"Error in slash_villain: {e}")
            await interaction.response.send_message("Ocorreu um erro ao combater o vilão.", ephemeral=True)

    @app_commands.command(name="item", description="Coletar itens que aparecem na Academia")
    @app_commands.describe(acao="Ação a ser realizada com o item")
    @app_commands.choices(acao=[
        app_commands.Choice(name="coletar", value="collect")
    ])
    async def slash_item(self, interaction: discord.Interaction, acao: str):
        """Collect items that appear in the Academy."""
        try:
            # Check if player exists
            player = get_player(interaction.user.id)
            if not player:
                await interaction.response.send_message(f"{interaction.user.mention}, você ainda não está registrado na Academia Tokugawa. Use /registro ingressar para criar seu personagem.", ephemeral=True)
                return

            # Find active collectible event in this channel
            active_collectible = None
            active_event_id = None

            for event_id, event_data in ACTIVE_EVENTS.items():
                if ('collectible' in event_id and 
                    event_data['channel_id'] == interaction.channel.id and 
                    not event_data['data'].get('collected', False)):
                    active_collectible = event_data
                    active_event_id = event_id
                    break

            if not active_collectible:
                await interaction.response.send_message("Não há itens para coletar neste canal no momento.", ephemeral=True)
                return

            # Handle collect action
            if acao == "collect":
                # Mark item as collected
                active_collectible['data']['collected'] = True
                active_collectible['participants'].append(interaction.user.id)

                # Add item to player's inventory
                item = active_collectible['data']['item']

                # Get current inventory
                inventory = player.get('inventory', {})

                # Add new item
                item_id = f"item_{datetime.now().timestamp()}"
                inventory[item_id] = item

                # Update player
                update_player(
                    interaction.user.id,
                    inventory=json.dumps(inventory)
                )

                # Calculate exp reward based on rarity
                rarity_exp = {
                    'common': 5,
                    'uncommon': 10,
                    'rare': 20,
                    'epic': 35,
                    'legendary': 50
                }
                exp_reward = rarity_exp.get(item['rarity'], 5)

                # Apply club buffs if any
                if player.get('club_id') and player['club_id'] in CLUB_BUFFS:
                    buff = CLUB_BUFFS[player['club_id']]
                    if buff['type'] == 'exp':
                        exp_reward = int(exp_reward * (1 + buff['value'] / 100))

                # Update player exp
                update_player(
                    interaction.user.id,
                    exp=player['exp'] + exp_reward
                )

                # Track progress for rankings
                if interaction.user.id not in PLAYER_PROGRESS['daily']:
                    PLAYER_PROGRESS['daily'][interaction.user.id] = {'exp_gained': 0, 'duels_won': 0, 'events_completed': 0}
                if interaction.user.id not in PLAYER_PROGRESS['weekly']:
                    PLAYER_PROGRESS['weekly'][interaction.user.id] = {'exp_gained': 0, 'duels_won': 0, 'events_completed': 0}

                PLAYER_PROGRESS['daily'][interaction.user.id]['exp_gained'] += exp_reward
                PLAYER_PROGRESS['daily'][interaction.user.id]['events_completed'] += 1
                PLAYER_PROGRESS['weekly'][interaction.user.id]['exp_gained'] += exp_reward
                PLAYER_PROGRESS['weekly'][interaction.user.id]['events_completed'] += 1

                # Rarity colors and emojis
                rarity_info = {
                    'common': {'color': 0x808080, 'emoji': "🔘"},
                    'uncommon': {'color': 0x00FF00, 'emoji': "🟢"},
                    'rare': {'color': 0x0000FF, 'emoji': "🔵"},
                    'epic': {'color': 0x800080, 'emoji': "🟣"},
                    'legendary': {'color': 0xFFA500, 'emoji': "🟠"}
                }

                rarity_data = rarity_info.get(item['rarity'], rarity_info['common'])

                # Send success message
                await interaction.response.send_message(
                    embed=create_basic_embed(
                        title=f"{player['name']} coletou o {item['name']}!",
                        description=(
                            f"{player['name']} foi o primeiro a coletar o {rarity_data['emoji']} **{item['name']}**!\n\n"
                            f"**Item Adicionado ao Inventário:**\n"
                            f"{rarity_data['emoji']} **{item['name']}** ({item['rarity'].capitalize()})\n"
                            f"{item['description']}\n\n"
                            f"**Bônus de EXP:** +{exp_reward} EXP"
                        ),
                        color=rarity_data['color']
                    )
                )

                # Remove the event
                ACTIVE_EVENTS.pop(active_event_id, None)

                # Update player activity
                current_hour = datetime.now().hour
                if current_hour in PLAYER_ACTIVITY:
                    PLAYER_ACTIVITY[current_hour]['count'] += 1
                else:
                    PLAYER_ACTIVITY[current_hour] = {'count': 1, 'last_updated': datetime.now()}

                logger.info(f"Player {player['name']} collected item {item['name']}")

        except Exception as e:
            logger.error(f"Error in slash_item: {e}")
            await interaction.response.send_message("Ocorreu um erro ao coletar o item.", ephemeral=True)

    @app_commands.command(name="turfwars", description="Comandos para participar das Turf Wars dominicais")
    @app_commands.describe(
        acao="Ação a ser realizada",
        nome_time="Nome do time (para criar ou entrar)",
        papel="Papel no time (para entrar)"
    )
    @app_commands.choices(acao=[
        app_commands.Choice(name="criar", value="create"),
        app_commands.Choice(name="entrar", value="join"),
        app_commands.Choice(name="sair", value="leave"),
        app_commands.Choice(name="info", value="info")
    ])
    @app_commands.choices(papel=[
        app_commands.Choice(name="monarca", value="monarch"),
        app_commands.Choice(name="rainha", value="queen"),
        app_commands.Choice(name="valete", value="jack"),
        app_commands.Choice(name="healer", value="healer")
    ])
    async def slash_turfwars(self, interaction: discord.Interaction, acao: str, nome_time: str = None, papel: str = None):
        """Commands for participating in Sunday Turf Wars."""
        try:
            # Check if player exists
            player = get_player(interaction.user.id)
            if not player:
                await interaction.response.send_message(f"{interaction.user.mention}, você ainda não está registrado na Academia Tokugawa. Use /registro ingressar para criar seu personagem.", ephemeral=True)
                return

            # Check if Turf Wars are active
            turf_wars = None
            for event_id, event_data in ACTIVE_EVENTS.items():
                if 'turf_wars' in event_id:
                    turf_wars = event_data
                    break

            if not turf_wars and acao != "info":
                await interaction.response.send_message("As Turf Wars não estão ativas no momento. Aguarde o próximo domingo às 14h!", ephemeral=True)
                return

            # Check if we're in signup phase for create/join actions
            if turf_wars and not turf_wars['data']['signup_phase'] and acao in ["create", "join"]:
                await interaction.response.send_message("A fase de inscrições das Turf Wars já terminou. Aguarde o próximo evento!", ephemeral=True)
                return

            # Handle different actions
            if acao == "create":
                if not nome_time:
                    await interaction.response.send_message("Você precisa fornecer um nome para o time.", ephemeral=True)
                    return

                # Check if team already exists
                if nome_time in TURF_WARS_TEAMS:
                    await interaction.response.send_message(f"O time '{nome_time}' já existe. Escolha outro nome ou entre para este time.", ephemeral=True)
                    return

                # Check if player is already in a team
                for team_name, team_data in TURF_WARS_TEAMS.items():
                    for role, member in team_data['members'].items():
                        if member and member['user_id'] == interaction.user.id:
                            await interaction.response.send_message(f"Você já está no time '{team_name}' como {role}. Saia primeiro para criar um novo time.", ephemeral=True)
                            return

                # Create new team
                TURF_WARS_TEAMS[nome_time] = {
                    'members': {
                        'monarch': {'user_id': interaction.user.id, 'name': player['name']},
                        'queen': None,
                        'jack': None,
                        'healer': None
                    },
                    'score': 0
                }

                await interaction.response.send_message(
                    embed=create_basic_embed(
                        title=f"Time '{nome_time}' criado!",
                        description=(
                            f"{player['name']} criou o time '{nome_time}' e se tornou o Monarca!\n\n"
                            f"Outros jogadores podem entrar usando:\n"
                            f"`/turfwars entrar {nome_time} [papel]`\n\n"
                            f"Papéis disponíveis: rainha, valete, healer"
                        ),
                        color=0xFF5733
                    )
                )

                logger.info(f"Player {player['name']} created Turf Wars team '{nome_time}'")

            elif acao == "join":
                if not nome_time or not papel:
                    await interaction.response.send_message("Você precisa fornecer o nome do time e o papel desejado.", ephemeral=True)
                    return

                # Check if team exists
                if nome_time not in TURF_WARS_TEAMS:
                    await interaction.response.send_message(f"O time '{nome_time}' não existe.", ephemeral=True)
                    return

                # Check if player is already in a team
                for team_name, team_data in TURF_WARS_TEAMS.items():
                    for role, member in team_data['members'].items():
                        if member and member['user_id'] == interaction.user.id:
                            await interaction.response.send_message(f"Você já está no time '{team_name}' como {role}. Saia primeiro para entrar em outro time.", ephemeral=True)
                            return

                # Check if role is available
                if TURF_WARS_TEAMS[nome_time]['members'][papel]:
                    await interaction.response.send_message(f"O papel de {papel} já está ocupado no time '{nome_time}'.", ephemeral=True)
                    return

                # Join team
                TURF_WARS_TEAMS[nome_time]['members'][papel] = {'user_id': interaction.user.id, 'name': player['name']}

                await interaction.response.send_message(
                    embed=create_basic_embed(
                        title=f"{player['name']} entrou no time '{nome_time}'!",
                        description=(
                            f"{player['name']} entrou no time '{nome_time}' como {papel.capitalize()}!\n\n"
                            f"Composição atual do time:\n"
                            + "\n".join([f"- {r.capitalize()}: {m['name'] if m else 'Vago'}" for r, m in TURF_WARS_TEAMS[nome_time]['members'].items()])
                        ),
                        color=0xFF5733
                    )
                )

                logger.info(f"Player {player['name']} joined Turf Wars team '{nome_time}' as {papel}")

            elif acao == "leave":
                # Find player's team
                player_team = None
                player_role = None

                for team_name, team_data in TURF_WARS_TEAMS.items():
                    for role, member in team_data['members'].items():
                        if member and member['user_id'] == interaction.user.id:
                            player_team = team_name
                            player_role = role
                            break
                    if player_team:
                        break

                if not player_team:
                    await interaction.response.send_message("Você não está em nenhum time das Turf Wars.", ephemeral=True)
                    return

                # Handle monarch leaving (disband team if no other members)
                if player_role == 'monarch':
                    # Check if team has other members
                    has_other_members = False
                    for role, member in TURF_WARS_TEAMS[player_team]['members'].items():
                        if role != 'monarch' and member:
                            has_other_members = True
                            break

                    if has_other_members:
                        # Promote someone else to monarch
                        for role, member in TURF_WARS_TEAMS[player_team]['members'].items():
                            if role != 'monarch' and member:
                                # Promote this member
                                TURF_WARS_TEAMS[player_team]['members']['monarch'] = member
                                TURF_WARS_TEAMS[player_team]['members'][role] = None

                                await interaction.response.send_message(
                                    embed=create_basic_embed(
                                        title=f"{player['name']} saiu do time '{player_team}'!",
                                        description=(
                                            f"{player['name']} saiu do time '{player_team}'!\n\n"
                                            f"{member['name']} foi promovido a Monarca!\n\n"
                                            f"Composição atual do time:\n"
                                            + "\n".join([f"- {r.capitalize()}: {m['name'] if m else 'Vago'}" for r, m in TURF_WARS_TEAMS[player_team]['members'].items()])
                                        ),
                                        color=0xFF5733
                                    )
                                )
                                break
                    else:
                        # Disband team
                        TURF_WARS_TEAMS.pop(player_team)

                        await interaction.response.send_message(
                            embed=create_basic_embed(
                                title=f"Time '{player_team}' foi desfeito!",
                                description=f"{player['name']} saiu e o time '{player_team}' foi desfeito por não ter outros membros.",
                                color=0xFF5733
                            )
                        )
                else:
                    # Regular member leaving
                    TURF_WARS_TEAMS[player_team]['members'][player_role] = None

                    await interaction.response.send_message(
                        embed=create_basic_embed(
                            title=f"{player['name']} saiu do time '{player_team}'!",
                            description=(
                                f"{player['name']} saiu do time '{player_team}'!\n\n"
                                f"Composição atual do time:\n"
                                + "\n".join([f"- {r.capitalize()}: {m['name'] if m else 'Vago'}" for r, m in TURF_WARS_TEAMS[player_team]['members'].items()])
                            ),
                            color=0xFF5733
                        )
                    )

                logger.info(f"Player {player['name']} left Turf Wars team '{player_team}'")

            elif acao == "info":
                # Show all teams
                if not TURF_WARS_TEAMS:
                    await interaction.response.send_message("Não há times registrados para as Turf Wars no momento.", ephemeral=True)
                    return

                teams_info = ""
                for team_name, team_data in TURF_WARS_TEAMS.items():
                    teams_info += f"**Time: {team_name}**\n"
                    for role, member in team_data['members'].items():
                        teams_info += f"- {role.capitalize()}: {member['name'] if member else 'Vago'}\n"

                    if turf_wars and turf_wars['data']['battle_phase']:
                        teams_info += f"- Pontuação: {team_data['score']}\n"

                    teams_info += "\n"

                status = "Inscrições Abertas" if turf_wars and turf_wars['data']['signup_phase'] else "Fase de Batalhas" if turf_wars and turf_wars['data']['battle_phase'] else "Inativo"

                await interaction.response.send_message(
                    embed=create_basic_embed(
                        title="Times das Turf Wars",
                        description=f"**Status do Evento:** {status}\n\n{teams_info}",
                        color=0xFF5733
                    ),
                    ephemeral=True
                )

        except Exception as e:
            logger.error(f"Error in slash_turfwars: {e}")
            await interaction.response.send_message("Ocorreu um erro ao processar o comando.", ephemeral=True)

    @app_commands.command(name="ranking", description="Ver rankings diários e semanais da Academia Tokugawa")
    @app_commands.describe(tipo="Tipo de ranking a ser exibido")
    @app_commands.choices(tipo=[
        app_commands.Choice(name="diário", value="daily"),
        app_commands.Choice(name="semanal", value="weekly"),
        app_commands.Choice(name="geral", value="overall")
    ])
    async def slash_ranking(self, interaction: discord.Interaction, tipo: str = "overall"):
        """View daily, weekly, and overall rankings."""
        try:
            if tipo == "daily":
                # Get daily rankings
                daily_players = []
                for user_id, progress in PLAYER_PROGRESS['daily'].items():
                    player = get_player(user_id)
                    if player:
                        daily_players.append({
                            'user_id': user_id,
                            'name': player['name'],
                            'level': player['level'],
                            'club_id': player.get('club_id'),
                            'club_name': get_club(player.get('club_id'))['name'] if player.get('club_id') else "Sem clube",
                            'exp_gained': progress['exp_gained'],
                            'duels_won': progress['duels_won'],
                            'events_completed': progress['events_completed']
                        })

                # Sort by exp gained
                daily_players.sort(key=lambda x: x['exp_gained'], reverse=True)

                # Create ranking embed
                if daily_players:
                    ranking_text = ""
                    for i, player in enumerate(daily_players[:10], 1):
                        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                        ranking_text += f"{medal} **{player['name']}** (Nível {player['level']}) - {player['club_name']}\n"
                        ranking_text += f"   EXP: +{player['exp_gained']} | Duelos: {player['duels_won']} | Eventos: {player['events_completed']}\n\n"

                    embed = create_basic_embed(
                        title="📊 Ranking Diário da Academia Tokugawa 📊",
                        description=ranking_text or "Nenhuma atividade registrada hoje.",
                        color=0x00FF00  # Green
                    )
                else:
                    embed = create_basic_embed(
                        title="📊 Ranking Diário da Academia Tokugawa 📊",
                        description="Nenhuma atividade registrada hoje.",
                        color=0x00FF00  # Green
                    )

                await interaction.response.send_message(embed=embed)

            elif tipo == "weekly":
                # Get weekly rankings
                weekly_players = []
                for user_id, progress in PLAYER_PROGRESS['weekly'].items():
                    player = get_player(user_id)
                    if player:
                        weekly_players.append({
                            'user_id': user_id,
                            'name': player['name'],
                            'level': player['level'],
                            'club_id': player.get('club_id'),
                            'club_name': get_club(player.get('club_id'))['name'] if player.get('club_id') else "Sem clube",
                            'exp_gained': progress['exp_gained'],
                            'duels_won': progress['duels_won'],
                            'events_completed': progress['events_completed']
                        })

                # Sort by exp gained
                weekly_players.sort(key=lambda x: x['exp_gained'], reverse=True)

                # Create ranking embed
                if weekly_players:
                    ranking_text = ""
                    for i, player in enumerate(weekly_players[:10], 1):
                        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                        ranking_text += f"{medal} **{player['name']}** (Nível {player['level']}) - {player['club_name']}\n"
                        ranking_text += f"   EXP: +{player['exp_gained']} | Duelos: {player['duels_won']} | Eventos: {player['events_completed']}\n\n"

                    embed = create_basic_embed(
                        title="📊 Ranking Semanal da Academia Tokugawa 📊",
                        description=ranking_text or "Nenhuma atividade registrada esta semana.",
                        color=0xFFA500  # Orange
                    )
                else:
                    embed = create_basic_embed(
                        title="📊 Ranking Semanal da Academia Tokugawa 📊",
                        description="Nenhuma atividade registrada esta semana.",
                        color=0xFFA500  # Orange
                    )

                await interaction.response.send_message(embed=embed)

            else:  # overall
                # Get top players
                top_players = get_top_players(10)

                # Create leaderboard embed
                embed = create_leaderboard_embed(top_players, "🏆 Ranking Geral da Academia Tokugawa 🏆")

                await interaction.response.send_message(embed=embed)

        except Exception as e:
            logger.error(f"Error in slash_ranking: {e}")
            await interaction.response.send_message("Ocorreu um erro ao exibir o ranking.", ephemeral=True)

async def setup(bot):
    """Add the cog to the bot."""
    import json
    await bot.add_cog(ScheduledEvents(bot))
    logger.info("ScheduledEvents cog loaded")
