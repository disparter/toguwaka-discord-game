import discord
from discord.ext import commands
from discord import app_commands
import logging
import random
import asyncio
import json
from datetime import datetime
from utils.database import get_player, update_player, get_club
from utils.embeds import create_basic_embed
from utils.game_mechanics import RARITIES
from cogs.activities import COOLDOWNS, COOLDOWN_DURATIONS

logger = logging.getLogger('tokugawa_bot')

# Shop items
SHOP_ITEMS = [
    {
        "id": 1,
        "name": "Poção de Treinamento",
        "description": "Reduz o tempo de cooldown do comando !treinar em 30 minutos.",
        "price": 50,
        "type": "consumable",
        "rarity": "common",
        "effects": {"cooldown_reduction": {"command": "treinar", "amount": 1800}}
    },
    {
        "id": 2,
        "name": "Amuleto de Foco",
        "description": "Aumenta a experiência ganha em treinamentos quando equipado.",
        "price": 100,
        "type": "accessory",
        "rarity": "uncommon",
        "effects": {"exp_boost": 1.5}
    },
    {
        "id": 3,
        "name": "Luvas de Combate",
        "description": "Aumenta a Destreza em +2 durante duelos.",
        "price": 200,
        "type": "equipment",
        "rarity": "rare",
        "effects": {"attribute_boost": {"dexterity": 2}}
    },
    {
        "id": 4,
        "name": "Grimório Arcano",
        "description": "Aumenta o Intelecto em +2 durante duelos.",
        "price": 200,
        "type": "equipment",
        "rarity": "rare",
        "effects": {"attribute_boost": {"intellect": 2}}
    },
    {
        "id": 5,
        "name": "Broche de Eloquência",
        "description": "Aumenta o Carisma em +2 durante duelos.",
        "price": 200,
        "type": "equipment",
        "rarity": "rare",
        "effects": {"attribute_boost": {"charisma": 2}}
    },
    {
        "id": 6,
        "name": "Cristal de Amplificação",
        "description": "Aumenta o Poder em +2 durante duelos.",
        "price": 200,
        "type": "equipment",
        "rarity": "rare",
        "effects": {"attribute_boost": {"power_stat": 2}}
    },
    {
        "id": 7,
        "name": "Pergaminho de Técnica",
        "description": "Ensina uma técnica especial aleatória ao seu personagem.",
        "price": 500,
        "type": "consumable",
        "rarity": "epic",
        "effects": {"learn_technique": True}
    },
    {
        "id": 8,
        "name": "Emblema do Clube",
        "description": "Aumenta sua reputação no clube atual.",
        "price": 300,
        "type": "consumable",
        "rarity": "uncommon",
        "effects": {"club_reputation": 50}
    },
    {
        "id": 9,
        "name": "Elixir de Atributo",
        "description": "Aumenta permanentemente um atributo aleatório em +1.",
        "price": 1000,
        "type": "consumable",
        "rarity": "legendary",
        "effects": {"permanent_attribute": 1}
    }
]

