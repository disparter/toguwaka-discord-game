import asyncio
import logging
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Now import the bot after environment variables are loaded
from bot import bot, TOKEN

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_bot_startup')

async def test_startup():
    """Test that the bot can start up without getting stuck."""
    logger.info("Starting bot startup test...")

    try:
        # Start the bot with a timeout
        logger.info("Attempting to start the bot...")

        # Create a task for the bot to start
        bot_task = asyncio.create_task(bot.start(TOKEN))

        # Wait for 10 seconds or until the bot is ready
        try:
            await asyncio.wait_for(asyncio.shield(bot_task), timeout=10)
            logger.info("Bot started successfully within timeout!")
        except asyncio.TimeoutError:
            logger.error("Bot startup timed out after 10 seconds!")
            # Cancel the bot task
            bot_task.cancel()
            try:
                await bot_task
            except asyncio.CancelledError:
                logger.info("Bot task cancelled successfully")

        # Close the bot connection
        if bot.is_ready():
            logger.info("Bot is ready, closing connection...")
            await bot.close()
            logger.info("Bot connection closed")
        else:
            logger.warning("Bot was not ready, but we're closing it anyway")
            await bot.close()
            logger.info("Bot connection closed")

    except Exception as e:
        logger.error(f"Error during bot startup test: {e}")
        logger.error(f"Exception type: {type(e).__name__}")

    logger.info("Bot startup test completed")

if __name__ == "__main__":
    asyncio.run(test_startup())
