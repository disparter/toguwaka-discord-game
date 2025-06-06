import discord
from discord.ext import commands
from discord import app_commands
import logging
import random
import asyncio
import json
from datetime import datetime
from utils.database import get_player, update_player, get_club, get_all_clubs
from utils.embeds import create_basic_embed, create_event_embed
from utils.game_mechanics import calculate_level_from_exp

logger = logging.getLogger('tokugawa_bot')

# Story mode progression tracking
# This will be stored in the player's data
# Format: {
#   "current_year": 1,
#   "current_chapter": 1,
#   "completed_chapters": [],
#   "club_progress": {},
#   "villain_defeats": [],
#   "minion_defeats": []
# }

# Story chapters structure
STORY_CHAPTERS = {
    1: {  # Year 1
        1: {
            "title": "Meu Primeiro Dia de Aula",
            "description": "Seu primeiro dia na Academia Tokugawa. Conheça a escola e seus colegas.",
            "dialogues": [
                {"npc": "Diretor", "text": "Bem-vindo à Academia Tokugawa! Estamos felizes em receber mais um estudante com habilidades especiais."},
                {"npc": "Diretor", "text": "Aqui você aprenderá a controlar e aprimorar seus poderes, além de receber uma educação de primeira classe."},
                {"npc": "Diretor", "text": "Lembre-se: com grandes poderes, vêm grandes responsabilidades. Esperamos que você honre o nome da nossa academia."},
                {"npc": "Junie", "text": "Olá! Eu sou Junie, sua assistente virtual. Estou aqui para ajudar com qualquer dúvida que você tenha sobre a academia."},
                {"npc": "Junie", "text": "Vamos começar com um tour pela escola? Temos vários clubes que você pode conhecer!"}
            ],
            "choices": [
                {"text": "Sim, vamos conhecer os clubes!", "next_dialogue": 5},
                {"text": "Prefiro explorar por conta própria.", "next_dialogue": 6}
            ],
            "completion_exp": 50,
            "completion_tusd": 100,
            "next_chapter": 2
        },
        2: {
            "title": "Registro no Clube",
            "description": "Escolha um clube para se juntar e conheça seu líder.",
            "dialogues": [
                {"npc": "Junie", "text": "Agora é hora de escolher um clube! Cada clube tem seu próprio foco e atividades."},
                {"npc": "Junie", "text": "Você já está registrado no clube {club_name}. Vamos conhecer o líder do clube!"}
            ],
            "club_leaders": {
                1: {"name": "Kai Flameheart", "description": "Um jovem de cabelos vermelhos e temperamento explosivo, mas com um coração leal."},
                2: {"name": "Luna Mindweaver", "description": "Uma garota misteriosa de olhos violeta que parece sempre saber o que você está pensando."},
                3: {"name": "Alexander Strategos", "description": "Um rapaz calculista de óculos que analisa cada situação como um jogo de xadrez."},
                4: {"name": "Gaia Naturae", "description": "Uma estudante serena conectada com a natureza, capaz de manipular todos os elementos."},
                5: {"name": "Ryuji Battleborn", "description": "Um lutador disciplinado que valoriza a força e a honra acima de tudo."}
            },
            "club_dialogues": {
                1: [  # Clube das Chamas
                    {"npc": "Kai Flameheart", "text": "Então você é o novato? Espero que tenha coragem suficiente para aguentar o calor do nosso treinamento!"},
                    {"npc": "Kai Flameheart", "text": "No Clube das Chamas, valorizamos a paixão e a intensidade. Nossos poderes são destrutivos, mas aprendemos a controlá-los."},
                    {"npc": "Kai Flameheart", "text": "Estamos sempre em rivalidade com os Elementalistas, mas é uma competição saudável... na maioria das vezes."}
                ],
                2: [  # Ilusionistas Mentais
                    {"npc": "Luna Mindweaver", "text": "Ah, uma nova mente para nossa coleção. Bem-vindo aos Ilusionistas Mentais."},
                    {"npc": "Luna Mindweaver", "text": "Aqui exploramos os recantos da mente e os limites da percepção. A realidade é apenas o que acreditamos que seja."},
                    {"npc": "Luna Mindweaver", "text": "Tenha cuidado com o Conselho Político. Eles sempre têm segundas intenções... não que nós não tenhamos também."}
                ],
                3: [  # Conselho Político
                    {"npc": "Alexander Strategos", "text": "Um novo peão no tabuleiro. Interessante. Bem-vindo ao Conselho Político."},
                    {"npc": "Alexander Strategos", "text": "Nosso clube controla a política estudantil da academia. Influência e estratégia são nossas armas."},
                    {"npc": "Alexander Strategos", "text": "Os Ilusionistas pensam que podem ler nossas mentes, mas sempre estamos três passos à frente."}
                ],
                4: [  # Elementalistas
                    {"npc": "Gaia Naturae", "text": "A natureza te trouxe até nós. Seja bem-vindo aos Elementalistas."},
                    {"npc": "Gaia Naturae", "text": "Estudamos a harmonia dos elementos e como utilizá-los em equilíbrio com o mundo ao nosso redor."},
                    {"npc": "Gaia Naturae", "text": "O Clube das Chamas tem poder, mas falta-lhes controle e respeito pelos elementos."}
                ],
                5: [  # Clube de Combate
                    {"npc": "Ryuji Battleborn", "text": "Mais um guerreiro se junta às nossas fileiras. Mostre seu valor no Clube de Combate."},
                    {"npc": "Ryuji Battleborn", "text": "Aqui, aprimoramos nossas técnicas de luta e nos tornamos mais fortes a cada dia. A disciplina é nossa fundação."},
                    {"npc": "Ryuji Battleborn", "text": "Todos os outros clubes têm suas forças, mas no final, é o guerreiro mais forte que permanece de pé."}
                ]
            },
            "completion_exp": 75,
            "completion_tusd": 150,
            "next_chapter": 3
        },
        3: {
            "title": "Primeiro Desafio",
            "description": "Enfrente seu primeiro desafio na academia: um estudante valentão que está intimidando os calouros.",
            "dialogues": [
                {"npc": "Estudante Assustado", "text": "P-por favor, ajude! Tem um valentão do terceiro ano intimidando todos os calouros!"},
                {"npc": "Junie", "text": "Isso é um problema sério. Como você quer lidar com isso?"}
            ],
            "choices": [
                {"text": "Confrontar o valentão diretamente", "next_dialogue": 2, "attribute_check": "power_stat", "threshold": 7},
                {"text": "Tentar conversar e resolver pacificamente", "next_dialogue": 3, "attribute_check": "charisma", "threshold": 7},
                {"text": "Elaborar um plano estratégico", "next_dialogue": 4, "attribute_check": "intellect", "threshold": 7},
                {"text": "Pedir ajuda a um professor", "next_dialogue": 5}
            ],
            "minion_battle": {
                "name": "Drake, o Valentão",
                "description": "Um estudante arrogante do terceiro ano que gosta de intimidar os mais fracos.",
                "power": "Super Força",
                "level": 5,
                "hp": 100,
                "attributes": {
                    "dexterity": 8,
                    "intellect": 5,
                    "charisma": 3,
                    "power_stat": 10
                }
            },
            "completion_exp": 100,
            "completion_tusd": 200,
            "next_chapter": 4
        }
    }
}

