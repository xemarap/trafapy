import pytest
from trafapy import TrafikanalysClient
import pandas as pd
from unittest.mock import patch

def test_client_can_build_queries():
    """Test that the client can build API queries."""
    client = TrafikanalysClient(cache_enabled=False)
    
    # Test query building
    query = client._build_query(
        "t10016", 
        {"ar": ["2020", "2021"], "drivmedel": "101", "bestand": ""}
    )
    
    expected = "t10016|ar:2020,2021|drivmedel:101|bestand"
    assert query == expected

@patch('trafapy.client.TrafikanalysClient._make_request')
def test_client_can_process_mock_data(mock_request):
    """Test that the client can process API-like data."""
    # Mock API response
    mock_request.return_value = {
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
    
    client = TrafikanalysClient(cache_enabled=False)
    df = client.get_data_as_dataframe("t10016", {"ar": ["2020", "2021"]})
    
    # Verify the data was processed correctly
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert "ar" in df.columns
    assert "antal" in df.columns
    assert df.iloc[0]["ar"] == "2020"
    assert df.iloc[1]["ar"] == "2021"

def test_cache_functionality():
    """Test that caching works."""
    import tempfile
    from trafapy.cache_utils import APICache
    
    temp_dir = tempfile.mkdtemp()
    cache = APICache(cache_dir=temp_dir, enabled=True)
    
    # Test saving and retrieving
    test_data = {"test": "data", "numbers": [1, 2, 3]}
    cache_key = "test_key"
    
    # Save to cache
    success = cache.save_to_cache(cache_key, test_data)
    assert success == True
    
    # Retrieve from cache
    retrieved = cache.get_from_cache(cache_key)
    assert retrieved == test_data
    
    # Clean up
    import shutil
    shutil.rmtree(temp_dir)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])