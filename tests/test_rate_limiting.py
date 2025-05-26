"""
Tests for rate limiting functionality in TrafaPy.

This module tests the RateLimiter class and rate limiting integration 
in the TrafikanalysClient.
"""

import pytest
import time
import requests
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

# Assuming the client module structure from the provided code
from trafapy.client import RateLimiter, TrafikanalysClient


class TestRateLimiter:
    """Test cases for the RateLimiter class."""
    
    def test_rate_limiter_initialization(self):
        """Test RateLimiter initialization with default and custom parameters."""
        # Default initialization
        limiter = RateLimiter()
        assert limiter.calls_per_second == 1.0
        assert limiter.burst_size == 5
        assert limiter.backoff_factor == 2.0
        assert limiter.max_retries == 3
        assert limiter.min_interval == 1.0
        assert limiter.call_times == []
        
        # Custom initialization
        limiter = RateLimiter(
            calls_per_second=2.0,
            burst_size=10,
            backoff_factor=1.5,
            max_retries=5
        )
        assert limiter.calls_per_second == 2.0
        assert limiter.burst_size == 10
        assert limiter.backoff_factor == 1.5
        assert limiter.max_retries == 5
        assert limiter.min_interval == 0.5
    
    def test_wait_if_needed_no_previous_calls(self):
        """Test that no waiting occurs when there are no previous calls."""
        limiter = RateLimiter(calls_per_second=2.0)
        
        start_time = time.time()
        limiter.wait_if_needed()
        end_time = time.time()
        
        # Should not wait significantly
        assert end_time - start_time < 0.1
        assert len(limiter.call_times) == 1
    
    def test_wait_if_needed_rate_limiting(self):
        """Test that rate limiting causes appropriate delays."""
        limiter = RateLimiter(calls_per_second=2.0)  # 0.5 second interval
        
        # First call
        start_time = time.time()
        limiter.wait_if_needed()
        first_call_time = time.time()
        
        # Second call immediately after
        limiter.wait_if_needed()
        second_call_time = time.time()
        
        # Should have waited at least 0.5 seconds between calls
        time_diff = second_call_time - first_call_time
        assert time_diff >= 0.4  # Allow some tolerance for timing
        assert len(limiter.call_times) == 2
    
    def test_wait_if_needed_burst_limiting(self):
        """Test that burst limiting works correctly."""
        limiter = RateLimiter(calls_per_second=10.0, burst_size=3)
        
        start_time = time.time()
        
        # Make burst_size calls quickly
        for i in range(3):
            limiter.wait_if_needed()
        
        # Should not have waited much for the burst
        burst_time = time.time()
        assert burst_time - start_time < 0.2
        
        # Next call should be rate limited by burst window
        limiter.wait_if_needed()
        after_burst_time = time.time()
        
        # Should have waited close to 1 second (burst window)
        total_time = after_burst_time - start_time
        assert total_time >= 0.8  # Allow some tolerance
    
    def test_call_times_cleanup(self):
        """Test that old call times are cleaned up properly."""
        limiter = RateLimiter(calls_per_second=2.0)
        
        # Add some old call times manually
        current_time = time.time()
        limiter.call_times = [
            current_time - 2.0,  # Should be cleaned up
            current_time - 0.5,  # Should remain
        ]
        
        limiter.wait_if_needed()
        
        # Only recent calls should remain
        assert len(limiter.call_times) == 2  # 1 old + 1 new
        assert all(current_time - call_time <= 1.0 for call_time in limiter.call_times[:-1])
    
    def test_execute_with_retry_success(self):
        """Test successful execution without retries."""
        limiter = RateLimiter(calls_per_second=5.0)
        
        mock_func = Mock(return_value="success")
        
        result = limiter.execute_with_retry(mock_func, "arg1", "arg2", kwarg1="value1")
        
        assert result == "success"
        assert mock_func.call_count == 1
        mock_func.assert_called_with("arg1", "arg2", kwarg1="value1")
    
    def test_execute_with_retry_rate_limit_error(self):
        """Test retry behavior on HTTP 429 (rate limit) errors."""
        limiter = RateLimiter(calls_per_second=10.0, max_retries=2)  # Fast for testing
        
        # Mock response for 429 error
        mock_response = Mock()
        mock_response.status_code = 429
        
        mock_error = requests.exceptions.RequestException("Rate limited")
        mock_error.response = mock_response
        
        mock_func = Mock(side_effect=[mock_error, mock_error, "success"])
        
        start_time = time.time()
        result = limiter.execute_with_retry(mock_func, debug=False)
        end_time = time.time()
        
        assert result == "success"
        assert mock_func.call_count == 3
        # Should have waited for backoff (2^0 * 2 + 2^1 * 2 = 6 seconds total)
        assert end_time - start_time >= 5.0  # Allow some tolerance
    
    def test_execute_with_retry_server_error(self):
        """Test retry behavior on server errors (5xx)."""
        limiter = RateLimiter(calls_per_second=10.0, max_retries=2)
        
        # Mock response for 500 error
        mock_response = Mock()
        mock_response.status_code = 500
        
        mock_error = requests.exceptions.RequestException("Server error")
        mock_error.response = mock_response
        
        mock_func = Mock(side_effect=[mock_error, "success"])
        
        start_time = time.time()
        result = limiter.execute_with_retry(mock_func, debug=False)
        end_time = time.time()
        
        assert result == "success"
        assert mock_func.call_count == 2
        # Should have waited for backoff (2^0 = 1 second)
        assert end_time - start_time >= 0.8
    
    def test_execute_with_retry_max_retries_exceeded(self):
        """Test that exceptions are raised when max retries are exceeded."""
        limiter = RateLimiter(calls_per_second=10.0, max_retries=1)
        
        mock_response = Mock()
        mock_response.status_code = 429
        
        mock_error = requests.exceptions.RequestException("Rate limited")
        mock_error.response = mock_response
        
        mock_func = Mock(side_effect=mock_error)
        
        with pytest.raises(requests.exceptions.RequestException):
            limiter.execute_with_retry(mock_func, debug=False)
        
        assert mock_func.call_count == 2  # Initial call + 1 retry
    
    def test_execute_with_retry_non_retryable_error(self):
        """Test that non-retryable errors are raised immediately."""
        limiter = RateLimiter(calls_per_second=10.0, max_retries=3)
        
        # Mock response for 400 error (client error, not retryable)
        mock_response = Mock()
        mock_response.status_code = 400
        
        mock_error = requests.exceptions.RequestException("Bad request")
        mock_error.response = mock_response
        
        mock_func = Mock(side_effect=mock_error)
        
        with pytest.raises(requests.exceptions.RequestException):
            limiter.execute_with_retry(mock_func, debug=False)
        
        assert mock_func.call_count == 1  # No retries for client errors


