import logging
import discord
from discord import app_commands

logger = logging.getLogger('tokugawa_bot')

class CommandRegistrar:
    """
    A utility class for registering commands with the bot's command tree.
    This class follows the Single Responsibility Principle by separating
    command registration logic from the cogs themselves.
    """

    @staticmethod
    async def register_commands(bot, cog):
        """
        Register all commands from a cog with the bot's command tree.
        
        Args:
            bot: The Discord bot instance
            cog: The cog containing commands to register
        """
        # Register command groups
        for attr_name in dir(cog):
            attr = getattr(cog, attr_name)
            if isinstance(attr, app_commands.Group):
                try:
                    bot.tree.add_command(attr)
                    logger.info(f"Added command group to command tree: /{attr.name}")
                except app_commands.errors.CommandAlreadyRegistered:
                    logger.info(f"Command group already registered: /{attr.name}")
        
        # Log all slash commands that were added through decorators
        for cmd in getattr(cog, "__cog_app_commands__", []):
            logger.info(f"{cog.__class__.__name__} cog added slash command: /{cmd.name}")