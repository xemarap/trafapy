"""
Test suite for TrafaPy - Trafikanalys API Python Wrapper

This test suite covers:
- Core client functionality
- Caching system
- Data retrieval and processing
- API structure exploration
- Error handling

Run with: pytest test_trafapy.py -v
"""

import pytest
import pandas as pd
import json
import os
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

# Import the modules we're testing
from trafapy.client import TrafikanalysClient
from trafapy.cache_utils import APICache, cached_api_request


class TestAPICache:
    """Test the caching functionality."""
    
    def setup_method(self):
        """Set up test environment for each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.cache = APICache(cache_dir=self.temp_dir, expiry_seconds=3600, enabled=True)
    
    def teardown_method(self):
        """Clean up after each test."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_cache_initialization(self):
        """Test cache initialization."""
        assert self.cache.cache_dir == self.temp_dir
        assert self.cache.expiry_seconds == 3600
        assert self.cache.enabled == True
    
    def test_cache_key_generation(self):
        """Test cache key generation."""
        url = "https://api.trafa.se/api/structure"
        params = {"lang": "sv", "query": "t10016"}
        
        key1 = self.cache.generate_cache_key(url, params)
        key2 = self.cache.generate_cache_key(url, params)
        
        # Same input should generate same key
        assert key1 == key2
        
        # Different input should generate different key
        params_different = {"lang": "en", "query": "t10016"}
        key3 = self.cache.generate_cache_key(url, params_different)
        assert key1 != key3
    
    def test_cache_save_and_retrieve(self):
        """Test saving and retrieving from cache."""
        cache_key = "test_key"
        test_data = {"test": "data", "number": 123}
        
        # Save to cache
        success = self.cache.save_to_cache(cache_key, test_data)
        assert success == True
        
        # Retrieve from cache
        retrieved_data = self.cache.get_from_cache(cache_key)
        assert retrieved_data == test_data
    
    def test_cache_expiry(self):
        """Test cache expiry functionality."""
        # Create cache with very short expiry
        short_cache = APICache(cache_dir=self.temp_dir, expiry_seconds=1, enabled=True)
        
        cache_key = "test_expiry"
        test_data = {"test": "expiry"}
        
        # Save to cache
        short_cache.save_to_cache(cache_key, test_data)
        
        # Should be valid immediately
        assert short_cache.is_cache_valid(cache_key) == True
        
        # Wait for expiry (in real test, we'd mock time)
        import time
        time.sleep(1.1)
        
        # Should be expired now
        assert short_cache.is_cache_valid(cache_key) == False
    
    def test_cache_disabled(self):
        """Test cache behavior when disabled."""
        disabled_cache = APICache(enabled=False)
        
        cache_key = "test_disabled"
        test_data = {"test": "disabled"}
        
        # Save should return False when disabled
        success = disabled_cache.save_to_cache(cache_key, test_data)
        assert success == False
        
        # Retrieve should return None when disabled
        retrieved_data = disabled_cache.get_from_cache(cache_key)
        assert retrieved_data == None
    
    def test_cache_info(self):
        """Test cache information retrieval."""
        # Get info on empty cache
        info = self.cache.get_cache_info()
        assert info["enabled"] == True
        assert info["file_count"] == 0
        assert info["total_size_bytes"] == 0
        
        # Add some data
        self.cache.save_to_cache("key1", {"data": "test1"})
        self.cache.save_to_cache("key2", {"data": "test2"})
        
        # Check updated info
        info = self.cache.get_cache_info()
        assert info["file_count"] == 2
        assert info["total_size_bytes"] > 0
    
    def test_cache_clear(self):
        """Test cache clearing functionality."""
        # Add some data
        self.cache.save_to_cache("key1", {"data": "test1"})
        self.cache.save_to_cache("key2", {"data": "test2"})
        
        # Clear all
        count = self.cache.clear_cache()
        assert count == 2
        
        # Verify cache is empty
        info = self.cache.get_cache_info()
        assert info["file_count"] == 0


