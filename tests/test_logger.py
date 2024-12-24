import pytest
import logging
from unittest.mock import MagicMock, patch
from src.bot.logger import BotLogger

@pytest.fixture
def mock_config():
    return {
        'log_level': 'INFO',
        'log_file': 'test.log'
    }

@pytest.fixture
def bot_logger(mock_config):
    return BotLogger(mock_config)

def test_logger_initialization(bot_logger):
    """Test that logger initializes correctly"""
    assert isinstance(bot_logger, BotLogger)
    assert bot_logger.config['log_level'] == 'INFO'

def test_logger_invalid_level(mock_config):
    """Test that logger handles invalid log level"""
    mock_config['log_level'] = 'INVALID'
    with pytest.raises(ValueError, match="Invalid log level"):
        BotLogger(mock_config)

def test_log_command(bot_logger, caplog):
    """Test command logging"""
    mock_ctx = MagicMock()
    mock_ctx.command.name = "test_command"
    mock_ctx.author.id = "123456"
    mock_ctx.author.__str__ = lambda x: "TestUser"
    mock_ctx.guild.name = "TestGuild"

    with caplog.at_level(logging.INFO):
        bot_logger.log_command(mock_ctx)
        assert "Command executed: test_command" in caplog.text
        assert "TestUser" in caplog.text
        assert "TestGuild" in caplog.text

def test_log_command_dm(bot_logger, caplog):
    """Test command logging in DM context"""
    mock_ctx = MagicMock()
    mock_ctx.command.name = "test_command"
    mock_ctx.author.id = "123456"
    mock_ctx.author.__str__ = lambda x: "TestUser"
    mock_ctx.guild = None

    with caplog.at_level(logging.INFO):
        bot_logger.log_command(mock_ctx)
        assert "Command executed: test_command" in caplog.text
        assert "DM" in caplog.text