# Club NPCs
CLUB_NPCS = {
    1: [  # Clube das Chamas
        {"name": "Kai Flameheart", "role": "Líder", "power": "Explosão de Fogo", "personality": "Intenso e leal"},
        {"name": "Ember", "role": "Vice-líder", "power": "Manipulação de Calor", "personality": "Calma e calculista"},
        {"name": "Blaze", "role": "Membro", "power": "Corpo de Magma", "personality": "Impulsivo e enérgico"}
    ],
    2: [  # Ilusionistas Mentais
        {"name": "Luna Mindweaver", "role": "Líder", "power": "Ilusão Total", "personality": "Misteriosa e perspicaz"},
        {"name": "Mirage", "role": "Vice-líder", "power": "Manipulação de Memória", "personality": "Gentil mas manipulador"},
        {"name": "Enigma", "role": "Membro", "power": "Projeção Astral", "personality": "Introvertido e observador"}
    ],
    3: [  # Conselho Político
        {"name": "Alexander Strategos", "role": "Líder", "power": "Persuasão Absoluta", "personality": "Calculista e ambicioso"},
        {"name": "Victoria", "role": "Vice-líder", "power": "Detecção de Mentiras", "personality": "Justa e rigorosa"},
        {"name": "Machiavelli", "role": "Membro", "power": "Manipulação Emocional", "personality": "Astuto e oportunista"}
    ],
    4: [  # Elementalistas
        {"name": "Gaia Naturae", "role": "Líder", "power": "Harmonia Elemental", "personality": "Serena e sábia"},
        {"name": "Aero", "role": "Vice-líder", "power": "Controle do Ar", "personality": "Livre e imprevisível"},
        {"name": "Terra", "role": "Membro", "power": "Manipulação da Terra", "personality": "Estável e confiável"}
    ],
    5: [  # Clube de Combate
        {"name": "Ryuji Battleborn", "role": "Líder", "power": "Força Sobre-Humana", "personality": "Disciplinado e honrado"},
        {"name": "Fist", "role": "Vice-líder", "power": "Impacto de Choque", "personality": "Agressivo mas justo"},
        {"name": "Shadow", "role": "Membro", "power": "Velocidade Extrema", "personality": "Silencioso e letal"}
    ]
}

