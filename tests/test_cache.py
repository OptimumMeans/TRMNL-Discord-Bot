import pytest
import asyncio
from src.bot.trmnl import DocCache

@pytest.fixture
def cache():
    return DocCache(ttl_seconds=1)

def test_cache_initialization(cache):
    """Test cache is properly initialized"""
    assert cache.ttl == 1
    assert cache.cache == {}
    assert cache.last_update == 0

def test_cache_update(cache):
    """Test cache update functionality"""
    test_data = {"test": "data"}
    cache.update(test_data)
    assert cache.get("test") == "data"
    assert cache.last_update > 0

@pytest.mark.asyncio
async def test_cache_ttl(cache):
    """Test cache TTL functionality"""
    test_data = {"test": "data"}
    cache.update(test_data)
    assert not cache.needs_refresh()
    
    await asyncio.sleep(1.1)
    assert cache.needs_refresh()

def test_cache_missing_key(cache):
    """Test handling of missing cache keys"""
    assert cache.get("nonexistent") is None