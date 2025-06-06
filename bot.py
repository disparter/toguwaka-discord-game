import os
import asyncio
import discord
from discord.ext import commands
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('tokugawa_bot')

# Configure CloudWatch logging if running in AWS
if os.environ.get('AWS_EXECUTION_ENV') is not None:
    try:
        import watchtower
        import boto3

        # Get the AWS region from environment or default to us-east-1
        aws_region = os.environ.get('AWS_REGION', 'us-east-1')

        # Create CloudWatch logs client
        cloudwatch_client = boto3.client('logs', region_name=aws_region)

        # Create CloudWatch handler
        cloudwatch_handler = watchtower.CloudWatchLogHandler(
            log_group='/ecs/tokugawa-bot',
            stream_name='discord-bot-logs',
            boto3_client=cloudwatch_client
        )

        # Add CloudWatch handler to logger
        logger.addHandler(cloudwatch_handler)
        logger.info("CloudWatch logging enabled")
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
    'cogs.scheduled_events',
    'cogs.junie_interaction',
    'cogs.story_mode',
    'cogs.betting',  # New betting cog for risk mechanics
    'cogs.moral_choices'  # New moral choices cog for dilemas and collective events
]

# This function is no longer needed as extensions are loaded in setup_hook

# Flag to track whether commands have been synced
commands_synced = False

@bot.event
async def on_ready():
    """Event triggered when the bot is ready and connected to Discord."""
    global commands_synced
    logger.info(f'{bot.user.name} has connected to Discord!')
    logger.info(f'Bot is in {len(bot.guilds)} guilds')

    # Set bot status
    await bot.change_presence(activity=discord.Game(name="Academia Tokugawa"))

    # Check if DynamoDB is enabled and run migration if needed
    try:
        import os
        from utils.database import get_system_flag, set_system_flag

        # Check if DynamoDB is enabled
        use_dynamodb = os.environ.get('USE_DYNAMODB', 'false').lower() == 'true'

        if use_dynamodb:
            # Check if migration has been executed before
            migration_flag = get_system_flag('migration_executed')

            if not migration_flag:
                logger.info("First time running with DynamoDB enabled. Starting migration...")

                # Import and run migration script
                from utils.migrate_to_dynamodb import migrate_all

                # Run migration
                success = migrate_all()

                if success:
                    # Set flag to indicate migration has been executed
                    set_system_flag('migration_executed', 'true')
                    logger.info("Migration completed successfully")
                else:
                    logger.error("Migration failed")
            else:
                logger.info("Migration already executed, skipping")
    except Exception as e:
        logger.error(f"Error checking/running migration: {e}")

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
