import discord
from discord import app_commands
from discord.ext import commands
from pathlib import Path
import json
import time
from typing import Optional, Dict
from datetime import datetime
from .rate_limiter import RateLimitedCog
from .logger import BotLogger
from .health import HealthMonitor
import logging
from datetime import UTC

class TrmnlBot:
    def __init__(self, config):
        self.config = config
        
        # Initialize logging and health monitoring
        intents = discord.Intents.default()
        intents.message_content = True
        
        self.bot = commands.Bot(
            command_prefix=config.get('prefix', '!'),
            intents=intents
        )
        
        # Create logger
        self.logger = BotLogger(config)
        
        # Set up event handlers
        @self.bot.event
        async def on_command(ctx):
            self.logger.log_command(ctx)
            # Health monitor will be available via bot.health after setup
            if hasattr(self.bot, 'health'):
                self.bot.health.increment_commands()

        @self.bot.event
        async def on_command_error(ctx, error):
            self.logger.log_error(error, ctx)
            if hasattr(self.bot, 'health'):
                self.bot.health.log_error(error)
            
            if isinstance(error, commands.CommandNotFound):
                await ctx.send("Command not found.")
            elif isinstance(error, commands.MissingPermissions):
                await ctx.send("You don't have permission to use this command.")

class TRMNLMetrics:
    def __init__(self):
        self.command_usage = {}
        self.admin_usage = {}
        self.last_errors = []
        
    def log_command(self, command_name: str, user_id: str):
        if command_name not in self.command_usage:
            self.command_usage[command_name] = []
        self.command_usage[command_name].append({
            'timestamp': datetime.now().isoformat(),
            'user_id': user_id
        })
        
    def log_admin_action(self, command_name: str, user_id: str):
        if command_name not in self.admin_usage:
            self.admin_usage[command_name] = []
        self.admin_usage[command_name].append({
            'timestamp': datetime.now().isoformat(),
            'user_id': user_id
        })

    def log_error(self, error: Exception, command_name: str):
        self.last_errors.append({
            'timestamp': datetime.now().isoformat(),
            'command': command_name,
            'error': str(error)
        })
        self.last_errors = self.last_errors[-100:]

class DocCache:
    def __init__(self, ttl_seconds: int = 3600):
        self.cache = {}
        self.ttl = ttl_seconds
        self.last_update = 0
        
    def needs_refresh(self) -> bool:
        return time.time() - self.last_update > self.ttl
        
    def update(self, docs_data: dict):
        self.cache = docs_data
        self.last_update = time.time()
        
    def get(self, key: str) -> Optional[dict]:
        return self.cache.get(key)

