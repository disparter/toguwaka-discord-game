import discord
from discord.ext import commands
import logging
import re
from utils.database import get_player

logger = logging.getLogger('tokugawa_bot')

class JunieInteraction(commands.Cog):
    """Cog for handling interactions with Junie."""
    
    def __init__(self, bot):
        self.bot = bot
        
    @commands.Cog.listener()
    async def on_message(self, message):
        """Listen for messages that mention Junie and respond appropriately."""
        # Ignore messages from bots (including self)
        if message.author.bot:
            return
            
        # Check if the message mentions "Junie" and contains a question
        content = message.content.lower()
        if "junie" in content and any(q in content for q in ["o que", "que devo", "o que devo", "o que fazer", "que fazer", "me ajude", "me ajuda", "sugestão", "sugestao", "what should", "help me"]):
            logger.info(f"Detected Junie interaction from {message.author.name}: {message.content}")
            
            # Get player data
            player = get_player(message.author.id)
            
            if not player:
                # Player is not registered
                await message.reply(
                    "Olá! Parece que você ainda não está registrado na Academia Tokugawa. Use `/registro ingressar` para criar seu personagem e começar sua jornada!"
                )
                return
                
            # Determine suggestion based on player state
            suggestion = self.get_suggestion_for_player(player)
            
            # Reply with the suggestion
            await message.reply(suggestion)
            
    def get_suggestion_for_player(self, player):
        """Get a suggestion for the player based on their state."""
        tusd = player.get('tusd', 0)
        level = player.get('level', 1)
        club_id = player.get('club_id')
        
        # Base response
        response = f"Olá, {player['name']}! "
        
        # Suggestions based on TUSD
        if tusd < 50:
            response += "Você está com poucos TUSD! Que tal usar o comando `/atividade explorar` para ganhar mais recursos? "
        elif tusd > 500:
            response += "Você tem bastante TUSD! Considere investir na loja com `/loja` para melhorar seu personagem. "
            
        # Suggestions based on level
        if level < 5:
            response += "Como você ainda está nos níveis iniciais, participar dos quizzes diários com `/quiz participar` pode ajudar a ganhar XP rapidamente. "
        elif level >= 10:
            response += "Com seu nível atual, você poderia tentar desafiar outros jogadores para duelos usando `/duelo desafiar`. "
            
        # Suggestions based on club membership
        if not club_id:
            response += "Você ainda não está em nenhum clube! Use `/clube entrar` para se juntar a um e ganhar benefícios adicionais. "
        else:
            response += "Não se esqueça de contribuir para seu clube participando de atividades! "
            
        # Add a random general suggestion
        import random
        general_suggestions = [
            "Participar dos eventos semanais é uma ótima maneira de ganhar recompensas extras!",
            "Melhorar seus atributos com `/treinar` pode desbloquear novas habilidades.",
            "Interagir com outros estudantes pode revelar segredos da Academia Tokugawa!",
            "Fique atento ao evento mensal 'Dia de Matéria' para testar seus conhecimentos!",
            "Verificar o ranking com `/ranking` pode te motivar a melhorar seu desempenho!"
        ]
        
        response += random.choice(general_suggestions)
        
        return response

async def setup(bot):
    """Add the cog to the bot."""
    await bot.add_cog(JunieInteraction(bot))
    logger.info("JunieInteraction cog loaded")