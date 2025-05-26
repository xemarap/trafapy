# TrafaPy: Swedish Transport Statistics API Wrapper

A comprehensive Python package for accessing and analyzing Swedish transport statistics through the Trafikanalys API.

## Overview

TrafaPy provides an intuitive interface to explore and retrieve data from Sweden's official transport statistics database. Whether you're researching vehicle registrations, traffic patterns, accidents, or transport trends, TrafaPy makes it easy to access and analyze this rich datasource.

## Installation

```bash
pip install git+https://github.com/xemarap/trafapy.git
```

## Requirements
TrafaPy requires Python 3.7+ and the following dependencies:

- requests (≥2.25.0) - HTTP library for API communication
- pandas (≥1.0.0) - Data manipulation and analysis
- numpy (≥1.19.0) - Numerical computing support

These dependencies are automatically installed when you install TrafaPy.

## Quick Start

```python
from trafapy import TrafikanalysClient

# Initialize client with caching enabled
trafa = TrafikanalysClient(
    language="sv",           # 'sv' for Swedish, 'en' for English  
    cache_enabled=True,      # Enable caching for better performance
    debug=False              # Set to True for detailed logging
)

# Find available datasets
products = trafa.list_products()
car_products = trafa.search_products("personbilar")

# Explore a specific dataset
product_code = "t10026"  # Passenger cars
variables = trafa.explore_product_variables(product_code)

# Get data
query = trafa.build_query(
    product_code=product_code,
    ar=['2023'],           # Year 2023
    reglan=['01'],         # Stockholm County
    drivmedel='all',       # All fuel types
    nyregunder=''          # New registrations (measure)
)

df = trafa.get_data_as_dataframe(product_code, query)
```

## Key Features

### 🔍 **API Exploration**
- **Product Discovery**: Search and browse available transport datasets
- **Variable Analysis**: Explore dimensions and measures for each dataset
- **Filter Options**: Discover available values for any variable
- **Interactive Building**: Step-by-step query construction

### 📊 **Data Retrieval**
- **Flexible Queries**: Build complex filters with multiple dimensions
- **Automated Value Fetching**: Use `'all'` to get all available options
- **DataFrame Integration**: Direct conversion to pandas DataFrames
- **Query Preview**: Inspect API calls before execution

### 🚀 **Performance & Reliability**
- **Smart Caching**: Automatic response caching with configurable expiry
- **Error Handling**: Robust error management and fallback options
- **Debug Mode**: Detailed logging for troubleshooting
- **Rate Limiting**: Built-in protection against API limits

### 🛠️ **Developer Experience**
- **Type Hints**: Full type annotation support
- **Comprehensive Documentation**: Detailed examples and API reference
- **Intuitive API**: Pythonic interface design
- **Cache Management**: Tools to monitor and clear cached data

## Core Functionality

### Exploring Available Data

```python
# List all datasets
products = trafa.list_products()
print(f"Found {len(products)} datasets")

# Search for specific topics
vehicles = trafa.search_products("fordon")
accidents = trafa.search_products("skador")
railways = trafa.search_products("järnväg")

# Explore dataset structure
product_code = "t10026"  # Passenger cars
variables = trafa.explore_product_variables(product_code)
print(variables[['name', 'label', 'type']])

# Check available filter options
years = trafa.explore_variable_options(product_code, "ar")
fuel_types = trafa.explore_variable_options(product_code, "drivmedel")
regions = trafa.explore_variable_options(product_code, "reglan")
```

### Building and Executing Queries

```python
# Manual query building
query = trafa.build_query(
    product_code="t10026",
    ar=['2020', '2021', '2022'],     # Specific years
    reglan=['01', '03'],             # Stockholm and Uppsala County
    drivmedel=['102', '103'],        # Diesel and electric
    nyregunder=''                    # New registrations measure
)

# Automated value fetching
query = trafa.build_query(
    product_code="t10026", 
    ar='all',                        # All available years
    drivmedel='all',                 # All fuel types
    reglan=['01'],                   # Specific region
    nyregunder=''
)

# Preview before executing
query_string = trafa.preview_query("t10026", query)
print(f"API URL: {query_string}")

# Get data as DataFrame
df = trafa.get_data_as_dataframe("t10026", query)
```

### Advanced Query Techniques

```python
# Get all values for a variable
all_years = trafa.get_all_available_values("t10026", "ar")
all_municipalities = trafa.get_all_available_values("t10026", "regkom")

# Filter municipalities by county (Stockholm = codes starting with "01")
stockholm_munis = [m for m in all_municipalities if m.startswith("01")]

# Complex multi-dimensional query
query = trafa.build_query(
    product_code="t10026",
    ar=all_years[-5:],               # Last 5 years
    reglan=['01'],                   # Stockholm county  
    regkom=stockholm_munis,          # All Stockholm municipalities  
    drivmedel=['103', '104', '105'], # Electric and hybrid vehicles
    itrfslut=''                      # Vehicles in traffic
)

df = trafa.get_data_as_dataframe("t10026", query)
```

## Cache Management

```python
# Check cache status
cache_info = trafa.get_cache_info()
print(f"Cache files: {cache_info['file_count']}")
print(f"Cache size: {cache_info['total_size_mb']} MB")
print(f"Cache location: {cache_info['cache_dir']}")

# Clear cache
deleted_count = trafa.clear_cache()  # Clear all
deleted_count = trafa.clear_cache(older_than_seconds=3600)  # Clear files older than 1 hour
```

## Error Handling

```python
try:
    df = trafa.get_data_as_dataframe(product_code, query)
except requests.exceptions.RequestException as e:
    print(f"Network error: {e}")
except ValueError as e:
    print(f"Invalid query parameters: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
    
    # Debug by exploring the dataset structure
    variables = trafa.explore_product_variables(product_code)
    print("Available variables:", variables['name'].tolist())
```

## Configuration Options

```python
from trafapy import TrafikanalysClient, DEFAULT_CACHE_DIR

trafa = TrafikanalysClient(
    language="sv",                    # Response language ('sv' or 'en')
    debug=True,                       # Enable debug logging
    cache_enabled=True,               # Enable response caching
    cache_dir=DEFAULT_CACHE_DIR,      # Cache directory location  
    cache_expiry_seconds=1800         # Cache expiry (30 minutes)
)
```

## API Reference

The Trafikanalys API provides access to official Swedish transport statistics. TrafaPy wraps two main endpoints:

- **Structure endpoint**: `/api/structure` - Dataset and variable metadata
- **Data endpoint**: `/api/data` - Statistical data retrieval

Query format: `{product}|{variable1}|{variable2:filter1,filter2}|{measure}`

Example: `t10026|ar:2023|reglan:01|drivmedel:103|nyregunder`

For a list with possible API calls and structures for each dataproduct, please visit [Trafikanalys API Documentation](https://www.trafa.se/sidor/api-dokumentation/)

## Contributing

Contributions are welcome! Please feel free to submit issues, feature requests, or pull requests.

## License

MIT License - see LICENSE file for details.

## Dependency Licenses
TrafaPy includes the following third-party dependencies with their respective licenses:

- requests
- pandas
- numpy

All dependency licenses are included in the `LICENSES/` directory for reference and compliance purposes.

## Links

- **Official API Documentation**: [Trafikanalys Open Data API](https://www.trafa.se/sidor/oppen-data-api/)
- **Data Catalog**: [Trafikanalys Statistics](https://www.trafa.se/statistik/)
- **GitHub Repository**: [TrafaPy on GitHub](https://github.com/xemarap/trafapy)

---

**TrafaPy** - Making Swedish transport data accessible to everyone 🚗📊🚂