# Special techniques
TECHNIQUES = [
    {
        "id": 1,
        "name": "Golpe Relâmpago",
        "description": "Um ataque rápido que surpreende o oponente. +30% de chance de vencer duelos físicos.",
        "type": "physical",
        "effects": {"duel_boost": {"type": "physical", "amount": 0.3}}
    },
    {
        "id": 2,
        "name": "Manipulação Mental",
        "description": "Confunde a mente do oponente. +30% de chance de vencer duelos mentais.",
        "type": "mental",
        "effects": {"duel_boost": {"type": "mental", "amount": 0.3}}
    },
    {
        "id": 3,
        "name": "Estratégia Mestre",
        "description": "Planeja vários passos à frente. +30% de chance de vencer duelos estratégicos.",
        "type": "strategic",
        "effects": {"duel_boost": {"type": "strategic", "amount": 0.3}}
    },
    {
        "id": 4,
        "name": "Charme Irresistível",
        "description": "Encanta qualquer um com palavras doces. +30% de chance de vencer duelos sociais.",
        "type": "social",
        "effects": {"duel_boost": {"type": "social", "amount": 0.3}}
    },
    {
        "id": 5,
        "name": "Explosão de Poder",
        "description": "Libera todo seu poder de uma vez. +20% de chance de vencer qualquer tipo de duelo.",
        "type": "all",
        "effects": {"duel_boost": {"type": "all", "amount": 0.2}}
    },
    {
        "id": 6,
        "name": "Punho de Aço",
        "description": "Fortalece os punhos para um impacto devastador. +35% de chance de vencer duelos físicos.",
        "type": "physical",
        "effects": {"duel_boost": {"type": "physical", "amount": 0.35}}
    },
    {
        "id": 7,
        "name": "Barreira Mental",
        "description": "Cria uma barreira que protege contra ataques mentais. +35% de chance de vencer duelos mentais.",
        "type": "mental",
        "effects": {"duel_boost": {"type": "mental", "amount": 0.35}}
    },
    {
        "id": 8,
        "name": "Tática Avançada",
        "description": "Utiliza táticas de guerra avançadas. +35% de chance de vencer duelos estratégicos.",
        "type": "strategic",
        "effects": {"duel_boost": {"type": "strategic", "amount": 0.35}}
    },
    {
        "id": 9,
        "name": "Persuasão Suprema",
        "description": "Técnica de persuasão que dobra a vontade dos outros. +35% de chance de vencer duelos sociais.",
        "type": "social",
        "effects": {"duel_boost": {"type": "social", "amount": 0.35}}
    },
    {
        "id": 10,
        "name": "Concentração Total",
        "description": "Foca toda sua energia em um único objetivo. +25% de chance de vencer qualquer tipo de duelo.",
        "type": "all",
        "effects": {"duel_boost": {"type": "all", "amount": 0.25}}
    },
    {
        "id": 11,
        "name": "Técnica do Dragão",
        "description": "Técnica ancestral que canaliza a força de um dragão. +40% de chance de vencer duelos físicos.",
        "type": "physical",
        "effects": {"duel_boost": {"type": "physical", "amount": 0.4}}
    },
    {
        "id": 12,
        "name": "Ilusão Suprema",
        "description": "Cria ilusões tão reais que confundem até os mais perspicazes. +40% de chance de vencer duelos mentais.",
        "type": "mental",
        "effects": {"duel_boost": {"type": "mental", "amount": 0.4}}
    },
    {
        "id": 13,
        "name": "Xadrez Dimensional",
        "description": "Visualiza o duelo como um jogo de xadrez multidimensional. +40% de chance de vencer duelos estratégicos.",
        "type": "strategic",
        "effects": {"duel_boost": {"type": "strategic", "amount": 0.4}}
    },
    {
        "id": 14,
        "name": "Aura de Liderança",
        "description": "Emana uma aura que inspira respeito e admiração. +40% de chance de vencer duelos sociais.",
        "type": "social",
        "effects": {"duel_boost": {"type": "social", "amount": 0.4}}
    },
    {
        "id": 15,
        "name": "Despertar Interior",
        "description": "Desperta todo o potencial oculto dentro de si. +30% de chance de vencer qualquer tipo de duelo.",
        "type": "all",
        "effects": {"duel_boost": {"type": "all", "amount": 0.3}}
    }
]

