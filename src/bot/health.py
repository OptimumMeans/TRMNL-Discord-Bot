import json
from datetime import datetime, timedelta, time, UTC
from typing import Dict, Any, Optional
import logging
import discord
from discord.ext import commands, tasks
from discord import app_commands

class HealthMonitor(commands.Cog):
    """Monitors bot health metrics and status with automated reporting"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.start_time = datetime.now(UTC)
        self.command_count = 0
        self.error_count = 0
        self.last_error = None
        self.guilds_count = 0
        self.last_report_time = None
        self.report_channel_id = self.bot.config.get('health_report_channel_id')
        self.alert_thresholds = {
            'error_rate': 50,  # Errors per hour
            'command_rate': 1000,  # Commands per hour
            'latency': 500,  # ms
            'guild_change': 10,  # Percent change
        }
        
        self._setup_tasks()
    
    def _setup_tasks(self):
        """Setup all background tasks"""
        self.health_check = tasks.loop(minutes=5)(self._health_check)
        self.daily_report = tasks.loop(time=time(0, 0))(self._send_daily_report)
        self.hourly_check = tasks.loop(hours=1)(self._check_thresholds)
    
    async def start(self):
        """Explicitly start all background tasks"""
        self.health_check.start()
        self.daily_report.start()
        self.hourly_check.start()
        
    def increment_commands(self):
        self.command_count += 1
        
    def log_error(self, error: Exception):
        self.error_count += 1
        self.last_error = {
            'error': str(error),
            'time': datetime.now(UTC).isoformat()
        }
    
    def get_uptime(self) -> str:
        delta = datetime.now(UTC) - self.start_time
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours}h {minutes}m {seconds}s"
    
    def get_health_metrics(self) -> Dict[str, Any]:
        """Get current health metrics"""
        return {
            'uptime': self.get_uptime(),
            'guilds': len(self.bot.guilds),
            'commands_executed': self.command_count,
            'errors': self.error_count,
            'last_error': self.last_error,
            'latency': f"{self.bot.latency * 1000:.2f}ms",
            'commands_per_hour': self._get_hourly_command_rate(),
            'errors_per_hour': self._get_hourly_error_rate()
        }

    def _get_hourly_command_rate(self) -> float:
        """Calculate commands per hour"""
        uptime_hours = (datetime.now(UTC) - self.start_time).total_seconds() / 3600
        return self.command_count / max(1, uptime_hours)

    def _get_hourly_error_rate(self) -> float:
        """Calculate errors per hour"""
        uptime_hours = (datetime.now(UTC) - self.start_time).total_seconds() / 3600
        return self.error_count / max(1, uptime_hours)

    async def _send_report(self, embed: discord.Embed) -> bool:
        """Send a report to the designated channel"""
        if not self.report_channel_id:
            logging.warning("No health report channel configured")
            return False
            
        try:
            channel = await self.bot.fetch_channel(int(self.report_channel_id))
            if not channel:
                logging.error(f"Could not find health report channel: {self.report_channel_id}")
                return False
                
            await channel.send(embed=embed)
            return True
        except Exception as e:
            logging.error(f"Failed to send health report: {str(e)}")
            return False

    async def _send_daily_report(self):
        """Send daily health report"""
        metrics = self.get_health_metrics()
        
        embed = discord.Embed(
            title="Daily Health Report",
            description=f"Report for {datetime.now(UTC).strftime('%Y-%m-%d')}",
            color=discord.Color.blue()
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
                    inline=True
                )
                
        await self._send_report(embed)
        self.last_report_time = datetime.now(UTC)

    async def _check_thresholds(self):
        """Check metrics against alert thresholds"""
        metrics = self.get_health_metrics()
        alerts = []
        
        # Check error rate
        if metrics['errors_per_hour'] > self.alert_thresholds['error_rate']:
            alerts.append(f"High error rate: {metrics['errors_per_hour']:.1f}/hour")
            
        # Check command rate
        if metrics['commands_per_hour'] > self.alert_thresholds['command_rate']:
            alerts.append(f"High command rate: {metrics['commands_per_hour']:.1f}/hour")
            
        # Check latency
        latency = float(metrics['latency'].replace('ms', ''))
        if latency > self.alert_thresholds['latency']:
            alerts.append(f"High latency: {latency:.1f}ms")
            
        if alerts:
            embed = discord.Embed(
                title="⚠️ Health Alert",
                description="\n".join(alerts),
                color=discord.Color.red()
            )
            await self._send_report(embed)
        
    async def _health_check(self):
        """Periodic health check task"""
        try:
            metrics = self.get_health_metrics()
            logging.info(f"Health check: {json.dumps(metrics, indent=2)}")
        except Exception as e:
            logging.error(f"Error in health check: {str(e)}")

async def setup(bot):
    """Setup function for the extension"""
    health_monitor = HealthMonitor(bot)
    await bot.add_cog(health_monitor)
    await health_monitor.start()
    bot.health = health_monitor  # Store reference for access from other cogs