class TestTrafikanalysClientRateLimiting:
    """Test cases for rate limiting integration in TrafikanalysClient."""
    
    def test_client_initialization_with_rate_limiting(self):
        """Test client initialization with rate limiting enabled."""
        client = TrafikanalysClient(
            rate_limit_enabled=True,
            calls_per_second=2.0,
            burst_size=10,
            enable_retry=True
        )
        
        assert client.rate_limit_enabled is True
        assert client.rate_limiter is not None
        assert client.rate_limiter.calls_per_second == 2.0
        assert client.rate_limiter.burst_size == 10
        assert client.rate_limiter.max_retries == 3
    
    def test_client_initialization_without_rate_limiting(self):
        """Test client initialization with rate limiting disabled."""
        client = TrafikanalysClient(rate_limit_enabled=False)
        
        assert client.rate_limit_enabled is False
        assert client.rate_limiter is None
    
    def test_configure_rate_limiting_enable(self):
        """Test enabling rate limiting after initialization."""
        client = TrafikanalysClient(rate_limit_enabled=False)
        
        client.configure_rate_limiting(
            enabled=True,
            calls_per_second=3.0,
            burst_size=8,
            enable_retry=False
        )
        
        assert client.rate_limit_enabled is True
        assert client.rate_limiter is not None
        assert client.rate_limiter.calls_per_second == 3.0
        assert client.rate_limiter.burst_size == 8
        assert client.rate_limiter.max_retries == 0
    
    def test_configure_rate_limiting_disable(self):
        """Test disabling rate limiting after initialization."""
        client = TrafikanalysClient(rate_limit_enabled=True)
        
        client.configure_rate_limiting(enabled=False)
        
        assert client.rate_limit_enabled is False
        assert client.rate_limiter is None
    
    def test_get_rate_limit_info_enabled(self):
        """Test getting rate limit info when enabled."""
        client = TrafikanalysClient(
            rate_limit_enabled=True,
            calls_per_second=2.0,
            burst_size=7
        )
        
        info = client.get_rate_limit_info()
        
        assert info["enabled"] is True
        assert info["calls_per_second"] == 2.0
        assert info["burst_size"] == 7
        assert info["recent_calls"] == 0
        assert "backoff_factor" in info
        assert "max_retries" in info
    
    def test_get_rate_limit_info_disabled(self):
        """Test getting rate limit info when disabled."""
        client = TrafikanalysClient(rate_limit_enabled=False)
        
        info = client.get_rate_limit_info()
        
        assert info["enabled"] is False
        assert info["calls_per_second"] == 0
        assert info["burst_size"] == 0
        assert info["recent_calls"] == 0
    
    @patch('trafapy.client.requests.Session.get')
    def test_make_request_with_rate_limiting(self, mock_get):
        """Test that API requests go through rate limiting when enabled."""
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"test": "data"}
        mock_get.return_value = mock_response
        
        client = TrafikanalysClient(
            rate_limit_enabled=True,
            calls_per_second=5.0  # Fast for testing
        )
        
        # Mock the rate limiter to track calls
        client.rate_limiter.execute_with_retry = Mock(
            side_effect=lambda func, *args, **kwargs: func(*args, **kwargs)
        )
        
        # Make request
        result = client._make_request("http://example.com", {"param": "value"})
        
        # Verify rate limiter was used
        assert client.rate_limiter.execute_with_retry.called
        assert result == {"test": "data"}
        mock_get.assert_called_once()
    
    @patch('trafapy.client.requests.Session.get')
    def test_make_request_without_rate_limiting(self, mock_get):
        """Test that API requests bypass rate limiting when disabled."""
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"test": "data"}
        mock_get.return_value = mock_response
        
        client = TrafikanalysClient(rate_limit_enabled=False)
        
        # Make request
        result = client._make_request("http://example.com", {"param": "value"})
        
        # Verify direct call without rate limiting
        assert result == {"test": "data"}
        mock_get.assert_called_once()
    
    @patch('trafapy.client.requests.Session.get')
    def test_make_request_handles_rate_limit_error(self, mock_get):
        """Test handling of rate limit errors in actual requests."""
        # Setup mock to simulate rate limit error then success
        mock_response_error = Mock()
        mock_response_error.status_code = 429
        mock_response_error.text = "Rate limited"
        
        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {"test": "data"}
        
        mock_error = requests.exceptions.RequestException("Rate limited")
        mock_error.response = mock_response_error
        
        mock_get.side_effect = [mock_error, mock_response_success]
        
        client = TrafikanalysClient(
            rate_limit_enabled=True,
            calls_per_second=10.0  # Fast for testing
        )
        
        # This should succeed after retry
        result = client._make_request("http://example.com", {"param": "value"})
        
        assert result == {"test": "data"}
        assert mock_get.call_count == 2  # Initial + 1 retry
    
    def test_integration_with_actual_methods(self):
        """Test that rate limiting integrates properly with client methods."""
        client = TrafikanalysClient(
            rate_limit_enabled=True,
            calls_per_second=10.0,  # Fast for testing
            cache_enabled=False  # Disable cache to ensure API calls
        )
        
        # Mock the actual request method to avoid real API calls
        client._make_request = Mock(return_value={
            "StructureItems": [
                {
                    "Name": "test_product",
                    "Label": "Test Product",
                    "Description": "Test description",
                    "Id": "1",
                    "UniqueId": "TEST1",
                    "ActiveFrom": "2023-01-01T00:00:00"
                }
            ]
        })
        
        # Call a method that makes API requests
        result = client.list_products()
        
        # Verify the method works and rate limiting doesn't break functionality
        assert len(result) == 1
        assert result.iloc[0]['code'] == 'test_product'
        assert client._make_request.called


