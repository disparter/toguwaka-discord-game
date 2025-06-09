import discord
from discord.ext import commands
from discord import app_commands
import logging
import random
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union

from src.utils.persistence.db_provider import get_player, update_player, get_club, get_all_clubs
from src.utils.embeds import create_basic_embed, create_event_embed
from src.utils.game_mechanics import calculate_level_from_exp
from story_mode.club_system import ClubSystem

class MoralChoices(commands.Cog):
    """Cog para gerenciar dilemas morais e eventos coletivos na Academia Tokugawa."""

    def __init__(self, bot):
        self.bot = bot
        self.active_dilemas = {}  # user_id: dilema_data
        self.active_collective_events = {}  # event_id: event_data
        self.player_moral_choices = {}  # user_id: {choice_type: count}
        self.cooldowns = {}  # user_id: {command: timestamp}
        self.logger = logging.getLogger('tokugawa.moral_choices')
        self.logger.info('MoralChoices cog initialized')
        self.club_system = ClubSystem()

    @app_commands.command(
        name="dilema",
        description="Enfrenta um dilema moral que testará seus valores e afetará sua reputação na Academia Tokugawa."
    )
    async def slash_dilema(self, interaction: discord.Interaction):
        """Comando para enfrentar um dilema moral."""
        user_id = interaction.user.id

        # Verificar cooldown
        if self._check_cooldown(user_id, "dilema"):
            remaining = self._get_remaining_cooldown(user_id, "dilema")
            await interaction.response.send_message(
                f"Você ainda está refletindo sobre seu último dilema. Tente novamente em {remaining} minutos.",
                ephemeral=True
            )
            return

        # Obter dados do jogador
        player_data = await get_player(user_id)
        if not player_data:
            await interaction.response.send_message(
                "Você precisa se registrar primeiro usando o comando `/registrar`.",
                ephemeral=True
            )
            return

        # Verificar se o jogador já está em um dilema
        if user_id in self.active_dilemas:
            await interaction.response.send_message(
                "Você já está enfrentando um dilema. Resolva-o antes de iniciar outro.",
                ephemeral=True
            )
            return

        # Gerar um dilema aleatório
        dilema = self._generate_random_dilema(player_data)
        self.active_dilemas[user_id] = dilema

        # Criar embed para o dilema
        embed = self._create_dilema_embed(dilema)

        # Criar botões para as escolhas
        view = discord.ui.View(timeout=300)  # 5 minutos para decidir

        for i, choice in enumerate(dilema["choices"]):
            button = discord.ui.Button(
                style=discord.ButtonStyle.primary,
                label=choice["label"],
                custom_id=f"dilema_choice_{i}"
            )
            button.callback = self._create_dilema_choice_callback(user_id, i)
            view.add_item(button)

        await interaction.response.send_message(embed=embed, view=view)

        # Definir cooldown
        self._set_cooldown(user_id, "dilema")

    def _create_dilema_choice_callback(self, user_id: int, choice_index: int):
        """Cria um callback para os botões de escolha do dilema."""
        async def dilema_choice_callback(interaction: discord.Interaction):
            # Verificar se o usuário é o mesmo que iniciou o dilema
            if interaction.user.id != user_id:
                await interaction.response.send_message(
                    "Este não é o seu dilema moral.",
                    ephemeral=True
                )
                return

            # Obter o dilema e a escolha
            dilema = self.active_dilemas.get(user_id)
            if not dilema:
                await interaction.response.send_message(
                    "Este dilema não está mais ativo.",
                    ephemeral=True
                )
                return

            choice = dilema["choices"][choice_index]

            # Aplicar consequências da escolha
            player_data = await get_player(user_id)

            # Registrar a escolha moral
            choice_type = choice.get("type", "neutral")
            if user_id not in self.player_moral_choices:
                self.player_moral_choices[user_id] = {}

            if choice_type not in self.player_moral_choices[user_id]:
                self.player_moral_choices[user_id][choice_type] = 0

            self.player_moral_choices[user_id][choice_type] += 1

            # Aplicar recompensas ou penalidades
            for attr, value in choice.get("effects", {}).items():
                if attr in player_data:
                    player_data[attr] += value

            # Atualizar reputação com facções, se aplicável
            for faction, value in choice.get("faction_reputation", {}).items():
                if "factions" not in player_data:
                    player_data["factions"] = {}

                if faction not in player_data["factions"]:
                    player_data["factions"][faction] = 0

                player_data["factions"][faction] += value

            # Salvar as alterações
            await update_player(user_id, player_data)

            # Remover o dilema ativo
            del self.active_dilemas[user_id]

            # Criar embed de resultado
            result_embed = discord.Embed(
                title="Resultado do Dilema",
                description=choice["result"],
                color=discord.Color.blue()
            )

            # Adicionar campos para efeitos
            effects_text = ""
            for attr, value in choice.get("effects", {}).items():
                sign = "+" if value > 0 else ""
                effects_text += f"{attr.capitalize()}: {sign}{value}\n"

            if effects_text:
                result_embed.add_field(name="Efeitos", value=effects_text, inline=False)

            # Adicionar campos para reputação com facções
            faction_text = ""
            for faction, value in choice.get("faction_reputation", {}).items():
                sign = "+" if value > 0 else ""
                faction_text += f"{faction}: {sign}{value}\n"

            if faction_text:
                result_embed.add_field(name="Reputação com Facções", value=faction_text, inline=False)

            # Adicionar campo para karma/moralidade
            result_embed.add_field(
                name="Impacto Moral",
                value=f"Esta escolha reflete uma tendência {choice_type.capitalize()}.",
                inline=False
            )

            await interaction.response.edit_message(embed=result_embed, view=None)

        return dilema_choice_callback

    @app_commands.command(
        name="atividade_moral",
        description="Participa de atividades coletivas morais na Academia Tokugawa."
    )
    @app_commands.choices(
        tipo=[
            app_commands.Choice(name="Motim", value="motim"),
            app_commands.Choice(name="Eleição", value="eleicao"),
            app_commands.Choice(name="Sabotagem", value="sabotagem"),
            app_commands.Choice(name="Coletivo", value="coletivo"),
            app_commands.Choice(name="Dilema", value="dilema")
        ]
    )
    @app_commands.choices(
        acao=[
            app_commands.Choice(name="Info", value="info"),
            app_commands.Choice(name="Participar", value="participar"),
            app_commands.Choice(name="Apoiar", value="apoiar"),
            app_commands.Choice(name="Reprimir", value="reprimir"),
            app_commands.Choice(name="Votar", value="votar"),
            app_commands.Choice(name="Candidatar", value="candidatar"),
            app_commands.Choice(name="Planejar", value="planejar"),
            app_commands.Choice(name="Executar", value="executar"),
            app_commands.Choice(name="Investigar", value="investigar")
        ]
    )
    async def slash_atividade_moral(
        self, 
        interaction: discord.Interaction, 
        tipo: str,
        acao: str,
        alvo: str = None
    ):
        """Comando para participar de atividades coletivas."""
        user_id = interaction.user.id

        # Verificar registro
        player_data = await get_player(user_id)
        if not player_data:
            await interaction.response.send_message(
                "Você precisa se registrar primeiro usando o comando `/registrar`.",
                ephemeral=True
            )
            return

        # Verificar cooldown
        if self._check_cooldown(user_id, f"atividade_{tipo}"):
            remaining = self._get_remaining_cooldown(user_id, f"atividade_{tipo}")
            await interaction.response.send_message(
                f"Você precisa esperar {remaining} minutos antes de participar de outra atividade deste tipo.",
                ephemeral=True
            )
            return

        # Processar com base no tipo e ação
        if tipo == "motim":
            await self._handle_motim(interaction, acao, alvo, player_data)
        elif tipo == "eleicao":
            await self._handle_eleicao(interaction, acao, alvo, player_data)
        elif tipo == "sabotagem":
            await self._handle_sabotagem(interaction, acao, alvo, player_data)
        elif tipo == "coletivo":
            await self._handle_coletivo(interaction, acao, alvo, player_data)
        elif tipo == "dilema":
            # Redirecionar para o comando de dilema
            await self.slash_dilema(interaction)
            return

        # Definir cooldown (exceto para ações de info)
        if acao != "info":
            self._set_cooldown(user_id, f"atividade_{tipo}")

    async def _handle_motim(self, interaction, acao, alvo, player_data):
        """Gerencia a participação em motins."""
        # Obter o ID do usuário
        user_id = interaction.user.id

        # Verificar se há um motim ativo
        active_motins = [e for e in self.active_collective_events.values() if e["type"] == "motim"]

        if acao == "info":
            if not active_motins:
                await interaction.response.send_message(
                    "Não há motins ativos no momento. A academia está em paz... por enquanto.",
                    ephemeral=True
                )
                return

            # Criar embed com informações sobre motins ativos
            embed = discord.Embed(
                title="Motins Ativos",
                description="Os seguintes motins estão ocorrendo na academia:",
                color=discord.Color.red()
            )

            for motim in active_motins:
                supporters = len(motim.get("supporters", []))
                suppressors = len(motim.get("suppressors", []))
                total = supporters + suppressors

                if total > 0:
                    support_percentage = (supporters / total) * 100
                else:
                    support_percentage = 0

                embed.add_field(
                    name=motim["title"],
                    value=(
                        f"{motim['description']}\n"
                        f"Apoiadores: {supporters} | Repressores: {suppressors}\n"
                        f"Suporte: {support_percentage:.1f}%\n"
                        f"ID: `{motim['id']}`"
                    ),
                    inline=False
                )

            await interaction.response.send_message(embed=embed)
            return

        # Para ações que requerem um motim específico
        if not alvo and active_motins:
            # Se houver apenas um motim ativo, use-o como alvo
            if len(active_motins) == 1:
                alvo = active_motins[0]["id"]
            else:
                await interaction.response.send_message(
                    "Existem múltiplos motins ativos. Por favor, especifique o ID do motim.",
                    ephemeral=True
                )
                return

        if not alvo:
            await interaction.response.send_message(
                "Não há motins ativos no momento.",
                ephemeral=True
            )
            return

        # Encontrar o motim alvo
        motim = next((m for m in active_motins if m["id"] == alvo), None)
        if not motim:
            await interaction.response.send_message(
                f"Motim com ID '{alvo}' não encontrado.",
                ephemeral=True
            )
            return

        # Processar a ação
        if acao == "apoiar":
            # Remover o jogador dos repressores, se estiver lá
            if user_id in motim.get("suppressors", []):
                motim["suppressors"].remove(user_id)

            # Adicionar o jogador aos apoiadores
            if "supporters" not in motim:
                motim["supporters"] = []

            if user_id not in motim["supporters"]:
                motim["supporters"].append(user_id)
                await interaction.response.send_message(
                    f"Você decidiu apoiar o motim '{motim['title']}'.",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    f"Você já está apoiando este motim.",
                    ephemeral=True
                )

        elif acao == "reprimir":
            # Remover o jogador dos apoiadores, se estiver lá
            if user_id in motim.get("supporters", []):
                motim["supporters"].remove(user_id)

            # Adicionar o jogador aos repressores
            if "suppressors" not in motim:
                motim["suppressors"] = []

            if user_id not in motim["suppressors"]:
                motim["suppressors"].append(user_id)
                await interaction.response.send_message(
                    f"Você decidiu reprimir o motim '{motim['title']}'.",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    f"Você já está reprimindo este motim.",
                    ephemeral=True
                )

        # Verificar se o motim deve ser resolvido
        self._check_motim_resolution(motim)

    def _check_motim_resolution(self, motim):
        """Verifica se um motim deve ser resolvido e aplica as consequências."""
        # Implementação básica - pode ser expandida
        supporters = len(motim.get("supporters", []))
        suppressors = len(motim.get("suppressors", []))
        total = supporters + suppressors

        # Resolver se houver pelo menos 10 participantes e 75% de suporte em uma direção
        if total >= 10:
            if supporters / total >= 0.75:
                # Motim bem-sucedido
                self._resolve_motim(motim, True)
            elif suppressors / total >= 0.75:
                # Motim reprimido
                self._resolve_motim(motim, False)

    def _resolve_motim(self, motim, success):
        """Resolve um motim e aplica as consequências."""
        # Implementação básica - pode ser expandida
        motim["resolved"] = True
        motim["success"] = success

        # Aplicar consequências (a ser implementado)
        # Por exemplo, alterar preços na loja, desbloquear áreas, etc.

        # Remover dos eventos ativos
        if motim["id"] in self.active_collective_events:
            del self.active_collective_events[motim["id"]]

    async def _handle_eleicao(self, interaction, acao, alvo, player_data):
        """Gerencia a participação em eleições."""
        # Implementação básica - pode ser expandida
        await interaction.response.send_message(
            "Sistema de eleições em desenvolvimento. Fique atento para atualizações futuras!",
            ephemeral=True
        )

    async def _handle_sabotagem(self, interaction, acao, alvo, player_data):
        """Gerencia a participação em sabotagens."""
        # Implementação básica - pode ser expandida
        await interaction.response.send_message(
            "Sistema de sabotagens em desenvolvimento. Fique atento para atualizações futuras!",
            ephemeral=True
        )

    async def _handle_coletivo(self, interaction, acao, alvo, player_data):
        """Gerencia a participação em eventos coletivos genéricos."""
        # Obter o ID do usuário
        user_id = interaction.user.id

        # Verificar eventos coletivos ativos
        active_events = list(self.active_collective_events.values())

        if acao == "info":
            if not active_events:
                await interaction.response.send_message(
                    "Não há eventos coletivos ativos no momento.",
                    ephemeral=True
                )
                return

            # Criar embed com informações sobre eventos ativos
            embed = discord.Embed(
                title="Eventos Coletivos Ativos",
                description="Os seguintes eventos coletivos estão ocorrendo na academia:",
                color=discord.Color.blue()
            )

            for event in active_events:
                participants = len(event.get("participants", []))
                required = event.get("required_participants", 0)

                embed.add_field(
                    name=event["title"],
                    value=(
                        f"{event['description']}\n"
                        f"Participantes: {participants}/{required}\n"
                        f"Tipo: {event['type'].capitalize()}\n"
                        f"ID: `{event['id']}`"
                    ),
                    inline=False
                )

            await interaction.response.send_message(embed=embed)
            return

        # Para ações que requerem um evento específico
        if not alvo:
            await interaction.response.send_message(
                "Por favor, especifique o ID do evento coletivo.",
                ephemeral=True
            )
            return

        # Encontrar o evento alvo
        event = self.active_collective_events.get(alvo)
        if not event:
            await interaction.response.send_message(
                f"Evento coletivo com ID '{alvo}' não encontrado.",
                ephemeral=True
            )
            return

        # Processar a ação
        if acao == "participar":
            # Adicionar o jogador aos participantes
            if "participants" not in event:
                event["participants"] = []

            if user_id not in event["participants"]:
                event["participants"].append(user_id)
                await interaction.response.send_message(
                    f"Você decidiu participar do evento '{event['title']}'.",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    f"Você já está participando deste evento.",
                    ephemeral=True
                )

            # Verificar se o evento deve ser ativado
            self._check_event_activation(event)

    def _check_event_activation(self, event):
        """Verifica se um evento coletivo deve ser ativado e aplica as consequências."""
        # Implementação básica - pode ser expandida
        participants = len(event.get("participants", []))
        required = event.get("required_participants", 0)

        if participants >= required:
            # Evento ativado
            self._activate_event(event)

    def _activate_event(self, event):
        """Ativa um evento coletivo e aplica as consequências."""
        # Implementação básica - pode ser expandida
        event["activated"] = True

        # Aplicar consequências (a ser implementado)
        # Por exemplo, revelar fragmentos do Segredo de Tokugawa

    def _generate_random_dilema(self, player_data):
        """Gera um dilema moral aleatório baseado nos dados do jogador."""
        # Lista de dilemas possíveis
        dilemas = [
            {
                "title": "Conhecimento Proibido",
                "description": "Você encontrou um livro antigo na Biblioteca Proibida que contém informações sobre o Segredo de Tokugawa. O livro está claramente marcado como restrito.",
                "choices": [
                    {
                        "label": "Ler o livro secretamente",
                        "result": "Você lê o livro e descobre informações valiosas sobre a verdadeira natureza da academia, mas um monitor o vê e reporta seu comportamento à administração.",
                        "type": "rebelde",
                        "effects": {"exp": 50, "tusd": -20},
                        "faction_reputation": {"Guardiões": -10, "Iluminados": 15}
                    },
                    {
                        "label": "Reportar o livro à administração",
                        "result": "Você entrega o livro ao diretor, que agradece sua honestidade. Ele oferece uma recompensa, mas você perde a chance de descobrir segredos importantes.",
                        "type": "leal",
                        "effects": {"exp": 20, "tusd": 50},
                        "faction_reputation": {"Guardiões": 15, "Iluminados": -10}
                    },
                    {
                        "label": "Compartilhar com seu clube",
                        "result": "Você compartilha o livro com membros confiáveis do seu clube. Juntos, vocês descobrem informações valiosas, mas agora todos estão envolvidos em algo potencialmente perigoso.",
                        "type": "colaborativo",
                        "effects": {"exp": 35, "tusd": 0},
                        "faction_reputation": {"Guardiões": -5, "Iluminados": 5}
                    }
                ]
            },
            {
                "title": "Amigo em Apuros",
                "description": "Seu amigo cometeu uma infração grave das regras da academia ao tentar acessar uma área restrita. Ele pede que você forneça um álibi falso.",
                "choices": [
                    {
                        "label": "Fornecer o álibi",
                        "result": "Você mente para proteger seu amigo. Ele escapa da punição, mas você se sente culpado e preocupado com as consequências futuras.",
                        "type": "leal_amigos",
                        "effects": {"carisma": 5, "intelecto": -5},
                        "faction_reputation": {"Guardiões": -5}
                    },
                    {
                        "label": "Recusar-se a mentir",
                        "result": "Você se recusa a mentir, mesmo para um amigo. Ele enfrenta as consequências de suas ações, mas sua integridade permanece intacta.",
                        "type": "justo",
                        "effects": {"intelecto": 10, "carisma": -5},
                        "faction_reputation": {"Guardiões": 5}
                    },
                    {
                        "label": "Convencê-lo a confessar",
                        "result": "Você convence seu amigo a assumir a responsabilidade por suas ações. A punição é reduzida devido à honestidade, e você ganha respeito por sua sabedoria.",
                        "type": "diplomatico",
                        "effects": {"intelecto": 5, "carisma": 5},
                        "faction_reputation": {"Guardiões": 10, "Iluminados": 5}
                    }
                ]
            },
            {
                "title": "Rivalidade de Clubes",
                "description": "Seu clube está em uma competição acirrada com um clube rival. Você descobre uma falha que poderia ser explorada para garantir a vitória do seu clube.",
                "choices": [
                    {
                        "label": "Explorar a falha",
                        "result": "Você explora a falha e seu clube vence, mas você sabe que a vitória não foi justa. Alguns membros suspeitam de trapaça.",
                        "type": "pragmatico",
                        "effects": {"poder": 10, "intelecto": -5},
                        "faction_reputation": {}
                    },
                    {
                        "label": "Ignorar a falha",
                        "result": "Você decide competir honestamente. Seu clube pode não vencer, mas você mantém sua integridade e ganha respeito.",
                        "type": "honesto",
                        "effects": {"intelecto": 5, "carisma": 5},
                        "faction_reputation": {}
                    },
                    {
                        "label": "Reportar a falha",
                        "result": "Você reporta a falha aos organizadores. A competição é adiada para corrigir o problema, e você ganha respeito por sua honestidade, mas alguns membros do seu clube ficam desapontados.",
                        "type": "justo",
                        "effects": {"intelecto": 10, "carisma": -5},
                        "faction_reputation": {}
                    }
                ]
            }
        ]

        # Selecionar um dilema aleatório
        dilema = random.choice(dilemas)

        # Adicionar um ID único
        dilema["id"] = f"dilema_{datetime.now().strftime('%Y%m%d%H%M%S')}_{random.randint(1000, 9999)}"

        return dilema

    def _create_dilema_embed(self, dilema):
        """Cria um embed para um dilema moral."""
        embed = discord.Embed(
            title=f"Dilema Moral: {dilema['title']}",
            description=dilema["description"],
            color=discord.Color.purple()
        )

        embed.add_field(
            name="Escolhas",
            value="Selecione uma das opções abaixo. Sua escolha afetará sua reputação e relacionamentos na academia.",
            inline=False
        )

        return embed

    def _check_cooldown(self, user_id, command):
        """Verifica se um comando está em cooldown para um usuário."""
        if user_id not in self.cooldowns:
            return False

        if command not in self.cooldowns[user_id]:
            return False

        cooldown_time = self.cooldowns[user_id][command]
        current_time = datetime.now()

        # Cooldown padrão de 30 minutos
        if current_time < cooldown_time + timedelta(minutes=30):
            return True

        return False

    def _get_remaining_cooldown(self, user_id, command):
        """Retorna o tempo restante de cooldown em minutos."""
        if not self._check_cooldown(user_id, command):
            return 0

        cooldown_time = self.cooldowns[user_id][command]
        current_time = datetime.now()

        remaining_seconds = (cooldown_time + timedelta(minutes=30) - current_time).total_seconds()
        remaining_minutes = max(1, int(remaining_seconds / 60))

        return remaining_minutes

    def _set_cooldown(self, user_id, command, custom_duration=None):
        """Define um cooldown para um comando."""
        if user_id not in self.cooldowns:
            self.cooldowns[user_id] = {}

        self.cooldowns[user_id][command] = datetime.now()

    @commands.command(name="alianca")
    async def form_alliance(self, ctx, *, club_name: str):
        """Forma uma aliança com outro clube."""
        # Get player data
        player = get_player(ctx.author.id)
        if not player:
            await ctx.send("Você precisa se registrar primeiro! Use o comando `!registrar`.")
            return

        # Check if player is in a club
        if not player.get('club'):
            await ctx.send("Você precisa estar em um clube para formar alianças!")
            return

        # Find target club
        target_club_id = None
        for club_id, name in self.club_system.CLUBS.items():
            if name.lower() == club_name.lower():
                target_club_id = club_id
                break

        if not target_club_id:
            await ctx.send(f"Clube '{club_name}' não encontrado. Use `!clubes` para ver a lista de clubes disponíveis.")
            return

        # Form alliance
        result = self.club_system.form_alliance(player, target_club_id)
        if "error" in result:
            await ctx.send(result["error"])
            return

        # Create embed
        embed = create_basic_embed(
            title="Aliança Formada!",
            description=f"Seu clube formou uma aliança com o clube {club_name}!",
            color=0x00FF00
        )

        # Add alliance information
        embed.add_field(
            name="Detalhes da Aliança",
            value=result["message"],
            inline=False
        )

        await ctx.send(embed=embed)

    @commands.command(name="rivalidade")
    async def declare_rivalry(self, ctx, *, club_name: str):
        """Declara rivalidade com outro clube."""
        # Get player data
        player = get_player(ctx.author.id)
        if not player:
            await ctx.send("Você precisa se registrar primeiro! Use o comando `!registrar`.")
            return

        # Check if player is in a club
        if not player.get('club'):
            await ctx.send("Você precisa estar em um clube para declarar rivalidades!")
            return

        # Find target club
        target_club_id = None
        for club_id, name in self.club_system.CLUBS.items():
            if name.lower() == club_name.lower():
                target_club_id = club_id
                break

        if not target_club_id:
            await ctx.send(f"Clube '{club_name}' não encontrado. Use `!clubes` para ver a lista de clubes disponíveis.")
            return

        # Declare rivalry
        result = self.club_system.declare_rivalry(player, target_club_id)
        if "error" in result:
            await ctx.send(result["error"])
            return

        # Create embed
        embed = create_basic_embed(
            title="Rivalidade Declarada!",
            description=f"Seu clube declarou rivalidade com o clube {club_name}!",
            color=0xFF0000
        )

        # Add rivalry information
        embed.add_field(
            name="Detalhes da Rivalidade",
            value=result["message"],
            inline=False
        )

        await ctx.send(embed=embed)

async def setup(bot):
    """Adiciona o cog ao bot."""
    await bot.add_cog(MoralChoices(bot))
    logging.getLogger('tokugawa').info('MoralChoices cog loaded')
