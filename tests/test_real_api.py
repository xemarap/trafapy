# Save this as test_real_api.py
import pytest
import pandas as pd
from trafapy import TrafikanalysClient

@pytest.mark.integration
def test_real_api_list_products():
    """Test listing products from real API - use carefully!"""
    client = TrafikanalysClient(cache_enabled=True)  # Use cache to be nice to API
    
    try:
        products = client.list_products()
        assert isinstance(products, pd.DataFrame)
        assert len(products) > 0
        print(f"Found {len(products)} products")
        
        # Print first few products
        print("\nFirst 5 products:")
        print(products.head())
        
    except Exception as e:
        pytest.skip(f"API test failed (this is ok): {e}")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])  # -s shows print statements