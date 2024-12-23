import discord
from discord import app_commands
from discord.ext import commands
from pathlib import Path
import json
from .rate_limiter import RateLimitedCog

class trmnl(RateLimitedCog):
    def __init__(self, bot) -> None:
        super().__init__(bot)  # Initialize the rate limiter
        self.bot = bot
        self.reload_docs()
    
    def reload_docs(self) -> None:
        """Reload the docs.json file"""
        docs_path = Path(__file__).parents[2] / "docs.json"
        with open(docs_path, 'r') as f:
            self.docs_data = json.load(f)

    @app_commands.command(
        name="sync",
        description="Sync all slash commands"
    )
    @app_commands.default_permissions(administrator=True)
    async def sync(self, interaction: discord.Interaction) -> None:
        """
        Sync all slash commands.
        Only administrators can use this command.
        """
        try:
            if not await self.handle_rate_limit(interaction, "sync"):
                return

            synced = await self.bot.tree.sync()
            embed = discord.Embed(
                title="Slash Commands Synced",
                description=f"Successfully synced {len(synced)} commands.",
                color=0x00FF00
            )
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await self.handle_command_error(interaction, e)

    @app_commands.command(
        name="reload_docs",
        description="Reload the docs.json file"
    )
    @app_commands.default_permissions(administrator=True)
    async def reload_docs_command(self, interaction: discord.Interaction) -> None:
        """
        Reload the docs.json file.
        Only administrators can use this command.
        """
        try:
            if not await self.handle_rate_limit(interaction, "reload_docs"):
                return

            self.reload_docs()
            embed = discord.Embed(
                title="Docs Reloaded",
                description="Successfully reloaded docs.json",
                color=0x00FF00
            )
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await self.handle_command_error(interaction, e)

    @app_commands.command(
        name="home",
        description="Get main TRMNL resources and information"
    )
    async def home(self, interaction: discord.Interaction) -> None:
        try:
            if not await self.handle_rate_limit(interaction, "home"):
                return

            doc = self.docs_data["docs"]["home"]
            embed = discord.Embed(
                title=doc["title"],
                description=doc["content"],
                color=0xBEBEFE
            )
            for name, url in doc["links"].items():
                embed.add_field(name=name, value=url, inline=False)
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await self.handle_command_error(interaction, e)

    @app_commands.command(
        name="docs",
        description="Get TRMNL documentation links"
    )
    async def docs(self, interaction: discord.Interaction) -> None:
        try:
            if not await self.handle_rate_limit(interaction, "docs"):
                return

            main_links = self.docs_data["categories"]["main"]["links"]
            embed = discord.Embed(
                title="TRMNL Documentation",
                description="Documentation and resource links:",
                color=0xBEBEFE
            )
            for name, url in main_links.items():
                embed.add_field(name=name, value=url, inline=False)
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await self.handle_command_error(interaction, e)

    @app_commands.command(
        name="framework",
        description="Get TRMNL framework documentation"
    )
    async def framework(self, interaction: discord.Interaction) -> None:
        try:
            if not await self.handle_rate_limit(interaction, "framework"):
                return

            doc = self.docs_data["docs"]["framework"]
            embed = discord.Embed(
                title=doc["title"],
                description=doc["content"],
                color=0xBEBEFE
            )
            for name, url in doc["links"].items():
                embed.add_field(name=name, value=url, inline=False)
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await self.handle_command_error(interaction, e)

    @app_commands.command(
        name="news",
        description="Get latest TRMNL news and updates"
    )
    async def news(self, interaction: discord.Interaction) -> None:
        try:
            if not await self.handle_rate_limit(interaction, "news"):
                return

            doc = self.docs_data["docs"]["news"]
            embed = discord.Embed(
                title=doc["title"],
                description=doc["content"],
                color=0xBEBEFE
            )
            for name, url in doc["links"].items():
                embed.add_field(name=name, value=url, inline=False)
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await self.handle_command_error(interaction, e)

    @app_commands.command(
        name="updates",
        description="Get all TRMNL blog posts and updates"
    )
    async def updates(self, interaction: discord.Interaction) -> None:
        try:
            if not await self.handle_rate_limit(interaction, "updates"):
                return

            blog_links = self.docs_data["categories"]["blog"]["links"]
            embed = discord.Embed(
                title="TRMNL Updates",
                description="All blog posts and updates:",
                color=0xBEBEFE
            )
            for name, url in blog_links.items():
                embed.add_field(name=name, value=url, inline=False)
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await self.handle_command_error(interaction, e)

    @app_commands.command(
        name="privacy",
        description="Get TRMNL privacy policy information"
    )
    async def privacy(self, interaction: discord.Interaction) -> None:
        try:
            if not await self.handle_rate_limit(interaction, "privacy"):
                return

            doc = self.docs_data["docs"]["privacy"]
            embed = discord.Embed(
                title=doc["title"],
                description=doc["content"],
                color=0xBEBEFE
            )
            for name, url in doc["links"].items():
                embed.add_field(name=name, value=url, inline=False)
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await self.handle_command_error(interaction, e)

    @app_commands.command(
        name="terms",
        description="Get TRMNL terms of service"
    )
    async def terms(self, interaction: discord.Interaction) -> None:
        try:
            if not await self.handle_rate_limit(interaction, "terms"):
                return

            legal_links = self.docs_data["categories"]["legal"]["links"]
            embed = discord.Embed(
                title="Terms of Service",
                description="TRMNL Terms of Service:",
                color=0xBEBEFE
            )
            embed.add_field(name="Terms of Service", value=legal_links["Terms of Service"], inline=False)
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await self.handle_command_error(interaction, e)

    @app_commands.command(
        name="diy",
        description="Get information about DIY TRMNL options"
    )
    async def diy(self, interaction: discord.Interaction) -> None:
        try:
            if not await self.handle_rate_limit(interaction, "diy"):
                return

            doc = self.docs_data["docs"]["diy"]
            embed = discord.Embed(
                title=doc["title"],
                description=doc["content"],
                color=0xBEBEFE
            )
            for name, url in doc["links"].items():
                embed.add_field(name=name, value=url, inline=False)
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await self.handle_command_error(interaction, e)

async def setup(bot) -> None:
    await bot.add_cog(trmnl(bot))