class StoryMode(commands.Cog):
    """Cog for the story mode functionality."""

    def __init__(self, bot):
        self.bot = bot
        self.active_stories = {}  # {user_id: {current_dialogue: int, chapter_data: dict}}

    # Group for story commands
    story_group = app_commands.Group(name="historia", description="Comandos do modo história da Academia Tokugawa")

    @story_group.command(name="iniciar", description="Iniciar ou continuar sua jornada no modo história")
    async def slash_start_story(self, interaction: discord.Interaction):
        """Start or continue the story mode."""
        try:
            # Check if player exists
            player = get_player(interaction.user.id)
            if not player:
                await interaction.response.send_message(
                    f"{interaction.user.mention}, você ainda não está registrado na Academia Tokugawa. "
                    f"Use /registro ingressar para criar seu personagem."
                )
                return

            # Check if player has story progress
            story_progress = player.get('story_progress', None)
            if not story_progress:
                # Initialize story progress
                story_progress = {
                    "current_year": 1,
                    "current_chapter": 1,
                    "completed_chapters": [],
                    "club_progress": {},
                    "villain_defeats": [],
                    "minion_defeats": []
                }
                
                # Update player with initial story progress
                update_player(interaction.user.id, story_progress=json.dumps(story_progress))
            elif isinstance(story_progress, str):
                # Parse JSON string to dict
                story_progress = json.loads(story_progress)

            # Get current chapter data
            year = story_progress["current_year"]
            chapter = story_progress["current_chapter"]
            
            if year in STORY_CHAPTERS and chapter in STORY_CHAPTERS[year]:
                chapter_data = STORY_CHAPTERS[year][chapter]
                
                # Send chapter intro
                embed = create_basic_embed(
                    title=f"Ano {year}, Capítulo {chapter}: {chapter_data['title']}",
                    description=chapter_data['description'],
                    color=0x9370DB  # Medium Purple
                )
                
                await interaction.response.send_message(embed=embed)
                
                # Start the story dialogue
                self.active_stories[interaction.user.id] = {
                    "current_dialogue": 0,
                    "chapter_data": chapter_data
                }
                
                # Send first dialogue
                await self.send_next_dialogue(interaction.user.id, interaction.channel)
            else:
                await interaction.response.send_message(
                    f"{interaction.user.mention}, não foi possível encontrar o próximo capítulo da história. "
                    f"Novos capítulos serão adicionados em breve!"
                )
        except Exception as e:
            logger.error(f"Error in slash_start_story: {e}")
            await interaction.response.send_message("Ocorreu um erro ao iniciar o modo história. Por favor, tente novamente mais tarde.")

    @story_group.command(name="status", description="Verificar seu progresso no modo história")
    async def slash_story_status(self, interaction: discord.Interaction):
        """Check story mode progress."""
        try:
            # Check if player exists
            player = get_player(interaction.user.id)
            if not player:
                await interaction.response.send_message(
                    f"{interaction.user.mention}, você ainda não está registrado na Academia Tokugawa. "
                    f"Use /registro ingressar para criar seu personagem."
                )
                return

            # Check if player has story progress
            story_progress = player.get('story_progress', None)
            if not story_progress:
                await interaction.response.send_message(
                    f"{interaction.user.mention}, você ainda não iniciou o modo história. "
                    f"Use /historia iniciar para começar sua jornada!"
                )
                return
            elif isinstance(story_progress, str):
                # Parse JSON string to dict
                story_progress = json.loads(story_progress)

            # Create embed with story progress
            embed = create_basic_embed(
                title=f"Progresso da História de {player['name']}",
                description=f"Acompanhe sua jornada na Academia Tokugawa!",
                color=0x9370DB  # Medium Purple
            )
            
            # Add current progress
            embed.add_field(
                name="Progresso Atual",
                value=f"**Ano:** {story_progress['current_year']}\n"
                      f"**Capítulo:** {story_progress['current_chapter']}",
                inline=False
            )
            
            # Add completed chapters
            completed = story_progress['completed_chapters']
            if completed:
                completed_text = "\n".join([f"Ano {c.split('-')[0]}, Capítulo {c.split('-')[1]}" for c in completed])
            else:
                completed_text = "Nenhum capítulo concluído ainda."
                
            embed.add_field(
                name="Capítulos Concluídos",
                value=completed_text,
                inline=False
            )
            
            # Add villain defeats if any
            villains = story_progress['villain_defeats']
            if villains:
                villains_text = "\n".join(villains)
                embed.add_field(
                    name="Vilões Derrotados",
                    value=villains_text,
                    inline=False
                )
            
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            logger.error(f"Error in slash_story_status: {e}")
            await interaction.response.send_message("Ocorreu um erro ao verificar o progresso da história. Por favor, tente novamente mais tarde.")

    async def send_next_dialogue(self, user_id, channel):
        """Send the next dialogue in the story."""
        if user_id not in self.active_stories:
            return
        
        story_data = self.active_stories[user_id]
        current_dialogue = story_data["current_dialogue"]
        chapter_data = story_data["chapter_data"]
        
        # Check if we've reached the end of dialogues
        if current_dialogue >= len(chapter_data["dialogues"]):
            # Check if there are choices to make
            if "choices" in chapter_data:
                await self.send_choices(user_id, channel, chapter_data["choices"])
            else:
                # Complete the chapter
                await self.complete_chapter(user_id, channel)
            return
        
        # Get the current dialogue
        dialogue = chapter_data["dialogues"][current_dialogue]
        
        # Get player data for personalization
        player = get_player(user_id)
        club = get_club(player['club_id']) if player and player.get('club_id') else None
        
        # Replace placeholders in text
        text = dialogue["text"]
        if "{player_name}" in text:
            text = text.replace("{player_name}", player['name'])
        if "{club_name}" in text and club:
            text = text.replace("{club_name}", club['name'])
        
        # Create embed for dialogue
        embed = create_basic_embed(
            title=f"{dialogue['npc']}",
            description=text,
            color=0x9370DB  # Medium Purple
        )
        
        # Send the dialogue
        message = await channel.send(embed=embed)
        
        # Increment dialogue counter
        self.active_stories[user_id]["current_dialogue"] += 1
        
        # Wait a moment before sending next dialogue
        await asyncio.sleep(3)
        
        # Send next dialogue
        await self.send_next_dialogue(user_id, channel)

    async def send_choices(self, user_id, channel, choices):
        """Send choices for the player to make."""
        # Create embed for choices
        embed = create_basic_embed(
            title="O que você vai fazer?",
            description="Escolha sua próxima ação:",
            color=0x9370DB  # Medium Purple
        )
        
        # Create buttons for choices
        view = discord.ui.View(timeout=60)
        
        for i, choice in enumerate(choices):
            button = discord.ui.Button(label=choice["text"], style=discord.ButtonStyle.primary, custom_id=str(i))
            
            async def button_callback(interaction, choice_index=i):
                if interaction.user.id != user_id:
                    await interaction.response.send_message("Esta não é sua história!", ephemeral=True)
                    return
                
                # Disable all buttons
                for child in view.children:
                    child.disabled = True
                await interaction.message.edit(view=view)
                
                # Process the choice
                chosen = choices[choice_index]
                
                # Check if there's an attribute check
                if "attribute_check" in chosen:
                    player = get_player(user_id)
                    attribute = chosen["attribute_check"]
                    threshold = chosen["threshold"]
                    
                    if player[attribute] >= threshold:
                        await interaction.response.send_message(f"Seu {attribute} é alto o suficiente para esta ação!")
                        
                        # Set the next dialogue based on successful check
                        self.active_stories[user_id]["current_dialogue"] = chosen["next_dialogue"]
                        
                        # Continue the story
                        await self.send_next_dialogue(user_id, channel)
                    else:
                        await interaction.response.send_message(
                            f"Seu {attribute} não é alto o suficiente para esta ação. "
                            f"Você precisa de pelo menos {threshold}, mas tem apenas {player[attribute]}."
                        )
                        
                        # Let the player choose again
                        await self.send_choices(user_id, channel, choices)
                else:
                    await interaction.response.send_message(f"Você escolheu: {chosen['text']}")
                    
                    # Set the next dialogue
                    self.active_stories[user_id]["current_dialogue"] = chosen["next_dialogue"]
                    
                    # Continue the story
                    await self.send_next_dialogue(user_id, channel)
            
            button.callback = button_callback
            view.add_item(button)
        
        # Send the choices
        await channel.send(embed=embed, view=view)

    async def complete_chapter(self, user_id, channel):
        """Complete the current chapter and give rewards."""
        if user_id not in self.active_stories:
            return
        
        chapter_data = self.active_stories[user_id]["chapter_data"]
        
        # Get player data
        player = get_player(user_id)
        if not player:
            return
        
        # Get story progress
        story_progress = player.get('story_progress', None)
        if not story_progress:
            return
        elif isinstance(story_progress, str):
            story_progress = json.loads(story_progress)
        
        # Get current chapter info
        year = story_progress["current_year"]
        chapter = story_progress["current_chapter"]
        
        # Add to completed chapters
        chapter_key = f"{year}-{chapter}"
        if chapter_key not in story_progress["completed_chapters"]:
            story_progress["completed_chapters"].append(chapter_key)
        
        # Set next chapter
        if "next_chapter" in chapter_data:
            story_progress["current_chapter"] = chapter_data["next_chapter"]
        else:
            # Move to next year if no more chapters in current year
            story_progress["current_year"] += 1
            story_progress["current_chapter"] = 1
        
        # Calculate rewards
        exp_reward = chapter_data.get("completion_exp", 50)
        tusd_reward = chapter_data.get("completion_tusd", 100)
        
        # Update player exp and tusd
        new_exp = player["exp"] + exp_reward
        new_tusd = player["tusd"] + tusd_reward
        
        # Check for level up
        new_level = calculate_level_from_exp(new_exp)
        level_up = new_level > player["level"]
        
        # Prepare update data
        update_data = {
            "exp": new_exp,
            "tusd": new_tusd,
            "story_progress": json.dumps(story_progress)
        }
        
        if level_up:
            update_data["level"] = new_level
        
        # Update player in database
        success = update_player(user_id, **update_data)
        
        if success:
            # Create completion embed
            embed = create_basic_embed(
                title=f"Capítulo Concluído!",
                description=f"Você completou o Ano {year}, Capítulo {chapter}: {chapter_data['title']}",
                color=0x00FF00  # Green
            )
            
            # Add rewards
            embed.add_field(
                name="Recompensas",
                value=f"**Experiência:** +{exp_reward} EXP\n"
                      f"**TUSD:** +{tusd_reward} 💰",
                inline=False
            )
            
            # Add level up message if applicable
            if level_up:
                embed.add_field(
                    name="Nível Aumentado!",
                    value=f"Você subiu para o nível {new_level}!",
                    inline=False
                )
            
            # Add next chapter info
            next_year = story_progress["current_year"]
            next_chapter = story_progress["current_chapter"]
            
            if next_year in STORY_CHAPTERS and next_chapter in STORY_CHAPTERS[next_year]:
                next_chapter_data = STORY_CHAPTERS[next_year][next_chapter]
                embed.add_field(
                    name="Próximo Capítulo",
                    value=f"Ano {next_year}, Capítulo {next_chapter}: {next_chapter_data['title']}",
                    inline=False
                )
            else:
                embed.add_field(
                    name="Próximo Capítulo",
                    value="Novos capítulos serão adicionados em breve!",
                    inline=False
                )
            
            await channel.send(embed=embed)
            
            # Clean up active story
            if user_id in self.active_stories:
                del self.active_stories[user_id]
        else:
            await channel.send("Ocorreu um erro ao completar o capítulo. Por favor, tente novamente mais tarde.")

    @commands.command(name="historia")
    async def story(self, ctx):
        """Iniciar ou continuar o modo história."""
        # Check if player exists
        player = get_player(ctx.author.id)
        if not player:
            await ctx.send(f"{ctx.author.mention}, você ainda não está registrado na Academia Tokugawa. Use !ingressar para criar seu personagem.")
            return

        # Check if player has story progress
        story_progress = player.get('story_progress', None)
        if not story_progress:
            # Initialize story progress
            story_progress = {
                "current_year": 1,
                "current_chapter": 1,
                "completed_chapters": [],
                "club_progress": {},
                "villain_defeats": [],
                "minion_defeats": []
            }
            
            # Update player with initial story progress
            update_player(ctx.author.id, story_progress=json.dumps(story_progress))
        elif isinstance(story_progress, str):
            # Parse JSON string to dict
            story_progress = json.loads(story_progress)

        # Get current chapter data
        year = story_progress["current_year"]
        chapter = story_progress["current_chapter"]
        
        if year in STORY_CHAPTERS and chapter in STORY_CHAPTERS[year]:
            chapter_data = STORY_CHAPTERS[year][chapter]
            
            # Send chapter intro
            embed = create_basic_embed(
                title=f"Ano {year}, Capítulo {chapter}: {chapter_data['title']}",
                description=chapter_data['description'],
                color=0x9370DB  # Medium Purple
            )
            
            await ctx.send(embed=embed)
            
            # Start the story dialogue
            self.active_stories[ctx.author.id] = {
                "current_dialogue": 0,
                "chapter_data": chapter_data
            }
            
            # Send first dialogue
            await self.send_next_dialogue(ctx.author.id, ctx.channel)
        else:
            await ctx.send(
                f"{ctx.author.mention}, não foi possível encontrar o próximo capítulo da história. "
                f"Novos capítulos serão adicionados em breve!"
            )

async def setup(bot):
    """Add the cog to the bot."""
    from utils.command_registrar import CommandRegistrar

    # Create and add the cog
    cog = StoryMode(bot)
    await bot.add_cog(cog)
    logger.info("StoryMode cog loaded")

    # Register commands using the CommandRegistrar
    await CommandRegistrar.register_commands(bot, cog)