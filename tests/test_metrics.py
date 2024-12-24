import pytest
from datetime import datetime
from src.bot.trmnl import TRMNLMetrics

@pytest.fixture
def metrics():
    return TRMNLMetrics()

def test_metrics_initialization(metrics):
    """Test metrics system initialization"""
    assert metrics.command_usage == {}
    assert metrics.admin_usage == {}
    assert metrics.last_errors == []

def test_command_logging(metrics):
    """Test command usage tracking"""
    metrics.log_command("test", "user123")
    assert "test" in metrics.command_usage
    assert len(metrics.command_usage["test"]) == 1
    
    command_log = metrics.command_usage["test"][0]
    assert command_log["user_id"] == "user123"
    assert isinstance(command_log["timestamp"], str)

def test_admin_action_logging(metrics):
    """Test admin action tracking"""
    metrics.log_admin_action("sync", "admin123")
    assert "sync" in metrics.admin_usage
    assert len(metrics.admin_usage["sync"]) == 1
    
    admin_log = metrics.admin_usage["sync"][0]
    assert admin_log["user_id"] == "admin123"
    assert isinstance(admin_log["timestamp"], str)

def test_error_logging(metrics):
    """Test error tracking"""
    error = Exception("test error")
    metrics.log_error(error, "test_command")
    
    assert len(metrics.last_errors) == 1
    error_log = metrics.last_errors[0]
    assert error_log["error"] == "test error"
    assert error_log["command"] == "test_command"
    assert isinstance(error_log["timestamp"], str)

def test_error_limit(metrics):
    """Test error list size limit"""
    for i in range(150):  # Over 100 limit
        metrics.log_error(Exception(f"error {i}"), "test")
    assert len(metrics.last_errors) == 100