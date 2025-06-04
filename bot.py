import os
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('tokugawa_bot')

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
# Check if we should use privileged intents (default: True)
USE_PRIVILEGED_INTENTS = os.getenv('USE_PRIVILEGED_INTENTS', 'True').lower() != 'false'
# Get guild ID for command registration (if provided)
GUILD_ID = os.getenv('GUILD_ID')

# Set up intents
# Note: The members and message_content intents are privileged intents
# You need to enable them in the Discord Developer Portal:
# 1. Go to https://discord.com/developers/applications/
# 2. Select your application/bot
# 3. Go to "Bot" settings
# 4. Enable "SERVER MEMBERS INTENT" and "MESSAGE CONTENT INTENT" under "Privileged Gateway Intents"
# 
# Alternatively, you can set USE_PRIVILEGED_INTENTS=False in your .env file
# to run the bot without privileged intents (with limited functionality)
intents = discord.Intents.default()

if USE_PRIVILEGED_INTENTS:
    logger.info("Using privileged intents (full functionality)")
    intents.message_content = True  # Privileged intent
    intents.members = True          # Privileged intent
else:
    logger.warning("Running without privileged intents (limited functionality)")
    logger.warning("Some features like member tracking and message content access will not work")
    # No privileged intents used

# Create bot instance with command prefix and command tree for slash commands
bot = commands.Bot(command_prefix='!', intents=intents)

# Make sure the bot is syncing application commands
bot.tree.on_error = lambda interaction, error: logger.error(f"Command tree error: {error}")

# Add a simple slash command for testing
@bot.tree.command(name="ping", description="Responde com 'Pong!' para verificar se o bot está funcionando")
async def slash_ping(interaction: discord.Interaction):
    """Slash command version of the ping command."""
    try:
        await interaction.response.send_message("Pong! 🏓")
    except discord.errors.NotFound:
        # If the interaction has expired, log it but don't try to respond
        logger.warning(f"Interaction expired for user {interaction.user.id} when using /ping")
    except Exception as e:
        logger.error(f"Error in slash_ping: {e}")

@bot.tree.command(name="teste", description="Comando de teste para verificar se os comandos estão sendo sincronizados")
async def slash_test(interaction: discord.Interaction):
    """Test command to verify that commands are being synced."""
    try:
        await interaction.response.send_message("Teste bem-sucedido! Os comandos estão sendo sincronizados corretamente.")
    except discord.errors.NotFound:
        # If the interaction has expired, log it but don't try to respond
        logger.warning(f"Interaction expired for user {interaction.user.id} when using /teste")
    except Exception as e:
        logger.error(f"Error in slash_test: {e}")

# Initial cogs to load
initial_extensions = [
    'cogs.registration',
    'cogs.player_status',
    'cogs.activities',
    'cogs.economy',
    'cogs.clubs',
    'cogs.scheduled_events'
]

async def load_extensions():
    """Load all extensions/cogs."""
    for extension in initial_extensions:
        try:
            await bot.load_extension(extension)
            logger.info(f'Loaded extension: {extension}')
        except Exception as e:
            logger.error(f'Failed to load extension {extension}: {e}')

@bot.event
async def on_ready():
    """Event triggered when the bot is ready and connected to Discord."""
    logger.info(f'{bot.user.name} has connected to Discord!')
    logger.info(f'Bot is in {len(bot.guilds)} guilds')

    # Set bot status
    await bot.change_presence(activity=discord.Game(name="Academia Tokugawa"))

    # Sync commands with guild
    await sync_commands()

@bot.command(name='ping')
async def ping(ctx):
    """Simple command to check if the bot is responsive."""
    await ctx.send('Pong! 🏓')

# Function to sync commands with guild
async def sync_commands():
    """Sync commands with guild if GUILD_ID is provided."""
    if GUILD_ID:
        try:
            # Log all commands in the command tree before syncing
            logger.info("Commands in command tree before syncing:")
            for cmd in bot.tree.get_commands():
                logger.info(f"Command in tree: /{cmd.name}")

            guild = discord.Object(id=int(GUILD_ID))
            # First sync commands to the guild
            commands = await bot.tree.sync(guild=guild)
            logger.info(f"Successfully synced {len(commands)} commands to guild ID: {GUILD_ID}")

            # Log each command that was synced
            for cmd in commands:
                logger.info(f"Command synced: /{cmd.name}")

            # If no commands were synced, log a warning
            if not commands:
                logger.warning("No commands were synced to the guild. Make sure commands are properly defined in cogs.")

                # Try syncing globally as a fallback
                logger.info("Trying to sync commands globally as a fallback...")
                global_commands = await bot.tree.sync()
                logger.info(f"Synced {len(global_commands)} commands globally")
                for cmd in global_commands:
                    logger.info(f"Command synced globally: /{cmd.name}")
        except Exception as e:
            logger.error(f"Failed to sync commands to guild: {e}")
            logger.error(f"Exception type: {type(e).__name__}")
            logger.error(f"Exception args: {e.args}")
    else:
        logger.info("No GUILD_ID provided. Commands will be registered globally (may take up to an hour).")
        try:
            # Sync commands globally
            commands = await bot.tree.sync()
            logger.info(f"Synced {len(commands)} commands globally")
            for cmd in commands:
                logger.info(f"Command synced globally: /{cmd.name}")
        except Exception as e:
            logger.error(f"Failed to sync commands globally: {e}")
            logger.error(f"Exception type: {type(e).__name__}")
            logger.error(f"Exception args: {e.args}")

# Run the bot
async def main():
    """Main function to run the bot."""
    try:
        # First load all extensions
        await load_extensions()

        # Start the bot (sync_commands will be called in on_ready)
        await bot.start(TOKEN)
    except discord.errors.PrivilegedIntentsRequired:
        logger.error("ERROR: Privileged intents are required but not enabled!")
        logger.error("Please follow these steps to enable privileged intents:")
        logger.error("1. Go to https://discord.com/developers/applications/")
        logger.error("2. Select your application/bot")
        logger.error("3. Go to 'Bot' settings")
        logger.error("4. Enable 'SERVER MEMBERS INTENT' and 'MESSAGE CONTENT INTENT' under 'Privileged Gateway Intents'")
        logger.error("5. Restart the bot")
        raise

if __name__ == '__main__':
    asyncio.run(main())
