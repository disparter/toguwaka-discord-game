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
from utils.database import get_player, update_player, get_club, get_all_clubs, get_top_players, get_top_players_by_reputation
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

# Dictionary to store the current day's subject
DAILY_SUBJECT = {
    # 'subject': 'Matemática',
    # 'emoji': '🧮',
    # 'description': 'Hoje é dia de Matemática! Participe do quiz para ganhar notas e XP!',
    # 'difficulty': 1,  # 1-5
    # 'questions': []
}

# Dictionary to store subject grades for quick access
SUBJECT_GRADES = {
    # user_id: {
    #     'subject': {
    #         'month': {
    #             'year': grade
    #         }
    #     }
    # }
}

# Dictionary to define voting categories
VOTING_CATEGORIES = {
    'most_beautiful': {
        'name': 'Aluno Mais Bonito',
        'description': 'Vote no aluno que você considera o mais bonito da Academia!',
        'attribute': 'charisma',
        'emoji': '✨',
        'reward_reputation': 50,
        'reward_buff': {'type': 'charisma', 'value': 10, 'duration': 7}  # 7 days
    },
    'most_funny': {
        'name': 'Aluno Mais Engraçado',
        'description': 'Vote no aluno que você considera o mais engraçado da Academia!',
        'attribute': 'charisma',
        'emoji': '😂',
        'reward_reputation': 50,
        'reward_buff': {'type': 'charisma', 'value': 10, 'duration': 7}
    },
    'most_intelligent': {
        'name': 'Aluno Mais Inteligente',
        'description': 'Vote no aluno que você considera o mais inteligente da Academia!',
        'attribute': 'intellect',
        'emoji': '🧠',
        'reward_reputation': 50,
        'reward_buff': {'type': 'intellect', 'value': 10, 'duration': 7}
    },
    'most_powerful': {
        'name': 'Aluno Mais Poderoso',
        'description': 'Vote no aluno que você considera o mais poderoso da Academia!',
        'attribute': 'power_stat',
        'emoji': '💪',
        'reward_reputation': 50,
        'reward_buff': {'type': 'power_stat', 'value': 10, 'duration': 7}
    }
}

# Dictionary to store active votes
ACTIVE_VOTES = {
    # 'category': {
    #     'start_time': datetime,
    #     'end_time': datetime,
    #     'week': week_number,
    #     'year': year,
    #     'votes': {
    #         voter_id: candidate_id
    #     }
    # }
}

