import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime, timedelta, time, UTC
import discord
import logging
from src.bot.health import HealthMonitor

@pytest.fixture
def mock_bot():
    bot = MagicMock()
    bot.latency = 0.05  # 50ms latency
    bot.guilds = [MagicMock(), MagicMock()]  # 2 guilds
    bot.config = {'health_report_channel_id': '123456789'}
    bot.fetch_channel = AsyncMock()
    return bot

@pytest.fixture
def health_monitor(mock_bot, caplog):
    """Create HealthMonitor with logging setup"""
    caplog.set_level(logging.INFO)  # Change to INFO to capture all logs
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

@pytest.mark.asyncio
async def test_high_error_rate_warning(health_monitor, caplog):
    """Test high error rate warning"""
    # Generate errors
    for _ in range(51):
        health_monitor.log_error(Exception("Test error"))
    
    # Mock the metrics to ensure high error rate
    metrics = health_monitor.get_health_metrics()
    
    # Test the actual health check
    await health_monitor._health_check()
    
    # Check the log message
    assert any("Health check" in record.message for record in caplog.records)

@pytest.mark.asyncio
async def test_daily_report(health_monitor):
    """Test daily report generation"""
    # Mock the channel
    mock_channel = AsyncMock()
    health_monitor.bot.fetch_channel.return_value = mock_channel
    
    # Send report
    await health_monitor._send_daily_report()
    
    # Verify report was sent
    assert mock_channel.send.called
    call_args = mock_channel.send.call_args
    assert isinstance(call_args[1]['embed'], discord.Embed)
    assert "Daily Health Report" in call_args[1]['embed'].title

@pytest.mark.asyncio
async def test_threshold_alerts(health_monitor):
    """Test alert generation for threshold violations"""
    # Mock the channel
    mock_channel = AsyncMock()
    health_monitor.bot.fetch_channel.return_value = mock_channel
    
    # Set threshold and trigger violation
    health_monitor.alert_thresholds['error_rate'] = 10
    for _ in range(20):  # Generate enough errors to trigger alert
        health_monitor.log_error(Exception("Test error"))
    
    # Check thresholds
    await health_monitor._check_thresholds()
    
    # Verify alert was sent
    assert mock_channel.send.called
    call_args = mock_channel.send.call_args
    assert isinstance(call_args[1]['embed'], discord.Embed)
    assert "Health Alert" in call_args[1]['embed'].title

@pytest.mark.asyncio
async def test_hourly_command_rate(health_monitor):
    """Test hourly command rate calculation"""
    # Set start time to 1 hour ago
    health_monitor.start_time = datetime.now(UTC) - timedelta(hours=1)
    
    # Add 100 commands
    for _ in range(100):
        health_monitor.increment_commands()
    
    # Check rate
    rate = health_monitor._get_hourly_command_rate()
    assert rate == 100.0  # Should be exactly 100 commands per hour

@pytest.mark.asyncio
async def test_report_channel_not_found(health_monitor, caplog):
    """Test handling of missing report channel"""
    caplog.set_level(logging.ERROR)  # Ensure we capture ERROR logs
    health_monitor.report_channel_id = "999999999"  # Non-existent channel
    health_monitor.bot.fetch_channel.return_value = None
    
    # Attempt to send report
    await health_monitor._send_daily_report()
    
    # Verify error was logged
    assert any("Could not find health report channel" in record.message
              for record in caplog.records)

def test_alert_thresholds_configuration(health_monitor):
    """Test alert thresholds configuration"""
    assert isinstance(health_monitor.alert_thresholds, dict)
    assert 'error_rate' in health_monitor.alert_thresholds
    assert 'command_rate' in health_monitor.alert_thresholds
    assert 'latency' in health_monitor.alert_thresholds
    assert 'guild_change' in health_monitor.alert_thresholds
    
    # Verify threshold values are positive numbers
    for threshold in health_monitor.alert_thresholds.values():
        assert threshold > 0