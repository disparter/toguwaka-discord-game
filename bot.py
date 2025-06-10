import os
import asyncio
import discord
from discord.ext import commands
import logging
from src.utils.persistence.db_provider import db_provider
from src.utils.persistence.dynamo_migration import normalize_player_data

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('tokugawa_bot')

# Configure CloudWatch logging if running in AWS
if (
    os.environ.get('AWS_EXECUTION_ENV') is not None or  # Lambda
    os.environ.get('ECS_CONTAINER_METADATA_URI_V4') is not None or  # ECS
    os.environ.get('AWS_CONTAINER_CREDENTIALS_RELATIVE_URI') is not None  # ECS
):
    try:
        import watchtower
        import boto3

        # Get the AWS region from environment or default to us-east-1
        aws_region = os.environ.get('AWS_REGION', 'us-east-1')

        # Create CloudWatch logs client
        cloudwatch_client = boto3.client('logs', region_name=aws_region)

        # Create CloudWatch handler with ECS-specific log group
        cloudwatch_handler = watchtower.CloudWatchLogHandler(
            log_group='/ecs/tokugawa-bot',
            stream_name=f'discord-bot-logs-{os.environ.get("HOSTNAME", "unknown")}',
            boto3_client=cloudwatch_client
        )

        # Add CloudWatch handler to logger
        logger.addHandler(cloudwatch_handler)
        logger.info("CloudWatch logging enabled for ECS environment")
    except ImportError:
        logger.warning("watchtower package not installed, CloudWatch logging disabled")
    except Exception as e:
        logger.error(f"Failed to set up CloudWatch logging: {e}")

# Get environment variables
TOKEN = os.environ.get('DISCORD_TOKEN')
if not TOKEN:
    logger.error("DISCORD_TOKEN environment variable is not set!")
    raise ValueError("DISCORD_TOKEN environment variable is required")

# Check if we should use privileged intents (default: True)
USE_PRIVILEGED_INTENTS = os.environ.get('USE_PRIVILEGED_INTENTS', 'True').lower() != 'false'
# Get guild ID for command registration (if provided)
GUILD_ID = os.environ.get('GUILD_ID')

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

# Create a custom bot class with setup_hook for loading extensions
class TokugawaBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Initialize config dictionary with values from environment variables
        self.config = {
            "guild_id": int(os.environ.get('GUILD_ID', 0)) if os.environ.get('GUILD_ID') else None,
            "admin_role_id": int(os.environ.get('ADMIN_ROLE_ID', 0)) if os.environ.get('ADMIN_ROLE_ID') else None,
        }
        logger.info(f"Bot initialized with config: {self.config}")

    async def setup_hook(self):
        """Setup hook that is called when the bot is starting up."""
        # Load all extensions
        for extension in initial_extensions:
            try:
                await self.load_extension(extension)
                logger.info(f'Loaded extension: {extension}')
            except Exception as e:
                logger.error(f'Failed to load extension {extension}: {e}')

# Create bot instance with command prefix and command tree for slash commands
bot = TokugawaBot(command_prefix='!', intents=intents)

# Make sure the bot is syncing application commands
async def on_app_command_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
    """Error handler for application commands."""
    if isinstance(error, discord.app_commands.CommandInvokeError):
        # If the original error is a NotFound error (interaction expired)
        if isinstance(error.original, discord.NotFound) and error.original.code == 10062:
            logger.warning(f"Interaction expired for user {interaction.user.id if interaction.user else 'Unknown'} when using /{interaction.command.name if interaction.command else 'Unknown'}")
            return

    # Log all other errors
    logger.error(f"Command tree error: {error}")

bot.tree.on_error = on_app_command_error

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
    'src.bot.cogs.registration',
    'src.bot.cogs.player_status',
    'src.bot.cogs.activities',
    'src.bot.cogs.economy',
    'src.bot.cogs.clubs',
    'src.bot.cogs.scheduled_events',
    'src.bot.cogs.junie_interaction',
    'src.bot.cogs.story_mode',
    'src.bot.cogs.betting',  # New betting cog for risk mechanics
    'src.bot.cogs.moral_choices',  # New moral choices cog for dilemas and collective events
    'src.bot.cogs.npc_interaction'  # New cog for NPC interactions and image registry
]

# This function is no longer needed as extensions are loaded in setup_hook

