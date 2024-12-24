import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta, UTC
import discord
import logging
from src.bot.health import HealthMonitor

@pytest.fixture
def mock_bot():
    bot = MagicMock()
    bot.latency = 0.05  # 50ms latency
    bot.guilds = [MagicMock(), MagicMock()]  # 2 guilds
    return bot

@pytest.fixture
def health_monitor(mock_bot, caplog):
    """Create HealthMonitor with logging setup"""
    # Ensure logging is set up for testing
    caplog.set_level(logging.WARNING)
    monitor = HealthMonitor(mock_bot)
    return monitor

def test_health_monitor_initialization(health_monitor):
    """Test initial state of health monitor"""
    assert health_monitor.command_count == 0
    assert health_monitor.error_count == 0
    assert health_monitor.last_error is None
    assert isinstance(health_monitor.start_time, datetime)

def test_increment_commands(health_monitor):
    """Test command counter"""
    initial_count = health_monitor.command_count
    health_monitor.increment_commands()
    assert health_monitor.command_count == initial_count + 1

def test_log_error(health_monitor):
    """Test error logging"""
    test_error = Exception("Test error")
    health_monitor.log_error(test_error)
    
    assert health_monitor.error_count == 1
    assert health_monitor.last_error is not None
    assert "Test error" in health_monitor.last_error['error']
    assert 'time' in health_monitor.last_error

def test_get_uptime(health_monitor):
    """Test uptime calculation"""
    # Mock the start time to be 2 hours ago
    health_monitor.start_time = datetime.now(UTC) - timedelta(hours=2)
    uptime = health_monitor.get_uptime()
    
    assert "2h" in uptime
    assert "0m" in uptime

def test_get_health_metrics(health_monitor):
    """Test health metrics generation"""
    metrics = health_monitor.get_health_metrics()
    
    assert 'uptime' in metrics
    assert 'guilds' in metrics
    assert metrics['guilds'] == 2  # From our mock bot
    assert 'commands_executed' in metrics
    assert 'errors' in metrics
    assert 'latency' in metrics
    assert '50.00ms' in metrics['latency']  # From our mock bot

@pytest.mark.asyncio
async def test_health_check(health_monitor):
    """Test health check method directly"""
    with patch.object(health_monitor, 'get_health_metrics') as mock_metrics:
        mock_metrics.return_value = {'test': 'metrics'}
        await health_monitor._health_check()
    
    # We don't test logging directly as it's covered by caplog tests elsewhere

@pytest.mark.asyncio
async def test_high_error_rate_warning(health_monitor, caplog):
    """Test high error rate warning"""
    # Generate errors
    for _ in range(51):
        health_monitor.log_error(Exception("Test error"))
        
    # Test the actual health check
    await health_monitor._health_check()  # Now properly awaited
    
    # The log message should now be captured
    assert "High error rate detected" in caplog.text
    assert "51 errors" in caplog.text