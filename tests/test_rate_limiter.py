import pytest
import time
import asyncio
from src.bot.rate_limiter import RateLimitManager, DiscordRateLimit

@pytest.fixture
def rate_limiter():
    return RateLimitManager()

def test_rate_limit_creation(rate_limiter):
    # Test initial state
    assert rate_limiter.global_limit == 50
    assert rate_limiter.global_remaining == 50
    assert rate_limiter.buckets == {}

def test_update_rate_limits(rate_limiter):
    # Test updating from headers
    headers = {
        'X-RateLimit-Limit': '5',
        'X-RateLimit-Remaining': '4',
        'X-RateLimit-Reset-After': '60.0',
        'X-RateLimit-Bucket': 'test_bucket'
    }
    
    rate_limiter.update_rate_limits(headers)
    
    assert 'test_bucket' in rate_limiter.buckets
    bucket = rate_limiter.buckets['test_bucket']
    assert bucket.limit == 5
    assert bucket.remaining == 4
    assert bucket.reset_after == 60.0

def test_check_rate_limit(rate_limiter):
    # Test rate limit checking
    headers = {
        'X-RateLimit-Limit': '2',
        'X-RateLimit-Remaining': '2',
        'X-RateLimit-Reset-After': '60.0',
        'X-RateLimit-Bucket': 'test_bucket'
    }
    
    rate_limiter.update_rate_limits(headers)
    
    # First request should succeed
    result = rate_limiter.check_rate_limit('test_bucket')
    assert result is None
    
    # Second request should succeed
    result = rate_limiter.check_rate_limit('test_bucket')
    assert result is None
    
    # Third request should be rate limited
    result = rate_limiter.check_rate_limit('test_bucket')
    assert isinstance(result, float)
    assert result > 0

def test_invalid_request_tracking(rate_limiter):
    # Test invalid request tracking
    assert not rate_limiter.track_invalid_request()  # First request
    
    # Simulate many invalid requests
    for _ in range(9998):
        rate_limiter.track_invalid_request()
    
    # Should return True when limit reached
    assert rate_limiter.track_invalid_request()

def test_rate_limit_reset(rate_limiter):
    headers = {
        'X-RateLimit-Limit': '1',
        'X-RateLimit-Remaining': '1',
        'X-RateLimit-Reset-After': '0.1',  # Short reset time for testing
        'X-RateLimit-Bucket': 'test_bucket'
    }
    
    rate_limiter.update_rate_limits(headers)
    
    # Use up the rate limit
    assert rate_limiter.check_rate_limit('test_bucket') is None
    assert isinstance(rate_limiter.check_rate_limit('test_bucket'), float)
    
    # Wait for reset
    time.sleep(0.2)
    
    # Should be able to make request again
    assert rate_limiter.check_rate_limit('test_bucket') is None
    
@pytest.mark.asyncio
async def test_global_rate_limit(rate_limiter):
    """Test global rate limit handling"""
    # Use up global limit
    for _ in range(50):
        assert rate_limiter.check_rate_limit("test") is None
    
    # Should be rate limited
    wait_time = rate_limiter.check_rate_limit("test")
    assert isinstance(wait_time, float)
    assert wait_time > 0
    
    # Wait for reset
    await asyncio.sleep(1.0)
    assert rate_limiter.check_rate_limit("test") is None

@pytest.mark.asyncio
async def test_concurrent_requests(rate_limiter):
    """Test handling of concurrent requests"""
    headers = {
        'X-RateLimit-Limit': '5',
        'X-RateLimit-Remaining': '5',
        'X-RateLimit-Reset-After': '1.0',
        'X-RateLimit-Bucket': 'test_bucket'
    }
    rate_limiter.update_rate_limits(headers)
    
    async def make_request():
        return rate_limiter.check_rate_limit('test_bucket')
    
    # Make concurrent requests
    tasks = [make_request() for _ in range(10)]
    results = await asyncio.gather(*tasks)
    
    # First 5 should succeed, rest should be rate limited
    success_count = sum(1 for r in results if r is None)
    assert success_count == 5
    assert all(isinstance(r, float) for r in results[5:])