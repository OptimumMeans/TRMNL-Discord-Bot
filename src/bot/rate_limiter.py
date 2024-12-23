from discord.ext import commands
import discord
from discord import app_commands
from typing import Dict, Optional
import time
import asyncio
from collections import defaultdict

class DiscordRateLimit:
    """Represents a Discord rate limit bucket"""
    def __init__(self, limit: int, remaining: int, reset_after: float, bucket: str):
        self.limit = limit
        self.remaining = remaining
        self.reset_after = reset_after
        self.reset_at = time.time() + reset_after
        self.bucket = bucket

class RateLimitManager:
    def __init__(self):
        # Global rate limit (50 requests per second per bot)
        self.global_limit = 50
        self.global_remaining = 50
        self.global_reset = time.time() + 1.0
        
        # Store rate limits by bucket ID
        self.buckets: Dict[str, DiscordRateLimit] = {}
        
        # Track invalid requests to prevent Cloudflare bans (10,000 per 10 minutes)
        self.invalid_requests = 0
        self.invalid_reset = time.time() + 600  # 10 minutes
        
    def update_rate_limits(self, headers: Dict[str, str]) -> None:
        """Update rate limit info from Discord response headers"""
        try:
            # Get rate limit info from headers
            limit = int(headers.get('X-RateLimit-Limit', 0))
            remaining = int(headers.get('X-RateLimit-Remaining', 0))
            reset_after = float(headers.get('X-RateLimit-Reset-After', 0))
            bucket = headers.get('X-RateLimit-Bucket', '')
            
            if bucket and limit:
                self.buckets[bucket] = DiscordRateLimit(
                    limit=limit,
                    remaining=remaining,
                    reset_after=reset_after,
                    bucket=bucket
                )
        except (ValueError, TypeError) as e:
            print(f"Error parsing rate limit headers: {e}")

    def check_rate_limit(self, bucket: str) -> Optional[float]:
        """
        Check if request would hit rate limit
        Returns: None if request can proceed, float seconds to wait if rate limited
        """
        now = time.time()
        
        # Check global rate limit
        if now >= self.global_reset:
            self.global_remaining = self.global_limit
            self.global_reset = now + 1.0
            
        if self.global_remaining <= 0:
            return self.global_reset - now
            
        # Check bucket-specific rate limit
        if bucket in self.buckets:
            rate_limit = self.buckets[bucket]
            if now >= rate_limit.reset_at:
                rate_limit.remaining = rate_limit.limit
                rate_limit.reset_at = now + rate_limit.reset_after
            
            if rate_limit.remaining <= 0:
                return rate_limit.reset_at - now
                
            rate_limit.remaining -= 1
            
        self.global_remaining -= 1
        return None

    def track_invalid_request(self) -> bool:
        """
        Track invalid requests to prevent Cloudflare bans
        Returns: True if requests should be paused
        """
        now = time.time()
        if now >= self.invalid_reset:
            self.invalid_requests = 0
            self.invalid_reset = now + 600
            
        self.invalid_requests += 1
        return self.invalid_requests >= 10000

class RateLimitedCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.rate_limiter = RateLimitManager()
        
    async def handle_rate_limit(self, interaction: discord.Interaction, bucket: str) -> bool:
        """
        Handle rate limiting for a command interaction
        Returns: True if command should proceed, False if rate limited
        """
        # Check rate limits
        retry_after = self.rate_limiter.check_rate_limit(bucket)
        
        if retry_after:
            embed = discord.Embed(
                title="Rate Limited",
                description=f"Please wait {retry_after:.1f} seconds before using this command again.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return False
            
        return True
        
    async def handle_command_error(self, interaction: discord.Interaction, error: Exception):
        """Handle command errors and track invalid requests"""
        try:
            if isinstance(error, (discord.Forbidden, discord.NotFound)):
                # Track 403 and 404 responses
                if self.rate_limiter.track_invalid_request():
                    print("WARNING: Approaching invalid request limit!")

            error_message = "An error occurred processing your command."
            
            try:
                if interaction.response.is_done():
                    await interaction.followup.send(error_message, ephemeral=True)
                else:
                    await interaction.response.send_message(error_message, ephemeral=True)
            except discord.errors.NotFound:
                # If interaction is completely invalid, we can't respond
                print(f"Could not respond to interaction: {error}")
                
        except Exception as e:
            print(f"Error in error handler: {e}")