# Dictionary to store the current week's theme
WEEKLY_THEME = {
    # 'theme': 'Semana da Ciência',
    # 'description': 'Durante esta semana, todas as atividades relacionadas a Física e Biologia concedem +50% de XP!',
    # 'start_date': datetime,
    # 'end_date': datetime,
    # 'buffs': {
    #     'subjects': ['Física', 'Biologia'],
    #     'exp_multiplier': 1.5
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

        # Schedule finding channels after bot is ready
        self.bot.loop.create_task(self.find_channels())

        logger.info("ScheduledEvents cog initialized")

    async def find_channels(self):
        """Find and set announcement and tournament channels."""
        await self.bot.wait_until_ready()
        logger.info("Finding channels for announcements and tournaments")

        for guild in self.bot.guilds:
            # Try to find announcement channel
            announcement_channel = discord.utils.get(guild.text_channels, name="anúncios") or \
                                  discord.utils.get(guild.text_channels, name="announcements") or \
                                  discord.utils.get(guild.text_channels, name="geral") or \
                                  discord.utils.get(guild.text_channels, name="general")

            if announcement_channel:
                self.announcement_channel_id = announcement_channel.id
                logger.info(f"Set announcement channel to: {announcement_channel.name} ({announcement_channel.id})")

            # Try to find tournament channel (can be the same as announcement channel)
            tournament_channel = discord.utils.get(guild.text_channels, name="torneios") or \
                               discord.utils.get(guild.text_channels, name="tournaments") or \
                               announcement_channel  # Fall back to announcement channel

            if tournament_channel:
                self.tournament_channel_id = tournament_channel.id
                logger.info(f"Set tournament channel to: {tournament_channel.name} ({tournament_channel.id})")

        if not self.announcement_channel_id:
            logger.warning("Could not find a suitable announcement channel")
        if not self.tournament_channel_id:
            logger.warning("Could not find a suitable tournament channel")

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
            logger.info(f"Checking scheduled events at {now.strftime('%Y-%m-%d %H:%M:%S')}")

            # Update player activity for the current hour
            current_hour = now.hour
            if current_hour not in PLAYER_ACTIVITY:
                PLAYER_ACTIVITY[current_hour] = {'count': 0, 'last_updated': now}

            # Check for Wednesday tournament (18:00)
            if now.weekday() == 2 and now.hour == 18 and now.minute < 5:
                logger.info("Time for Wednesday tournament")
                await self.start_wednesday_tournament()

            # Check for Sunday Turf Wars (14:00)
            if now.weekday() == 6 and now.hour == 14 and now.minute < 5:
                logger.info("Time for Sunday Turf Wars")
                await self.start_turf_wars()

            # Check for daily morning announcements (8:00)
            if now.hour == 8 and now.minute < 5:
                logger.info("Time for daily morning announcements")
                await self.send_daily_announcements()

            # Check for daily subject announcement (9:00)
            if now.hour == 9 and now.minute < 5:
                logger.info("Time for daily subject announcement")
                await self.announce_daily_subject()

            # Check for "Dia de Matéria" event (first day of the month at 10:00)
            if now.day == 1 and now.hour == 10 and now.minute < 5:
                logger.info("Time for Dia de Matéria event")
                await self.check_dia_de_materia_event()

            # Check for random events based on player activity
            await self.check_random_events()

            # Clean up expired events
            await self.cleanup_expired_events()

        except Exception as e:
            logger.error(f"Error in check_scheduled_events: {e}")

    @tasks.loop(time=time(hour=0, minute=0))  # Run at midnight
    async def daily_reset(self):
        """Reset daily player progress, generate new buffs, and select daily subject."""
        try:
            logger.info("Starting daily reset")

            # Reset daily player progress
            PLAYER_PROGRESS['daily'] = {}
            logger.info("Reset daily player progress")

            # Generate new club buffs
            await self.generate_club_buffs()
            logger.info("Generated new club buffs")

            # Select daily subject
            await self.select_daily_subject()
            logger.info("Selected daily subject")

            # Check monthly grades (will only run on the last day of the month)
            await self.check_monthly_grades()
            logger.info("Checked monthly grades")

            logger.info("Daily reset completed successfully")
        except Exception as e:
            logger.error(f"Error in daily_reset: {e}")
            # Try to select a default subject if selection failed
            try:
                if not DAILY_SUBJECT or not DAILY_SUBJECT.get('subject'):
                    logger.info("Attempting to set default subject after error")
                    DAILY_SUBJECT.clear()
                    DAILY_SUBJECT.update({
                        'subject': 'Matemática',
                        'emoji': '🧮',
                        'description': 'Hoje é dia de Matemática! Participe do quiz para ganhar notas e XP!',
                        'difficulty': 1,
                        'questions': [
                            {
                                'question': 'Quanto é 2 + 2?',
                                'options': ['3', '4', '5', '6'],
                                'correct': 1,  # 4
                                'difficulty': 1
                            }
                        ]
                    })
                    logger.info(f"Set default subject: {DAILY_SUBJECT['subject']}")
            except Exception as inner_e:
                logger.error(f"Error setting default subject: {inner_e}")

    async def select_daily_subject(self):
        """Select a random subject for the day and prepare quiz questions."""
        try:
            # Define available subjects with their properties
            subjects = [
                {
                    'subject': 'Matemática',
                    'emoji': '🧮',
                    'description': 'Hoje é dia de Matemática! Participe do quiz para ganhar notas e XP!',
                    'difficulty': 2,
                    'questions': [
                        {
                            'question': 'Quanto é 15 × 7?',
                            'options': ['95', '105', '115', '125'],
                            'correct': 1,  # 105
                            'difficulty': 1
                        },
                        {
                            'question': 'Se 3x + 7 = 22, qual é o valor de x?',
                            'options': ['3', '5', '7', '9'],
                            'correct': 1,  # 5
                            'difficulty': 2
                        },
                        {
                            'question': 'Qual é a área de um círculo com raio 4?',
                            'options': ['16π', '8π', '4π', '12π'],
                            'correct': 0,  # 16π
                            'difficulty': 3
                        }
                    ]
                },
                {
                    'subject': 'Física',
                    'emoji': '⚛️',
                    'description': 'Hoje é dia de Física! Participe do quiz para ganhar notas e XP!',
                    'difficulty': 3,
                    'questions': [
                        {
                            'question': 'Qual é a unidade de medida de força no Sistema Internacional?',
                            'options': ['Watt', 'Newton', 'Joule', 'Pascal'],
                            'correct': 1,  # Newton
                            'difficulty': 1
                        },
                        {
                            'question': 'Qual é a fórmula da Segunda Lei de Newton?',
                            'options': ['F = ma', 'E = mc²', 'v = d/t', 'P = mg'],
                            'correct': 0,  # F = ma
                            'difficulty': 2
                        },
                        {
                            'question': 'O que é um quantum?',
                            'options': ['Uma partícula subatômica', 'Uma quantidade discreta de energia', 'Um tipo de onda', 'Um campo magnético'],
                            'correct': 1,  # Uma quantidade discreta de energia
                            'difficulty': 3
                        }
                    ]
                },
                {
                    'subject': 'Biologia',
                    'emoji': '🧬',
                    'description': 'Hoje é dia de Biologia! Participe do quiz para ganhar notas e XP!',
                    'difficulty': 2,
                    'questions': [
                        {
                            'question': 'Qual é a organela responsável pela respiração celular?',
                            'options': ['Mitocôndria', 'Ribossomo', 'Complexo de Golgi', 'Lisossomo'],
                            'correct': 0,  # Mitocôndria
                            'difficulty': 1
                        },
                        {
                            'question': 'Qual é o processo pelo qual as plantas produzem seu próprio alimento?',
                            'options': ['Respiração', 'Fotossíntese', 'Digestão', 'Fermentação'],
                            'correct': 1,  # Fotossíntese
                            'difficulty': 1
                        },
                        {
                            'question': 'O que é um alelo?',
                            'options': ['Um tipo de célula', 'Uma forma alternativa de um gene', 'Um tipo de proteína', 'Um organismo unicelular'],
                            'correct': 1,  # Uma forma alternativa de um gene
                            'difficulty': 2
                        }
                    ]
                },
                {
                    'subject': 'Artes Marciais',
                    'emoji': '🥋',
                    'description': 'Hoje é dia de Artes Marciais! Participe do quiz para ganhar notas e XP!',
                    'difficulty': 1,
                    'questions': [
                        {
                            'question': 'Qual arte marcial se originou no Japão e significa "caminho suave"?',
                            'options': ['Karatê', 'Judô', 'Taekwondo', 'Kung Fu'],
                            'correct': 1,  # Judô
                            'difficulty': 1
                        },
                        {
                            'question': 'Qual é a cor do cinturão mais alto no Karatê tradicional?',
                            'options': ['Preto', 'Vermelho', 'Branco', 'Marrom'],
                            'correct': 0,  # Preto
                            'difficulty': 1
                        },
                        {
                            'question': 'Qual arte marcial utiliza principalmente movimentos circulares e é conhecida por sua fluidez?',
                            'options': ['Muay Thai', 'Capoeira', 'Aikido', 'Boxe'],
                            'correct': 2,  # Aikido
                            'difficulty': 2
                        }
                    ]
                },
                {
                    'subject': 'Habilidades Especiais',
                    'emoji': '✨',
                    'description': 'Hoje é dia de Habilidades Especiais! Participe do quiz para ganhar notas e XP!',
                    'difficulty': 3,
                    'questions': [
                        {
                            'question': 'Qual é o nome da habilidade de mover objetos com a mente?',
                            'options': ['Telepatia', 'Telecinese', 'Clarividência', 'Precognição'],
                            'correct': 1,  # Telecinese
                            'difficulty': 1
                        },
                        {
                            'question': 'Qual habilidade permite ver o futuro?',
                            'options': ['Telepatia', 'Empatia', 'Precognição', 'Clarividência'],
                            'correct': 2,  # Precognição
                            'difficulty': 2
                        },
                        {
                            'question': 'Qual é o nome da habilidade de se curar rapidamente?',
                            'options': ['Regeneração', 'Cura', 'Imortalidade', 'Vitalidade'],
                            'correct': 0,  # Regeneração
                            'difficulty': 1
                        }
                    ]
                },
                {
                    'subject': 'Atletismo',
                    'emoji': '🏃',
                    'description': 'Hoje é dia de Atletismo! Participe do quiz para ganhar notas e XP!',
                    'difficulty': 1,
                    'questions': [
                        {
                            'question': 'Qual é a distância de uma maratona em quilômetros?',
                            'options': ['21,0975 km', '42,195 km', '10 km', '100 km'],
                            'correct': 1,  # 42,195 km
                            'difficulty': 1
                        },
                        {
                            'question': 'Qual é o recorde mundial dos 100 metros rasos masculino?',
                            'options': ['9,58s', '9,69s', '9,82s', '9,95s'],
                            'correct': 0,  # 9,58s
                            'difficulty': 2
                        },
                        {
                            'question': 'Qual destes não é um evento de atletismo nas Olimpíadas?',
                            'options': ['Lançamento de dardo', 'Salto com vara', 'Corrida de obstáculos', 'Levantamento de peso'],
                            'correct': 3,  # Levantamento de peso
                            'difficulty': 2
                        }
                    ]
                }
            ]

            # Check if there's a weekly theme that affects subject selection
            if WEEKLY_THEME and 'subjects' in WEEKLY_THEME.get('buffs', {}):
                # Filter subjects based on weekly theme
                themed_subjects = [s for s in subjects if s['subject'] in WEEKLY_THEME['buffs']['subjects']]
                if themed_subjects:
                    # Higher chance to select themed subjects
                    if random.random() < 0.7:  # 70% chance to select a themed subject
                        selected_subject = random.choice(themed_subjects)
                    else:
                        selected_subject = random.choice(subjects)
                else:
                    selected_subject = random.choice(subjects)
            else:
                # Random selection if no theme
                selected_subject = random.choice(subjects)

            # Update global DAILY_SUBJECT
            DAILY_SUBJECT.clear()
            DAILY_SUBJECT.update(selected_subject)

            logger.info(f"Selected daily subject: {DAILY_SUBJECT['subject']}")

        except Exception as e:
            logger.error(f"Error selecting daily subject: {e}")
            # Fallback to a default subject
            DAILY_SUBJECT.clear()
            DAILY_SUBJECT.update({
                'subject': 'Matemática',
                'emoji': '🧮',
                'description': 'Hoje é dia de Matemática! Participe do quiz para ganhar notas e XP!',
                'difficulty': 1,
                'questions': []
            })

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
        """Reset weekly player progress and update club rankings."""
        try:
            # Only reset on Monday
            if datetime.now().weekday() == 0:
                # Reset weekly player progress
                PLAYER_PROGRESS['weekly'] = {}
                logger.info("Weekly reset completed")

                # Update club reputation based on weekly activities
                from utils.database import update_club_reputation_weekly
                if update_club_reputation_weekly():
                    logger.info("Updated club reputation based on weekly activities")

                    # Announce top clubs
                    await self.announce_top_clubs()
                else:
                    logger.error("Failed to update club reputation")
        except Exception as e:
            logger.error(f"Error in weekly_reset: {e}")

    async def announce_top_clubs(self):
        """Announce the top three clubs of the week."""
        try:
            # Get top clubs by activity
            from utils.database import get_top_clubs_by_activity
            top_clubs = get_top_clubs_by_activity(limit=3)

            if not top_clubs:
                logger.info("No club activities recorded this week")
                return

            # If we don't have a channel ID, try to find one
            if not self.announcement_channel_id:
                await self.find_channels()

            if not self.announcement_channel_id:
                logger.error("No announcement channel available for top clubs announcement")
                return

            channel = self.bot.get_channel(self.announcement_channel_id)
            if not channel:
                logger.error(f"Could not find announcement channel with ID {self.announcement_channel_id}")
                # Try to find channels again
                await self.find_channels()
                channel = self.bot.get_channel(self.announcement_channel_id)
                if not channel:
                    logger.error("Still could not find announcement channel after retry")
                    return

            # Create ranking message
            club_ranking = ""
            for i, club in enumerate(top_clubs):
                position = i + 1
                if position == 1:
                    prefix = "🥇"
                elif position == 2:
                    prefix = "🥈"
                elif position == 3:
                    prefix = "🥉"
                else:
                    prefix = f"{position}º"

                club_ranking += f"{prefix} {club['name']} ({club['total_points']} pontos)\n"

            # Create announcement embed
            embed = create_basic_embed(
                title="🏆 Ranking Semanal de Clubes 🏆",
                description=(
                    f"Os clubes de destaque desta semana são:\n\n"
                    f"{club_ranking}\n"
                    f"Continue contribuindo para seu clube!"
                ),
                color=0xFFD700  # Gold
            )

            # Send the announcement
            await channel.send(
                content="@everyone O ranking semanal de clubes foi atualizado!",
                embed=embed
            )

            logger.info(f"Announced top clubs: {', '.join([club['name'] for club in top_clubs])}")

        except Exception as e:
            logger.error(f"Error announcing top clubs: {e}")

    @check_scheduled_events.before_loop
    @daily_reset.before_loop
    @weekly_reset.before_loop
    async def before_tasks(self):
        """Wait until the bot is ready before starting tasks."""
        await self.bot.wait_until_ready()

    async def start_wednesday_tournament(self):
        """Start the Wednesday tournament event."""
        try:
            logger.info("Preparing to start Wednesday tournament")

            # If we don't have a channel ID, try to find one
            if not self.tournament_channel_id:
                logger.info("No tournament channel set, trying to find one")
                await self.find_channels()

            if not self.tournament_channel_id:
                logger.error("No tournament channel available for Wednesday tournament")
                return

            channel = self.bot.get_channel(self.tournament_channel_id)
            if not channel:
                logger.error(f"Could not find tournament channel with ID {self.tournament_channel_id}")
                # Try to find channels again
                logger.info("Trying to find channels again")
                await self.find_channels()
                channel = self.bot.get_channel(self.tournament_channel_id)
                if not channel:
                    logger.error("Still could not find tournament channel after retry")
                    return

            logger.info(f"Found tournament channel: {channel.name} ({channel.id})")

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
            logger.info("Preparing to start Sunday Turf Wars")

            # If we don't have a channel ID, try to find one
            if not self.tournament_channel_id:
                logger.info("No tournament channel set, trying to find one")
                await self.find_channels()

            if not self.tournament_channel_id:
                logger.error("No tournament channel available for Sunday Turf Wars")
                return

            channel = self.bot.get_channel(self.tournament_channel_id)
            if not channel:
                logger.error(f"Could not find tournament channel with ID {self.tournament_channel_id}")
                # Try to find channels again
                logger.info("Trying to find channels again")
                await self.find_channels()
                channel = self.bot.get_channel(self.tournament_channel_id)
                if not channel:
                    logger.error("Still could not find tournament channel after retry")
                    return

            logger.info(f"Found tournament channel: {channel.name} ({channel.id})")

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
                    # Check if monarchs choose democracy mode
                    team1_democracy = random.random() < 0.3  # 30% chance for democracy mode
                    team2_democracy = random.random() < 0.3  # 30% chance for democracy mode

                    # Apply democracy mode effects
                    democracy_messages = []

                    if team1_democracy:
                        # Get monarch player
                        monarch1_player = get_player(monarch1['user_id'])
                        if monarch1_player:
                            # Apply -10 XP penalty to monarch
                            update_player(monarch1['user_id'], exp=monarch1_player['exp'] - 10)

                            # Apply +10 XP bonus to all team members
                            for member in team1_fighters:
                                if member['user_id'] != monarch1['user_id']:  # Skip monarch who already got -10
                                    member_player = get_player(member['user_id'])
                                    if member_player:
                                        update_player(member['user_id'], exp=member_player['exp'] + 10)

                            democracy_messages.append(f"O Monarca de {team1_name} escolheu o **modo democracia**! O time ganha +10 XP, mas o Monarca perde 10 XP.")

                    if team2_democracy:
                        # Get monarch player
                        monarch2_player = get_player(monarch2['user_id'])
                        if monarch2_player:
                            # Apply -10 XP penalty to monarch
                            update_player(monarch2['user_id'], exp=monarch2_player['exp'] - 10)

                            # Apply +10 XP bonus to all team members
                            for member in team2_fighters:
                                if member['user_id'] != monarch2['user_id']:  # Skip monarch who already got -10
                                    member_player = get_player(member['user_id'])
                                    if member_player:
                                        update_player(member['user_id'], exp=member_player['exp'] + 10)

                            democracy_messages.append(f"O Monarca de {team2_name} escolheu o **modo democracia**! O time ganha +10 XP, mas o Monarca perde 10 XP.")

                    # Monarchs select fighters (democracy mode means random selection)
                    fighter1 = random.choice(team1_fighters)
                    fighter2 = random.choice(team2_fighters)

                    # Create description with democracy messages if any
                    description = ""
                    if democracy_messages:
                        description += "\n".join(democracy_messages) + "\n\n"

                    description += (
                        f"O Monarca de {team1_name} escolheu **{fighter1['name']}**!\n"
                        f"O Monarca de {team2_name} escolheu **{fighter2['name']}**!"
                    )

                    await channel.send(
                        embed=create_basic_embed(
                            title=f"Batalha {battle_num}",
                            description=description,
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
            logger.info("Preparing to send daily announcements")

            # If we don't have a channel ID, try to find one
            if not self.announcement_channel_id:
                logger.info("No announcement channel set, trying to find one")
                await self.find_channels()

            if not self.announcement_channel_id:
                logger.error("No announcement channel available for daily announcements")
                return

            channel = self.bot.get_channel(self.announcement_channel_id)
            if not channel:
                logger.error(f"Could not find announcement channel with ID {self.announcement_channel_id}")
                # Try to find channels again
                logger.info("Trying to find channels again")
                await self.find_channels()
                channel = self.bot.get_channel(self.announcement_channel_id)
                if not channel:
                    logger.error("Still could not find announcement channel after retry")
                    return

            logger.info(f"Found announcement channel: {channel.name} ({channel.id})")

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
                        'events_completed': progress['events_completed'],
                        'reputation': player.get('reputation', 0)
                    })

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
                        'exp_gained': progress['exp_gained'],
                        'duels_won': progress['duels_won'],
                        'events_completed': progress['events_completed'],
                        'reputation': player.get('reputation', 0)
                    })

            # Get overall top players
            overall_players = get_top_players(10)

            # Get top players by reputation from database
            reputation_players = []
            try:
                # Use the database function to get top players by reputation
                top_by_reputation = get_top_players_by_reputation(10)
                for player in top_by_reputation:
                    reputation_players.append({
                        'user_id': player['user_id'],
                        'name': player['name'],
                        'level': player['level'],
                        'club_id': player.get('club_id'),
                        'reputation': player.get('reputation', 0)
                    })
            except Exception as e:
                logger.error(f"Error getting top players by reputation: {e}")
                # Fallback to using daily players if database function fails
                for player in daily_players:
                    if player['reputation'] > 0:
                        reputation_players.append(player)

            # Sort players
            daily_players.sort(key=lambda x: x['exp_gained'], reverse=True)
            weekly_players.sort(key=lambda x: x['exp_gained'], reverse=True)
            reputation_players.sort(key=lambda x: x['reputation'], reverse=True)

            # Get top players for each category
            top_daily = daily_players[:5]
            top_weekly = weekly_players[:5]
            top_reputation = reputation_players[:5]

            # Create daily ranking embed
            embeds = []

            # Daily ranking embed
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

            embeds.append(daily_embed)

            # Weekly ranking embed
            if top_weekly:
                ranking_text = ""
                for i, player in enumerate(top_weekly, 1):
                    medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                    club = get_club(player['club_id']) if player.get('club_id') else None
                    club_name = club['name'] if club else "Sem clube"
                    ranking_text += f"{medal} **{player['name']}** (Nível {player['level']}) - {club_name}\n"
                    ranking_text += f"   EXP: +{player['exp_gained']} | Duelos: {player['duels_won']} | Eventos: {player['events_completed']}\n\n"

                weekly_embed = create_basic_embed(
                    title="📈 Ranking Semanal da Academia Tokugawa 📈",
                    description=ranking_text or "Nenhuma atividade registrada esta semana.",
                    color=0x1E90FF  # Blue
                )

                embeds.append(weekly_embed)

            # Overall ranking embed
            if overall_players:
                ranking_text = ""
                for i, player in enumerate(overall_players, 1):
                    medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                    club = get_club(player.get('club_id')) if player.get('club_id') else None
                    club_name = club['name'] if club else "Sem clube"
                    ranking_text += f"{medal} **{player['name']}** (Nível {player['level']}) - {club_name}\n"
                    ranking_text += f"   EXP Total: {player['exp']} | Poder: {player['power']}\n\n"

                overall_embed = create_basic_embed(
                    title="🏆 Ranking Geral da Academia Tokugawa 🏆",
                    description=ranking_text or "Nenhum estudante registrado.",
                    color=0xFFD700  # Gold
                )

                embeds.append(overall_embed)

            # Reputation ranking embed
            if top_reputation:
                ranking_text = ""
                for i, player in enumerate(top_reputation, 1):
                    medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                    club = get_club(player['club_id']) if player.get('club_id') else None
                    club_name = club['name'] if club else "Sem clube"
                    ranking_text += f"{medal} **{player['name']}** (Nível {player['level']}) - {club_name}\n"
                    ranking_text += f"   Reputação: {player['reputation']} pontos\n\n"

                reputation_embed = create_basic_embed(
                    title="⭐ Ranking de Reputação da Academia Tokugawa ⭐",
                    description=ranking_text or "Nenhum estudante com reputação registrada.",
                    color=0xFFA500  # Orange
                )

                embeds.append(reputation_embed)

            # Generate daily news
            news_embed = await self.generate_daily_news()
            embeds.append(news_embed)

            # Send morning message
            greeting_messages = [
                "Bom dia, estudantes da Academia Tokugawa! Preparem-se para mais um dia épico!",
                "Amanheceu na Academia Tokugawa! Que desafios nos aguardam hoje?",
                "O sol nasce sobre a Academia Tokugawa! Quem se destacará hoje?",
                "Despertem, futuros heróis da Academia Tokugawa! Um novo dia de aventuras começa!",
                "O Conselho Estudantil saúda todos os estudantes nesta bela manhã!"
            ]

            # Send the first message with greeting and daily ranking
            await channel.send(
                content=random.choice(greeting_messages),
                embed=embeds[0]  # Daily ranking
            )

            # Send the rest of the embeds in groups of 2 to avoid Discord's embed limit
            for i in range(1, len(embeds), 2):
                group = embeds[i:i+2]
                await channel.send(embeds=group)

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

                    # Generate news content with more creative messages
                    news_items = [
                        f"🌟 O clube **{featured_club['name']}** ganhou destaque hoje! Todos os membros recebem {buff_description}.",
                        f"🏆 O reitor da academia enviou sua benção aos **{featured_club['name']}** por sua performance incrível! {buff_description} para todos os membros!",
                        f"🎉 Hoje é o dia do **{featured_club['name']}**! Chequem seus clubes para saber mais sobre as atividades! Todos os membros recebem {buff_description}.",
                        f"⭐ Os **{featured_club['name']}** demonstraram grande valor e recebem {buff_description} hoje!",
                        f"📢 Atenção! O Conselho Estudantil reconhece a contribuição dos **{featured_club['name']}** para a Academia! {buff_description} para todos os membros!"
                    ]
                else:
                    news_items = [
                        "📝 Nenhum clube se destacou o suficiente para receber bônus hoje.",
                        "🔍 O Conselho Estudantil está avaliando o desempenho dos clubes para futuros benefícios.",
                        "☀️ Hoje é um dia tranquilo na Academia Tokugawa."
                    ]
            else:
                news_items = [
                    "📣 Nenhum clube ativo foi encontrado na Academia Tokugawa.",
                    "🔄 O Conselho Estudantil está recrutando novos membros para os clubes!",
                    "🌤️ Hoje é um dia tranquilo na Academia Tokugawa."
                ]

            # Add random news items with more variety and creativity
            random_news = [
                "⚠️ Um novo Vilão misterioso foi avistado próximo à Academia! Fiquem alertas para possíveis invasões!",
                "🎭 O Festival dos Poderes está se aproximando! Preparem-se para demonstrar suas habilidades e ganhar prêmios exclusivos!",
                "📚 Rumores indicam que um artefato poderoso foi descoberto na biblioteca da Academia. Quem o encontrará primeiro?",
                "🏗️ O Conselho Estudantil anunciou melhorias nas instalações de treinamento! Espere bônus de EXP nos próximos dias!",
                "🎤 Uma competição de talentos será realizada em breve! Comecem a praticar para impressionar os juízes!",
                "👀 Visitantes de uma academia rival foram vistos observando nossos estudantes. Estejam preparados para possíveis desafios!",
                "🔮 Uma nova técnica secreta foi descoberta por um dos professores! Participem das aulas para aprendê-la!",
                "📣 O diretor da Academia está planejando um anúncio importante para esta semana. O que será?",
                "🌪️ Anomalias climáticas foram detectadas ao redor da Academia! Estejam preparados para eventos inesperados!",
                "🎁 Minions foram avistados carregando itens valiosos! Fiquem atentos para coletá-los!",
                "🏅 Hoje é o dia do 'Festival dos Poderes'! Chequem seus clubes para saber mais sobre as atividades!",
                "🌟 Uma estrela cadente foi avistada sobre a Academia! Dizem que ela traz sorte para quem a vê primeiro!"
            ]

            # Add 2-3 random news items for more content
            for _ in range(random.randint(2, 3)):
                news_items.append(random.choice(random_news))
                random_news.remove(news_items[-1])  # Prevent duplicates

            # Create news embed with a more engaging title
            news_text = "\n\n".join([f"• {item}" for item in news_items])

            news_embed = create_basic_embed(
                title="📰 Notícias Diárias do Conselho Estudantil 📰",
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

            # Calculate total activity across all hours with more weight on recent hours
            total_activity = 0
            recent_activity = 0
            for hour, data in PLAYER_ACTIVITY.items():
                hours_ago = (current_hour - hour) % 24
                recency_weight = max(0.1, 1.0 - (hours_ago / 24))  # More recent = higher weight
                total_activity += data.get('count', 0)
                if hours_ago <= 3:  # Last 3 hours
                    recent_activity += data.get('count', 0)

            # Adjust chance based on recent activity (more responsive to spikes in activity)
            current_activity = PLAYER_ACTIVITY.get(current_hour, {}).get('count', 0)
            activity_multiplier = min(4.0, max(0.5, 1.0 + (current_activity / 5) + (recent_activity / 20)))

            # If there's been a sudden spike in activity, increase chance significantly
            if current_activity > 0 and current_activity > sum(data.get('count', 0) for h, data in PLAYER_ACTIVITY.items() if h != current_hour) / max(1, len(PLAYER_ACTIVITY) - 1) * 2:
                activity_multiplier *= 1.5
                logger.info(f"Activity spike detected! Multiplier increased to {activity_multiplier}")

            final_chance = base_chance * hour_multiplier * activity_multiplier

            # Log the chance calculation for debugging
            logger.info(f"Event chance: {final_chance:.4f} (base: {base_chance}, hour: {hour_multiplier}, activity: {activity_multiplier})")

            # Roll for event
            if random.random() < final_chance:
                # Choose a random event type with dynamic weights based on recent events
                # More rare events become more likely if they haven't happened in a while
                event_types = ['minion', 'villain', 'collectible']

                # Default weights
                base_weights = [0.6, 0.3, 0.1]  # 60% minion, 30% villain, 10% collectible

                # Adjust weights based on recent events (last 10 events)
                recent_events = [event['data']['type'] for event_id, event in ACTIVE_EVENTS.items() 
                                if 'data' in event and 'type' in event['data']][-10:]

                adjusted_weights = base_weights.copy()
                if recent_events:
                    # Count occurrences of each event type
                    event_counts = {event_type: recent_events.count(event_type) for event_type in event_types}

                    # Adjust weights - less frequent events get higher weights
                    total_events = len(recent_events)
                    for i, event_type in enumerate(event_types):
                        count = event_counts.get(event_type, 0)
                        if count == 0:  # If event hasn't happened recently, increase its chance
                            adjusted_weights[i] *= 1.5
                        elif count / total_events > base_weights[i] * 1.5:  # If event is happening too often
                            adjusted_weights[i] *= 0.7

                # Normalize weights
                weight_sum = sum(adjusted_weights)
                normalized_weights = [w / weight_sum for w in adjusted_weights]

                event_type = random.choices(event_types, weights=normalized_weights, k=1)[0]
                logger.info(f"Selected event type: {event_type} with weights {normalized_weights}")

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
            # Create minion event with expanded types and rarities
            minion_types = {
                'common': ['Slime', 'Goblin', 'Esqueleto', 'Zumbi', 'Rato Gigante', 'Kobold', 'Imp'],
                'uncommon': ['Ogro', 'Harpia', 'Lobo Sombrio', 'Aranha Venenosa', 'Golem de Pedra'],
                'rare': ['Minotauro', 'Quimera', 'Basilisco', 'Manticora', 'Hidra Jovem'],
                'epic': ['Dragão Menor', 'Behemoth', 'Kraken Jovem', 'Fênix Sombria'],
                'legendary': ['Leviatã', 'Dragão Ancião', 'Titã Elemental', 'Beholder']
            }

            # Select rarity with weighted probability
            rarity_weights = {'common': 0.6, 'uncommon': 0.25, 'rare': 0.1, 'epic': 0.04, 'legendary': 0.01}
            rarity = random.choices(list(rarity_weights.keys()), 
                                   weights=list(rarity_weights.values()), k=1)[0]

            # Select minion from the chosen rarity
            minion_name = random.choice(minion_types[rarity])

            # Determine rewards based on rarity
            reward_multipliers = {
                'common': 1.0,
                'uncommon': 2.0,
                'rare': 3.5,
                'epic': 5.0,
                'legendary': 10.0
            }

            base_exp = random.randint(10, 30)
            base_tusd = random.randint(5, 15)
            base_reputation = random.randint(1, 5)

            exp_reward = int(base_exp * reward_multipliers[rarity])
            tusd_reward = int(base_tusd * reward_multipliers[rarity])
            reputation_reward = int(base_reputation * reward_multipliers[rarity])

            # Rarity colors
            rarity_colors = {
                'common': 0x808080,  # Gray
                'uncommon': 0x00FF00,  # Green
                'rare': 0x0000FF,  # Blue
                'epic': 0x800080,  # Purple
                'legendary': 0xFFA500  # Orange
            }

            # Rarity indicators
            rarity_indicators = {
                'common': '',
                'uncommon': '★',
                'rare': '★★',
                'epic': '★★★',
                'legendary': '★★★★'
            }

            # Create dynamic descriptions based on rarity
            descriptions = {
                'common': [
                    f"Um {minion_name} invadiu a Academia Tokugawa!\n\n",
                    f"Um {minion_name} foi avistado nos corredores da Academia!\n\n",
                    f"Cuidado! Um {minion_name} está causando problemas na Academia!\n\n"
                ],
                'uncommon': [
                    f"Um {minion_name} perigoso está ameaçando os estudantes da Academia!\n\n",
                    f"Alerta! Um {minion_name} foi detectado próximo ao refeitório!\n\n",
                    f"Um {minion_name} está destruindo equipamentos da Academia!\n\n"
                ],
                'rare': [
                    f"Um poderoso {minion_name} está causando caos na Academia Tokugawa!\n\n",
                    f"Emergência! Um {minion_name} invadiu o laboratório principal!\n\n",
                    f"Um {minion_name} está desafiando os estudantes para combate!\n\n"
                ],
                'epic': [
                    f"ALERTA MÁXIMO! Um {minion_name} extremamente perigoso foi detectado!\n\n",
                    f"Um temível {minion_name} está destruindo parte da Academia!\n\n",
                    f"Um {minion_name} está ameaçando a segurança de toda a Academia!\n\n"
                ],
                'legendary': [
                    f"EMERGÊNCIA TOTAL! Um lendário {minion_name} está atacando a Academia!\n\n",
                    f"Um {minion_name} de poder inimaginável apareceu! Todos os estudantes estão em perigo!\n\n",
                    f"A Academia está sob ataque de um {minion_name} ancestral! Precisamos de heróis!\n\n"
                ]
            }

            description = random.choice(descriptions[rarity])
            description += f"Seja o primeiro a derrotá-lo usando o comando `/minion atacar` para ganhar:\n"
            description += f"• {exp_reward} EXP\n"
            description += f"• {tusd_reward} TUSD\n"
            description += f"• {reputation_reward} pontos de Reputação"

            # Create event embed
            embed = create_basic_embed(
                title=f"⚠️ {rarity_indicators[rarity]} Um {minion_name} apareceu! {rarity_indicators[rarity]} ⚠️",
                description=description,
                color=rarity_colors[rarity]
            )

            # Add rarity footer
            embed.set_footer(text=f"Raridade: {rarity.capitalize()}")

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
                    'rarity': rarity,
                    'defeated': False,
                    'exp_reward': exp_reward,
                    'tusd_reward': tusd_reward,
                    'reputation_reward': reputation_reward
                }
            }

            logger.info(f"Triggered {rarity} minion event ({minion_name}) in channel {channel.name}")
        except Exception as e:
            logger.error(f"Error triggering minion event: {e}")

    async def trigger_villain_event(self, channel):
        """Trigger a random villain invasion event."""
        try:
            # Create villain event with expanded types and tiers
            villain_tiers = {
                'tier1': {
                    'names': [
                        'Lorde das Sombras', 'Mestre do Caos', 'Imperador do Gelo', 
                        'Rainha das Chamas', 'Senhor dos Pesadelos', 'Caçador de Almas'
                    ],
                    'title': 'Vilão',
                    'color': 0x800080,  # Purple
                    'emoji': '🔥',
                    'multiplier': 1.0,
                    'duration': 30  # minutes
                },
                'tier2': {
                    'names': [
                        'General Apocalipse', 'Devorador de Mentes', 'Arquimago Corrompido',
                        'Ceifador de Almas', 'Comandante Sanguinário', 'Destruidor de Mundos'
                    ],
                    'title': 'Vilão Poderoso',
                    'color': 0xCC0000,  # Dark Red
                    'emoji': '⚡',
                    'multiplier': 1.5,
                    'duration': 45  # minutes
                },
                'tier3': {
                    'names': [
                        'Lorde Supremo Voidbringer', 'Imperatriz Eterna das Trevas', 'Titã Primordial',
                        'Avatar da Destruição', 'Entidade Cósmica Malévola', 'Deus Antigo Desperto'
                    ],
                    'title': 'Vilão Lendário',
                    'color': 0xFF0000,  # Bright Red
                    'emoji': '☠️',
                    'multiplier': 2.5,
                    'duration': 60  # minutes
                }
            }

            # Determine tier based on recent activity and time of day
            now = datetime.now()
            current_hour = now.hour

            # Higher tier chance during peak hours and with more activity
            activity_count = sum(data.get('count', 0) for hour, data in PLAYER_ACTIVITY.items())
            recent_activity = sum(data.get('count', 0) for hour, data in PLAYER_ACTIVITY.items() 
                                if (current_hour - hour) % 24 <= 3)  # Last 3 hours

            # Base chances for each tier
            tier_chances = {'tier1': 0.7, 'tier2': 0.25, 'tier3': 0.05}

            # Adjust based on time of day
            if 17 <= current_hour <= 22:  # Evening hours - more chance for higher tiers
                tier_chances['tier1'] -= 0.2
                tier_chances['tier2'] += 0.1
                tier_chances['tier3'] += 0.1

            # Adjust based on activity
            if activity_count > 20 or recent_activity > 10:  # High activity
                tier_chances['tier1'] -= 0.1
                tier_chances['tier2'] -= 0.05
                tier_chances['tier3'] += 0.15

            # Select tier
            tier = random.choices(
                list(tier_chances.keys()),
                weights=list(tier_chances.values()),
                k=1
            )[0]

            # Get tier data
            tier_data = villain_tiers[tier]

            # Select villain name
            villain_name = random.choice(tier_data['names'])

            # Determine villain strength based on server activity and tier
            base_strength = 100
            activity_multiplier = max(1.0, min(3.0, 1.0 + (activity_count / 20)))
            tier_multiplier = tier_data['multiplier']

            villain_strength = int(base_strength * activity_multiplier * tier_multiplier)

            # Calculate rewards based on tier and strength
            base_exp_reward = 50
            base_tusd_reward = 25
            base_reputation_reward = 10

            exp_reward = int(base_exp_reward * tier_multiplier)
            tusd_reward = int(base_tusd_reward * tier_multiplier)
            reputation_reward = int(base_reputation_reward * tier_multiplier)

            # Create dynamic descriptions based on tier
            descriptions = {
                'tier1': [
                    f"O temível **{villain_name}** está invadindo a Academia Tokugawa!",
                    f"**{villain_name}** foi avistado nos portões da Academia! Todos em alerta!",
                    f"A Academia está sob ataque de **{villain_name}**! Preparem-se para o combate!"
                ],
                'tier2': [
                    f"ALERTA MÁXIMO! O poderoso **{villain_name}** está causando destruição na Academia!",
                    f"**{villain_name}** rompeu as defesas da Academia! Todos os estudantes são convocados!",
                    f"Um inimigo formidável, **{villain_name}**, está desafiando os heróis da Academia!"
                ],
                'tier3': [
                    f"EMERGÊNCIA TOTAL! O lendário **{villain_name}** está ameaçando toda a existência da Academia!",
                    f"O temido **{villain_name}** surgiu das sombras! A sobrevivência da Academia está em jogo!",
                    f"**{villain_name}** - uma ameaça de proporções catastróficas - está atacando! Todos os heróis são necessários!"
                ]
            }

            description = random.choice(descriptions[tier]) + "\n\n"
            description += f"**Força do Vilão:** {villain_strength} HP\n\n"
            description += f"Todos os estudantes devem se unir para derrotá-lo! Use o comando `/vilao atacar` para combater esta ameaça!\n\n"
            description += f"**Recompensas por participação:**\n"
            description += f"• {exp_reward} EXP (base)\n"
            description += f"• {tusd_reward} TUSD (base)\n"
            description += f"• {reputation_reward} pontos de Reputação (base)\n\n"
            description += f"**Quanto mais estudantes participarem, maiores serão as recompensas para todos!**"

            # Create event embed
            embed = create_basic_embed(
                title=f"{tier_data['emoji']} ALERTA: {tier_data['title']} {villain_name} está invadindo a Academia! {tier_data['emoji']}",
                description=description,
                color=tier_data['color']
            )

            # Add footer with time remaining
            duration_minutes = tier_data['duration']
            embed.set_footer(text=f"Evento ativo por {duration_minutes} minutos | Tier: {tier[-1]}")

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
                'end_time': datetime.now() + timedelta(minutes=tier_data['duration']),
                'participants': [],
                'data': {
                    'type': 'villain',
                    'name': villain_name,
                    'tier': tier,
                    'strength': villain_strength,
                    'current_hp': villain_strength,
                    'defeated': False,
                    'base_exp_reward': exp_reward,
                    'base_tusd_reward': tusd_reward,
                    'base_reputation_reward': reputation_reward,
                    'team_bonus_threshold': 5  # Number of participants needed for team bonus
                }
            }

            logger.info(f"Triggered {tier} villain event ({villain_name}) in channel {channel.name}")
        except Exception as e:
            logger.error(f"Error triggering villain event: {e}")

    async def trigger_collectible_event(self, channel):
        """Trigger a random collectible item appearance event."""
        try:
            # Create collectible event with expanded types and categories
            collectible_categories = {
                'ancient': {
                    'items': [
                        'Pergaminho Antigo', 'Tomo Ancestral', 'Relíquia Histórica', 
                        'Manuscrito Arcano', 'Artefato Perdido', 'Inscrição Rúnica'
                    ],
                    'emoji': '📜',
                    'description': 'conhecimento ancestral',
                    'buff': 'intellect'
                },
                'magical': {
                    'items': [
                        'Cristal Misterioso', 'Amuleto Encantado', 'Orbe Arcano', 
                        'Poção Brilhante', 'Essência Mágica', 'Pedra Elemental'
                    ],
                    'emoji': '✨',
                    'description': 'poder mágico',
                    'buff': 'power_stat'
                },
                'artifact': {
                    'items': [
                        'Fragmento de Artefato', 'Engrenagem Misteriosa', 'Dispositivo Estranho', 
                        'Componente Tecnológico', 'Mecanismo Antigo', 'Núcleo Energético'
                    ],
                    'emoji': '⚙️',
                    'description': 'tecnologia avançada',
                    'buff': 'dexterity'
                },
                'spiritual': {
                    'items': [
                        'Amuleto Espiritual', 'Talismã Protetor', 'Símbolo Sagrado', 
                        'Ícone Abençoado', 'Medalhão Divino', 'Selo Celestial'
                    ],
                    'emoji': '🔮',
                    'description': 'energia espiritual',
                    'buff': 'charisma'
                }
            }

            # Select a random category
            category = random.choice(list(collectible_categories.keys()))
            category_data = collectible_categories[category]

            # Select a random item from the category
            collectible_name = random.choice(category_data['items'])

            # Determine rarity with weighted probability
            rarities = ['common', 'uncommon', 'rare', 'epic', 'legendary']
            weights = [0.4, 0.3, 0.2, 0.08, 0.02]  # 40% common, 2% legendary
            rarity = random.choices(rarities, weights=weights, k=1)[0]

            # Rarity colors
            rarity_colors = {
                'common': 0x808080,      # Gray
                'uncommon': 0x00FF00,    # Green
                'rare': 0x0000FF,        # Blue
                'epic': 0x800080,        # Purple
                'legendary': 0xFFA500    # Orange
            }

            # Rarity indicators
            rarity_indicators = {
                'common': '',
                'uncommon': '★',
                'rare': '★★',
                'epic': '★★★',
                'legendary': '★★★★'
            }

            # Rarity translations to Portuguese
            rarity_pt = {
                'common': 'comum',
                'uncommon': 'incomum',
                'rare': 'raro',
                'epic': 'épico',
                'legendary': 'lendário'
            }

            # Determine rewards based on rarity
            reward_multipliers = {
                'common': 1.0,
                'uncommon': 2.0,
                'rare': 3.5,
                'epic': 5.0,
                'legendary': 10.0
            }

            # Base rewards
            base_exp = random.randint(5, 15)
            base_tusd = random.randint(3, 10)
            base_reputation = random.randint(1, 3)
            base_buff_duration = 24  # hours

            # Calculate actual rewards
            exp_reward = int(base_exp * reward_multipliers[rarity])
            tusd_reward = int(base_tusd * reward_multipliers[rarity])
            reputation_reward = int(base_reputation * reward_multipliers[rarity])
            buff_value = int(5 * reward_multipliers[rarity])
            buff_duration = int(base_buff_duration * reward_multipliers[rarity])

            # Create dynamic descriptions based on rarity and category
            descriptions = {
                'common': [
                    f"Um {rarity_pt[rarity]} **{collectible_name}** foi avistado na Academia Tokugawa!",
                    f"Um {rarity_pt[rarity]} **{collectible_name}** apareceu nos corredores da Academia!",
                    f"Alguém deixou um {rarity_pt[rarity]} **{collectible_name}** na sala de aula!"
                ],
                'uncommon': [
                    f"Um {rarity_pt[rarity]} **{collectible_name}** emitindo uma fraca aura foi encontrado!",
                    f"Um {rarity_pt[rarity]} **{collectible_name}** com propriedades interessantes apareceu!",
                    f"Um objeto incomum, um {rarity_pt[rarity]} **{collectible_name}**, foi detectado na Academia!"
                ],
                'rare': [
                    f"Um {rarity_pt[rarity]} **{collectible_name}** de grande poder foi descoberto!",
                    f"Um valioso {rarity_pt[rarity]} **{collectible_name}** apareceu misteriosamente!",
                    f"Um {rarity_pt[rarity]} **{collectible_name}** com propriedades únicas foi avistado!"
                ],
                'epic': [
                    f"Um {rarity_pt[rarity]} **{collectible_name}** de poder extraordinário surgiu na Academia!",
                    f"Um impressionante {rarity_pt[rarity]} **{collectible_name}** está emanando energia poderosa!",
                    f"Um {rarity_pt[rarity]} **{collectible_name}** de origem misteriosa apareceu!"
                ],
                'legendary': [
                    f"Um LENDÁRIO **{collectible_name}** de poder inimaginável foi descoberto!",
                    f"Um artefato de eras passadas, um {rarity_pt[rarity]} **{collectible_name}**, apareceu!",
                    f"Um {rarity_pt[rarity]} **{collectible_name}** que poucos já viram em vida foi encontrado!"
                ]
            }

            description = random.choice(descriptions[rarity]) + "\n\n"
            description += f"Este item contém {category_data['description']} que pode aumentar seus atributos!\n\n"
            description += f"Seja o primeiro a coletá-lo usando o comando `/item coletar` para ganhar:\n"
            description += f"• {exp_reward} EXP\n"
            description += f"• {tusd_reward} TUSD\n"
            description += f"• {reputation_reward} pontos de Reputação\n"
            description += f"• +{buff_value}% de {category_data['buff'].capitalize()} por {buff_duration} horas"

            # Create event embed
            embed = create_basic_embed(
                title=f"{category_data['emoji']} {rarity_indicators[rarity]} Um {collectible_name} apareceu! {rarity_indicators[rarity]} {category_data['emoji']}",
                description=description,
                color=rarity_colors.get(rarity, 0x1E90FF)
            )

            # Add rarity footer
            embed.set_footer(text=f"Raridade: {rarity_pt[rarity].capitalize()} | Categoria: {category.capitalize()}")

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
                    'exp_reward': exp_reward,
                    'tusd_reward': tusd_reward,
                    'reputation_reward': reputation_reward,
                    'item': {
                        'name': collectible_name,
                        'description': f"Um {rarity_pt[rarity]} {category} item coletado durante um evento especial. Contém {category_data['description']}.",
                        'type': 'collectible',
                        'rarity': rarity,
                        'effects': {
                            'attribute': category_data['buff'],
                            'value': buff_value,
                            'duration': buff_duration
                        }
                    }
                }
            }

            logger.info(f"Triggered collectible event in channel {channel.name}")
        except Exception as e:
            logger.error(f"Error triggering collectible event: {e}")

    async def announce_daily_subject(self):
        """Announce the daily subject and start the quiz event."""
        try:
            if not DAILY_SUBJECT:
                logger.error("No daily subject selected")
                # Try to set a default subject
                try:
                    logger.info("Setting default subject for announcement")
                    DAILY_SUBJECT.clear()
                    DAILY_SUBJECT.update({
                        'subject': 'Matemática',
                        'emoji': '🧮',
                        'description': 'Hoje é dia de Matemática! Participe do quiz para ganhar notas e XP!',
                        'difficulty': 1,
                        'questions': [
                            {
                                'question': 'Quanto é 2 + 2?',
                                'options': ['3', '4', '5', '6'],
                                'correct': 1,  # 4
                                'difficulty': 1
                            }
                        ]
                    })
                    logger.info(f"Set default subject: {DAILY_SUBJECT['subject']}")
                except Exception as e:
                    logger.error(f"Error setting default subject: {e}")
                    return

            # If we still don't have a channel ID, try to find one
            if not self.announcement_channel_id:
                await self.find_channels()

            if not self.announcement_channel_id:
                logger.error("No announcement channel available for daily subject announcement")
                return

            channel = self.bot.get_channel(self.announcement_channel_id)
            if not channel:
                logger.error(f"Could not find announcement channel with ID {self.announcement_channel_id}")
                # Try to find channels again
                await self.find_channels()
                channel = self.bot.get_channel(self.announcement_channel_id)
                if not channel:
                    logger.error("Still could not find announcement channel after retry")
                    return

            # Create subject announcement embed
            embed = create_basic_embed(
                title=f"{DAILY_SUBJECT['emoji']} Aula de {DAILY_SUBJECT['subject']} {DAILY_SUBJECT['emoji']}",
                description=(
                    f"{DAILY_SUBJECT['description']}\n\n"
                    f"**Dificuldade:** {'⭐' * DAILY_SUBJECT['difficulty']}\n\n"
                    f"Para participar do quiz e ganhar notas, use o comando `/quiz participar`.\n"
                    f"O quiz estará disponível durante todo o dia de hoje!"
                ),
                color=0x4169E1  # Royal Blue
            )

            # Send the announcement
            await channel.send(
                content="@everyone Uma nova aula começou na Academia Tokugawa!",
                embed=embed
            )

            # Store event data
            event_id = f"daily_subject_{datetime.now().strftime('%Y%m%d')}"
            ACTIVE_EVENTS[event_id] = {
                'channel_id': channel.id,
                'message_id': None,  # No specific message to track
                'start_time': datetime.now(),
                'end_time': datetime.now().replace(hour=23, minute=59, second=59),  # End at midnight
                'participants': [],
                'data': {
                    'type': 'daily_subject',
                    'subject': DAILY_SUBJECT['subject'],
                    'difficulty': DAILY_SUBJECT['difficulty'],
                    'questions': DAILY_SUBJECT['questions']
                }
            }

            logger.info(f"Daily subject announced: {DAILY_SUBJECT['subject']}")
        except Exception as e:
            logger.error(f"Error announcing daily subject: {e}")

    async def evaluate_quiz_answer(self, interaction, question_index, answer_index):
        """Evaluate a quiz answer and update player's grade."""
        try:
            # Get the active quiz event
            event_id = f"daily_subject_{datetime.now().strftime('%Y%m%d')}"
            quiz_event = ACTIVE_EVENTS.get(event_id)

            if not quiz_event:
                await interaction.response.send_message("Não há nenhum quiz ativo hoje.", ephemeral=True)
                return

            # Get player
            player = get_player(interaction.user.id)
            if not player:
                await interaction.response.send_message("Você precisa estar registrado para participar do quiz.", ephemeral=True)
                return

            # Check if player already participated
            if interaction.user.id in quiz_event['participants']:
                await interaction.response.send_message("Você já participou do quiz de hoje.", ephemeral=True)
                return

            # Get question and correct answer
            questions = quiz_event['data']['questions']
            if question_index >= len(questions):
                await interaction.response.send_message("Pergunta inválida.", ephemeral=True)
                return

            question = questions[question_index]
            correct_answer_index = question['correct']

            # Check if answer is correct
            is_correct = answer_index == correct_answer_index

            # Calculate grade based on difficulty and correctness
            max_grade = 10.0
            question_difficulty = question['difficulty']
            subject_difficulty = quiz_event['data']['difficulty']

            # Base grade for participation
            base_grade = 5.0

            # Additional grade for correct answer, weighted by difficulty
            difficulty_multiplier = (question_difficulty + subject_difficulty) / 2
            correct_bonus = (max_grade - base_grade) * (difficulty_multiplier / 3)

            final_grade = base_grade
            if is_correct:
                final_grade += correct_bonus

            # Round to one decimal place
            final_grade = round(final_grade, 1)

            # Get current month and year
            now = datetime.now()
            current_month = now.month
            current_year = now.year

            # Update player's grade in the database
            subject = quiz_event['data']['subject']
            update_player_grade(interaction.user.id, subject, final_grade, current_month, current_year)

            # Add player to participants
            quiz_event['participants'].append(interaction.user.id)

            # Calculate XP reward based on grade and difficulty
            xp_reward = int(final_grade * (subject_difficulty + 1))

            # Apply club buffs if any
            if player.get('club_id') and player['club_id'] in CLUB_BUFFS:
                buff = CLUB_BUFFS[player['club_id']]
                if buff['type'] == 'exp':
                    xp_reward = int(xp_reward * (1 + buff['value'] / 100))

            # Apply weekly theme buff if applicable
            if WEEKLY_THEME and 'subjects' in WEEKLY_THEME.get('buffs', {}) and subject in WEEKLY_THEME['buffs']['subjects']:
                xp_multiplier = WEEKLY_THEME['buffs'].get('exp_multiplier', 1.0)
                xp_reward = int(xp_reward * xp_multiplier)

            # Update player XP
            update_player(
                interaction.user.id,
                exp=player['exp'] + xp_reward
            )

            # Track progress for rankings
            if interaction.user.id not in PLAYER_PROGRESS['daily']:
                PLAYER_PROGRESS['daily'][interaction.user.id] = {'exp_gained': 0, 'duels_won': 0, 'events_completed': 0}
            if interaction.user.id not in PLAYER_PROGRESS['weekly']:
                PLAYER_PROGRESS['weekly'][interaction.user.id] = {'exp_gained': 0, 'duels_won': 0, 'events_completed': 0}

            PLAYER_PROGRESS['daily'][interaction.user.id]['exp_gained'] += xp_reward
            PLAYER_PROGRESS['daily'][interaction.user.id]['events_completed'] += 1
            PLAYER_PROGRESS['weekly'][interaction.user.id]['exp_gained'] += xp_reward
            PLAYER_PROGRESS['weekly'][interaction.user.id]['events_completed'] += 1

            # Check if player learns a technique (only if answer is correct)
            technique_learned = None
            if is_correct:
                # 30% chance to learn a technique if answer is correct
                if random.random() < 0.3:
                    try:
                        # Import TECHNIQUES from economy.py
                        from cogs.economy import TECHNIQUES

                        # Get player's techniques
                        techniques = player['techniques']

                        # Filter techniques the player doesn't have yet
                        available_techniques = [t for t in TECHNIQUES if str(t["id"]) not in techniques]

                        if available_techniques:
                            # Select a random technique to learn
                            technique = random.choice(available_techniques)

                            # Add technique to player's techniques
                            techniques[str(technique["id"])] = technique

                            # Update player in database
                            update_player(
                                interaction.user.id,
                                techniques=json.dumps(techniques)
                            )

                            technique_learned = technique
                    except Exception as e:
                        logger.error(f"Error learning technique: {e}")

            # Send result message
            if is_correct:
                result_message = f"✅ Resposta correta! Sua nota foi {final_grade}/10.0"
            else:
                correct_option = question['options'][correct_answer_index]
                result_message = f"❌ Resposta incorreta. A resposta correta era: {correct_option}\nSua nota foi {final_grade}/10.0"

            # Build rewards description
            rewards_description = (
                f"**Recompensas:**\n"
                f"- +{xp_reward} EXP\n"
                f"- Nota registrada para o mês de {now.strftime('%B/%Y')}"
            )

            # Add technique learned if any
            if technique_learned:
                rewards_description += f"\n- Técnica aprendida: **{technique_learned['name']}**"

            await interaction.response.send_message(
                embed=create_basic_embed(
                    title=f"Resultado do Quiz de {subject}",
                    description=(
                        f"{result_message}\n\n"
                        f"{rewards_description}"
                    ),
                    color=0x00FF00 if is_correct else 0xFF0000
                ),
                ephemeral=True
            )

            logger.info(f"Player {player['name']} completed quiz with grade {final_grade}")

        except Exception as e:
            logger.error(f"Error evaluating quiz answer: {e}")
            await interaction.response.send_message("Ocorreu um erro ao avaliar sua resposta.", ephemeral=True)

    async def check_monthly_grades(self):
        """Check if it's the end of the month and evaluate monthly grades."""
        try:
            now = datetime.now()

            # Check if it's the last day of the month
            tomorrow = now + timedelta(days=1)
            if now.month != tomorrow.month:
                logger.info("End of month detected, evaluating monthly grades")

                # Get all players
                conn = sqlite3.connect('data/tokugawa.db')
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute("SELECT user_id, name FROM players")
                players = cursor.fetchall()
                conn.close()

                for player in players:
                    user_id = player['user_id']
                    name = player['name']

                    # Get player's grades for this month
                    grades = get_monthly_average_grades(user_id, now.month, now.year)

                    if grades:
                        # Calculate how many subjects the player passed
                        passing_grade = 6.0
                        passed_subjects = [g for g in grades if g['average_grade'] >= passing_grade]

                        if passed_subjects:
                            # Calculate rewards based on number of passed subjects
                            num_passed = len(passed_subjects)
                            xp_reward = 50 * num_passed
                            reputation_reward = 10 * num_passed

                            # Update player
                            player_data = get_player(user_id)
                            if player_data:
                                update_player(
                                    user_id,
                                    exp=player_data['exp'] + xp_reward
                                )

                                # Update reputation
                                update_player_reputation(user_id, reputation_reward)

                                logger.info(f"Player {name} passed {num_passed} subjects, awarded {xp_reward} XP and {reputation_reward} reputation")

                # If there's an announcement channel, send a message
                if self.announcement_channel_id:
                    channel = self.bot.get_channel(self.announcement_channel_id)
                    if channel:
                        await channel.send(
                            embed=create_basic_embed(
                                title="📚 Avaliação Mensal da Academia Tokugawa 📚",
                                description=(
                                    f"O mês de {now.strftime('%B/%Y')} chegou ao fim!\n\n"
                                    f"As notas mensais foram avaliadas e os alunos que obtiveram média igual ou superior a 6,0 em qualquer matéria receberam recompensas!\n\n"
                                    f"Parabéns a todos os alunos que se dedicaram aos estudos este mês!"
                                ),
                                color=0x4169E1
                            )
                        )
        except Exception as e:
            logger.error(f"Error checking monthly grades: {e}")

    async def check_dia_de_materia_event(self):
        """Check if it's time to create the 'Dia de Matéria' event."""
        try:
            now = datetime.now()

            # Create event ID for the current month
            event_id = f"dia_de_materia_{now.strftime('%Y%m')}"

            # Check if the event already exists
            if event_id in ACTIVE_EVENTS:
                logger.info(f"'Dia de Matéria' event already exists for {now.strftime('%B/%Y')}")
                return

            # If we don't have a channel ID, try to find one
            if not self.announcement_channel_id:
                await self.find_channels()

            if not self.announcement_channel_id:
                logger.error("No announcement channel available for 'Dia de Matéria' event")
                return

            channel = self.bot.get_channel(self.announcement_channel_id)
            if not channel:
                logger.error(f"Could not find announcement channel with ID {self.announcement_channel_id}")
                # Try to find channels again
                await self.find_channels()
                channel = self.bot.get_channel(self.announcement_channel_id)
                if not channel:
                    logger.error("Still could not find announcement channel after retry")
                    return

            # Calculate event end date (last day of the current month)
            next_month = now.replace(day=28) + timedelta(days=4)  # Move to next month
            end_date = next_month.replace(day=1) - timedelta(days=1)  # Last day of current month
            end_date = end_date.replace(hour=23, minute=59, second=59)  # End at midnight

            # Create event announcement embed
            embed = create_basic_embed(
                title="📚 Evento: Dia de Matéria 📚",
                description=(
                    "Prepare-se! O evento 'Dia de Matéria' está programado para começar em breve e testará suas habilidades intelectuais.\n\n"
                    "Durante este evento, você terá a oportunidade de demonstrar seu conhecimento em diversas matérias e ganhar recompensas especiais!\n\n"
                    "Fique atento aos anúncios diários para participar dos quizzes e melhorar suas notas!"
                ),
                color=0x4169E1  # Royal Blue
            )

            # Send the announcement
            message = await channel.send(
                content="@everyone Um novo evento mensal está chegando!",
                embed=embed
            )

            # Store event data
            ACTIVE_EVENTS[event_id] = {
                'channel_id': channel.id,
                'message_id': message.id,
                'start_time': now,
                'end_time': end_date,
                'participants': [],
                'data': {
                    'type': 'dia_de_materia',
                    'month': now.month,
                    'year': now.year,
                    'description': "Evento mensal que testa suas habilidades intelectuais em diversas matérias."
                }
            }

            logger.info(f"Created 'Dia de Matéria' event for {now.strftime('%B/%Y')}")

        except Exception as e:
            logger.error(f"Error creating 'Dia de Matéria' event: {e}")

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

                    # Handle Dia de Matéria event cleanup
                    elif 'dia_de_materia' in event_id:
                        try:
                            channel = self.bot.get_channel(event_data['channel_id'])
                            if channel:
                                await channel.send(
                                    embed=create_basic_embed(
                                        title="📚 Evento: Dia de Matéria - Encerrado 📚",
                                        description=(
                                            f"O evento 'Dia de Matéria' do mês de {event_data['data']['month']}/{event_data['data']['year']} foi encerrado!\n\n"
                                            f"Esperamos que você tenha aproveitado para melhorar suas habilidades intelectuais.\n\n"
                                            f"Um novo evento começará no próximo mês. Fique atento!"
                                        ),
                                        color=0x4169E1  # Royal Blue
                                    )
                                )
                        except Exception as e:
                            logger.error(f"Error sending Dia de Matéria end message: {e}")

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

    # Quiz command group
    quiz_group = app_commands.Group(name="quiz", description="Comandos relacionados aos quizzes diários da Academia Tokugawa")

    @quiz_group.command(name="participar", description="Participar do quiz diário da matéria atual")
    async def slash_quiz_participate(self, interaction: discord.Interaction):
        """Participate in the daily subject quiz."""
        try:
            # Get the active quiz event
            event_id = f"daily_subject_{datetime.now().strftime('%Y%m%d')}"
            quiz_event = ACTIVE_EVENTS.get(event_id)

            if not quiz_event:
                await interaction.response.send_message("Não há nenhum quiz ativo hoje. Aguarde o anúncio da próxima aula!", ephemeral=True)
                return

            # Get player
            player = get_player(interaction.user.id)
            if not player:
                await interaction.response.send_message("Você precisa estar registrado para participar do quiz. Use /registro ingressar para criar seu personagem.", ephemeral=True)
                return

            # Check if player already participated
            if interaction.user.id in quiz_event['participants']:
                await interaction.response.send_message("Você já participou do quiz de hoje. Volte amanhã para um novo quiz!", ephemeral=True)
                return

            # Get a random question from the quiz
            questions = quiz_event['data']['questions']
            if not questions:
                await interaction.response.send_message("Este quiz não possui perguntas. Por favor, informe um administrador.", ephemeral=True)
                return

            question_index = random.randint(0, len(questions) - 1)
            question = questions[question_index]

            # Create options for the select menu
            options = []
            for i, option_text in enumerate(question['options']):
                options.append(
                    discord.SelectOption(
                        label=option_text,
                        value=str(i),
                        description=f"Opção {i+1}"
                    )
                )

            # Create select menu for answering
            select = discord.ui.Select(
                placeholder="Escolha sua resposta",
                options=options
            )

            # Create view with select menu
            view = discord.ui.View(timeout=60)  # 60 seconds timeout
            view.add_item(select)

            # Handle select menu interaction
            async def select_callback(select_interaction):
                if select_interaction.user.id != interaction.user.id:
                    await select_interaction.response.send_message("Este não é o seu quiz!", ephemeral=True)
                    return

                # Get selected answer
                answer_index = int(select_interaction.data['values'][0])

                # Evaluate answer
                await self.evaluate_quiz_answer(select_interaction, question_index, answer_index)

                # Disable the select menu
                select.disabled = True
                await interaction.edit_original_response(view=view)

            select.callback = select_callback

            # Send the quiz question
            subject = quiz_event['data']['subject']
            await interaction.response.send_message(
                embed=create_basic_embed(
                    title=f"Quiz de {subject}",
                    description=(
                        f"**Pergunta:** {question['question']}\n\n"
                        f"Escolha a resposta correta no menu abaixo."
                    ),
                    color=0x4169E1
                ),
                view=view,
                ephemeral=True
            )

            logger.info(f"Player {player['name']} started quiz for subject {subject}")

        except Exception as e:
            logger.error(f"Error in slash_quiz_participate: {e}")
            await interaction.response.send_message("Ocorreu um erro ao iniciar o quiz.", ephemeral=True)

    @quiz_group.command(name="notas", description="Ver suas notas nas diferentes matérias")
    async def slash_quiz_grades(self, interaction: discord.Interaction):
        """View your grades in different subjects."""
        try:
            # Get player
            player = get_player(interaction.user.id)
            if not player:
                await interaction.response.send_message("Você precisa estar registrado para ver suas notas. Use /registro ingressar para criar seu personagem.", ephemeral=True)
                return

            # Get current month and year
            now = datetime.now()
            current_month = now.month
            current_year = now.year

            # Get player's grades
            grades = get_player_grades(interaction.user.id, month=current_month, year=current_year)

            if not grades:
                await interaction.response.send_message("Você ainda não possui notas registradas neste mês.", ephemeral=True)
                return

            # Group grades by subject
            subjects_grades = {}
            for grade in grades:
                subject = grade['subject']
                if subject not in subjects_grades:
                    subjects_grades[subject] = []
                subjects_grades[subject].append(grade['grade'])

            # Calculate average for each subject
            averages = {}
            for subject, grades_list in subjects_grades.items():
                averages[subject] = sum(grades_list) / len(grades_list)

            # Create embed with grades
            description = f"**Notas do mês de {now.strftime('%B/%Y')}:**\n\n"

            for subject, average in averages.items():
                # Determine if passing or failing
                status = "✅ Aprovado" if average >= 6.0 else "❌ Reprovado"
                description += f"**{subject}:** {average:.1f}/10.0 - {status}\n"

            await interaction.response.send_message(
                embed=create_basic_embed(
                    title=f"Boletim de {player['name']}",
                    description=description,
                    color=0x4169E1
                ),
                ephemeral=True
            )

            logger.info(f"Player {player['name']} viewed their grades")

        except Exception as e:
            logger.error(f"Error in slash_quiz_grades: {e}")
            await interaction.response.send_message("Ocorreu um erro ao buscar suas notas.", ephemeral=True)

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