class TestRateLimitingEdgeCases:
    """Test edge cases and error conditions for rate limiting."""
    
    def test_rate_limiter_with_zero_calls_per_second(self):
        """Test rate limiter behavior with very low rate limits."""
        with pytest.raises((ValueError, ZeroDivisionError)):
            RateLimiter(calls_per_second=0.0)
    
    def test_rate_limiter_with_negative_values(self):
        """Test rate limiter with invalid negative values."""
        # Should handle gracefully or raise appropriate errors
        limiter = RateLimiter(
            calls_per_second=-1.0,
            burst_size=-5,
            max_retries=-1
        )
        
        # The behavior should be defined - either handle gracefully or fail predictably
        # This test documents current behavior and can be adjusted based on requirements
        assert limiter.calls_per_second == -1.0  # Current behavior
    
    def test_burst_size_larger_than_reasonable(self):
        """Test rate limiter with very large burst size."""
        limiter = RateLimiter(calls_per_second=1.0, burst_size=1000)
        
        # Should not cause performance issues
        start_time = time.time()
        for _ in range(10):  # Much less than burst size
            limiter.wait_if_needed(debug=False)
        end_time = time.time()
        
        # Should complete quickly since all calls are within burst
        assert end_time - start_time < 1.0
    
    def test_rate_limiting_with_exception_in_function(self):
        """Test rate limiting when the executed function raises non-HTTP exceptions."""
        limiter = RateLimiter(calls_per_second=10.0, max_retries=2)
        
        def failing_function():
            raise ValueError("Test error")
        
        # Non-HTTP exceptions should be raised immediately without retries
        with pytest.raises(ValueError):
            limiter.execute_with_retry(failing_function)


# Performance and stress tests
class TestRateLimitingPerformance:
    """Performance tests for rate limiting functionality."""
    
    def test_rate_limiter_memory_usage(self):
        """Test that rate limiter doesn't accumulate too much memory."""
        limiter = RateLimiter(calls_per_second=100.0, burst_size=50)
        
        # Make many calls to see if call_times list grows unbounded
        for _ in range(200):
            limiter.wait_if_needed()
        
        # call_times should be cleaned up and not grow indefinitely
        assert len(limiter.call_times) <= limiter.burst_size + 10  # Some tolerance
    
    def test_rate_limiter_timing_accuracy(self):
        """Test timing accuracy of rate limiting."""
        limiter = RateLimiter(calls_per_second=2.0)  # 0.5 second intervals
        
        times = []
        for _ in range(3):
            start_time = time.time()
            limiter.wait_if_needed()
            times.append(time.time() - start_time)
        
        # First call should be immediate
        assert times[0] < 0.1
        
        # Subsequent calls should wait approximately 0.5 seconds
        for wait_time in times[1:]:
            assert 0.4 <= wait_time <= 0.7  # Allow some timing tolerance


if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v"])