import discord
import logging
from discord import app_commands
from discord.ext import commands

from story_mode.story_mode import StoryMode
from utils.command_registrar import CommandRegistrar
from utils.embeds import create_basic_embed
from utils.persistence import db_provider
from utils.config import STORY_MODE_DIR

logger = logging.getLogger('tokugawa_bot')


class CompanionInteractionCog(commands.Cog):
    """
    A cog that handles interactions with companions in the game.
    """

    def __init__(self, bot):
        self.bot = bot
        self.story_mode = StoryMode(STORY_MODE_DIR)
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
        player_data = await db_provider.get_player(user_id)

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
        player_data = await db_provider.get_player(user_id)

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
            await interaction.followup.send(f"{nome} não está disponível para recrutamento no capítulo atual.",
                                            ephemeral=True)
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
        player_data["story_progress"] = result["player_data"]["story_progress"]
        await db_provider.update_player(user_id, player_data)

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
        Slash command to activate a recruited companion.
        """
        try:
            await interaction.response.defer(ephemeral=True)
        except discord.errors.NotFound:
            logger.error("A interação expirou antes que pudesse ser processada.")
            return

        user_id = interaction.user.id
        player_data = await db_provider.get_player(user_id)

        if not player_data:
            await interaction.followup.send("Você precisa criar um personagem primeiro! Use /registrar", ephemeral=True)
            return

        # Find companion by name
        companion = self.story_mode.companion_system.get_companion_by_name(nome)

        if not companion:
            await interaction.followup.send(f"Companheiro '{nome}' não encontrado.", ephemeral=True)
            return

        # Check if companion is recruited
        if not companion.is_recruited(player_data):
            await interaction.followup.send(f"Você precisa recrutar {nome} primeiro usando o comando /recrutar.",
                                            ephemeral=True)
            return

        # Activate the companion
        result = self.story_mode.activate_companion(player_data, companion.npc_id)

        if "error" in result:
            await interaction.followup.send(f"Erro ao ativar companheiro: {result['error']}", ephemeral=True)
            return

        # Update player data in database
        player_data["story_progress"] = result["player_data"]["story_progress"]
        await db_provider.update_player(user_id, player_data)

        # Create success embed
        embed = create_basic_embed(
            title=f"Companheiro Ativado: {nome}",
            description=result.get("message", f"Você ativou {nome} como seu companheiro ativo!"),
            color=discord.Color.green()
        )

        companion_info = result.get("companion_info", {})
        embed.add_field(
            name="Informações",
            value=f"**Tipo de Poder**: {companion_info.get('power_type', 'Desconhecido').capitalize()}\n"
                  f"**Especialização**: {companion_info.get('specialization', 'Desconhecida').capitalize()}\n"
                  f"**Nível de Sincronização**: {companion_info.get('sync_level', 1)}",
            inline=False
        )

        embed.add_field(
            name="Próximos Passos",
            value="Use `/status_companheiro " + nome + "` para ver detalhes e missões disponíveis.\n"
                                                       "Use `/sincronizar [habilidade]` para usar habilidades de sincronização.",
            inline=False
        )

        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="desativar_companheiro", description="Desativar seu companheiro atual")
    async def slash_deactivate_companion(self, interaction: discord.Interaction):
        """
        Slash command to deactivate the current active companion.
        """
        try:
            await interaction.response.defer(ephemeral=True)
        except discord.errors.NotFound:
            logger.error("A interação expirou antes que pudesse ser processada.")
            return

        user_id = interaction.user.id
        player_data = await db_provider.get_player(user_id)

        if not player_data:
            await interaction.followup.send("Você precisa criar um personagem primeiro! Use /registrar", ephemeral=True)
            return

        # Check if there's an active companion
        active_companion = self.story_mode.get_active_companion(player_data)
        if not active_companion:
            await interaction.followup.send("Você não tem nenhum companheiro ativo no momento.", ephemeral=True)
            return

        # Deactivate the companion
        result = self.story_mode.deactivate_companion(player_data)

        if "error" in result:
            await interaction.followup.send(f"Erro ao desativar companheiro: {result['error']}", ephemeral=True)
            return

        # Update player data in database
        player_data["story_progress"] = result["player_data"]["story_progress"]
        await db_provider.update_player(user_id, player_data)

        # Create success embed
        embed = create_basic_embed(
            title="Companheiro Desativado",
            description=result.get("message", f"Você desativou {active_companion['name']} como seu companheiro ativo."),
            color=discord.Color.blue()
        )

        embed.add_field(
            name="Próximos Passos",
            value="Use `/companheiros` para ver seus companheiros disponíveis.\n"
                  "Use `/ativar_companheiro [nome]` para ativar outro companheiro.",
            inline=False
        )

        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="status_companheiro", description="Ver detalhes de um companheiro recrutado")
    @app_commands.describe(
        nome="Nome do companheiro"
    )
    async def slash_companion_status(self, interaction: discord.Interaction, nome: str):
        """
        Slash command to view detailed status of a recruited companion.
        """
        try:
            await interaction.response.defer(ephemeral=True)
        except discord.errors.NotFound:
            logger.error("A interação expirou antes que pudesse ser processada.")
            return

        user_id = interaction.user.id
        player_data = await db_provider.get_player(user_id)

        if not player_data:
            await interaction.followup.send("Você precisa criar um personagem primeiro! Use /registrar", ephemeral=True)
            return

        # Find companion by name
        companion = self.story_mode.companion_system.get_companion_by_name(nome)

        if not companion:
            await interaction.followup.send(f"Companheiro '{nome}' não encontrado.", ephemeral=True)
            return

        # Check if companion is recruited
        if not companion.is_recruited(player_data):
            await interaction.followup.send(f"Você precisa recrutar {nome} primeiro usando o comando /recrutar.",
                                            ephemeral=True)
            return

        # Get companion status
        status = self.story_mode.get_companion_status(player_data, companion.npc_id)

        if "error" in status:
            await interaction.followup.send(f"Erro ao obter status do companheiro: {status['error']}", ephemeral=True)
            return

        # Create status embed
        embed = create_basic_embed(
            title=f"Status do Companheiro: {nome}",
            description=status.get("description", f"Informações detalhadas sobre {nome}"),
            color=discord.Color.blue()
        )

        # Add basic info
        embed.add_field(
            name="Informações Básicas",
            value=f"**Tipo de Poder**: {status['power_type'].capitalize()}\n"
                  f"**Especialização**: {status['specialization'].capitalize()}\n"
                  f"**Nível de Sincronização**: {status['sync_level']}\n"
                  f"**Progresso da História**: {status['arc_progress']}%",
            inline=False
        )

        # Add background info
        if "background" in status:
            embed.add_field(
                name="História",
                value=f"**Origem**: {status['background'].get('origin', 'Desconhecida')}\n"
                      f"**Motivação**: {status['background'].get('motivation', 'Desconhecida')}",
                inline=False
            )

        # Add abilities info
        if "abilities" in status:
            abilities_text = ""
            for ability in status["abilities"]:
                abilities_text += f"**{ability['name']}** - {ability['description']}\n"
                if "cooldown" in ability:
                    abilities_text += f"Cooldown: {ability['cooldown']} minutos\n"
                abilities_text += "\n"

            embed.add_field(
                name="Habilidades",
                value=abilities_text,
                inline=False
            )

        # Add missions info
        if "missions" in status:
            missions_text = ""
            for mission in status["missions"]:
                status_emoji = "✅" if mission["completed"] else "⏳"
                missions_text += f"{status_emoji} **{mission['name']}**\n"
                missions_text += f"{mission['description']}\n"
                if "rewards" in mission:
                    rewards_text = ", ".join([f"{k}: {v}" for k, v in mission["rewards"].items()])
                    missions_text += f"Recompensas: {rewards_text}\n"
                missions_text += "\n"

            embed.add_field(
                name="Missões",
                value=missions_text,
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
        player_data = await db_provider.get_player(user_id)

        if not player_data:
            await interaction.followup.send("Você precisa criar um personagem primeiro! Use /registrar", ephemeral=True)
            return

        # Find companion by name
        companion = self.story_mode.companion_system.get_companion_by_name(nome)

        if not companion:
            await interaction.followup.send(f"Companheiro '{nome}' não encontrado.", ephemeral=True)
            return

        # Check if companion is recruited
        if not companion.is_recruited(player_data):
            await interaction.followup.send(f"Você precisa recrutar {nome} primeiro usando o comando /recrutar.",
                                            ephemeral=True)
            return

        # Complete the mission
        result = self.story_mode.complete_companion_mission(player_data, companion.npc_id, id_missao)

        if "error" in result:
            await interaction.followup.send(f"Erro ao completar missão: {result['error']}", ephemeral=True)
            return

        # Update player data in database
        player_data["story_progress"] = result["player_data"]["story_progress"]
        await db_provider.update_player(user_id, player_data)

        # Create success embed
        embed = create_basic_embed(
            title=f"Missão Completada: {result['mission_name']}",
            description=result.get("message", f"Você completou a missão de {nome}!"),
            color=discord.Color.green()
        )

        # Add rewards info
        if "rewards" in result:
            rewards_text = ""
            for reward_type, reward_value in result["rewards"].items():
                rewards_text += f"**{reward_type.capitalize()}**: {reward_value}\n"

            embed.add_field(
                name="Recompensas",
                value=rewards_text,
                inline=False
            )

        # Add next steps
        embed.add_field(
            name="Próximos Passos",
            value="Use `/status_companheiro " + nome + "` para ver outras missões disponíveis.",
            inline=False
        )

        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="sincronizar",
                          description="Usar uma habilidade de sincronização com seu companheiro ativo")
    @app_commands.describe(
        id_habilidade="ID da habilidade de sincronização a ser usada"
    )
    async def slash_sync_ability(self, interaction: discord.Interaction, id_habilidade: str):
        """
        Slash command to use a sync ability with the active companion.
        """
        try:
            await interaction.response.defer(ephemeral=True)
        except discord.errors.NotFound:
            logger.error("A interação expirou antes que pudesse ser processada.")
            return

        user_id = interaction.user.id
        player_data = await db_provider.get_player(user_id)

        if not player_data:
            await interaction.followup.send("Você precisa criar um personagem primeiro! Use /registrar", ephemeral=True)
            return

        # Check if there's an active companion
        active_companion = self.story_mode.get_active_companion(player_data)
        if not active_companion:
            await interaction.followup.send("Você não tem nenhum companheiro ativo no momento.", ephemeral=True)
            return

        # Use the sync ability
        result = self.story_mode.use_sync_ability(player_data, id_habilidade)

        if "error" in result:
            await interaction.followup.send(f"Erro ao usar habilidade: {result['error']}", ephemeral=True)
            return

        # Update player data in database
        player_data["story_progress"] = result["player_data"]["story_progress"]
        await db_provider.update_player(user_id, player_data)

        # Create success embed
        embed = create_basic_embed(
            title=f"Habilidade de Sincronização: {result['ability_name']}",
            description=result.get("message",
                                   f"Você usou a habilidade de sincronização com {active_companion['name']}!"),
            color=discord.Color.green()
        )

        # Add effects info
        if "effects" in result:
            effects_text = ""
            for effect_type, effect_value in result["effects"].items():
                effects_text += f"**{effect_type.capitalize()}**: {effect_value}\n"

            embed.add_field(
                name="Efeitos",
                value=effects_text,
                inline=False
            )

        # Add cooldown info
        if "cooldown" in result:
            embed.add_field(
                name="Cooldown",
                value=f"Esta habilidade estará disponível novamente em {result['cooldown']} minutos.",
                inline=False
            )

        await interaction.followup.send(embed=embed, ephemeral=True)


async def setup(bot):
    """
    Setup function for the cog.
    """
    # Create and add the cog
    cog = CompanionInteractionCog(bot)
    await bot.add_cog(cog)
    logger.info("CompanionInteractionCog setup complete")

    # Register commands using the CommandRegistrar
    await CommandRegistrar.register_commands(bot, cog)