class Economy(commands.Cog):
    """Cog for economy and shop commands."""

    def __init__(self, bot):
        self.bot = bot
        self.market_listings = {}  # {listing_id: {seller_id, item_id, price, item_data}}
        self.next_listing_id = 1

    def _check_cooldown(self, user_id, command):
        """Check if a command is on cooldown for a user."""
        now = datetime.now().timestamp()

        # Initialize user cooldowns if not exists
        if user_id not in COOLDOWNS:
            COOLDOWNS[user_id] = {}

        # Check if command is on cooldown
        if command in COOLDOWNS[user_id] and COOLDOWNS[user_id][command] > now:
            # Calculate remaining time
            remaining = COOLDOWNS[user_id][command] - now
            minutes, seconds = divmod(int(remaining), 60)
            hours, minutes = divmod(minutes, 60)

            if hours > 0:
                time_str = f"{hours}h {minutes}m {seconds}s"
            elif minutes > 0:
                time_str = f"{minutes}m {seconds}s"
            else:
                time_str = f"{seconds}s"

            return time_str

        return None

    def _set_cooldown(self, user_id, command, custom_duration=None):
        """Set a cooldown for a command for a user.

        Args:
            user_id: The user ID
            command: The command name
            custom_duration: Optional custom duration in seconds. If not provided, uses the default duration.
        """
        if user_id not in COOLDOWNS:
            COOLDOWNS[user_id] = {}

        duration = custom_duration if custom_duration is not None else COOLDOWN_DURATIONS.get(command, 3600)  # Default 1 hour
        expiry_time = datetime.now().timestamp() + duration
        COOLDOWNS[user_id][command] = expiry_time

        # Store cooldown in database
        try:
            from utils.database import store_cooldown
            store_cooldown(user_id, command, expiry_time)
        except Exception as e:
            logger.error(f"Error storing cooldown in database: {e}")

    # Group for economy commands
    economy_group = app_commands.Group(name="economia", description="Comandos de economia da Academia Tokugawa")

    @economy_group.command(name="loja", description="Acessar a loja da Academia Tokugawa")
    async def slash_shop(self, interaction: discord.Interaction):
        """Slash command version of the shop command."""
        # Check if player exists
        player = get_player(interaction.user.id)
        if not player:
            await interaction.response.send_message(f"{interaction.user.mention}, você ainda não está registrado na Academia Tokugawa. Use /registro ingressar para criar seu personagem.")
            return

        # Create shop embed
        embed = create_basic_embed(
            title="Loja da Academia Tokugawa",
            description=f"Bem-vindo à loja oficial da Academia! Você tem {player['tusd']} TUSD 💰\n\n"
                        f"Para comprar um item, use o comando `/economia comprar <id>`",
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

        await interaction.response.send_message(embed=embed)

    @economy_group.command(name="comprar", description="Comprar um item da loja")
    async def slash_buy(self, interaction: discord.Interaction, item_id: int):
        """Slash command version of the buy command."""
        # Check if player exists
        player = get_player(interaction.user.id)
        if not player:
            await interaction.response.send_message(f"{interaction.user.mention}, você ainda não está registrado na Academia Tokugawa. Use /registro ingressar para criar seu personagem.")
            return

        # Find the item
        item = next((i for i in SHOP_ITEMS if i["id"] == item_id), None)
        if not item:
            await interaction.response.send_message(f"{interaction.user.mention}, item não encontrado. Use `/economia loja` para ver os itens disponíveis.")
            return

        # Check if player has enough TUSD
        if player["tusd"] < item["price"]:
            await interaction.response.send_message(f"{interaction.user.mention}, você não tem TUSD suficiente para comprar este item. Preço: {item['price']} TUSD, Seu saldo: {player['tusd']} TUSD")
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
        success = update_player(interaction.user.id, **update_data)

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

            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Ocorreu um erro durante a compra. Por favor, tente novamente mais tarde.")

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

    @economy_group.command(name="usar", description="Usar um item do inventário")
    async def slash_use_item(self, interaction: discord.Interaction, item_id: int):
        """Slash command version of the use_item command."""
        try:
            # Check if player exists
            player = get_player(interaction.user.id)
            if not player:
                await interaction.response.send_message(f"{interaction.user.mention}, você ainda não está registrado na Academia Tokugawa. Use /registro ingressar para criar seu personagem.")
                return

            # Check if player has the item
            inventory = player["inventory"]
            if str(item_id) not in inventory:
                await interaction.response.send_message(f"{interaction.user.mention}, você não possui este item em seu inventário.")
                return

            # Get item data
            item_data = inventory[str(item_id)]

            # Check if item is usable
            if item_data["type"] != "consumable":
                await interaction.response.send_message(f"{interaction.user.mention}, este item não pode ser usado diretamente. Itens do tipo {item_data['type']} são aplicados automaticamente.")
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
                if interaction.user.id in COOLDOWNS and command in COOLDOWNS[interaction.user.id]:
                    COOLDOWNS[interaction.user.id][command] -= amount
                    use_message = f"Você usou {item_data['name']} e reduziu o cooldown do comando /{command} em 30 minutos!"
                else:
                    await interaction.response.send_message(f"{interaction.user.mention}, este comando não está em cooldown no momento.")
                    return

            elif "club_reputation" in item_data["effects"]:
                # Increase club reputation
                if not player["club_id"]:
                    await interaction.response.send_message(f"{interaction.user.mention}, você precisa estar em um clube para usar este item.")
                    return

                # Get club data
                club = get_club(player["club_id"])
                if not club:
                    await interaction.response.send_message(f"{interaction.user.mention}, seu clube não existe mais.")
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
                        await interaction.response.send_message(f"{interaction.user.mention}, esta poção tem um atributo inválido.")
                        return

                elif potion_type == "currency":
                    # Currency potion increases TUSD
                    update_data["tusd"] = player["tusd"] + amount
                    use_message = f"Você bebeu {item_data['name']} e ganhou {amount} TUSD! Sua carteira está mais cheia."

                elif potion_type == "health":
                    # Health potion would be used in combat (not implemented yet)
                    use_message = f"Você bebeu {item_data['name']} e se sente revigorado! Sua saúde foi restaurada."

                else:
                    await interaction.response.send_message(f"{interaction.user.mention}, este tipo de poção não é reconhecido.")
                    return

            else:
                await interaction.response.send_message(f"{interaction.user.mention}, este item não pode ser usado no momento.")
                return

            # Remove item from inventory
            inventory[str(item_id)]["quantity"] -= 1
            if inventory[str(item_id)]["quantity"] <= 0:
                del inventory[str(item_id)]

            update_data["inventory"] = json.dumps(inventory)

            # Update player in database
            success = update_player(interaction.user.id, **update_data)

            if success:
                # Create use confirmation embed
                rarity = RARITIES.get(item_data["rarity"], RARITIES["common"])
                embed = create_basic_embed(
                    title="Item Usado!",
                    description=use_message,
                    color=rarity["color"]
                )

                await interaction.response.send_message(embed=embed)
            else:
                await interaction.response.send_message("Ocorreu um erro ao usar o item. Por favor, tente novamente mais tarde.")
        except discord.errors.NotFound:
            # If the interaction has expired, log it but don't try to respond
            logger.warning(f"Interaction expired for user {interaction.user.id} when using /economia usar")
        except Exception as e:
            logger.error(f"Error in slash_use_item: {e}")

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
                await interaction.response.send_message(f"{interaction.user.mention}, você não possui este item em seu inventário.")
                return

            # Get item data
            item_data = inventory[str(item_id)]

            # Check if item is an accessory
            if item_data["type"] != "accessory":
                await interaction.response.send_message(f"{interaction.user.mention}, apenas acessórios podem ser equipados. Este item é do tipo {item_data['type']}.")
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
                    await interaction.response.send_message(embed=embed)
                else:
                    await interaction.response.send_message("Ocorreu um erro ao desequipar o acessório. Por favor, tente novamente mais tarde.")
                return

            # Check if there's a cooldown for this accessory
            cooldown = self._check_cooldown(interaction.user.id, f"accessory_{item_id}")
            if cooldown:
                await interaction.response.send_message(f"{interaction.user.mention}, este acessório está em cooldown. Tempo restante: {cooldown}")
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

                await interaction.response.send_message(embed=embed)
            else:
                await interaction.response.send_message("Ocorreu um erro ao equipar o acessório. Por favor, tente novamente mais tarde.")
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
            await ctx.send(f"{ctx.author.mention}, você precisa especificar o ID do item que deseja comprar. Use `!loja` para ver os itens disponíveis.")
            return

        # Find the item
        item = next((i for i in SHOP_ITEMS if i["id"] == item_id), None)
        if not item:
            await ctx.send(f"{ctx.author.mention}, item não encontrado. Use `!loja` para ver os itens disponíveis.")
            return

        # Check if player has enough TUSD
        if player["tusd"] < item["price"]:
            await ctx.send(f"{ctx.author.mention}, você não tem TUSD suficiente para comprar este item. Preço: {item['price']} TUSD, Seu saldo: {player['tusd']} TUSD")
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

            await ctx.send(embed=embed)
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

        await ctx.send(embed=embed)

    @commands.command(name="vender")
    async def sell(self, ctx, item_id: int = None, price: int = None):
        """Vender um item no mercado."""
        # Check if player exists
        player = get_player(ctx.author.id)
        if not player:
            await ctx.send(f"{ctx.author.mention}, você ainda não está registrado na Academia Tokugawa. Use !ingressar para criar seu personagem.")
            return

        # Check if item_id and price are provided
        if item_id is None or price is None:
            await ctx.send(f"{ctx.author.mention}, você precisa especificar o ID do item e o preço. Exemplo: `!vender 1 100`")
            return

        # Check if price is valid
        if price <= 0:
            await ctx.send(f"{ctx.author.mention}, o preço deve ser maior que zero.")
            return

        # Check if player has the item
        inventory = player["inventory"]
        if str(item_id) not in inventory:
            await ctx.send(f"{ctx.author.mention}, você não possui este item em seu inventário.")
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
            await ctx.send(f"{ctx.author.mention}, você ainda não está registrado na Academia Tokugawa. Use !ingressar para criar seu personagem.")
            return

        # Check if listing_id is provided
        if listing_id is None:
            await ctx.send(f"{ctx.author.mention}, você precisa especificar o ID da listagem. Use `!mercado` para ver as listagens disponíveis.")
            return

        # Check if listing exists
        if listing_id not in self.market_listings:
            await ctx.send(f"{ctx.author.mention}, listagem não encontrada. Use `!mercado` para ver as listagens disponíveis.")
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

            await ctx.send(embed=embed)

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
            await ctx.send(f"{ctx.author.mention}, você precisa especificar o ID do item que deseja equipar. Use `!inventario` para ver seus itens.")
            return

        # Check if player has the item
        inventory = player["inventory"]
        if str(item_id) not in inventory:
            await ctx.send(f"{ctx.author.mention}, você não possui este item em seu inventário.")
            return

        # Get item data
        item_data = inventory[str(item_id)]

        # Check if item is an accessory
        if item_data["type"] != "accessory":
            await ctx.send(f"{ctx.author.mention}, apenas acessórios podem ser equipados. Este item é do tipo {item_data['type']}.")
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
                await ctx.send(embed=embed)
            else:
                await ctx.send("Ocorreu um erro ao desequipar o acessório. Por favor, tente novamente mais tarde.")
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

            await ctx.send(embed=embed)
        else:
            await ctx.send("Ocorreu um erro ao equipar o acessório. Por favor, tente novamente mais tarde.")

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
            await ctx.send(f"{ctx.author.mention}, você precisa especificar o ID do item que deseja usar. Use `!inventario` para ver seus itens.")
            return

        # Check if player has the item
        inventory = player["inventory"]
        if str(item_id) not in inventory:
            await ctx.send(f"{ctx.author.mention}, você não possui este item em seu inventário.")
            return

        # Get item data
        item_data = inventory[str(item_id)]

        # Check if item is usable
        if item_data["type"] != "consumable":
            await ctx.send(f"{ctx.author.mention}, este item não pode ser usado diretamente. Itens do tipo {item_data['type']} são aplicados automaticamente.")
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
                await ctx.send(f"{ctx.author.mention}, este comando não está em cooldown no momento.")
                return

        elif "club_reputation" in item_data["effects"]:
            # Increase club reputation
            if not player["club_id"]:
                await ctx.send(f"{ctx.author.mention}, você precisa estar em um clube para usar este item.")
                return

            # Get club data
            club = get_club(player["club_id"])
            if not club:
                await ctx.send(f"{ctx.author.mention}, seu clube não existe mais.")
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
                    await ctx.send(f"{ctx.author.mention}, esta poção tem um atributo inválido.")
                    return

            elif potion_type == "currency":
                # Currency potion increases TUSD
                update_data["tusd"] = player["tusd"] + amount
                use_message = f"Você bebeu {item_data['name']} e ganhou {amount} TUSD! Sua carteira está mais cheia."

            elif potion_type == "health":
                # Health potion would be used in combat (not implemented yet)
                use_message = f"Você bebeu {item_data['name']} e se sente revigorado! Sua saúde foi restaurada."

            else:
                await ctx.send(f"{ctx.author.mention}, este tipo de poção não é reconhecido.")
                return

        else:
            await ctx.send(f"{ctx.author.mention}, este item não pode ser usado no momento.")
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

            await ctx.send(embed=embed)
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

    # Log the slash commands that were added
    for cmd in cog.__cog_app_commands__:
        logger.info(f"Economy cog added slash command: /{cmd.name}")
