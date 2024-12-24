import json
from datetime import datetime, UTC  # Use UTC instead of utcnow
from typing import Dict, Any
import logging
from discord.ext import commands, tasks

class HealthMonitor:
    """Monitors bot health metrics and status"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.start_time = datetime.now(UTC)  # Use timezone-aware datetime
        self.command_count = 0
        self.error_count = 0
        self.last_error = None
        self.guilds_count = 0
        
        # Don't auto-start the task - we'll start it explicitly when needed
        self._setup_task()
    
    def _setup_task(self):
        """Setup the background task without starting it"""
        self.health_check = tasks.loop(minutes=5)(self._health_check)
    
    async def start(self):
        """Explicitly start the background task"""
        self.health_check.start()
    
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
        return {
            'uptime': self.get_uptime(),
            'guilds': len(self.bot.guilds),
            'commands_executed': self.command_count,
            'errors': self.error_count,
            'last_error': self.last_error,
            'latency': f"{self.bot.latency * 1000:.2f}ms"
        }
        
    async def _health_check(self):
        """Periodic health check task"""
        try:
            metrics = self.get_health_metrics()
            logging.info(f"Health check: {json.dumps(metrics, indent=2)}")
            
            # Alert on high error rate
            if self.error_count > 50:  # Configurable threshold
                logging.warning(f"High error rate detected: {self.error_count} errors")
        except Exception as e:
            logging.error(f"Error in health check: {str(e)}")