# Flag to track whether commands have been synced
commands_synced = False

@bot.event
async def on_ready():
    """Event triggered when the bot is ready and connected to Discord."""
    global commands_synced

    logger.info(f'Bot is ready! Logged in as {bot.user.name}')

    # Initialize database
    db_initialized = False
    try:
        # Use init_db directly from db_provider to avoid circular dependencies
        logger.info("Initializing database...")
        db_initialized = await db_provider.init_db()
        if db_initialized:
            logger.info("Database initialized successfully")
        else:
            logger.error("Failed to initialize database")
            logger.warning("Continuing bot execution despite database initialization failure")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        logger.error(f"Exception type: {type(e).__name__}")
        logger.error(f"Exception args: {e.args}")
        logger.warning("Continuing bot execution despite database initialization error")

    # Try to sync data if needed (only if database initialization failed)
    if not db_initialized:
        try:
            logger.info("Attempting to sync data to DynamoDB...")
            if not await db_provider.sync_to_dynamo_if_empty():
                logger.error("Failed to sync data to DynamoDB")
                # Don't close the bot, just log the error and continue
                logger.warning("Continuing bot execution despite DynamoDB sync failure")
        except Exception as e:
            logger.error(f"Error syncing data to DynamoDB: {e}")
            logger.error(f"Exception type: {type(e).__name__}")
            logger.warning("Continuing bot execution despite DynamoDB sync error")

    # Normalize player data (regardless of database initialization status)
    try:
        logger.info("Starting player data normalization...")
        logger.info("Calling normalize_player_data function...")
        success = await normalize_player_data()
        logger.info(f"normalize_player_data function returned: {success}")
        if success:
            logger.info("Player data normalization completed successfully!")
        else:
            logger.error("Player data normalization failed!")
            logger.warning("Continuing bot execution despite player migration failure")
    except Exception as e:
        logger.error(f"Exception during player data normalization: {str(e)}")
        logger.error(f"Exception type: {type(e).__name__}")
        logger.error(f"Exception args: {e.args}")
        logger.warning("Continuing bot execution despite player migration error")

    # Sync commands with guild only if they haven't been synced already
    if not commands_synced:
        await sync_commands()
        commands_synced = True
        logger.info("Commands synced successfully")
    else:
        logger.info("Commands already synced, skipping sync")

@bot.command(name='ping')
async def ping(ctx):
    """Simple command to check if the bot is responsive."""
    await ctx.send('Pong! 🏓')

# Function to sync commands with guild
async def sync_commands():
    """Sync commands with guild if GUILD_ID is provided."""
    try:
        # Log all commands in the command tree before syncing
        logger.info("Commands in command tree before syncing:")
        for cmd in bot.tree.get_commands():
            logger.info(f"Command in tree: /{cmd.name}")

        # Always sync commands globally first to ensure all commands are registered
        logger.info("Syncing commands globally...")
        global_commands = await bot.tree.sync()
        logger.info(f"Synced {len(global_commands)} commands globally")
        for cmd in global_commands:
            logger.info(f"Command synced globally: /{cmd.name}")

        # Then sync to guild if GUILD_ID is provided
        if GUILD_ID:
            try:
                guild = discord.Object(id=int(GUILD_ID))
                # Sync commands to the guild
                commands = await bot.tree.sync(guild=guild)
                logger.info(f"Successfully synced {len(commands)} commands to guild ID: {GUILD_ID}")

                # Log each command that was synced
                for cmd in commands:
                    logger.info(f"Command synced: /{cmd.name}")

                # If no commands were synced, log a warning
                if not commands:
                    logger.warning("No commands were synced to the guild. Using global commands instead.")
            except Exception as e:
                logger.error(f"Failed to sync commands to guild: {e}")
                logger.error(f"Exception type: {type(e).__name__}")
                logger.error(f"Exception args: {e.args}")
                logger.info("Using globally synced commands as fallback")
        else:
            logger.info("No GUILD_ID provided. Using globally synced commands.")
    except Exception as e:
        logger.error(f"Failed to sync commands: {e}")
        logger.error(f"Exception type: {type(e).__name__}")
        logger.error(f"Exception args: {e.args}")

# Run the bot
async def main():
    """Main function to run the bot."""
    try:
        # Start the bot using async context manager
        # Extensions are loaded in setup_hook
        async with bot:
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
