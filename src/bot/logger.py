import logging
import sys
from typing import Dict, Any, Optional
from discord.ext import commands

class BotLogger:
    """Handles bot logging configuration and management"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging with validation"""
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        # Validate log level
        level = self.config.get('log_level', 'INFO').upper()
        if level not in ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'):
            raise ValueError(f"Invalid log level: {level}")
            
        # Configure root logger - modified for Heroku
        logging.basicConfig(
            level=getattr(logging, level),
            format=log_format,
            handlers=[
                logging.StreamHandler()  # Only use StreamHandler for Heroku
            ]
        )
        
        # Create discord.py logger
        discord_logger = logging.getLogger('discord')
        discord_logger.setLevel(logging.INFO)
        
        logging.info("Logging system initialized")
        
    def log_command(self, ctx: commands.Context):
        """Log command execution"""
        logging.info(
            f"Command executed: {ctx.command.name} "
            f"by {ctx.author} ({ctx.author.id}) "
            f"in {ctx.guild.name if ctx.guild else 'DM'}"
        )
        
    def log_error(self, error: Exception, ctx: Optional[commands.Context] = None):
        """Log error with context if available"""
        if ctx:
            logging.error(
                f"Error in command {ctx.command.name}: {str(error)} "
                f"by {ctx.author} in {ctx.guild.name if ctx.guild else 'DM'}"
            )
        else:
            logging.error(f"Error: {str(error)}")