class TRMNL(RateLimitedCog):
    def __init__(self, bot) -> None:
        super().__init__(bot)
        self.bot = bot
        self.metrics = TRMNLMetrics()
        self.doc_cache = DocCache()
        
        # Initialize feedback channel ID with proper logging
        self.feedback_channel_id = self.bot.config.get('feedback_channel_id')
        if self.feedback_channel_id:
            logging.info(f"Feedback channel configured with ID: {self.feedback_channel_id}")
        else:
            logging.warning("No feedback channel ID configured in config.json")
            
        self.load_docs()
        
    def load_docs(self) -> None:
        """Load or reload the docs.json file"""
        if not self.doc_cache.needs_refresh() and self.doc_cache.cache:
            return  # Use cached data if it's still valid
            
        docs_path = Path(__file__).parents[2] / "docs.json"
        with open(docs_path, 'r') as f:
            docs_data = json.load(f)
            self.doc_cache.update(docs_data)
            self.docs_data = docs_data  # Keep for backward compatibility

    @app_commands.command(name="sync", description="Sync all slash commands")
    @app_commands.default_permissions(administrator=True)
    async def sync(self, interaction: discord.Interaction) -> None:
        """
        Sync all slash commands.
        Only administrators can use this command.
        """
        try:
            if not await self.handle_rate_limit(interaction, "sync"):
                return

            # Defer the response to prevent timeout
            await interaction.response.defer(ephemeral=True)
            
            # Sync commands
            synced = await self.bot.tree.sync()
            
            # Send the follow-up
            embed = discord.Embed(
                title="Slash Commands Synced",
                description=f"Successfully synced {len(synced)} commands.",
                color=0x00FF00
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            self.metrics.log_admin_action("sync", str(interaction.user.id))
            
        except Exception as e:
            try:
                await interaction.followup.send(
                    "An error occurred while syncing commands.",
                    ephemeral=True
                )
            except:
                if not interaction.response.is_done():
                    await interaction.response.send_message(
                        "An error occurred while syncing commands.",
                        ephemeral=True
                    )
            self.metrics.log_error(e, "sync")

    @app_commands.command(name="reload_docs", description="Reload the docs.json file")
    @app_commands.default_permissions(administrator=True)
    async def reload_docs_command(self, interaction: discord.Interaction) -> None:
        try:
            if not await self.handle_rate_limit(interaction, "reload_docs"):
                return

            self.load_docs()
            embed = discord.Embed(
                title="Docs Reloaded",
                description="Successfully reloaded docs.json",
                color=0x00FF00
            )
            await interaction.response.send_message(embed=embed)
            self.metrics.log_admin_action("reload_docs", str(interaction.user.id))
        except Exception as e:
            await self.handle_command_error(interaction, e)

    @app_commands.command(name="status", description="Show bot status and latency")
    async def status(self, interaction: discord.Interaction) -> None:
        try:
            if not await self.handle_rate_limit(interaction, "status"):
                return

            latency = round(self.bot.latency * 1000)
            command_count = sum(len(usages) for usages in self.metrics.command_usage.values())
            
            embed = discord.Embed(
                title="TRMNL Bot Status",
                color=discord.Color.green()
            )
            embed.add_field(name="Latency", value=f"{latency}ms")
            embed.add_field(name="Commands Used", value=str(command_count))
            
            await interaction.response.send_message(embed=embed)
            self.metrics.log_command("status", str(interaction.user.id))
        except Exception as e:
            self.metrics.log_error(e, "status")
            await self.handle_command_error(interaction, e)

    @app_commands.command(name="search", description="Search TRMNL documentation")
    async def search(self, interaction: discord.Interaction, query: str) -> None:
        try:
            if not await self.handle_rate_limit(interaction, "search"):
                return

            if len(query) < 2:
                embed = discord.Embed(
                    title="Invalid Search",
                    description="Search query must be at least 2 characters long.",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(
                    embed=embed,
                    ephemeral=True
                )
                return
                
            results = []
            for category in self.docs_data["categories"].values():
                for name, url in category.get("links", {}).items():
                    if query.lower() in name.lower():
                        results.append((name, url))
                        
            embed = discord.Embed(
                title=f"Search Results for '{query}'",
                color=discord.Color.blue()
            )
            
            if results:
                for name, url in results[:5]:
                    embed.add_field(name=name, value=url, inline=False)
            else:
                embed.description = "No results found."
                
            await interaction.response.send_message(embed=embed)
            self.metrics.log_command("search", str(interaction.user.id))
        except Exception as e:
            self.metrics.log_error(e, "search")
            await self.handle_command_error(interaction, e)

    @app_commands.command(name="home", description="Get main TRMNL resources and information")
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
            self.metrics.log_command("home", str(interaction.user.id))
        except Exception as e:
            self.metrics.log_error(e, "home")
            await self.handle_command_error(interaction, e)

    @app_commands.command(name="docs", description="Get TRMNL documentation links")
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
            self.metrics.log_command("docs", str(interaction.user.id))
        except Exception as e:
            self.metrics.log_error(e, "docs")
            await self.handle_command_error(interaction, e)

    @app_commands.command(name="framework", description="Get TRMNL framework documentation")
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
            self.metrics.log_command("framework", str(interaction.user.id))
        except Exception as e:
            self.metrics.log_error(e, "framework")
            await self.handle_command_error(interaction, e)

    @app_commands.command(name="news", description="Get latest TRMNL news and updates")
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
            self.metrics.log_command("news", str(interaction.user.id))
        except Exception as e:
            self.metrics.log_error(e, "news")
            await self.handle_command_error(interaction, e)

    @app_commands.command(name="updates", description="Get all TRMNL blog posts and updates")
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
            self.metrics.log_command("updates", str(interaction.user.id))
        except Exception as e:
            self.metrics.log_error(e, "updates")
            await self.handle_command_error(interaction, e)

    @app_commands.command(name="privacy", description="Get TRMNL privacy policy information")
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
            self.metrics.log_command("privacy", str(interaction.user.id))
        except Exception as e:
            self.metrics.log_error(e, "privacy")
            await self.handle_command_error(interaction, e)

    @app_commands.command(name="terms", description="Get TRMNL terms of service")
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
            self.metrics.log_command("terms", str(interaction.user.id))
        except Exception as e:
            self.metrics.log_error(e, "terms")
            await self.handle_command_error(interaction, e)

    @app_commands.command(name="diy", description="Get information about DIY TRMNL options")
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
            self.metrics.log_command("diy", str(interaction.user.id))
        except Exception as e:
            self.metrics.log_error(e, "diy")
            await self.handle_command_error(interaction, e)

    @app_commands.command(name="changelog", description="Show recent bot updates")
    async def changelog(self, interaction: discord.Interaction) -> None:
        try:
            if not await self.handle_rate_limit(interaction, "changelog"):
                return

            with open('UPDATES.md', 'r') as f:
                content = f.read()
                
            embed = discord.Embed(
                title="TRMNL Bot Changelog",
                color=discord.Color.blue()
            )
            
            version_info = content.split('##')[1] if '##' in content else content
            embed.description = version_info[:4000]  # Discord embed limit
            
            await interaction.response.send_message(embed=embed)
            self.metrics.log_command("changelog", str(interaction.user.id))
        except Exception as e:
            self.metrics.log_error(e, "changelog")
            await self.handle_command_error(interaction, e)

    @app_commands.command(name="support", description="Get TRMNL support information")
    async def support(self, interaction: discord.Interaction) -> None:
        try:
            if not await self.handle_rate_limit(interaction, "support"):
                return

            embed = discord.Embed(
                title="TRMNL Support",
                description="Need help with TRMNL? Here's how to get support:",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="Documentation",
                value="https://docs.usetrmnl.com",
                inline=False
            )
            embed.add_field(
                name="Discord Community",
                value="https://discord.gg/trmnl",
                inline=False
            )
            
            await interaction.response.send_message(embed=embed)
            self.metrics.log_command("support", str(interaction.user.id))
        except Exception as e:
            self.metrics.log_error(e, "support")
            await self.handle_command_error(interaction, e)

    @app_commands.command(name="feedback", description="Submit feedback about TRMNL")
    async def feedback(self, interaction: discord.Interaction, message: str) -> None:
        try:
            if not await self.handle_rate_limit(interaction, "feedback"):
                return

            if len(message) < 10:
                embed = discord.Embed(
                    title="Invalid Feedback",
                    description="Feedback message must be at least 10 characters long.",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(
                    embed=embed,
                    ephemeral=True
                )
                return
            
            # Acknowledge the feedback first
            await interaction.response.send_message(
                "Thank you for your feedback!",
                ephemeral=True
            )
            
            # Then handle the feedback channel
            if self.feedback_channel_id:
                try:
                    feedback_channel = await self.bot.fetch_channel(int(self.feedback_channel_id))
                    if feedback_channel:
                        embed = discord.Embed(
                            title="User Feedback",
                            description=message,
                            color=discord.Color.blue(),
                            timestamp=datetime.now(UTC)
                        )
                        embed.set_footer(text=f"From: {interaction.user.name} ({interaction.user.id})")
                        embed.add_field(name="Server", value=interaction.guild.name if interaction.guild else "DM", inline=True)
                        
                        await feedback_channel.send(embed=embed)
                        logging.info(f"Feedback sent to channel {self.feedback_channel_id}")
                    else:
                        logging.error(f"Could not find feedback channel with ID {self.feedback_channel_id}")
                except Exception as e:
                    logging.error(f"Error sending feedback to channel: {str(e)}")
            else:
                logging.warning("No feedback channel configured")
                
            self.metrics.log_command("feedback", str(interaction.user.id))
        except Exception as e:
            self.metrics.log_error(e, "feedback")
            await self.handle_command_error(interaction, e)
            
    @app_commands.command(name="health", description="Get bot health metrics")
    @app_commands.default_permissions(administrator=True)
    async def health(self, interaction: discord.Interaction) -> None:
        """Get current bot health metrics"""
        try:
            if not await self.handle_rate_limit(interaction, "health"):
                return
                
            metrics = self.bot.health.get_health_metrics()
            
            embed = discord.Embed(
                title="TRMNL Bot Health Metrics",
                color=discord.Color.blue(),
                timestamp=interaction.created_at
            )
            
            for key, value in metrics.items():
                if key == 'last_error' and value:
                    embed.add_field(
                        name=key.replace('_', ' ').title(),
                        value=f"```{value['error']}\nat {value['time']}```",
                        inline=False
                    )
                else:
                    embed.add_field(
                        name=key.replace('_', ' ').title(),
                        value=str(value),
                        inline=True)
            
            await interaction.response.send_message(embed=embed)
            self.metrics.log_command("health", str(interaction.user.id))
        except Exception as e:
            self.metrics.log_error(e, "health")
            await self.handle_command_error(interaction, e)
            
    @app_commands.command(
        name="pipeline",
        description="See upcoming TRMNL features and releases"
    )
    async def pipeline(self, interaction: discord.Interaction) -> None:
        try:
            if not await self.handle_rate_limit(interaction, "pipeline"):
                return

            doc = self.docs_data["docs"]["pipeline"]
            embed = discord.Embed(
                title=doc["title"],
                description=doc["content"],
                color=0x7289DA  # Discord Blurple color
            )
            
            # Add roadmap and feedback links if available
            for name, url in doc["links"].items():
                embed.add_field(name=name, value=url, inline=False)
            
            # Add a note about changelog
            embed.add_field(
                name="Want to see past updates?",
                value="Use `/changelog` to view released updates!",
                inline=False
            )
            
            embed.set_footer(text="Release dates are tentative and subject to change.")
            
            await interaction.response.send_message(embed=embed)
            self.metrics.log_command("pipeline", str(interaction.user.id))
            
        except Exception as e:
            self.metrics.log_error(e, "pipeline")
            await self.handle_command_error(interaction, e)

async def setup(bot) -> None:
    await bot.add_cog(TRMNL(bot))