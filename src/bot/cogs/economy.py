import discord
from discord.ext import commands
from discord import app_commands
import logging
import random
import asyncio
import json
import os
from datetime import datetime, timedelta
from src.utils.persistence import db_provider
from src.utils.persistence.db_provider import get_player, update_player, get_club
from src.utils.embeds import create_basic_embed
from src.utils.game_mechanics import RARITIES
from src.utils.club_perks import apply_shop_discount
from src.bot.cogs.activities import COOLDOWNS, COOLDOWN_DURATIONS

logger = logging.getLogger('tokugawa_bot')

# Load JSON data
def load_json(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading JSON file {file_path}: {e}")
        return {}

# Load all economy data from JSON files
ITEM_CATEGORIES = load_json('data/economy/item_categories.json')
ITEM_TYPES = load_json('data/economy/item_types.json')
SEASONS = load_json('data/economy/seasons.json')
ALTERNATIVE_CURRENCIES = load_json('data/economy/alternative_currencies.json')

# Load more economy data from JSON files
SPECIAL_CURRENCY_ITEMS = load_json('data/economy/special_currency_items.json')
ITEM_EXCHANGES = load_json('data/economy/item_exchanges.json')

# Load items from new category-based structure
TRAINING_ITEMS = load_json('data/economy/items/training_items.json')
COMBAT_ITEMS = load_json('data/economy/items/combat_items.json')
ENERGY_ITEMS = load_json('data/economy/items/energy_items.json')
ATTRIBUTE_ITEMS = load_json('data/economy/items/attribute_items.json')
SOCIAL_ITEMS = load_json('data/economy/items/social_items.json')

# Itens sazonais (baseados na estação/bimestre)
SEASONAL_ITEMS = load_json('data/economy/seasonal_items.json')

# Itens de eventos especiais (desbloqueados por eventos específicos)
EVENT_ITEMS = load_json('data/economy/event_items.json')

# Itens lendários (desbloqueados por progresso avançado ou eventos especiais)
LEGENDARY_ITEMS = load_json('data/economy/legendary_items.json')

# Itens temáticos de clubes (disponíveis apenas para membros de clubes específicos)
CLUB_ITEMS = load_json('data/economy/club_items.json')

# Função para obter os itens disponíveis com base no bimestre atual, eventos ativos, nível do jogador e clube
def get_available_shop_items(bimestre=1, active_events=None, player_level=1, player_club=None, current_date=None):
    """
    Retorna os itens disponíveis na loja com base no bimestre atual, eventos ativos, nível do jogador e clube.

    Args:
        bimestre (int): O bimestre atual (1-4)
        active_events (list): Lista de eventos ativos
        player_level (int): Nível atual do jogador
        player_club (str): Clube do jogador
        current_date (datetime): Data atual para rotação de itens

    Returns:
        dict: Dicionário com categorias de itens disponíveis na loja
    """
    if active_events is None:
        active_events = []

    if current_date is None:
        current_date = datetime.now()

    # Inicializa o dicionário de itens por categoria
    available_items = {
        "consumable": [],
        "accessory": [],
        "equipment": [],
        "legendary": [],
        "thematic": []
    }

    # Adiciona itens de treinamento
    for item in TRAINING_ITEMS:
        item_type = item.get("type", "consumable")
        if item_type in available_items:
            available_items[item_type].append(item)

    # Adiciona itens de combate
    for item in COMBAT_ITEMS:
        item_type = item.get("type", "consumable")
        if item_type in available_items:
            available_items[item_type].append(item)

    # Adiciona itens de energia
    for item in ENERGY_ITEMS:
        item_type = item.get("type", "consumable")
        if item_type in available_items:
            available_items[item_type].append(item)

    # Adiciona itens de atributo
    for item in ATTRIBUTE_ITEMS:
        item_type = item.get("type", "consumable")
        if item_type in available_items:
            available_items[item_type].append(item)

    # Adiciona itens sociais
    for item in SOCIAL_ITEMS:
        item_type = item.get("type", "consumable")
        if item_type in available_items:
            available_items[item_type].append(item)

    # Adiciona itens sazonais com base no bimestre atual
    season = SEASONS.get(bimestre, "spring")
    if season in SEASONAL_ITEMS:
        for item in SEASONAL_ITEMS[season]:
            item_type = item.get("type", "consumable")
            if item_type in available_items:
                available_items[item_type].append(item)

    # Adiciona itens de eventos ativos
    for event in active_events:
        if event in EVENT_ITEMS:
            for item in EVENT_ITEMS[event]:
                item_type = item.get("type", "consumable")
                if item_type in available_items:
                    available_items[item_type].append(item)

    # Adiciona itens lendários com base no nível do jogador
    for item in LEGENDARY_ITEMS:
        if player_level >= item.get("level_required", 1):
            available_items["legendary"].append(item)

    # Adiciona itens temáticos de clube se o jogador pertencer a um clube
    if player_club and player_club in CLUB_ITEMS:
        for item in CLUB_ITEMS[player_club]:
            item_type = item.get("type", "consumable")
            if item_type in available_items:
                available_items["thematic"].append(item)

    return available_items

# Lista de itens da loja (para compatibilidade com código existente)
SHOP_ITEMS = []
SHOP_ITEMS.extend(TRAINING_ITEMS)
SHOP_ITEMS.extend(COMBAT_ITEMS)
SHOP_ITEMS.extend(ENERGY_ITEMS)
SHOP_ITEMS.extend(ATTRIBUTE_ITEMS)
SHOP_ITEMS.extend(SOCIAL_ITEMS)

# Categorias de técnicas
TECHNIQUE_CATEGORIES = {
    "attack": "Ataque",
    "defense": "Defesa",
    "support": "Suporte",
    "tactical": "Tática Especial"
}

# Níveis de técnicas
TECHNIQUE_TIERS = {
    "basic": "Básica",
    "advanced": "Avançada",
    "exclusive": "Exclusiva",
    "master": "Mestre"
}

# Sistema de técnicas expandido
TECHNIQUES = [
    # Técnicas Básicas (disponíveis para todos no início)
    {
        "id": 1,
        "name": "Golpe Relâmpago",
        "description": "Um ataque rápido que surpreende o oponente. +30% de chance de vencer duelos físicos.",
        "type": "physical",
        "category": "attack",
        "tier": "basic",
        "level": 1,
        "max_level": 3,
        "club_required": None,
        "effects": {"duel_boost": {"type": "physical", "amount": 0.3}},
        "evolution": {
            "2": {"name": "Golpe Relâmpago Aprimorado", "description": "Um ataque rápido com maior precisão. +35% de chance de vencer duelos físicos.", "effects": {"duel_boost": {"type": "physical", "amount": 0.35}}},
            "3": {"name": "Golpe Relâmpago Supremo", "description": "Um ataque rápido com precisão mortal. +40% de chance de vencer duelos físicos e 10% de dano adicional.", "effects": {"duel_boost": {"type": "physical", "amount": 0.4}, "damage_boost": 0.1}}
        }
    },
    {
        "id": 2,
        "name": "Manipulação Mental",
        "description": "Confunde a mente do oponente. +30% de chance de vencer duelos mentais.",
        "type": "mental",
        "category": "attack",
        "tier": "basic",
        "level": 1,
        "max_level": 3,
        "club_required": None,
        "effects": {"duel_boost": {"type": "mental", "amount": 0.3}},
        "evolution": {
            "2": {"name": "Manipulação Mental Aprimorada", "description": "Confunde a mente do oponente com maior eficácia. +35% de chance de vencer duelos mentais.", "effects": {"duel_boost": {"type": "mental", "amount": 0.35}}},
            "3": {"name": "Manipulação Mental Suprema", "description": "Confunde a mente do oponente com precisão mortal. +40% de chance de vencer duelos mentais e 10% de dano adicional.", "effects": {"duel_boost": {"type": "mental", "amount": 0.4}, "damage_boost": 0.1}}
        }
    }
]

class Economy(commands.Cog):
    """Cog for economy and shop commands."""

    def __init__(self, bot):
        self.bot = bot
        self.market_listings = {}  # {listing_id: {seller_id, item_id, price, item_data}}
        self.next_listing_id = 1
        self.exchange_cooldowns = {}  # {user_id: timestamp}

    async def _check_cooldown(self, user_id, command):
        """Check if a command is on cooldown for a user."""
        try:
            cooldowns = await db_provider.get_cooldowns()

            # Ensure cooldowns is a dictionary
            if not isinstance(cooldowns, dict):
                logger.warning(f"Cooldowns is not a dictionary: {type(cooldowns)}")
                return None

            user_cooldowns = cooldowns.get(str(user_id), {})
            command_cooldown = user_cooldowns.get(command)

            if command_cooldown:
                expiry = datetime.fromtimestamp(command_cooldown)
                if datetime.now() < expiry:
                    remaining = expiry - datetime.now()
                    minutes = int(remaining.total_seconds() // 60)
                    seconds = int(remaining.total_seconds() % 60)
                    return f"{minutes}m {seconds}s"
            return None
        except Exception as e:
            logger.error(f"Error checking cooldown: {e}")
            return None

    async def _set_cooldown(self, user_id, command, custom_duration=None):
        """Set a cooldown for a command for a user."""
        try:
            duration = custom_duration or COOLDOWN_DURATIONS.get(command, 3600)
            expiry = datetime.now() + timedelta(seconds=duration)
            await db_provider.store_cooldown(str(user_id), command, int(expiry.timestamp()))
        except Exception as e:
            logger.error(f"Error setting cooldown: {e}")

    # Group for economy commands
    economy_group = app_commands.Group(name="economia", description="Comandos de economia da Academia Tokugawa")

    # Group for technique commands
    technique_group = app_commands.Group(name="tecnica", description="Comandos relacionados às técnicas da Academia Tokugawa")

    @technique_group.command(name="evoluir", description="Evoluir uma técnica para o próximo nível")
    async def slash_evolve_technique(self, interaction: discord.Interaction, technique_id: int):
        """Evolve a technique to the next level."""
        try:
            # Check if player exists
            player = await db_provider.get_player(interaction.user.id)
            if not player:
                await interaction.response.send_message(f"{interaction.user.mention}, você ainda não está registrado na Academia Tokugawa. Use /registro ingressar para criar seu personagem.", ephemeral=True)
                return

            # Get player's techniques
            techniques = player.get('techniques', [])
            if not techniques:
                await interaction.response.send_message(f"{interaction.user.mention}, você ainda não possui nenhuma técnica.", ephemeral=True)
                return

            # Find the technique to evolve
            technique = None
            for t in techniques:
                if t['id'] == technique_id:
                    technique = t
                    break

            if not technique:
                await interaction.response.send_message(f"{interaction.user.mention}, você não possui a técnica com ID {technique_id}.", ephemeral=True)
                return

            # Check if technique can be evolved
            if technique['level'] >= technique['max_level']:
                await interaction.response.send_message(f"{interaction.user.mention}, esta técnica já está no nível máximo.", ephemeral=True)
                return

            # Get the evolution data
            evolution = technique.get('evolution', {}).get(str(technique['level'] + 1))
            if not evolution:
                await interaction.response.send_message(f"{interaction.user.mention}, não foi possível encontrar os dados de evolução para esta técnica.", ephemeral=True)
                return

            # Check if player has enough TUSD
            cost = evolution.get('cost', 1000)  # Default cost if not specified
            if player.get('tusd', 0) < cost:
                await interaction.response.send_message(f"{interaction.user.mention}, você não possui TUSD suficiente para evoluir esta técnica. Custo: {cost} TUSD", ephemeral=True)
                return

            # Update the technique
            technique['level'] += 1
            technique['name'] = evolution['name']
            technique['description'] = evolution['description']
            technique['effects'] = evolution['effects']

            # Update player in database
            success = await db_provider.update_player(
                interaction.user.id,
                techniques=techniques,
                tusd=player['tusd'] - cost
            )

            if success:
                await interaction.response.send_message(
                    embed=create_basic_embed(
                        title="Técnica Evoluída!",
                        description=(
                            f"{interaction.user.mention}, sua técnica foi evoluída com sucesso!\n\n"
                            f"**Nova Técnica:** {technique['name']}\n"
                            f"**Nível:** {technique['level']}\n"
                            f"**Descrição:** {technique['description']}\n\n"
                            f"Custo: {cost} TUSD"
                        ),
                        color=0x00FF00
                    )
                )
            else:
                await interaction.response.send_message("Ocorreu um erro ao evoluir a técnica. Por favor, tente novamente mais tarde.", ephemeral=True)
        except Exception as e:
            logger.error(f"Error in slash_evolve_technique: {e}")
            await interaction.response.send_message("Ocorreu um erro ao evoluir a técnica. Por favor, tente novamente mais tarde.", ephemeral=True)

    @technique_group.command(name="listar", description="Listar todas as suas técnicas")
    async def slash_list_techniques(self, interaction: discord.Interaction):
        """List all techniques owned by the player."""
        try:
            # Check if player exists
            player = await db_provider.get_player(interaction.user.id)
            if not player:
                await interaction.response.send_message(f"{interaction.user.mention}, você ainda não está registrado na Academia Tokugawa. Use /registro ingressar para criar seu personagem.", ephemeral=True)
                return

            # Get player's techniques
            techniques = player.get('techniques', [])
            if not techniques:
                await interaction.response.send_message(f"{interaction.user.mention}, você ainda não possui nenhuma técnica.", ephemeral=True)
                return

            # Create embed for techniques list
            embed = create_basic_embed(
                title="Suas Técnicas",
                description=f"{interaction.user.mention}, aqui estão todas as suas técnicas:",
                color=0x00FF00
            )

            # Group techniques by category
            techniques_by_category = {}
            for technique in techniques:
                category = technique.get('category', 'other')
                if category not in techniques_by_category:
                    techniques_by_category[category] = []
                techniques_by_category[category].append(technique)

            # Add each category to the embed
            for category, techs in techniques_by_category.items():
                category_name = TECHNIQUE_CATEGORIES.get(category, category.capitalize())
                tech_list = "\n".join([
                    f"**{t['name']}** (Nível {t['level']}/{t['max_level']})"
                    for t in techs
                ])
                embed.add_field(
                    name=category_name,
                    value=tech_list,
                    inline=False
                )

            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            logger.error(f"Error in slash_list_techniques: {e}")
            await interaction.response.send_message("Ocorreu um erro ao listar suas técnicas. Por favor, tente novamente mais tarde.", ephemeral=True)

    @technique_group.command(name="info", description="Ver informações detalhadas sobre uma técnica")
    async def slash_technique_info(self, interaction: discord.Interaction, technique_id: int):
        """Show detailed information about a specific technique."""
        try:
            # Check if player exists
            player = await db_provider.get_player(interaction.user.id)
            if not player:
                await interaction.response.send_message(f"{interaction.user.mention}, você ainda não está registrado na Academia Tokugawa. Use /registro ingressar para criar seu personagem.", ephemeral=True)
                return

            # Get player's techniques
            techniques = player.get('techniques', [])
            if not techniques:
                await interaction.response.send_message(f"{interaction.user.mention}, você ainda não possui nenhuma técnica.", ephemeral=True)
                return

            # Find the technique
            technique = None
            for t in techniques:
                if t['id'] == technique_id:
                    technique = t
                    break

            if not technique:
                await interaction.response.send_message(f"{interaction.user.mention}, você não possui a técnica com ID {technique_id}.", ephemeral=True)
                return

            # Create embed for technique info
            embed = create_basic_embed(
                title=technique['name'],
                description=technique['description'],
                color=0x00FF00
            )

            # Add technique details
            embed.add_field(
                name="Nível",
                value=f"{technique['level']}/{technique['max_level']}",
                inline=True
            )

            embed.add_field(
                name="Categoria",
                value=TECHNIQUE_CATEGORIES.get(technique['category'], technique['category'].capitalize()),
                inline=True
            )

            embed.add_field(
                name="Tipo",
                value=technique['type'].capitalize(),
                inline=True
            )

            # Add effects
            effects_text = ""
            for effect_type, effect_data in technique['effects'].items():
                if effect_type == 'duel_boost':
                    effects_text += f"**Bônus em Duelos:** +{int(effect_data['amount'] * 100)}% de chance de vencer duelos {effect_data['type']}\n"
                elif effect_type == 'damage_boost':
                    effects_text += f"**Bônus de Dano:** +{int(effect_data * 100)}%\n"
                elif effect_type == 'exp_boost':
                    effects_text += f"**Bônus de EXP:** +{int(effect_data * 100)}%\n"
                elif effect_type == 'hp_boost':
                    effects_text += f"**Bônus de HP:** +{int(effect_data * 100)}%\n"

            if effects_text:
                embed.add_field(
                    name="Efeitos",
                    value=effects_text,
                    inline=False
                )

            # Add evolution info if available
            if technique['level'] < technique['max_level']:
                evolution = technique.get('evolution', {}).get(str(technique['level'] + 1))
                if evolution:
                    embed.add_field(
                        name="Próxima Evolução",
                        value=(
                            f"**Nome:** {evolution['name']}\n"
                            f"**Descrição:** {evolution['description']}\n"
                            f"**Custo:** {evolution.get('cost', 1000)} TUSD"
                        ),
                        inline=False
                    )

            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            logger.error(f"Error in slash_technique_info: {e}")
            await interaction.response.send_message("Ocorreu um erro ao mostrar informações da técnica. Por favor, tente novamente mais tarde.", ephemeral=True)

    @economy_group.command(name="loja", description="Acessar a loja da Academia Tokugawa")
    async def slash_shop(self, interaction: discord.Interaction):
        """Access the Academy's shop."""
        try:
            # Check if player exists
            player = await db_provider.get_player(interaction.user.id)
            if not player:
                await interaction.response.send_message(f"{interaction.user.mention}, você ainda não está registrado na Academia Tokugawa. Use /registro ingressar para criar seu personagem.", ephemeral=True)
                return

            # Get available items based on player's status
            available_items = get_available_shop_items(
                bimestre=player.get('bimestre', 1),
                active_events=player.get('active_events', []),
                player_level=player.get('level', 1),
                player_club=player.get('club_id'),
                current_date=datetime.now()
            )

            # Create embed for shop
            embed = create_basic_embed(
                title="Loja da Academia Tokugawa",
                description=f"{interaction.user.mention}, bem-vindo à loja! Aqui estão os itens disponíveis:",
                color=0x00FF00
            )

            # Add items by category
            for category, items in available_items.items():
                if items:
                    item_list = "\n".join([
                        f"**{item['name']}** (ID: {item['id']}) - {item['price']} TUSD\n{item['description']}"
                        for item in items
                    ])
                    embed.add_field(
                        name=category.capitalize(),
                        value=item_list,
                        inline=False
                    )

            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            logger.error(f"Error in slash_shop: {e}")
            await interaction.response.send_message("Ocorreu um erro ao acessar a loja. Por favor, tente novamente mais tarde.", ephemeral=True)

    @economy_group.command(name="comprar", description="Comprar um item da loja")
    async def slash_buy(self, interaction: discord.Interaction, item_id: int):
        """Buy an item from the shop."""
        try:
            # Check if player exists
            player = await db_provider.get_player(interaction.user.id)
            if not player:
                await interaction.response.send_message(f"{interaction.user.mention}, você ainda não está registrado na Academia Tokugawa. Use /registro ingressar para criar seu personagem.", ephemeral=True)
                return

            # Get available items
            available_items = get_available_shop_items(
                bimestre=player.get('bimestre', 1),
                active_events=player.get('active_events', []),
                player_level=player.get('level', 1),
                player_club=player.get('club_id'),
                current_date=datetime.now()
            )

            # Find the item
            item = None
            for category_items in available_items.values():
                for i in category_items:
                    if i['id'] == item_id:
                        item = i
                        break
                if item:
                    break

            if not item:
                await interaction.response.send_message(f"{interaction.user.mention}, o item com ID {item_id} não está disponível na loja.", ephemeral=True)
                return

            # Check if player has enough TUSD
            price = item['price']
            if player.get('tusd', 0) < price:
                await interaction.response.send_message(f"{interaction.user.mention}, você não possui TUSD suficiente para comprar este item. Preço: {price} TUSD", ephemeral=True)
                return

            # Add item to player's inventory
            inventory = player.get('inventory', {})
            if isinstance(inventory, str):
                try:
                    inventory = json.loads(inventory)
                except Exception:
                    inventory = {}
            if not isinstance(inventory, dict):
                inventory = {}

            item_id = f"item_{datetime.now().timestamp()}"
            inventory[item_id] = item

            # Update player in database
            success = await db_provider.update_player(
                interaction.user.id,
                inventory=json.dumps(inventory),
                tusd=player['tusd'] - price
            )

            if success:
                await interaction.response.send_message(
                    embed=create_basic_embed(
                        title="Item Comprado!",
                        description=(
                            f"{interaction.user.mention}, você comprou o item com sucesso!\n\n"
                            f"**Item:** {item['name']}\n"
                            f"**Preço:** {price} TUSD\n"
                            f"**Descrição:** {item['description']}\n\n"
                            f"O item foi adicionado ao seu inventário."
                        ),
                        color=0x00FF00
                    )
                )
            else:
                await interaction.response.send_message("Ocorreu um erro ao comprar o item. Por favor, tente novamente mais tarde.", ephemeral=True)
        except Exception as e:
            logger.error(f"Error in slash_buy: {e}")
            await interaction.response.send_message("Ocorreu um erro ao comprar o item. Por favor, tente novamente mais tarde.", ephemeral=True)

    @economy_group.command(name="usar", description="Usar um item do inventário")
    async def slash_use_item(self, interaction: discord.Interaction, item_id: int):
        """Use an item from the inventory."""
        try:
            # Check if player exists
            player = await db_provider.get_player(interaction.user.id)
            if not player:
                await interaction.response.send_message(f"{interaction.user.mention}, você ainda não está registrado na Academia Tokugawa. Use /registro ingressar para criar seu personagem.", ephemeral=True)
                return

            # Get player's inventory
            inventory = player.get('inventory', {})
            if isinstance(inventory, str):
                try:
                    inventory = json.loads(inventory)
                except Exception:
                    inventory = {}
            if not isinstance(inventory, dict):
                inventory = {}

            # Find the item
            item = None
            for i_id, i in inventory.items():
                if i['id'] == item_id:
                    item = i
                    item_key = i_id
                    break

            if not item:
                await interaction.response.send_message(f"{interaction.user.mention}, você não possui o item com ID {item_id}.", ephemeral=True)
                return

            # Check if item is usable
            if item.get('type') not in ['consumable', 'accessory']:
                await interaction.response.send_message(f"{interaction.user.mention}, este item não pode ser usado.", ephemeral=True)
                return

            # Apply item effects
            update_data = {}
            effects_applied = []

            for effect_type, effect_data in item.get('effects', {}).items():
                if effect_type == 'hp_boost':
                    current_hp = player.get('hp', 100)
                    max_hp = player.get('max_hp', 100)
                    hp_gain = int(max_hp * effect_data)
                    new_hp = min(max_hp, current_hp + hp_gain)
                    update_data['hp'] = new_hp
                    effects_applied.append(f"+{hp_gain} HP")
                elif effect_type == 'exp_boost':
                    exp_gain = int(player.get('exp', 0) * effect_data)
                    update_data['exp'] = player.get('exp', 0) + exp_gain
                    effects_applied.append(f"+{exp_gain} EXP")
                elif effect_type == 'attribute_boost':
                    for attr, boost in effect_data.items():
                        current_value = player.get(attr, 5)
                        update_data[attr] = current_value + boost
                        effects_applied.append(f"+{boost} {attr.capitalize()}")

            # Remove item from inventory if it's consumable
            if item['type'] == 'consumable':
                inventory.pop(item_key)
                update_data['inventory'] = json.dumps(inventory)

            # Update player in database
            success = await db_provider.update_player(interaction.user.id, **update_data)

            if success:
                await interaction.response.send_message(
                    embed=create_basic_embed(
                        title="Item Usado!",
                        description=(
                            f"{interaction.user.mention}, você usou o item com sucesso!\n\n"
                            f"**Item:** {item['name']}\n"
                            f"**Efeitos Aplicados:**\n" + "\n".join(effects_applied)
                        ),
                        color=0x00FF00
                    )
                )
            else:
                await interaction.response.send_message("Ocorreu um erro ao usar o item. Por favor, tente novamente mais tarde.", ephemeral=True)
        except Exception as e:
            logger.error(f"Error in slash_use_item: {e}")
            await interaction.response.send_message("Ocorreu um erro ao usar o item. Por favor, tente novamente mais tarde.", ephemeral=True)

    @economy_group.command(name="mercado", description="Acessar o mercado de itens entre jogadores")
    async def slash_market(self, interaction: discord.Interaction):
        """Slash command version of the market command."""
        try:
            # Check if player exists
            player = get_player(interaction.user.id)
            if not player:
                await interaction.response.send_message(f"{interaction.user.mention}, você ainda não está registrado na Academia Tokugawa. Use /registro ingressar para criar seu personagem.")
                return

            # Create market embed
            embed = create_basic_embed(
                title="Mercado da Academia Tokugawa",
                description=f"Bem-vindo ao mercado de itens entre alunos! Você tem {player['tusd']} TUSD 💰\n\n"
                            f"Para vender um item, use `/economia vender <id_do_item> <preço>`\n"
                            f"Para comprar um item, use `/economia comprar_mercado <id_da_listagem>`",
                color=0x00FF00  # Green
            )

            # Add listings to embed
            if not self.market_listings:
                embed.add_field(
                    name="Nenhum item à venda",
                    value="Seja o primeiro a vender algo no mercado!",
                    inline=False
                )
            else:
                for listing_id, listing in self.market_listings.items():
                    seller = self.bot.get_user(listing["seller_id"])
                    seller_name = seller.display_name if seller else "Desconhecido"

                    rarity = RARITIES.get(listing["item_data"]["rarity"], RARITIES["common"])
                    embed.add_field(
                        name=f"{listing_id}. {rarity['emoji']} {listing['item_data']['name']} - {listing['price']} TUSD",
                        value=f"{listing['item_data']['description']}\nVendedor: {seller_name}",
                        inline=False
                    )

            await interaction.response.send_message(embed=embed)
        except discord.errors.NotFound:
            # If the interaction has expired, log it but don't try to respond
            logger.warning(f"Interaction expired for user {interaction.user.id} when using /economia mercado")
        except Exception as e:
            logger.error(f"Error in slash_market: {e}")

    @economy_group.command(name="vender", description="Vender um item no mercado")
    async def slash_sell(self, interaction: discord.Interaction, item_id: int, price: int):
        """Slash command version of the sell command."""
        try:
            # Check if player exists
            player = get_player(interaction.user.id)
            if not player:
                await interaction.response.send_message(f"{interaction.user.mention}, você ainda não está registrado na Academia Tokugawa. Use /registro ingressar para criar seu personagem.")
                return

            # Check if price is valid
            if price <= 0:
                await interaction.response.send_message(f"{interaction.user.mention}, o preço deve ser maior que zero.")
                return

            # Check if player has the item
            inventory = player["inventory"]
            if str(item_id) not in inventory:
                await interaction.response.send_message(f"{interaction.user.mention}, você não possui este item em seu inventário.")
                return

            # Get item data
            item_data = inventory[str(item_id)]

            # Create listing
            listing_id = self.next_listing_id
            self.next_listing_id += 1

            self.market_listings[listing_id] = {
                "seller_id": interaction.user.id,
                "item_id": item_id,
                "price": price,
                "item_data": item_data
            }

            # Remove item from inventory
            inventory[str(item_id)]["quantity"] -= 1
            if inventory[str(item_id)]["quantity"] <= 0:
                del inventory[str(item_id)]

            # Update player in database
            success = update_player(interaction.user.id, inventory=json.dumps(inventory))

            if success:
                # Create listing confirmation embed
                rarity = RARITIES.get(item_data["rarity"], RARITIES["common"])
                embed = create_basic_embed(
                    title="Item Colocado à Venda!",
                    description=f"Você colocou {rarity['emoji']} **{item_data['name']}** à venda por {price} TUSD.\n\n"
                                f"ID da listagem: {listing_id}",
                    color=rarity["color"]
                )

                await interaction.response.send_message(embed=embed)
            else:
                await interaction.response.send_message("Ocorreu um erro ao colocar o item à venda. Por favor, tente novamente mais tarde.")
        except discord.errors.NotFound:
            # If the interaction has expired, log it but don't try to respond
            logger.warning(f"Interaction expired for user {interaction.user.id} when using /economia vender")
        except Exception as e:
            logger.error(f"Error in slash_sell: {e}")

    @economy_group.command(name="comprar_mercado", description="Comprar um item do mercado")
    async def slash_buy_market(self, interaction: discord.Interaction, listing_id: int):
        """Slash command version of the buy_market command."""
        try:
            # Check if player exists
            player = get_player(interaction.user.id)
            if not player:
                await interaction.response.send_message(f"{interaction.user.mention}, você ainda não está registrado na Academia Tokugawa. Use /registro ingressar para criar seu personagem.")
                return

            # Check if listing exists
            if listing_id not in self.market_listings:
                await interaction.response.send_message(f"{interaction.user.mention}, listagem não encontrada. Use `/economia mercado` para ver as listagens disponíveis.")
                return

            # Get listing data
            listing = self.market_listings[listing_id]

            # Check if player is trying to buy their own item
            if listing["seller_id"] == interaction.user.id:
                await interaction.response.send_message(f"{interaction.user.mention}, você não pode comprar seu próprio item.")
                return

            # Check if player has enough TUSD
            if player["tusd"] < listing["price"]:
                await interaction.response.send_message(f"{interaction.user.mention}, você não tem TUSD suficiente para comprar este item. Preço: {listing['price']} TUSD, Seu saldo: {player['tusd']} TUSD")
                return

            # Get seller data
            seller = get_player(listing["seller_id"])
            if not seller:
                await interaction.response.send_message(f"{interaction.user.mention}, o vendedor não existe mais. A listagem será removida.")
                del self.market_listings[listing_id]
                return

            # Process the purchase
            buyer_inventory = player["inventory"]

            # Add item to buyer's inventory
            if str(listing["item_id"]) in buyer_inventory:
                # If buyer already has this item, increase quantity
                buyer_inventory[str(listing["item_id"])]["quantity"] += 1
            else:
                # Add new item to inventory
                item_data = listing["item_data"].copy()
                item_data["quantity"] = 1
                buyer_inventory[str(listing["item_id"])] = item_data

            # Update buyer data
            buyer_update = {
                "tusd": player["tusd"] - listing["price"],
                "inventory": json.dumps(buyer_inventory)
            }

            # Update seller data
            seller_update = {
                "tusd": seller["tusd"] + listing["price"]
            }

            # Update both players in database
            buyer_success = update_player(interaction.user.id, **buyer_update)
            seller_success = update_player(listing["seller_id"], **seller_update)

            if buyer_success and seller_success:
                # Remove listing
                del self.market_listings[listing_id]

                # Create purchase confirmation embed
                rarity = RARITIES.get(listing["item_data"]["rarity"], RARITIES["common"])
                embed = create_basic_embed(
                    title="Compra Realizada!",
                    description=f"Você comprou {rarity['emoji']} **{listing['item_data']['name']}** por {listing['price']} TUSD.\n\n"
                                f"Saldo atual: {buyer_update['tusd']} TUSD 💰",
                    color=rarity["color"]
                )

                await interaction.response.send_message(embed=embed)

                # Notify seller if they're online
                seller_user = self.bot.get_user(listing["seller_id"])
                if seller_user:
                    seller_embed = create_basic_embed(
                        title="Item Vendido!",
                        description=f"Seu item {rarity['emoji']} **{listing['item_data']['name']}** foi vendido por {listing['price']} TUSD.\n\n"
                                    f"Saldo atual: {seller_update['tusd']} TUSD 💰",
                        color=rarity["color"]
                    )

                    try:
                        await seller_user.send(embed=seller_embed)
                    except:
                        # Ignore if we can't DM the seller
                        pass
            else:
                await interaction.response.send_message("Ocorreu um erro durante a compra. Por favor, tente novamente mais tarde.")
        except discord.errors.NotFound:
            # If the interaction has expired, log it but don't try to respond
            logger.warning(f"Interaction expired for user {interaction.user.id} when using /economia comprar_mercado")
        except Exception as e:
            logger.error(f"Error in slash_buy_market: {e}")

    @economy_group.command(name="trocar", description="Trocar itens por recompensas")
    async def slash_exchange(self, interaction: discord.Interaction, exchange_id: int):
        """Permite trocar itens por outros itens ou moedas especiais."""
        # Check if player exists
        player = get_player(interaction.user.id)
        if not player:
            await interaction.response.send_message(f"{interaction.user.mention}, você ainda não está registrado na Academia Tokugawa. Use /registro ingressar para criar seu personagem.")
            return

        # Check cooldown (1 hour between exchanges)
        user_id = str(interaction.user.id)
        now = datetime.now().timestamp()
        if user_id in self.exchange_cooldowns and self.exchange_cooldowns[user_id] > now:
            remaining = self.exchange_cooldowns[user_id] - now
            minutes, seconds = divmod(int(remaining), 60)
            await interaction.response.send_message(f"{interaction.user.mention}, você precisa esperar {minutes}m {seconds}s para fazer outra troca.")
            return

        # Find the exchange
        exchange = next((e for e in ITEM_EXCHANGES if e["id"] == exchange_id), None)
        if not exchange:
            await interaction.response.send_message(f"{interaction.user.mention}, troca não encontrada. Use `/economia loja` para ver as trocas disponíveis.")
            return

        # Check requirements
        inventory = player["inventory"]
        requirements_met = True
        items_to_remove = []

        # Check item requirements
        if "items" in exchange["requirements"]:
            req = exchange["requirements"]["items"]
            rarity = req.get("rarity", None)
            category = req.get("category", None)
            count = req.get("count", 1)

            # Find matching items
            matching_items = []
            for item_id, item in inventory.items():
                if rarity and item.get("rarity") != rarity:
                    continue
                if category and item.get("category") != category:
                    continue

                # Add item to matching items (considering quantity)
                for _ in range(item.get("quantity", 1)):
                    matching_items.append(item_id)
                    if len(matching_items) >= count:
                        break

                if len(matching_items) >= count:
                    break

            if len(matching_items) < count:
                requirements_met = False
                await interaction.response.send_message(
                    f"{interaction.user.mention}, você não tem itens suficientes para esta troca. "
                    f"Necessário: {count} itens de raridade {rarity or 'qualquer'}"
                )
                return

            # Mark items for removal
            for item_id in matching_items[:count]:
                items_to_remove.append(item_id)

        # Check currency requirements
        if "currency" in exchange["requirements"]:
            req = exchange["requirements"]["currency"]
            currency_type = req.get("type", "TUSD")
            amount = req.get("amount", 0)

            if currency_type == "TUSD":
                if player["tusd"] < amount:
                    requirements_met = False
                    await interaction.response.send_message(
                        f"{interaction.user.mention}, você não tem TUSD suficiente para esta troca. "
                        f"Necessário: {amount} TUSD, Seu saldo: {player['tusd']} TUSD"
                    )
                    return
            else:
                alt_currencies = player.get("currencies", {})
                if alt_currencies.get(currency_type, 0) < amount:
                    requirements_met = False
                    currency_info = ALTERNATIVE_CURRENCIES.get(currency_type, {"name": currency_type})
                    await interaction.response.send_message(
                        f"{interaction.user.mention}, você não tem {currency_info['name']} suficiente para esta troca. "
                        f"Necessário: {amount} {currency_info['name']}, Seu saldo: {alt_currencies.get(currency_type, 0)} {currency_info['name']}"
                    )
                    return

        # Process the exchange if requirements are met
        if requirements_met:
            # Remove items from inventory
            for item_id in items_to_remove:
                if inventory[item_id]["quantity"] > 1:
                    inventory[item_id]["quantity"] -= 1
                else:
                    del inventory[item_id]

            # Remove currency if required
            update_data = {"inventory": json.dumps(inventory)}
            if "currency" in exchange["requirements"]:
                req = exchange["requirements"]["currency"]
                currency_type = req.get("type", "TUSD")
                amount = req.get("amount", 0)

                if currency_type == "TUSD":
                    update_data["tusd"] = player["tusd"] - amount
                else:
                    alt_currencies = player.get("currencies", {})
                    alt_currencies[currency_type] = alt_currencies.get(currency_type, 0) - amount
                    update_data["currencies"] = json.dumps(alt_currencies)

            # Process reward
            reward_message = ""

            # Item reward
            if "item_rarity" in exchange["reward"]:
                rarity = exchange["reward"]["item_rarity"]
                is_random = exchange["reward"].get("random", False)

                # Get all items of the specified rarity
                all_items = []
                for item_list in [TRAINING_ITEMS, COMBAT_ITEMS, ENERGY_ITEMS, ATTRIBUTE_ITEMS, SOCIAL_ITEMS]:
                    all_items.extend([item for item in item_list if item["rarity"] == rarity])

                for season_items in SEASONAL_ITEMS.values():
                    all_items.extend([item for item in season_items if item["rarity"] == rarity])

                for event_items in EVENT_ITEMS.values():
                    all_items.extend([item for item in event_items if item["rarity"] == rarity])

                # Choose a random item or a specific one
                if all_items:
                    if is_random:
                        reward_item = random.choice(all_items)
                    else:
                        reward_item = all_items[0]  # First item as default

                    # Add item to inventory
                    if str(reward_item["id"]) in inventory:
                        inventory[str(reward_item["id"])]["quantity"] += 1
                    else:
                        inventory_item = {
                            "id": reward_item["id"],
                            "name": reward_item["name"],
                            "description": reward_item["description"],
                            "type": reward_item["type"],
                            "rarity": reward_item["rarity"],
                            "effects": reward_item["effects"],
                            "quantity": 1
                        }

                        # Add category and season/event info if applicable
                        if "category" in reward_item:
                            inventory_item["category"] = reward_item["category"]
                        if "season" in reward_item:
                            inventory_item["season"] = reward_item["season"]
                        if "event" in reward_item:
                            inventory_item["event"] = reward_item["event"]

                        inventory[str(reward_item["id"])] = inventory_item

                    update_data["inventory"] = json.dumps(inventory)
                    reward_message = f"Você recebeu: {reward_item['name']} (Raridade: {rarity.capitalize()})"

            # Currency reward
            if "currency" in exchange["reward"]:
                req = exchange["reward"]["currency"]
                currency_type = req.get("type", "TUSD")
                amount = req.get("amount", 0)

                if currency_type == "TUSD":
                    update_data["tusd"] = player["tusd"] + amount
                    reward_message = f"Você recebeu: {amount} TUSD"
                elif currency_type == "seasonal_token":
                    # Get current season token
                    story_progress = player.get('story_progress', {})
                    bimestre = story_progress.get('bimestre_corrente', 1)
                    season = SEASONS.get(bimestre, "spring")
                    season_token = f"{season}_token"

                    alt_currencies = player.get("currencies", {})
                    alt_currencies[season_token] = alt_currencies.get(season_token, 0) + amount
                    update_data["currencies"] = json.dumps(alt_currencies)

                    currency_info = ALTERNATIVE_CURRENCIES.get(season_token, {"name": season_token})
                    reward_message = f"Você recebeu: {amount} {currency_info['name']}"
                else:
                    alt_currencies = player.get("currencies", {})
                    alt_currencies[currency_type] = alt_currencies.get(currency_type, 0) + amount
                    update_data["currencies"] = json.dumps(alt_currencies)

                    currency_info = ALTERNATIVE_CURRENCIES.get(currency_type, {"name": currency_type})
                    reward_message = f"Você recebeu: {amount} {currency_info['name']}"

            # Update player data
            update_player(interaction.user.id, update_data)

            # Set cooldown (1 hour)
            self.exchange_cooldowns[user_id] = now + 3600

            await interaction.response.send_message(
                f"{interaction.user.mention}, troca realizada com sucesso!\n{reward_message}\n"
                f"Você poderá fazer outra troca em 1 hora."
            )

    @economy_group.command(name="equipar", description="Equipar um acessório do inventário")
    async def slash_equip_item(self, interaction: discord.Interaction, item_id: int):
        """Slash command to equip an accessory item."""
        try:
            # Check if player exists
            player = get_player(interaction.user.id)
            if not player:
                await interaction.response.send_message(f"{interaction.user.mention}, você ainda não está registrado na Academia Tokugawa. Use /registro ingressar para criar seu personagem.")
                return

            # Check if player has the item
            inventory = player["inventory"]
            if str(item_id) not in inventory:
                await interaction.response.send_message(f"{interaction.user.mention}, você não possui este item em seu inventário.", ephemeral=True)
                return

            # Get item data
            item_data = inventory[str(item_id)]

            # Check if item is an accessory
            if item_data["type"] != "accessory":
                await interaction.response.send_message(f"{interaction.user.mention}, apenas acessórios podem ser equipados. Este item é do tipo {item_data['type']}.", ephemeral=True)
                return

            # Check if the item is already equipped
            if item_data.get("equipped", False):
                # Unequip the item
                inventory[str(item_id)]["equipped"] = False
                update_data = {"inventory": json.dumps(inventory)}
                success = update_player(interaction.user.id, **update_data)

                if success:
                    embed = create_basic_embed(
                        title="Acessório Desequipado!",
                        description=f"Você desequipou {item_data['name']}.",
                        color=RARITIES.get(item_data["rarity"], RARITIES["common"])["color"]
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                else:
                    await interaction.response.send_message("Ocorreu um erro ao desequipar o acessório. Por favor, tente novamente mais tarde.", ephemeral=True)
                return

            # Check if there's a cooldown for this accessory
            cooldown = self._check_cooldown(interaction.user.id, f"accessory_{item_id}")
            if cooldown:
                await interaction.response.send_message(f"{interaction.user.mention}, este acessório está em cooldown. Tempo restante: {cooldown}", ephemeral=True)
                return

            # Unequip any other equipped accessories of the same type
            for inv_item_id, inv_item in inventory.items():
                if inv_item["type"] == "accessory" and inv_item.get("equipped", False):
                    inventory[inv_item_id]["equipped"] = False

            # Equip the new accessory
            inventory[str(item_id)]["equipped"] = True

            # Set cooldown for this accessory (4 hours)
            self._set_cooldown(interaction.user.id, f"accessory_{item_id}", 14400)  # 4 hours in seconds

            # Update player in database
            update_data = {"inventory": json.dumps(inventory)}
            success = update_player(interaction.user.id, **update_data)

            if success:
                # Create equip confirmation embed
                rarity = RARITIES.get(item_data["rarity"], RARITIES["common"])
                embed = create_basic_embed(
                    title="Acessório Equipado!",
                    description=f"Você equipou {item_data['name']}. Os efeitos do acessório estão ativos!",
                    color=rarity["color"]
                )

                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message("Ocorreu um erro ao equipar o acessório. Por favor, tente novamente mais tarde.", ephemeral=True)
        except discord.errors.NotFound:
            # If the interaction has expired, log it but don't try to respond
            logger.warning(f"Interaction expired for user {interaction.user.id} when using /economia equipar")
        except Exception as e:
            logger.error(f"Error in slash_equip_item: {e}")

    @commands.command(name="loja")
    async def shop(self, ctx):
        """Acessar a loja da Academia Tokugawa."""
        # Check if player exists
        player = get_player(ctx.author.id)
        if not player:
            await ctx.send(f"{ctx.author.mention}, você ainda não está registrado na Academia Tokugawa. Use !ingressar para criar seu personagem.")
            return

        # Create shop embed
        embed = create_basic_embed(
            title="Loja da Academia Tokugawa",
            description=f"Bem-vindo à loja oficial da Academia! Você tem {player['tusd']} TUSD 💰\n\n"
                        f"Para comprar um item, use o comando `!comprar <id>`",
            color=0xFFD700  # Gold
        )

        # Add items to embed
        for item in SHOP_ITEMS:
            rarity = RARITIES.get(item["rarity"], RARITIES["common"])
            embed.add_field(
                name=f"{item['id']}. {rarity['emoji']} {item['name']} - {item['price']} TUSD",
                value=f"{item['description']}\nTipo: {item['type'].capitalize()}",
                inline=False
            )

        await ctx.send(embed=embed)

    @commands.command(name="comprar")
    async def buy(self, ctx, item_id: int = None):
        """Comprar um item da loja."""
        # Check if player exists
        player = get_player(ctx.author.id)
        if not player:
            await ctx.send(f"{ctx.author.mention}, você ainda não está registrado na Academia Tokugawa. Use !ingressar para criar seu personagem.")
            return

        # Check if item_id is provided
        if item_id is None:
            await ctx.send(f"{ctx.author.mention}, você precisa especificar o ID do item que deseja comprar. Use `!loja` para ver os itens disponíveis.", ephemeral=True)
            return

        # Find the item
        item = next((i for i in SHOP_ITEMS if i["id"] == item_id), None)
        if not item:
            await ctx.send(f"{ctx.author.mention}, item não encontrado. Use `!loja` para ver os itens disponíveis.", ephemeral=True)
            return

        # Check if player has enough TUSD
        if player["tusd"] < item["price"]:
            await ctx.send(f"{ctx.author.mention}, você não tem TUSD suficiente para comprar este item. Preço: {item['price']} TUSD, Seu saldo: {player['tusd']} TUSD", ephemeral=True)
            return

        # Process the purchase
        inventory = player["inventory"]

        # Add item to inventory
        if str(item["id"]) in inventory:
            # If player already has this item, increase quantity
            inventory[str(item["id"])]["quantity"] += 1
        else:
            # Add new item to inventory
            inventory[str(item["id"])] = {
                "id": item["id"],
                "name": item["name"],
                "description": item["description"],
                "type": item["type"],
                "rarity": item["rarity"],
                "effects": item["effects"],
                "quantity": 1
            }

        # Update player data
        update_data = {
            "tusd": player["tusd"] - item["price"],
            "inventory": json.dumps(inventory)
        }

        # Special handling for permanent attribute items
        if item["type"] == "consumable" and "permanent_attribute" in item["effects"]:
            # Choose a random attribute to increase
            attribute = random.choice(["dexterity", "intellect", "charisma", "power_stat"])
            update_data[attribute] = player[attribute] + item["effects"]["permanent_attribute"]

            # Remove the item from inventory since it's consumed immediately
            inventory[str(item["id"])]["quantity"] -= 1
            if inventory[str(item["id"])]["quantity"] <= 0:
                del inventory[str(item["id"])]

            update_data["inventory"] = json.dumps(inventory)

        # Special handling for technique scrolls
        if item["type"] == "consumable" and "learn_technique" in item["effects"]:
            # Choose a random technique
            technique = random.choice(TECHNIQUES)
            techniques = player["techniques"]

            if str(technique["id"]) not in techniques:
                techniques[str(technique["id"])] = technique
                update_data["techniques"] = json.dumps(techniques)

                # Remove the item from inventory since it's consumed immediately
                inventory[str(item["id"])]["quantity"] -= 1
                if inventory[str(item["id"])]["quantity"] <= 0:
                    del inventory[str(item["id"])]

                update_data["inventory"] = json.dumps(inventory)

        # Update player in database
        success = update_player(ctx.author.id, **update_data)

        if success:
            # Create purchase confirmation embed
            rarity = RARITIES.get(item["rarity"], RARITIES["common"])
            embed = create_basic_embed(
                title="Compra Realizada!",
                description=f"Você comprou {rarity['emoji']} **{item['name']}** por {item['price']} TUSD.\n\n"
                            f"Saldo atual: {update_data['tusd']} TUSD 💰",
                color=rarity["color"]
            )

            # Add special messages for consumed items
            if item["type"] == "consumable" and "permanent_attribute" in item["effects"]:
                attribute_names = {
                    "dexterity": "Destreza 🏃‍♂️",
                    "intellect": "Intelecto 🧠",
                    "charisma": "Carisma 💬",
                    "power_stat": "Poder ⚡"
                }
                embed.add_field(
                    name="Item Consumido!",
                    value=f"O Elixir aumentou seu atributo de {attribute_names[attribute]} em +{item['effects']['permanent_attribute']}!",
                    inline=False
                )

            if item["type"] == "consumable" and "learn_technique" in item["effects"] and "techniques" in update_data:
                embed.add_field(
                    name="Técnica Aprendida!",
                    value=f"Você aprendeu a técnica **{technique['name']}**!\n{technique['description']}",
                    inline=False
                )

            await ctx.send(embed=embed, ephemeral=True)
        else:
            await ctx.send("Ocorreu um erro durante a compra. Por favor, tente novamente mais tarde.")

    @commands.command(name="mercado")
    async def market(self, ctx):
        """Acessar o mercado de itens entre jogadores."""
        # Check if player exists
        player = get_player(ctx.author.id)
        if not player:
            await ctx.send(f"{ctx.author.mention}, você ainda não está registrado na Academia Tokugawa. Use !ingressar para criar seu personagem.")
            return

        # Create market embed
        embed = create_basic_embed(
            title="Mercado da Academia Tokugawa",
            description=f"Bem-vindo ao mercado de itens entre alunos! Você tem {player['tusd']} TUSD 💰\n\n"
                        f"Para vender um item, use `!vender <id_do_item> <preço>`\n"
                        f"Para comprar um item, use `!comprar_mercado <id_da_listagem>`",
            color=0x00FF00  # Green
        )

        # Add listings to embed
        if not self.market_listings:
            embed.add_field(
                name="Nenhum item à venda",
                value="Seja o primeiro a vender algo no mercado!",
                inline=False
            )
        else:
            for listing_id, listing in self.market_listings.items():
                seller = self.bot.get_user(listing["seller_id"])
                seller_name = seller.display_name if seller else "Desconhecido"

                rarity = RARITIES.get(listing["item_data"]["rarity"], RARITIES["common"])
                embed.add_field(
                    name=f"{listing_id}. {rarity['emoji']} {listing['item_data']['name']} - {listing['price']} TUSD",
                    value=f"{listing['item_data']['description']}\nVendedor: {seller_name}",
                    inline=False
                )

        await ctx.send(embed=embed, ephemeral=True)

    @commands.command(name="vender")
    async def sell(self, ctx, item_id: int = None, price: int = None):
        """Vender um item no mercado."""
        # Check if player exists
        player = get_player(ctx.author.id)
        if not player:
            await ctx.send(f"{ctx.author.mention}, você ainda não está registrado na Academia Tokugawa. Use !ingressar para criar seu personagem.", ephemeral=True)
            return

        # Check if item_id and price are provided
        if item_id is None or price is None:
            await ctx.send(f"{ctx.author.mention}, você precisa especificar o ID do item e o preço. Exemplo: `!vender 1 100`", ephemeral=True)
            return

        # Check if price is valid
        if price <= 0:
            await ctx.send(f"{ctx.author.mention}, o preço deve ser maior que zero.", ephemeral=True)
            return

        # Check if player has the item
        inventory = player["inventory"]
        if str(item_id) not in inventory:
            await ctx.send(f"{ctx.author.mention}, você não possui este item em seu inventário.", ephemeral=True)
            return

        # Get item data
        item_data = inventory[str(item_id)]

        # Create listing
        listing_id = self.next_listing_id
        self.next_listing_id += 1

        self.market_listings[listing_id] = {
            "seller_id": ctx.author.id,
            "item_id": item_id,
            "price": price,
            "item_data": item_data
        }

        # Remove item from inventory
        inventory[str(item_id)]["quantity"] -= 1
        if inventory[str(item_id)]["quantity"] <= 0:
            del inventory[str(item_id)]

        # Update player in database
        success = update_player(ctx.author.id, inventory=json.dumps(inventory))

        if success:
            # Create listing confirmation embed
            rarity = RARITIES.get(item_data["rarity"], RARITIES["common"])
            embed = create_basic_embed(
                title="Item Colocado à Venda!",
                description=f"Você colocou {rarity['emoji']} **{item_data['name']}** à venda por {price} TUSD.\n\n"
                            f"ID da listagem: {listing_id}",
                color=rarity["color"]
            )

            await ctx.send(embed=embed)
        else:
            await ctx.send("Ocorreu um erro ao colocar o item à venda. Por favor, tente novamente mais tarde.")

    @commands.command(name="comprar_mercado")
    async def buy_market(self, ctx, listing_id: int = None):
        """Comprar um item do mercado."""
        # Check if player exists
        player = get_player(ctx.author.id)
        if not player:
            await ctx.send(f"{ctx.author.mention}, você ainda não está registrado na Academia Tokugawa. Use !ingressar para criar seu personagem.", ephemeral=True)
            return

        # Check if listing_id is provided
        if listing_id is None:
            await ctx.send(f"{ctx.author.mention}, você precisa especificar o ID da listagem. Use `!mercado` para ver as listagens disponíveis.", ephemeral=True)
            return

        # Check if listing exists
        if listing_id not in self.market_listings:
            await ctx.send(f"{ctx.author.mention}, listagem não encontrada. Use `!mercado` para ver as listagens disponíveis.", ephemeral=True)
            return

        # Get listing data
        listing = self.market_listings[listing_id]

        # Check if player is trying to buy their own item
        if listing["seller_id"] == ctx.author.id:
            await ctx.send(f"{ctx.author.mention}, você não pode comprar seu próprio item.")
            return

        # Check if player has enough TUSD
        if player["tusd"] < listing["price"]:
            await ctx.send(f"{ctx.author.mention}, você não tem TUSD suficiente para comprar este item. Preço: {listing['price']} TUSD, Seu saldo: {player['tusd']} TUSD")
            return

        # Get seller data
        seller = get_player(listing["seller_id"])
        if not seller:
            await ctx.send(f"{ctx.author.mention}, o vendedor não existe mais. A listagem será removida.")
            del self.market_listings[listing_id]
            return

        # Process the purchase
        buyer_inventory = player["inventory"]

        # Add item to buyer's inventory
        if str(listing["item_id"]) in buyer_inventory:
            # If buyer already has this item, increase quantity
            buyer_inventory[str(listing["item_id"])]["quantity"] += 1
        else:
            # Add new item to inventory
            item_data = listing["item_data"].copy()
            item_data["quantity"] = 1
            buyer_inventory[str(listing["item_id"])] = item_data

        # Update buyer data
        buyer_update = {
            "tusd": player["tusd"] - listing["price"],
            "inventory": json.dumps(buyer_inventory)
        }

        # Update seller data
        seller_update = {
            "tusd": seller["tusd"] + listing["price"]
        }

        # Update both players in database
        buyer_success = update_player(ctx.author.id, **buyer_update)
        seller_success = update_player(listing["seller_id"], **seller_update)

        if buyer_success and seller_success:
            # Remove listing
            del self.market_listings[listing_id]

            # Create purchase confirmation embed
            rarity = RARITIES.get(listing["item_data"]["rarity"], RARITIES["common"])
            embed = create_basic_embed(
                title="Compra Realizada!",
                description=f"Você comprou {rarity['emoji']} **{listing['item_data']['name']}** por {listing['price']} TUSD.\n\n"
                            f"Saldo atual: {buyer_update['tusd']} TUSD 💰",
                color=rarity["color"]
            )

            await ctx.send(embed=embed, ephemeral=True)

            # Notify seller if they're online
            seller_user = self.bot.get_user(listing["seller_id"])
            if seller_user:
                seller_embed = create_basic_embed(
                    title="Item Vendido!",
                    description=f"Seu item {rarity['emoji']} **{listing['item_data']['name']}** foi vendido por {listing['price']} TUSD.\n\n"
                                f"Saldo atual: {seller_update['tusd']} TUSD 💰",
                    color=rarity["color"]
                )

                try:
                    await seller_user.send(embed=seller_embed, ephemeral=True)
                except:
                    # Ignore if we can't DM the seller
                    pass
        else:
            await ctx.send("Ocorreu um erro durante a compra. Por favor, tente novamente mais tarde.")

    @commands.command(name="equipar")
    async def equip_item(self, ctx, item_id: int = None):
        """Equipar um acessório do inventário."""
        # Check if player exists
        player = get_player(ctx.author.id)
        if not player:
            await ctx.send(f"{ctx.author.mention}, você ainda não está registrado na Academia Tokugawa. Use !ingressar para criar seu personagem.")
            return

        # Check if item_id is provided
        if item_id is None:
            await ctx.send(f"{ctx.author.mention}, você precisa especificar o ID do item que deseja equipar. Use `!inventario` para ver seus itens.", ephemeral=True)
            return

        # Check if player has the item
        inventory = player["inventory"]
        if str(item_id) not in inventory:
            await ctx.send(f"{ctx.author.mention}, você não possui este item em seu inventário.", ephemeral=True)
            return

        # Get item data
        item_data = inventory[str(item_id)]

        # Check if item is an accessory
        if item_data["type"] != "accessory":
            await ctx.send(f"{ctx.author.mention}, apenas acessórios podem ser equipados. Este item é do tipo {item_data['type']}.", ephemeral=True)
            return

        # Check if the item is already equipped
        if item_data.get("equipped", False):
            # Unequip the item
            inventory[str(item_id)]["equipped"] = False
            update_data = {"inventory": json.dumps(inventory)}
            success = update_player(ctx.author.id, **update_data)

            if success:
                embed = create_basic_embed(
                    title="Acessório Desequipado!",
                    description=f"Você desequipou {item_data['name']}.",
                    color=RARITIES.get(item_data["rarity"], RARITIES["common"])["color"]
                )
                await ctx.send(embed=embed, ephemeral=True)
            else:
                await ctx.send("Ocorreu um erro ao desequipar o acessório. Por favor, tente novamente mais tarde.", ephemeral=True)
            return

        # Check if there's a cooldown for this accessory
        cooldown = self._check_cooldown(ctx.author.id, f"accessory_{item_id}")
        if cooldown:
            await ctx.send(f"{ctx.author.mention}, este acessório está em cooldown. Tempo restante: {cooldown}")
            return

        # Unequip any other equipped accessories of the same type
        for inv_item_id, inv_item in inventory.items():
            if inv_item["type"] == "accessory" and inv_item.get("equipped", False):
                inventory[inv_item_id]["equipped"] = False

        # Equip the new accessory
        inventory[str(item_id)]["equipped"] = True

        # Set cooldown for this accessory (4 hours)
        self._set_cooldown(ctx.author.id, f"accessory_{item_id}", 14400)  # 4 hours in seconds

        # Update player in database
        update_data = {"inventory": json.dumps(inventory)}
        success = update_player(ctx.author.id, **update_data)

        if success:
            # Create equip confirmation embed
            rarity = RARITIES.get(item_data["rarity"], RARITIES["common"])
            embed = create_basic_embed(
                title="Acessório Equipado!",
                description=f"Você equipou {item_data['name']}. Os efeitos do acessório estão ativos!",
                color=rarity["color"]
            )

            await ctx.send(embed=embed, ephemeral=True)
        else:
            await ctx.send("Ocorreu um erro ao equipar o acessório. Por favor, tente novamente mais tarde.", ephemeral=True)

    @commands.command(name="usar")
    async def use_item(self, ctx, item_id: int = None):
        """Usar um item do inventário."""
        # Check if player exists
        player = get_player(ctx.author.id)
        if not player:
            await ctx.send(f"{ctx.author.mention}, você ainda não está registrado na Academia Tokugawa. Use !ingressar para criar seu personagem.")
            return

        # Check if item_id is provided
        if item_id is None:
            await ctx.send(f"{ctx.author.mention}, você precisa especificar o ID do item que deseja usar. Use `!inventario` para ver seus itens.", ephemeral=True)
            return

        # Check if player has the item
        inventory = player["inventory"]
        if str(item_id) not in inventory:
            await ctx.send(f"{ctx.author.mention}, você não possui este item em seu inventário.", ephemeral=True)
            return

        # Get item data
        item_data = inventory[str(item_id)]

        # Check if item is usable
        if item_data["type"] != "consumable":
            await ctx.send(f"{ctx.author.mention}, este item não pode ser usado diretamente. Itens do tipo {item_data['type']} são aplicados automaticamente.", ephemeral=True)
            return

        # Process item use
        update_data = {}
        use_message = ""

        # Handle different item effects
        if "cooldown_reduction" in item_data["effects"]:
            # Reduce cooldown for a command
            command = item_data["effects"]["cooldown_reduction"]["command"]
            amount = item_data["effects"]["cooldown_reduction"]["amount"]

            # Check if command is on cooldown
            if ctx.author.id in COOLDOWNS and command in COOLDOWNS[ctx.author.id]:
                COOLDOWNS[ctx.author.id][command] -= amount
                use_message = f"Você usou {item_data['name']} e reduziu o cooldown do comando !{command} em 30 minutos!"
            else:
                await ctx.send(f"{ctx.author.mention}, este comando não está em cooldown no momento.", ephemeral=True)
                return

        elif "club_reputation" in item_data["effects"]:
            # Increase club reputation
            if not player["club_id"]:
                await ctx.send(f"{ctx.author.mention}, você precisa estar em um clube para usar este item.", ephemeral=True)
                return

            # Get club data
            club = get_club(str(player["club_id"]))
            if not club:
                await ctx.send(f"{ctx.author.mention}, seu clube não existe mais.", ephemeral=True)
                return

            # TODO: Implement club reputation update
            use_message = f"Você usou {item_data['name']} e aumentou sua reputação no clube {club['name']}!"

        elif "potion" in item_data["effects"]:
            # Handle potion effects
            potion_type = item_data["effects"]["potion"]["type"]
            amount = item_data["effects"]["potion"]["amount"]

            if potion_type == "training":
                # Training potion increases experience
                update_data["exp"] = player["exp"] + amount
                use_message = f"Você bebeu {item_data['name']} e ganhou {amount} de experiência! Seu treinamento foi acelerado."

            elif potion_type == "attribute":
                # Attribute potion increases a specific attribute
                attribute = item_data["effects"]["potion"]["attribute"]
                if attribute in ["dexterity", "intellect", "charisma", "power_stat"]:
                    update_data[attribute] = player[attribute] + amount
                    attribute_names = {
                        "dexterity": "Destreza",
                        "intellect": "Intelecto",
                        "charisma": "Carisma",
                        "power_stat": "Poder"
                    }
                    use_message = f"Você bebeu {item_data['name']} e aumentou seu atributo de {attribute_names[attribute]} em {amount} pontos!"
                else:
                    await ctx.send(f"{ctx.author.mention}, esta poção tem um atributo inválido.", ephemeral=True)
                    return

            elif potion_type == "currency":
                # Currency potion increases TUSD
                update_data["tusd"] = player["tusd"] + amount
                use_message = f"Você bebeu {item_data['name']} e ganhou {amount} TUSD! Sua carteira está mais cheia."

            elif potion_type == "health":
                # Health potion would be used in combat (not implemented yet)
                use_message = f"Você bebeu {item_data['name']} e se sente revigorado! Sua saúde foi restaurada."

            else:
                await ctx.send(f"{ctx.author.mention}, este tipo de poção não é reconhecido.", ephemeral=True)
                return

        else:
            await ctx.send(f"{ctx.author.mention}, este item não pode ser usado no momento.", ephemeral=True)
            return

        # Remove item from inventory
        inventory[str(item_id)]["quantity"] -= 1
        if inventory[str(item_id)]["quantity"] <= 0:
            del inventory[str(item_id)]

        update_data["inventory"] = json.dumps(inventory)

        # Update player in database
        success = update_player(ctx.author.id, **update_data)

        if success:
            # Create use confirmation embed
            rarity = RARITIES.get(item_data["rarity"], RARITIES["common"])
            embed = create_basic_embed(
                title="Item Usado!",
                description=use_message,
                color=rarity["color"]
            )

            await ctx.send(embed=embed, ephemeral=True)
        else:
            await ctx.send("Ocorreu um erro ao usar o item. Por favor, tente novamente mais tarde.")

async def setup(bot):
    """Add the cog to the bot."""
    cog = Economy(bot)
    await bot.add_cog(cog)
    logger.info("Economy cog loaded")

    # Add the economy_group to the bot's command tree
    try:
        bot.tree.add_command(cog.economy_group)
        logger.info(f"Added economy_group to command tree: /{cog.economy_group.name}")
    except discord.app_commands.errors.CommandAlreadyRegistered:
        logger.info(f"Economy_group already registered: /{cog.economy_group.name}")

    # Add the technique_group to the bot's command tree
    try:
        bot.tree.add_command(cog.technique_group)
        logger.info(f"Added technique_group to command tree: /{cog.technique_group.name}")
    except discord.app_commands.errors.CommandAlreadyRegistered:
        logger.info(f"Technique_group already registered: /{cog.technique_group.name}")

    # Log the slash commands that were added
    for cmd in cog.__cog_app_commands__:
        logger.info(f"Economy cog added slash command: /{cmd.name}")