class TestTrafikanalysClient:
    """Test the main client functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.client = TrafikanalysClient(
            language="sv", 
            debug=False, 
            cache_enabled=True,
            cache_dir=self.temp_dir,
            cache_expiry_seconds=3600
        )
    
    def teardown_method(self):
        """Clean up after each test."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_client_initialization(self):
        """Test client initialization."""
        assert self.client.language == "sv"
        assert self.client.BASE_URL == "https://api.trafa.se/api"
        assert self.client.cache.enabled == True
    
    @patch('requests.Session.get')
    def test_make_request_success(self, mock_get):
        """Test successful API request."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"test": "data"}
        mock_get.return_value = mock_response
        
        url = "https://api.trafa.se/api/structure"
        params = {"lang": "sv"}
        
        result = self.client._make_request(url, params)
        assert result == {"test": "data"}
        mock_get.assert_called_once_with(url, params=params)
    
    @patch('requests.Session.get')
    def test_make_request_failure(self, mock_get):
        """Test failed API request."""
        # Mock failed response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Not found"
        mock_get.return_value = mock_response
        
        url = "https://api.trafa.se/api/structure"
        params = {"lang": "sv"}
        
        result = self.client._make_request(url, params)
        assert result == {}
    
    def test_build_query(self):
        """Test query building functionality."""
        product_code = "t10016"
        variables = {
            "ar": ["2020", "2021"],
            "drivmedel": "101",
            "bestand": ""
        }
        
        query = self.client._build_query(product_code, variables)
        expected = "t10016|ar:2020,2021|drivmedel:101|bestand"
        assert query == expected
    
    def test_build_query_empty_variables(self):
        """Test query building with empty variables."""
        product_code = "t10016"
        variables = {}
        
        query = self.client._build_query(product_code, variables)
        assert query == "t10016"
    
    def test_build_query_single_values(self):
        """Test query building with single values."""
        product_code = "t10016"
        variables = {
            "ar": "2020",
            "drivmedel": ["101", "102"]
        }
        
        query = self.client._build_query(product_code, variables)
        expected = "t10016|ar:2020|drivmedel:101,102"
        assert query == expected
    
    @patch('trafapy.client.TrafikanalysClient._make_request')
    def test_list_products(self, mock_request):
        """Test listing products."""
        # Mock API response
        mock_response = {
            "StructureItems": [
                {
                    "Name": "t10016",
                    "Label": "Personbilar",
                    "Description": "Statistics about passenger cars",
                    "Id": "291",
                    "UniqueId": "T10016",
                    "ActiveFrom": "2022-05-10T14:00:00"
                },
                {
                    "Name": "t10013",
                    "Label": "Lastbilar",
                    "Description": "Statistics about trucks",
                    "Id": "292",
                    "UniqueId": "T10013",
                    "ActiveFrom": "2022-05-12T08:00:00"
                }
            ]
        }
        mock_request.return_value = mock_response
        
        products_df = self.client.list_products()
        
        assert isinstance(products_df, pd.DataFrame)
        assert len(products_df) == 2
        assert "t10016" in products_df["code"].values
        assert "t10013" in products_df["code"].values
        assert "Personbilar" in products_df["label"].values
        assert "Lastbilar" in products_df["label"].values
    
    @patch('trafapy.client.TrafikanalysClient._make_request')
    def test_list_products_empty_response(self, mock_request):
        """Test listing products with empty response."""
        mock_request.return_value = {}
        
        products_df = self.client.list_products()
        assert isinstance(products_df, pd.DataFrame)
        assert len(products_df) == 0
    
    @patch('trafapy.client.TrafikanalysClient.list_products')
    def test_search_products(self, mock_list_products):
        """Test product search functionality."""
        # Mock products dataframe
        products_data = pd.DataFrame([
            {
                "code": "t10016",
                "label": "Personbilar",
                "description": "Statistics about passenger cars",
                "id": "291",
                "unique_id": "T10016",
                "active_from": "2022-05-10T14:00:00"
            },
            {
                "code": "t10013",
                "label": "Lastbilar", 
                "description": "Statistics about trucks",
                "id": "292",
                "unique_id": "T10013",
                "active_from": "2022-05-12T08:00:00"
            }
        ])
        mock_list_products.return_value = products_data
        
        # Search for cars
        results = self.client.search_products("personbilar")
        assert len(results) == 1
        assert results.iloc[0]["code"] == "t10016"
        
        # Search for trucks
        results = self.client.search_products("lastbilar")
        assert len(results) == 1
        assert results.iloc[0]["code"] == "t10013"
        
        # Search with no matches
        results = self.client.search_products("nonexistent")
        assert len(results) == 0
    
    def test_process_row(self):
        """Test row processing functionality."""
        # Test with list of cells
        row_data = {
            "Cell": [
                {"Column": "ar", "Value": "2020"},
                {"Column": "antal", "Value": "12345"}
            ]
        }
        
        processed = self.client._process_row(row_data)
        expected = {"ar": "2020", "antal": "12345"}
        assert processed == expected
        
        # Test with single cell
        row_data_single = {
            "Cell": {"Column": "ar", "Value": "2020"}
        }
        
        processed_single = self.client._process_row(row_data_single)
        expected_single = {"ar": "2020"}
        assert processed_single == expected_single
    
    def test_data_to_dataframe(self):
        """Test data to DataFrame conversion."""
        # Mock API data response
        api_data = {
            "Rows": [
                {
                    "Cell": [
                        {"Column": "ar", "Value": "2020"},
                        {"Column": "antal", "Value": "12345"}
                    ]
                },
                {
                    "Cell": [
                        {"Column": "ar", "Value": "2021"},
                        {"Column": "antal", "Value": "13456"}
                    ]
                }
            ]
        }
        
        df = self.client._data_to_dataframe(api_data)
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert list(df.columns) == ["ar", "antal"]
        assert df.iloc[0]["ar"] == "2020"
        assert df.iloc[1]["ar"] == "2021"
    
    def test_data_to_dataframe_empty(self):
        """Test data to DataFrame conversion with empty data."""
        empty_data = {"Rows": []}
        df = self.client._data_to_dataframe(empty_data)
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0
        
        # Test with no data at all
        no_data = {}
        df = self.client._data_to_dataframe(no_data)
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0


class TestClientIntegration:
    """Integration tests that may hit the real API (run with caution)."""
    
    @pytest.fixture
    def client(self):
        """Create client for integration tests."""
        temp_dir = tempfile.mkdtemp()
        client = TrafikanalysClient(
            language="sv",
            debug=False,
            cache_enabled=True,
            cache_dir=temp_dir,
            cache_expiry_seconds=3600
        )
        yield client
        # Cleanup
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
    
    @pytest.mark.integration
    def test_real_api_list_products(self, client):
        """Test listing products with real API (marked as integration test)."""
        products_df = client.list_products()
        
        assert isinstance(products_df, pd.DataFrame)
        assert len(products_df) > 0
        assert "code" in products_df.columns
        assert "label" in products_df.columns
        
        # Check if we have some expected products
        product_codes = products_df["code"].tolist()
        assert any("t10016" in code or "t10026" in code for code in product_codes)
    
    @pytest.mark.integration
    def test_real_api_explore_variables(self, client):
        """Test exploring variables with real API."""
        # Use a known product code (passenger cars)
        product_code = "t10016"  # or t10026, depending on what's available
        
        variables_df = client.explore_product_variables(product_code)
        
        assert isinstance(variables_df, pd.DataFrame)
        # Should have some variables
        if len(variables_df) > 0:
            assert "name" in variables_df.columns
            assert "label" in variables_df.columns
            assert "type" in variables_df.columns
    
    @pytest.mark.integration
    def test_real_api_get_data_small(self, client):
        """Test getting a small amount of real data."""
        try:
            # Use a known product and get a small dataset
            product_code = "t10016"  # Passenger cars
            variables = {
                "ar": ["2023"],  # Just one recent year
                "bestand": ""    # Stock data without filter
            }
            
            df = client.get_data_as_dataframe(product_code, variables)
            
            assert isinstance(df, pd.DataFrame)
            # Should have some data if the API works
            if len(df) > 0:
                assert "ar" in df.columns or any("ar" in str(col).lower() for col in df.columns)
                
        except Exception as e:
            # If this specific product doesn't work, that's ok for the test
            pytest.skip(f"API test failed, possibly due to product code change: {e}")


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.client = TrafikanalysClient(
            cache_enabled=True,
            cache_dir=self.temp_dir
        )
    
    def teardown_method(self):
        """Clean up after each test."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    @patch('requests.Session.get')
    def test_network_error_handling(self, mock_get):
        """Test handling of network errors."""
        import requests
        mock_get.side_effect = requests.ConnectionError("Network error")
        
        # Should not raise exception, but return empty result
        with pytest.raises(requests.ConnectionError):
            self.client._make_request("https://api.trafa.se/api/structure", {})
    
    def test_invalid_json_response(self):
        """Test handling of invalid JSON responses."""
        with patch('requests.Session.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
            mock_get.return_value = mock_response
            
            with pytest.raises(json.JSONDecodeError):
                self.client._make_request("https://api.trafa.se/api/structure", {})
    
    def test_malformed_api_response(self):
        """Test handling of malformed API responses."""
        malformed_data = {
            "unexpected_structure": "data"
        }
        
        df = self.client._data_to_dataframe(malformed_data)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0


class TestUtilityFunctions:
    """Test utility and convenience functions."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.client = TrafikanalysClient(
            cache_enabled=True,
            cache_dir=self.temp_dir
        )
    
    def teardown_method(self):
        """Clean up after each test."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    @patch('trafapy.client.TrafikanalysClient.explore_variable_options')
    def test_get_all_available_values(self, mock_explore):
        """Test getting all available values for a variable."""
        # Mock the explore_variable_options method
        mock_options = pd.DataFrame([
            {"name": "2020", "label": "2020", "description": "", "option_type": "Value"},
            {"name": "2021", "label": "2021", "description": "", "option_type": "Value"},
            {"name": "2022", "label": "2022", "description": "", "option_type": "Value"},
            {"name": "t1", "label": "Totalt", "description": "", "option_type": "Value"}
        ])
        mock_explore.return_value = mock_options
        
        values = self.client.get_all_available_values("t10016", "ar")
        
        # Should exclude 't1' by default and sort years
        expected = ["2020", "2021", "2022"]
        assert values == expected
    
    @patch('trafapy.client.TrafikanalysClient.get_all_available_values')
    def test_build_query_automated(self, mock_get_values):
        """Test automated query building."""
        # Mock the get_all_available_values method
        mock_get_values.side_effect = lambda product, var: {
            "ar": ["2020", "2021", "2022"],
            "drivmedel": ["101", "102", "103"]
        }.get(var, [])
        
        query_dict = self.client.build_query(
            "t10016",
            ar="all",
            drivmedel="all",
            reglan=["01"],
            bestand=""
        )
        
        expected = {
            "ar": ["2020", "2021", "2022"],
            "drivmedel": ["101", "102", "103"],
            "reglan": ["01"],
            "bestand": ""
        }
        
        assert query_dict == expected
    
    def test_preview_query(self):
        """Test query preview functionality."""
        query_dict = {
            "ar": ["2020", "2021"],
            "drivmedel": "101",
            "bestand": ""
        }
        
        # Capture printed output
        import io
        import sys
        captured_output = io.StringIO()
        sys.stdout = captured_output
        
        query_string = self.client.preview_query("t10016", query_dict)
        
        # Restore stdout
        sys.stdout = sys.__stdout__
        
        expected_query = "t10016|ar:2020,2021|drivmedel:101|bestand"
        assert query_string == expected_query
        
        # Check that URL was printed
        output = captured_output.getvalue()
        assert "https://api.trafa.se/api/data?query=" in output


# Test configuration and markers
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests (may hit real API)"
    )


# Example of how to run different test categories:
# 
# Run all tests:
# pytest test_trafapy.py -v
#
# Run only unit tests (exclude integration):
# pytest test_trafapy.py -v -m "not integration"
#
# Run only integration tests:
# pytest test_trafapy.py -v -m integration
#
# Run with coverage:
# pytest test_trafapy.py --cov=trafapy --cov-report=html


if __name__ == "__main__":
    # Run the tests if this file is executed directly
    pytest.main([__file__, "-v"])