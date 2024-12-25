import logging
import os
import platform
import sys
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

class DiscordBot(commands.Bot):
    def __init__(self) -> None:
        super().__init__(
            command_prefix=os.getenv('BOT_PREFIX', '!'),
            intents=intents,
            help_command=None,
        )
        # Use environment variables instead of config.json
        self.config = {
            'prefix': os.getenv('BOT_PREFIX', '!'),
            'feedback_channel_id': os.getenv('FEEDBACK_CHANNEL_ID'),
            'health_report_channel_id': os.getenv('HEALTH_REPORT_CHANNEL_ID'),
            'log_level': os.getenv('LOG_LEVEL', 'INFO'),
            'log_file': None  # Use console logging for Heroku
        }
        self.feedback_channel_id = self.config.get('feedback_channel_id')

    async def setup_hook(self) -> None:
        """
        This will just be executed when the bot starts the first time.
        """
        print(f"Logged in as {self.user.name}")
        print(f"discord.py API version: {discord.__version__}")
        print(f"Python version: {platform.python_version()}")
        print("-------------------")
        
        # Load extensions - health must be loaded first
        await self.load_extension("src.bot.health")
        
        self.health = self.get_cog("HealthMonitor")
        
        await self.load_extension("src.bot.trmnl")
        
        print("Starting command sync...")
        try:
            print("Syncing commands...")
            synced = await self.tree.sync()
            print(f"Synced {len(synced)} commands")
        except Exception as e:
            print(f"Error syncing commands: {str(e)}")

    async def on_tree_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError) -> None:
        if interaction.response.is_done():
            await interaction.followup.send(f'An error occurred: {error}', ephemeral=True)
        else:
            await interaction.response.send_message(f'An error occurred: {error}', ephemeral=True)

bot = DiscordBot()
bot.run(os.getenv("DISCORD_TOKEN"))