import discord
from discord.ext import commands
from discord import app_commands
import logging
from typing import Dict, List, Any, Optional, Union

from utils.database import get_player, update_player
from utils.embeds import create_basic_embed
from story_mode.story_mode import StoryMode

logger = logging.getLogger('tokugawa_bot')

class CompanionInteractionCog(commands.Cog):
    """
    A cog that handles interactions with companions in the game.
    """
    def __init__(self, bot):
        self.bot = bot
        self.story_mode = StoryMode()
        logger.info("CompanionInteractionCog initialized")

    def cog_load(self):
        """Called when the cog is loaded."""
        logger.info("CompanionInteractionCog loaded")

    @app_commands.command(name="companheiros", description="Visualizar seus companheiros disponíveis e recrutados")
    async def slash_view_companions(self, interaction: discord.Interaction):
        """
        Slash command to view available and recruited companions.
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

        # Get current chapter
        story_progress = player_data.get("story_progress", {})
        chapter_id = story_progress.get("current_chapter", "1_1")

        # Get available companions for recruitment
        available_companions = self.story_mode.get_available_companions(player_data, chapter_id)
        
        # Get already recruited companions
        recruited_companions = self.story_mode.get_recruited_companions(player_data)
        
        # Get active companion
        active_companion = self.story_mode.get_active_companion(player_data)

        # Create embed for companions
        embed = create_basic_embed(
            title="Seus Companheiros",
            description="Companheiros são aliados que podem acompanhá-lo em sua jornada, fornecendo habilidades especiais e histórias únicas.",
            color=discord.Color.blue()
        )

        # Add active companion section if there is one
        if active_companion:
            embed.add_field(
                name="🌟 Companheiro Ativo",
                value=f"**{active_companion['name']}** - {active_companion['power_type'].capitalize()} ({active_companion['specialization'].capitalize()})\n"
                      f"Nível de Sincronização: {active_companion['sync_level']}\n"
                      f"Progresso da História: {active_companion['arc_progress']}%",
                inline=False
            )

        # Add recruited companions section
        if recruited_companions:
            recruited_text = ""
            for companion in recruited_companions:
                # Skip the active companion as it's already shown
                if active_companion and companion['id'] == active_companion['id']:
                    continue
                    
                status = "Inativo"
                recruited_text += f"**{companion['name']}** - {companion['power_type'].capitalize()} ({companion['specialization'].capitalize()})\n"
                recruited_text += f"Nível de Sincronização: {companion['sync_level']} | Progresso: {companion['arc_progress']}%\n\n"
            
            if recruited_text:
                embed.add_field(
                    name="🤝 Companheiros Recrutados",
                    value=recruited_text,
                    inline=False
                )
        
        # Add available companions section
        if available_companions:
            available_text = ""
            for companion in available_companions:
                available_text += f"**{companion['name']}** - {companion['power_type'].capitalize()} ({companion['specialization'].capitalize()})\n"
                available_text += f"Origem: {companion['background'].get('origin', 'Desconhecida')}\n\n"
            
            embed.add_field(
                name="✨ Companheiros Disponíveis para Recrutamento",
                value=available_text,
                inline=False
            )
        
        # Add instructions
        embed.add_field(
            name="Comandos Disponíveis",
            value="Use `/recrutar [nome]` para recrutar um companheiro disponível.\n"
                  "Use `/ativar_companheiro [nome]` para ativar um companheiro recrutado.\n"
                  "Use `/desativar_companheiro` para desativar seu companheiro atual.\n"
                  "Use `/status_companheiro [nome]` para ver detalhes de um companheiro.\n"
                  "Use `/sincronizar [habilidade]` para usar uma habilidade de sincronização.",
            inline=False
        )

        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="recrutar", description="Recrutar um companheiro disponível")
    @app_commands.describe(
        nome="Nome do companheiro que deseja recrutar"
    )
    async def slash_recruit_companion(self, interaction: discord.Interaction, nome: str):
        """
        Slash command to recruit a companion.
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

        # Find companion by name
        companion = self.story_mode.companion_system.get_companion_by_name(nome)
        
        if not companion:
            await interaction.followup.send(f"Companheiro '{nome}' não encontrado.", ephemeral=True)
            return
        
        # Check if companion is available in current chapter
        story_progress = player_data.get("story_progress", {})
        chapter_id = story_progress.get("current_chapter", "1_1")
        
        if chapter_id not in companion.get_available_chapters():
            await interaction.followup.send(f"{nome} não está disponível para recrutamento no capítulo atual.", ephemeral=True)
            return
        
        # Check if already recruited
        if companion.is_recruited(player_data):
            await interaction.followup.send(f"Você já recrutou {nome}.", ephemeral=True)
            return
        
        # Recruit the companion
        result = self.story_mode.recruit_companion(player_data, companion.npc_id)
        
        if "error" in result:
            await interaction.followup.send(f"Erro ao recrutar companheiro: {result['error']}", ephemeral=True)
            return
        
        # Update player data in database
        update_player(user_id, story_progress=result["player_data"]["story_progress"])
        
        # Create success embed
        embed = create_basic_embed(
            title=f"Companheiro Recrutado: {nome}",
            description=result.get("message", f"Você recrutou {nome} como seu companheiro!"),
            color=discord.Color.green()
        )
        
        companion_info = result.get("companion_info", {})
        embed.add_field(
            name="Informações",
            value=f"**Tipo de Poder**: {companion_info.get('power_type', 'Desconhecido').capitalize()}\n"
                  f"**Especialização**: {companion_info.get('specialization', 'Desconhecida').capitalize()}",
            inline=False
        )
        
        embed.add_field(
            name="Próximos Passos",
            value="Use `/ativar_companheiro " + nome + "` para ativar este companheiro.\n"
                  "Use `/status_companheiro " + nome + "` para ver detalhes e missões disponíveis.",
            inline=False
        )
        
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="ativar_companheiro", description="Ativar um companheiro recrutado")
    @app_commands.describe(
        nome="Nome do companheiro que deseja ativar"
    )
    async def slash_activate_companion(self, interaction: discord.Interaction, nome: str):
        """
        Slash command to activate a companion.
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

        # Find companion by name
        companion = self.story_mode.companion_system.get_companion_by_name(nome)
        
        if not companion:
            await interaction.followup.send(f"Companheiro '{nome}' não encontrado.", ephemeral=True)
            return
        
        # Check if recruited
        if not companion.is_recruited(player_data):
            await interaction.followup.send(f"Você ainda não recrutou {nome}. Use /recrutar para recrutá-lo primeiro.", ephemeral=True)
            return
        
        # Check if already active
        if companion.is_active(player_data):
            await interaction.followup.send(f"{nome} já está ativo.", ephemeral=True)
            return
        
        # Activate the companion
        result = self.story_mode.activate_companion(player_data, companion.npc_id)
        
        if "error" in result:
            await interaction.followup.send(f"Erro ao ativar companheiro: {result['error']}", ephemeral=True)
            return
        
        # Update player data in database
        update_player(user_id, story_progress=result["player_data"]["story_progress"])
        
        # Create success embed
        embed = create_basic_embed(
            title=f"Companheiro Ativado: {nome}",
            description=result.get("message", f"{nome} agora está ativo e acompanhando você!"),
            color=discord.Color.green()
        )
        
        companion_info = result.get("companion_info", {})
        
        # Add available sync abilities if any
        available_abilities = companion_info.get("available_sync_abilities", [])
        if available_abilities:
            abilities_text = ""
            for ability in available_abilities:
                status = "🔄 Em cooldown" if ability.get("on_cooldown", False) else "✅ Disponível"
                abilities_text += f"**{ability['name']}**: {ability['description']}\n{status}\n\n"
            
            embed.add_field(
                name="Habilidades de Sincronização Disponíveis",
                value=abilities_text,
                inline=False
            )
        
        embed.add_field(
            name="Próximos Passos",
            value="Use `/sincronizar [habilidade]` para usar uma habilidade de sincronização.\n"
                  "Use `/status_companheiro " + nome + "` para ver missões disponíveis.",
            inline=False
        )
        
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="desativar_companheiro", description="Desativar seu companheiro atual")
    async def slash_deactivate_companion(self, interaction: discord.Interaction):
        """
        Slash command to deactivate the current companion.
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

        # Get active companion
        active_companion = self.story_mode.get_active_companion(player_data)
        
        if not active_companion:
            await interaction.followup.send("Você não tem nenhum companheiro ativo no momento.", ephemeral=True)
            return
        
        # Deactivate the companion
        result = self.story_mode.deactivate_companion(player_data, active_companion["id"])
        
        if "error" in result:
            await interaction.followup.send(f"Erro ao desativar companheiro: {result['error']}", ephemeral=True)
            return
        
        # Update player data in database
        update_player(user_id, story_progress=result["player_data"]["story_progress"])
        
        # Create success embed
        embed = create_basic_embed(
            title="Companheiro Desativado",
            description=result.get("message", f"{active_companion['name']} não está mais acompanhando você."),
            color=discord.Color.blue()
        )
        
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="status_companheiro", description="Ver detalhes de um companheiro recrutado")
    @app_commands.describe(
        nome="Nome do companheiro"
    )
    async def slash_companion_status(self, interaction: discord.Interaction, nome: str):
        """
        Slash command to view companion status.
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

        # Find companion by name
        companion = self.story_mode.companion_system.get_companion_by_name(nome)
        
        if not companion:
            await interaction.followup.send(f"Companheiro '{nome}' não encontrado.", ephemeral=True)
            return
        
        # Check if recruited
        if not companion.is_recruited(player_data):
            await interaction.followup.send(f"Você ainda não recrutou {nome}. Use /recrutar para recrutá-lo primeiro.", ephemeral=True)
            return
        
        # Get companion status
        status = self.story_mode.get_companion_status(player_data, companion.npc_id)
        
        if "error" in status:
            await interaction.followup.send(f"Erro ao obter status do companheiro: {status['error']}", ephemeral=True)
            return
        
        # Create status embed
        embed = create_basic_embed(
            title=f"Status de {status['name']}",
            description=status['story_arc']['description'],
            color=discord.Color.gold()
        )
        
        # Add basic info
        embed.add_field(
            name="Informações Básicas",
            value=f"**Tipo de Poder**: {status['power_type'].capitalize()}\n"
                  f"**Especialização**: {status['specialization'].capitalize()}\n"
                  f"**Status**: {'Ativo' if status['active'] else 'Inativo'}\n"
                  f"**Progresso da História**: {status['arc_progress']}%\n"
                  f"**Nível de Sincronização**: {status['sync_level']}",
            inline=False
        )
        
        # Add available missions if any
        available_missions = status.get("available_missions", [])
        if available_missions:
            missions_text = ""
            for mission in available_missions:
                missions_text += f"**{mission['name']}**: {mission['description']}\n"
            
            embed.add_field(
                name="Missões Disponíveis",
                value=missions_text,
                inline=False
            )
        
        # Add completed missions if any
        completed_missions = status.get("completed_missions", [])
        if completed_missions:
            completed_text = ""
            for mission in completed_missions:
                completed_text += f"**{mission['name']}**: {mission['description']}\n"
            
            embed.add_field(
                name="Missões Completadas",
                value=completed_text,
                inline=False
            )
        
        # Add available sync abilities if any
        available_abilities = status.get("available_sync_abilities", [])
        if available_abilities:
            abilities_text = ""
            for ability in available_abilities:
                status_text = "🔄 Em cooldown" if ability.get("on_cooldown", False) else "✅ Disponível"
                abilities_text += f"**{ability['name']}**: {ability['description']}\n{status_text}\n\n"
            
            embed.add_field(
                name="Habilidades de Sincronização",
                value=abilities_text,
                inline=False
            )
        
        # Add commands
        embed.add_field(
            name="Comandos Disponíveis",
            value="Use `/completar_missao [nome] [id_missao]` para completar uma missão.\n"
                  "Use `/sincronizar [nome] [id_habilidade]` para usar uma habilidade de sincronização.",
            inline=False
        )
        
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="completar_missao", description="Completar uma missão de companheiro")
    @app_commands.describe(
        nome="Nome do companheiro",
        id_missao="ID da missão a ser completada"
    )
    async def slash_complete_mission(self, interaction: discord.Interaction, nome: str, id_missao: str):
        """
        Slash command to complete a companion mission.
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

        # Find companion by name
        companion = self.story_mode.companion_system.get_companion_by_name(nome)
        
        if not companion:
            await interaction.followup.send(f"Companheiro '{nome}' não encontrado.", ephemeral=True)
            return
        
        # Check if recruited
        if not companion.is_recruited(player_data):
            await interaction.followup.send(f"Você ainda não recrutou {nome}. Use /recrutar para recrutá-lo primeiro.", ephemeral=True)
            return
        
        # Complete the mission
        result = self.story_mode.complete_companion_mission(player_data, companion.npc_id, id_missao)
        
        if "error" in result:
            await interaction.followup.send(f"Erro ao completar missão: {result['error']}", ephemeral=True)
            return
        
        # Update player data in database
        update_player(user_id, 
                      story_progress=result["player_data"]["story_progress"],
                      exp=result["player_data"].get("exp", player_data.get("exp", 0)),
                      tusd=result["player_data"].get("tusd", player_data.get("tusd", 0)))
        
        # Create success embed
        embed = create_basic_embed(
            title=f"Missão Completada: {result['mission_name']}",
            description=result['mission_description'],
            color=discord.Color.green()
        )
        
        # Add rewards
        rewards = result.get("rewards", {})
        rewards_text = ""
        
        if "exp" in rewards:
            rewards_text += f"**EXP**: {rewards['exp']}\n"
        
        if "tusd" in rewards:
            rewards_text += f"**TUSD**: {rewards['tusd']}\n"
        
        if "special_item" in rewards:
            rewards_text += f"**Item Especial**: {rewards['special_item']}\n"
        
        if "arc_progress" in rewards:
            rewards_text += f"**Progresso da História**: +{rewards['arc_progress']}%\n"
        
        if rewards_text:
            embed.add_field(
                name="Recompensas",
                value=rewards_text,
                inline=False
            )
        
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="sincronizar", description="Usar uma habilidade de sincronização com seu companheiro ativo")
    @app_commands.describe(
        id_habilidade="ID da habilidade de sincronização a ser usada"
    )
    async def slash_sync_ability(self, interaction: discord.Interaction, id_habilidade: str):
        """
        Slash command to use a synchronization ability.
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

        # Get active companion
        active_companion = self.story_mode.get_active_companion(player_data)
        
        if not active_companion:
            await interaction.followup.send("Você não tem nenhum companheiro ativo. Use /ativar_companheiro para ativar um companheiro.", ephemeral=True)
            return
        
        # Perform the sync ability
        result = self.story_mode.perform_sync_ability(player_data, active_companion["id"], id_habilidade)
        
        if "error" in result:
            await interaction.followup.send(f"Erro ao usar habilidade de sincronização: {result['error']}", ephemeral=True)
            return
        
        # Update player data in database
        update_player(user_id, story_progress=result["player_data"]["story_progress"])
        
        # Create success embed
        embed = create_basic_embed(
            title=f"Sincronização: {result['ability_name']}",
            description=result['ability_description'],
            color=discord.Color.purple()
        )
        
        # Add applied effects
        applied_effects = result.get("applied_effects", {})
        effects_text = ""
        
        if "stat_boost" in applied_effects:
            effects_text += "**Aumento de Atributos**:\n"
            for stat, value in applied_effects["stat_boost"].items():
                effects_text += f"- {stat.replace('_', ' ').capitalize()}: x{value}\n"
        
        if "power_boost" in applied_effects:
            power_boost = applied_effects["power_boost"]
            effects_text += f"\n**Aumento de Poder**:\n"
            effects_text += f"- {power_boost['power_id'].capitalize()}: +{power_boost['amount']} pontos\n"
        
        if "special_action" in applied_effects:
            special_action = applied_effects["special_action"]
            effects_text += f"\n**Ação Especial**:\n"
            effects_text += f"- Tipo: {special_action['type'].capitalize()}\n"
            
            for key, value in special_action.items():
                if key != "type":
                    effects_text += f"- {key.replace('_', ' ').capitalize()}: {value}\n"
        
        if effects_text:
            embed.add_field(
                name="Efeitos Aplicados",
                value=effects_text,
                inline=False
            )
        
        embed.set_footer(text=f"Sincronização com {active_companion['name']} bem-sucedida!")
        
        await interaction.followup.send(embed=embed, ephemeral=True)

async def setup(bot):
    """
    Setup function for the cog.
    """
    from utils.command_registrar import CommandRegistrar

    # Create and add the cog
    cog = CompanionInteractionCog(bot)
    await bot.add_cog(cog)
    logger.info("CompanionInteractionCog setup complete")

    # Register commands using the CommandRegistrar
    await CommandRegistrar.register_commands(bot, cog)