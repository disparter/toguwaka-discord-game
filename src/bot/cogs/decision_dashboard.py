import discord
from discord.ext import commands
from discord import app_commands
import logging
import json
from typing import Dict, List, Any, Optional, Union
import matplotlib.pyplot as plt
import io
import numpy as np
from collections import Counter, defaultdict

from src.utils.persistence.db_provider import get_player, get_all_players
from src.utils.embeds import create_basic_embed
from story_mode.story_mode import StoryMode
from story_mode.narrative_logger import get_narrative_logger

# Set up logging
logger = logging.getLogger(__name__)

class DecisionDashboard(commands.Cog):
    """Cog for the Decision Dashboard functionality."""

    def __init__(self, bot):
        self.bot = bot
        self.story_mode = StoryMode()
        self.narrative_logger = get_narrative_logger()

    # Group for dashboard commands
    dashboard_group = app_commands.Group(name="dashboard", description="Dashboard de Comparação de Decisões")

    @dashboard_group.command(name="escolhas", description="Compare suas escolhas narrativas com a comunidade")
    async def slash_choice_comparison(self, interaction: discord.Interaction, chapter_id: str = None):
        """
        Shows a comparison of the player's narrative choices with the community.

        Args:
            interaction: The Discord interaction
            chapter_id: Optional chapter ID to filter choices
        """
        try:
            # Defer the response since this might take some time
            await interaction.response.defer(ephemeral=True)

            # Get player data
            player = get_player(interaction.user.id)
            if not player:
                await interaction.followup.send(
                    f"{interaction.user.mention}, você ainda não está registrado na Academia Tokugawa. "
                    "Use !ingressar para criar seu personagem."
                )
                return

            # Get player's choices
            player_choices = self._get_player_choices(player, chapter_id)
            if not player_choices:
                await interaction.followup.send(
                    f"Você ainda não fez escolhas narrativas{' neste capítulo' if chapter_id else ''}."
                )
                return

            # Get community choices
            community_choices = self._get_community_choices(chapter_id)

            # Create comparison visualization
            embed, file = self._create_choice_comparison(player, player_choices, community_choices, chapter_id)

            # Send the response
            await interaction.followup.send(embed=embed, file=file)

        except discord.errors.NotFound:
            logger.warning(f"Interaction expired for user {interaction.user.id} when using /dashboard escolhas")
        except Exception as e:
            logger.error(f"Error in slash_choice_comparison: {e}")
            await interaction.followup.send(f"Ocorreu um erro ao gerar o dashboard: {str(e)}")

    @dashboard_group.command(name="caminhos", description="Visualize os caminhos narrativos mais populares")
    async def slash_path_analysis(self, interaction: discord.Interaction):
        """
        Shows an analysis of narrative paths through the story.
        """
        try:
            # Defer the response since this might take some time
            await interaction.response.defer(ephemeral=True)

            # Get player data
            player = get_player(interaction.user.id)
            if not player:
                await interaction.followup.send(
                    f"{interaction.user.mention}, você ainda não está registrado na Academia Tokugawa. "
                    "Use !ingressar para criar seu personagem."
                )
                return

            # Get player's path
            player_path = self._get_player_path(player)
            if not player_path:
                await interaction.followup.send("Você ainda não progrediu o suficiente na história.")
                return

            # Get community paths
            community_paths = self._get_community_paths()

            # Create path analysis visualization
            embed, file = self._create_path_analysis(player, player_path, community_paths)

            # Send the response
            await interaction.followup.send(embed=embed, file=file)

        except discord.errors.NotFound:
            logger.warning(f"Interaction expired for user {interaction.user.id} when using /dashboard caminhos")
        except Exception as e:
            logger.error(f"Error in slash_path_analysis: {e}")
            await interaction.followup.send(f"Ocorreu um erro ao gerar o dashboard: {str(e)}")

    @dashboard_group.command(name="faccoes", description="Compare estatísticas de facções e alianças")
    async def slash_faction_stats(self, interaction: discord.Interaction):
        """
        Shows statistics about factions and alliances.
        """
        try:
            # Defer the response since this might take some time
            await interaction.response.defer(ephemeral=True)

            # Get player data
            player = get_player(interaction.user.id)
            if not player:
                await interaction.followup.send(
                    f"{interaction.user.mention}, você ainda não está registrado na Academia Tokugawa. "
                    "Use !ingressar para criar seu personagem."
                )
                return

            # Get player's faction data
            player_faction = self._get_player_faction_data(player)
            if not player_faction:
                await interaction.followup.send("Você ainda não se juntou a uma facção.")
                return

            # Get community faction data
            community_factions = self._get_community_faction_data()

            # Create faction statistics visualization
            embed, file = self._create_faction_stats(player, player_faction, community_factions)

            # Send the response
            await interaction.followup.send(embed=embed, file=file)

        except discord.errors.NotFound:
            logger.warning(f"Interaction expired for user {interaction.user.id} when using /dashboard faccoes")
        except Exception as e:
            logger.error(f"Error in slash_faction_stats: {e}")
            await interaction.followup.send(f"Ocorreu um erro ao gerar o dashboard: {str(e)}")

    @dashboard_group.command(name="estilo", description="Analise seu estilo de jogo")
    async def slash_gameplay_style(self, interaction: discord.Interaction):
        """
        Analyzes the player's gameplay style based on their choices.
        """
        try:
            # Defer the response since this might take some time
            await interaction.response.defer(ephemeral=True)

            # Get player data
            player = get_player(interaction.user.id)
            if not player:
                await interaction.followup.send(
                    f"{interaction.user.mention}, você ainda não está registrado na Academia Tokugawa. "
                    "Use !ingressar para criar seu personagem."
                )
                return

            # Get player's choices for style analysis
            player_choices = self._get_player_choices(player)
            if not player_choices:
                await interaction.followup.send("Você ainda não fez escolhas suficientes para análise de estilo.")
                return

            # Analyze player's style
            style_analysis = self._analyze_gameplay_style(player, player_choices)

            # Get community style data
            community_styles = self._get_community_style_data()

            # Create style analysis visualization
            embed, file = self._create_style_analysis(player, style_analysis, community_styles)

            # Send the response
            await interaction.followup.send(embed=embed, file=file)

        except discord.errors.NotFound:
            logger.warning(f"Interaction expired for user {interaction.user.id} when using /dashboard estilo")
        except Exception as e:
            logger.error(f"Error in slash_gameplay_style: {e}")
            await interaction.followup.send(f"Ocorreu um erro ao gerar o dashboard: {str(e)}")

    @dashboard_group.command(name="analytics", description="Visualize estatísticas de fluxo narrativo")
    async def slash_narrative_analytics(self, interaction: discord.Interaction, chapter_id: str = None):
        """
        Shows analytics from the narrative logger.

        Args:
            interaction: The Discord interaction
            chapter_id: Optional chapter ID to filter analytics
        """
        try:
            # Defer the response since this might take some time
            await interaction.response.defer(ephemeral=True)

            # Get player data
            player = get_player(interaction.user.id)
            if not player:
                await interaction.followup.send(
                    f"{interaction.user.mention}, você ainda não está registrado na Academia Tokugawa. "
                    "Use !ingressar para criar seu personagem."
                )
                return

            # Get analytics data from the narrative logger
            if chapter_id:
                # Get chapter-specific analytics
                analytics_data = self.narrative_logger.get_chapter_analytics(chapter_id)

                # Create embed for chapter analytics
                embed = create_basic_embed(
                    title=f"Análise de Fluxo Narrativo - Capítulo {chapter_id}",
                    description="Estatísticas detalhadas sobre este capítulo da história.",
                    color=discord.Color.blue()
                )

                # Add choices field
                choices_str = ""
                for choice, count in analytics_data.get("choices", {}).items():
                    choices_str += f"**{choice}**: {count} vezes\n"

                if choices_str:
                    embed.add_field(
                        name="Escolhas Mais Comuns",
                        value=choices_str or "Nenhuma escolha registrada.",
                        inline=False
                    )

                # Add errors field
                errors_str = ""
                for error, count in analytics_data.get("errors", {}).items():
                    errors_str += f"**{error}**: {count} vezes\n"

                if errors_str:
                    embed.add_field(
                        name="Erros Mais Comuns",
                        value=errors_str or "Nenhum erro registrado.",
                        inline=False
                    )

                # Add paths field
                paths_str = ""
                for path, count in analytics_data.get("paths", {}).items():
                    paths_str += f"**{path}**: {count} vezes\n"

                if paths_str:
                    embed.add_field(
                        name="Caminhos Mais Comuns",
                        value=paths_str or "Nenhum caminho registrado.",
                        inline=False
                    )

                # Add total visits
                embed.add_field(
                    name="Total de Visitas",
                    value=str(analytics_data.get("total_visits", 0)),
                    inline=False
                )

                # Send the response
                await interaction.followup.send(embed=embed)
            else:
                # Get general analytics
                analytics_data = self.narrative_logger.export_analytics_for_dashboard()

                # Create embed for general analytics
                embed = create_basic_embed(
                    title="Análise de Fluxo Narrativo",
                    description="Estatísticas gerais sobre os fluxos narrativos do jogo.",
                    color=discord.Color.blue()
                )

                # Add most common paths field
                paths_str = ""
                for path, count in analytics_data.get("most_common_paths", {}).items():
                    paths_str += f"**{path}**: {count} vezes\n"

                embed.add_field(
                    name="Caminhos Mais Comuns",
                    value=paths_str or "Nenhum caminho registrado.",
                    inline=False
                )

                # Add most common errors field
                errors_str = ""
                error_count = 0
                for chapter, errors in analytics_data.get("most_common_errors", {}).items():
                    if error_count >= 5:  # Limit to 5 errors
                        break
                    for error, count in errors.items():
                        errors_str += f"**{chapter} - {error}**: {count} vezes\n"
                        error_count += 1
                        if error_count >= 5:
                            break

                embed.add_field(
                    name="Erros Mais Comuns",
                    value=errors_str or "Nenhum erro registrado.",
                    inline=False
                )

                # Add total logs field
                total_logs = analytics_data.get("total_logs", {})
                embed.add_field(
                    name="Total de Registros",
                    value=f"**Escolhas**: {total_logs.get('choices', 0)}\n"
                          f"**Caminhos**: {total_logs.get('paths', 0)}\n"
                          f"**Erros**: {total_logs.get('errors', 0)}",
                    inline=False
                )

                # Send the response
                await interaction.followup.send(embed=embed)

        except discord.errors.NotFound:
            logger.warning(f"Interaction expired for user {interaction.user.id} when using /dashboard analytics")
        except Exception as e:
            logger.error(f"Error in slash_narrative_analytics: {e}")
            await interaction.followup.send(f"Ocorreu um erro ao gerar o dashboard: {str(e)}")

    def _get_player_choices(self, player: Dict[str, Any], chapter_id: str = None) -> Dict[str, Any]:
        """
        Gets the player's choices, optionally filtered by chapter.

        Args:
            player: The player data
            chapter_id: Optional chapter ID to filter choices

        Returns:
            Dictionary of player choices
        """
        if 'story_progress' not in player or not player['story_progress']:
            return {}

        story_progress = json.loads(player['story_progress']) if isinstance(player['story_progress'], str) else player['story_progress']

        if 'story_choices' not in story_progress:
            return {}

        if chapter_id:
            return {chapter_id: story_progress['story_choices'].get(chapter_id, {})} if chapter_id in story_progress['story_choices'] else {}
        else:
            return story_progress['story_choices']

    def _get_community_choices(self, chapter_id: str = None) -> Dict[str, Dict[str, Counter]]:
        """
        Gets aggregated choices from all players.

        Args:
            chapter_id: Optional chapter ID to filter choices

        Returns:
            Dictionary mapping chapters to choice keys to counts of each choice value
        """
        all_players = get_all_players()
        community_choices = defaultdict(lambda: defaultdict(Counter))

        for player_data in all_players:
            player_choices = self._get_player_choices(player_data, chapter_id)

            for ch_id, choices in player_choices.items():
                for choice_key, choice_value in choices.items():
                    community_choices[ch_id][choice_key][choice_value] += 1

        return community_choices

    def _get_player_path(self, player: Dict[str, Any]) -> List[str]:
        """
        Gets the player's path through the story (completed chapters).

        Args:
            player: The player data

        Returns:
            List of completed chapter IDs in order
        """
        if 'story_progress' not in player or not player['story_progress']:
            return []

        story_progress = json.loads(player['story_progress']) if isinstance(player['story_progress'], str) else player['story_progress']

        if 'completed_chapters' not in story_progress:
            return []

        return story_progress['completed_chapters']

    def _get_community_paths(self) -> Dict[str, int]:
        """
        Gets aggregated paths from all players.

        Returns:
            Dictionary mapping path strings to counts
        """
        all_players = get_all_players()
        path_counts = Counter()

        for player_data in all_players:
            player_path = self._get_player_path(player_data)
            if player_path:
                path_str = "->".join(player_path)
                path_counts[path_str] += 1

        return path_counts

    def _get_player_faction_data(self, player: Dict[str, Any]) -> Dict[str, Any]:
        """
        Gets the player's faction data.

        Args:
            player: The player data

        Returns:
            Dictionary with faction information
        """
        # For now, we'll use club_id as a proxy for faction
        club_id = player.get('club_id')
        if not club_id:
            return {}

        # Get faction reputations if available
        faction_data = {'club_id': club_id, 'reputations': {}}

        if 'story_progress' in player and player['story_progress']:
            story_progress = json.loads(player['story_progress']) if isinstance(player['story_progress'], str) else player['story_progress']

            if 'faction_reputations' in story_progress:
                faction_data['reputations'] = story_progress['faction_reputations']

        return faction_data

    def _get_community_faction_data(self) -> Dict[str, Dict[str, int]]:
        """
        Gets aggregated faction data from all players.

        Returns:
            Dictionary with faction statistics
        """
        all_players = get_all_players()
        club_counts = Counter()
        faction_reputations = defaultdict(list)

        for player_data in all_players:
            faction_data = self._get_player_faction_data(player_data)

            if 'club_id' in faction_data and faction_data['club_id']:
                club_counts[faction_data['club_id']] += 1

            for faction_id, reputation in faction_data.get('reputations', {}).items():
                faction_reputations[faction_id].append(reputation)

        # Calculate average reputations
        avg_reputations = {}
        for faction_id, reputations in faction_reputations.items():
            if reputations:
                avg_reputations[faction_id] = sum(reputations) / len(reputations)

        return {
            'club_counts': dict(club_counts),
            'avg_reputations': avg_reputations
        }

    def _analyze_gameplay_style(self, player: Dict[str, Any], player_choices: Dict[str, Any]) -> Dict[str, float]:
        """
        Analyzes the player's gameplay style based on their choices.

        Args:
            player: The player data
            player_choices: The player's choices

        Returns:
            Dictionary mapping style dimensions to scores
        """
        # Define style dimensions
        styles = {
            'diplomático': 0,
            'agressivo': 0,
            'estratégico': 0,
            'impulsivo': 0,
            'leal': 0,
            'individualista': 0
        }

        # Simple heuristic: count choice keys that contain certain keywords
        choice_count = 0

        for chapter_id, choices in player_choices.items():
            for choice_key, choice_value in choices.items():
                choice_count += 1

                # This is a simplified example - in a real implementation,
                # you would have a more sophisticated mapping of choices to styles
                if 'diplomatic' in choice_key or choice_value in [0, 3]:  # Assuming certain choice values indicate diplomatic choices
                    styles['diplomático'] += 1

                if 'aggressive' in choice_key or choice_value in [1, 4]:
                    styles['agressivo'] += 1

                if 'strategic' in choice_key or choice_value in [2, 5]:
                    styles['estratégico'] += 1

                if 'impulsive' in choice_key or choice_value in [6, 9]:
                    styles['impulsivo'] += 1

                if 'loyal' in choice_key or choice_value in [7, 10]:
                    styles['leal'] += 1

                if 'individual' in choice_key or choice_value in [8, 11]:
                    styles['individualista'] += 1

        # Normalize scores
        if choice_count > 0:
            for style in styles:
                styles[style] = (styles[style] / choice_count) * 10  # Scale to 0-10

        return styles

    def _get_community_style_data(self) -> Dict[str, float]:
        """
        Gets aggregated style data from all players.

        Returns:
            Dictionary mapping style dimensions to average scores
        """
        all_players = get_all_players()
        all_styles = []

        for player_data in all_players:
            player_choices = self._get_player_choices(player_data)
            if player_choices:
                style = self._analyze_gameplay_style(player_data, player_choices)
                all_styles.append(style)

        # Calculate average styles
        avg_styles = {}
        if all_styles:
            for style_dim in all_styles[0].keys():
                avg_styles[style_dim] = sum(s[style_dim] for s in all_styles) / len(all_styles)

        return avg_styles

    def _create_choice_comparison(self, player: Dict[str, Any], player_choices: Dict[str, Any], 
                                 community_choices: Dict[str, Dict[str, Counter]], chapter_id: str = None) -> tuple:
        """
        Creates a visualization comparing player choices with community choices.

        Args:
            player: The player data
            player_choices: The player's choices
            community_choices: Aggregated community choices
            chapter_id: Optional chapter ID to filter choices

        Returns:
            Tuple of (embed, file) for the visualization
        """
        # Create a new figure
        plt.figure(figsize=(10, 6))

        # Select a chapter to visualize if not specified
        if not chapter_id and player_choices:
            # Use the most recent chapter
            chapter_id = list(player_choices.keys())[-1]

        # Get choices for the selected chapter
        chapter_choices = player_choices.get(chapter_id, {})
        community_chapter_choices = community_choices.get(chapter_id, {})

        # Select a choice to visualize (first one with community data)
        choice_key = None
        for key in chapter_choices:
            if key in community_chapter_choices and community_chapter_choices[key]:
                choice_key = key
                break

        if not choice_key:
            # Create a simple embed if no comparable choices found
            embed = create_basic_embed(
                title="Comparação de Escolhas",
                description="Não há dados suficientes para comparar suas escolhas com a comunidade neste capítulo.",
                color=discord.Color.blue()
            )
            return embed, None

        # Get the player's choice and community choices for this key
        player_choice = chapter_choices[choice_key]
        choice_counts = community_chapter_choices[choice_key]

        # Prepare data for plotting
        labels = []
        values = []
        colors = []

        for choice_value, count in choice_counts.items():
            labels.append(f"Opção {choice_value}")
            values.append(count)
            colors.append('red' if choice_value == player_choice else 'blue')

        # Create bar chart
        plt.bar(labels, values, color=colors)
        plt.title(f"Comparação de Escolhas - Capítulo {chapter_id}")
        plt.xlabel("Opções")
        plt.ylabel("Número de Jogadores")

        # Add text to highlight player's choice
        for i, (label, value) in enumerate(zip(labels, values)):
            if colors[i] == 'red':
                plt.text(i, value + 0.5, "Sua escolha", ha='center', fontweight='bold')

        # Save the figure to a bytes buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)

        # Create a Discord file from the buffer
        file = discord.File(buf, filename="choice_comparison.png")

        # Create embed with the image
        embed = create_basic_embed(
            title="Dashboard de Comparação de Decisões",
            description=f"Veja como suas escolhas no capítulo {chapter_id} se comparam às da comunidade.",
            color=discord.Color.blue()
        )
        embed.set_image(url="attachment://choice_comparison.png")

        # Add some statistics
        total_players = sum(values)
        player_choice_count = choice_counts.get(player_choice, 0)
        percentage = (player_choice_count / total_players) * 100 if total_players > 0 else 0

        embed.add_field(
            name="Estatísticas",
            value=f"**{percentage:.1f}%** dos jogadores fizeram a mesma escolha que você.\n"
                  f"**{player_choice_count}** de **{total_players}** jogadores escolheram a opção {player_choice}.",
            inline=False
        )

        return embed, file

    def _create_path_analysis(self, player: Dict[str, Any], player_path: List[str], 
                             community_paths: Dict[str, int]) -> tuple:
        """
        Creates a visualization of narrative paths.

        Args:
            player: The player data
            player_path: The player's path through the story
            community_paths: Aggregated community paths

        Returns:
            Tuple of (embed, file) for the visualization
        """
        # Create a new figure
        plt.figure(figsize=(10, 6))

        # Convert player path to string
        player_path_str = "->".join(player_path)

        # Get the top 5 most common paths
        top_paths = dict(community_paths.most_common(5))

        # Ensure player's path is included
        if player_path_str not in top_paths:
            top_paths[player_path_str] = community_paths.get(player_path_str, 1)

        # Prepare data for plotting
        labels = []
        values = []
        colors = []

        for path_str, count in top_paths.items():
            # Shorten path strings for display
            if len(path_str) > 20:
                display_str = path_str[:8] + "..." + path_str[-8:]
            else:
                display_str = path_str

            labels.append(display_str)
            values.append(count)
            colors.append('red' if path_str == player_path_str else 'blue')

        # Create bar chart
        plt.bar(labels, values, color=colors)
        plt.title("Análise de Caminhos Narrativos")
        plt.xlabel("Caminhos")
        plt.ylabel("Número de Jogadores")
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()

        # Add text to highlight player's path
        for i, (label, value) in enumerate(zip(labels, values)):
            if colors[i] == 'red':
                plt.text(i, value + 0.5, "Seu caminho", ha='center', fontweight='bold')

        # Save the figure to a bytes buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)

        # Create a Discord file from the buffer
        file = discord.File(buf, filename="path_analysis.png")

        # Create embed with the image
        embed = create_basic_embed(
            title="Análise de Caminhos Narrativos",
            description="Veja como seu caminho pela história se compara aos caminhos mais populares.",
            color=discord.Color.blue()
        )
        embed.set_image(url="attachment://path_analysis.png")

        # Add some statistics
        total_players = sum(community_paths.values())
        player_path_count = community_paths.get(player_path_str, 1)
        percentage = (player_path_count / total_players) * 100 if total_players > 0 else 0

        # Determine if the path is common or rare
        path_rarity = "muito comum" if percentage > 30 else \
                      "comum" if percentage > 15 else \
                      "incomum" if percentage > 5 else \
                      "raro" if percentage > 1 else "extremamente raro"

        embed.add_field(
            name="Estatísticas",
            value=f"Seu caminho é **{path_rarity}**.\n"
                  f"**{percentage:.1f}%** dos jogadores seguiram o mesmo caminho que você.\n"
                  f"**{player_path_count}** de **{total_players}** jogadores completaram esta sequência de capítulos.",
            inline=False
        )

        return embed, file

    def _create_faction_stats(self, player: Dict[str, Any], player_faction: Dict[str, Any], 
                             community_factions: Dict[str, Dict[str, int]]) -> tuple:
        """
        Creates a visualization of faction statistics.

        Args:
            player: The player data
            player_faction: The player's faction data
            community_factions: Aggregated community faction data

        Returns:
            Tuple of (embed, file) for the visualization
        """
        # Create a new figure
        plt.figure(figsize=(10, 6))

        # Get player's club ID
        player_club_id = player_faction.get('club_id')

        # Get club distribution
        club_counts = community_factions.get('club_counts', {})

        # Prepare data for plotting
        labels = []
        values = []
        colors = []

        for club_id, count in club_counts.items():
            labels.append(f"Clube {club_id}")
            values.append(count)
            colors.append('red' if club_id == player_club_id else 'blue')

        # Create pie chart
        plt.pie(values, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
        plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
        plt.title("Distribuição de Jogadores por Clube")

        # Save the figure to a bytes buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)

        # Create a Discord file from the buffer
        file = discord.File(buf, filename="faction_stats.png")

        # Create embed with the image
        embed = create_basic_embed(
            title="Estatísticas de Facções e Alianças",
            description="Veja como os jogadores estão distribuídos entre os diferentes clubes.",
            color=discord.Color.blue()
        )
        embed.set_image(url="attachment://faction_stats.png")

        # Add some statistics
        total_players = sum(club_counts.values())
        player_club_count = club_counts.get(player_club_id, 0)
        percentage = (player_club_count / total_players) * 100 if total_players > 0 else 0

        embed.add_field(
            name="Estatísticas",
            value=f"**{percentage:.1f}%** dos jogadores escolheram o mesmo clube que você.\n"
                  f"**{player_club_count}** de **{total_players}** jogadores estão no Clube {player_club_id}.",
            inline=False
        )

        return embed, file

    def _create_style_analysis(self, player: Dict[str, Any], player_style: Dict[str, float], 
                              community_styles: Dict[str, float]) -> tuple:
        """
        Creates a visualization of gameplay style analysis.

        Args:
            player: The player data
            player_style: The player's style analysis
            community_styles: Aggregated community style data

        Returns:
            Tuple of (embed, file) for the visualization
        """
        # Create a new figure
        plt.figure(figsize=(10, 6))

        # Prepare data for radar chart
        categories = list(player_style.keys())
        N = len(categories)

        # Convert to numpy arrays for plotting
        player_values = np.array([player_style.get(cat, 0) for cat in categories])
        community_values = np.array([community_styles.get(cat, 0) for cat in categories])

        # Create angles for each category
        angles = np.linspace(0, 2*np.pi, N, endpoint=False).tolist()

        # Close the loop
        player_values = np.concatenate((player_values, [player_values[0]]))
        community_values = np.concatenate((community_values, [community_values[0]]))
        angles = angles + [angles[0]]
        categories = categories + [categories[0]]

        # Create radar chart
        ax = plt.subplot(111, polar=True)

        # Plot player values
        ax.plot(angles, player_values, 'r-', linewidth=2, label='Você')
        ax.fill(angles, player_values, 'r', alpha=0.25)

        # Plot community values
        ax.plot(angles, community_values, 'b-', linewidth=2, label='Comunidade')
        ax.fill(angles, community_values, 'b', alpha=0.25)

        # Set category labels
        plt.xticks(angles[:-1], categories[:-1])

        # Set y-axis limits
        ax.set_ylim(0, 10)

        # Add legend
        plt.legend(loc='upper right', bbox_to_anchor=(0.1, 0.1))

        plt.title("Análise de Estilo de Jogo")

        # Save the figure to a bytes buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)

        # Create a Discord file from the buffer
        file = discord.File(buf, filename="style_analysis.png")

        # Create embed with the image
        embed = create_basic_embed(
            title="Análise de Estilo de Jogo",
            description="Veja como seu estilo de jogo se compara com o da comunidade.",
            color=discord.Color.blue()
        )
        embed.set_image(url="attachment://style_analysis.png")

        # Determine dominant style
        dominant_style = max(player_style.items(), key=lambda x: x[1])[0]

        # Add style analysis
        embed.add_field(
            name="Seu Estilo Dominante",
            value=f"Seu estilo de jogo é predominantemente **{dominant_style}**.",
            inline=False
        )

        # Add style comparison
        style_comparisons = []
        for style, player_score in player_style.items():
            community_score = community_styles.get(style, 0)
            difference = player_score - community_score

            if abs(difference) < 1:
                comparison = f"similar à média"
            elif difference > 0:
                comparison = f"mais {style} que a média"
            else:
                comparison = f"menos {style} que a média"

            style_comparisons.append(f"**{style.capitalize()}**: {comparison}")

        embed.add_field(
            name="Comparação com a Comunidade",
            value="\n".join(style_comparisons),
            inline=False
        )

        # Add content suggestions based on style
        suggestions = {
            'diplomático': "Experimente missões de negociação e alianças com NPCs.",
            'agressivo': "Busque desafios de combate e competições entre clubes.",
            'estratégico': "Explore missões que envolvem planejamento e resolução de problemas complexos.",
            'impulsivo': "Participe de eventos de ação rápida e desafios com tempo limitado.",
            'leal': "Aprofunde-se em missões relacionadas ao seu clube e construa relacionamentos com NPCs.",
            'individualista': "Busque missões solo e oportunidades para desenvolver habilidades únicas."
        }

        embed.add_field(
            name="Sugestões de Conteúdo",
            value=suggestions.get(dominant_style, "Continue explorando diferentes aspectos do jogo."),
            inline=False
        )

        return embed, file

def setup(bot):
    """
    Adds the DecisionDashboard cog to the bot.

    Args:
        bot: The Discord bot instance
    """
    try:
        # Check if matplotlib is available
        import matplotlib
        bot.add_cog(DecisionDashboard(bot))
        logger.info("DecisionDashboard cog loaded successfully")
    except ImportError:
        logger.error("Failed to load DecisionDashboard cog: matplotlib is required")
        raise ImportError("The matplotlib library is required for the DecisionDashboard cog. Please install it with 'pip install matplotlib'.")
