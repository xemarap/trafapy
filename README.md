# TrafaPy: Swedish Transport Statistics API Wrapper

A comprehensive Python package for accessing and analyzing Swedish transport statistics through the Trafikanalys API.

[![Python Versions](https://img.shields.io/badge/python-3.7%20%7C%203.8%20%7C%203.9%20%7C%203.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue)](#)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**Note:** This is an independent project and is not associated with Trafikanalys.

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

These dependencies are automatically installed when you install TrafaPy.

## Quick Start

```python
from trafapy import TrafikanalysClient

# Initialize client
trafa = TrafikanalysClient(
    rate_limit_enabled=True,    # 'True' is default
    cache_enabled=True          # 'False' as default, but it is recommended to enable
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
- **Automatic Batching**: Handle large queries seamlessly with smart batching

### 🚀 **Performance & Reliability**
- **Smart Caching**: Automatic response caching with configurable expiry
- **Intelligent Batching**: Automatic splitting of large queries to avoid API limits
- **Rate Limiting**: Built-in and configurable protection against API limits
- **Error Handling**: Robust error management and fallback options
- **Debug Mode**: Detailed logging for troubleshooting

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
    reglan=['01'],                   # Specific region
    drivmedel='all',                 # All fuel types
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

### Large Dataset Handling with Automatic Batching

TrafaPy automatically handles large queries that would otherwise fail due to URL length limits by intelligently splitting them into smaller batches.

```python
# Large query example - this will be automatically batched
query = trafa.build_query(
    product_code="t10026",
    ar='all',                        # All available years (20+ values)
    reglan='all',                    # All counties
    regkom='all',          # All municipalities (290+ values)
    drivmedel='all',                 # All fuel types (10+ values)
    nyregunder=''
)

# TrafaPy automatically detects this is a large query and handles batching
df = trafa.get_data_as_dataframe("t10026", query, show_progress=True)
```

**Example output:**
```
📊 Large query detected - retrieving data in 3 batches...
  📋 Batching variable 'regkom' (52 values)
  ✅ Created 3 batches (max 50 values per variable)
  🔄 Processing batch 1/3... ✅ 1,250 rows
  🔄 Processing batch 2/3... ✅ 987 rows  
  🔄 Processing batch 3/3... ✅ 423 rows
  🔗 Combining data from 3 successful batches... ✅
✅ Batch processing complete! Retrieved 2,660 total rows
```

#### Batching Configuration

```python
# Configure batching behavior
trafa.configure_batching(max_batch_size=100)  # Increase batch size

# Check current batching settings
batch_info = trafa.get_batching_info()
print(f"Max batch size: {batch_info['max_batch_size']}")

# Disable batching (not recommended for large queries)
df = trafa.get_data_as_dataframe(product_code, query, use_batching=False)
```

#### When Batching Activates

Batching automatically activates when:
- Any variable has more than 50 values (default `max_batch_size`)
- The resulting URL would exceed typical length limits
- Multiple large variables are combined in a single query

**How it works:**
1. **Detection**: TrafaPy identifies variables with too many values
2. **Smart Splitting**: The largest variable is split into manageable chunks
3. **Parallel Processing**: Each batch is processed with rate limiting
4. **Automatic Merging**: Results are combined and deduplicated
5. **Progress Tracking**: Real-time progress updates during processing

### Error handling

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

## Responsible API use

TrafaPy follows Trafikanalys guidelines for responsible API usage. Trafikanalys strongly recommends using caching to reduce unnecessary API load.

### Configuration Options

```python
# Recommended production configuration
trafa = TrafikanalysClient(
    cache_enabled=True,        # Enable caching
    rate_limit_enabled=True,   # Enable rate limiting
    calls_per_second=1.0,      # Balanced rate
    burst_size=5,              # Allow interactive bursts
    enable_retry=True,         # Handle errors gracefully
    max_batch_size=50,         # Reasonable batch size
    debug=False                # Clean logs in production
)
```

### Cache Management

```python
# Enable caching for better performance and API courtesy
trafa = TrafikanalysClient(cache_enabled=True)

# Check cache status
cache_info = trafa.get_cache_info()
print(f"Cache files: {cache_info['file_count']}")
print(f"Cache size: {cache_info['total_size_mb']} MB")
print(f"Cache location: {cache_info['cache_dir']}")

# Clear cache
deleted_count = trafa.clear_cache()  # Clear all
deleted_count = trafa.clear_cache(older_than_seconds=3600)  # Clear files older than 1 hour
```

### Rate Limiting

TrafaPy includes built-in rate limiting to protect the Trafikanalys API from overload and ensure reliable access for all users.

#### Configure Rate Limiting

Rate limiting is enabled by default to protect the API. You can adjust settings:

```python
# Change rate limiting settings
trafa.configure_rate_limiting(
    enabled=True,
    calls_per_second=2.0,      # Increase rate for bulk operations
    burst_size=10,             # Allow larger bursts
    enable_retry=True
)

# Check current settings
rate_info = trafa.get_rate_limit_info()
print(f"Rate: {rate_info['calls_per_second']} calls/sec")

# Disable rate limiting (use with caution)
trafa.configure_rate_limiting(enabled=False)
```

#### Rate Limiting Settings

| Setting | Description | Recommended Values |
|---------|-------------|-------------------|
| `calls_per_second` | Base rate limit | `0.5-2.0` depending on use case |
| `burst_size` | Quick calls allowed | `3-10` for responsive interaction |
| `enable_retry` | Automatic retry on errors | `True` (recommended) |

### Batching Configuration

| Setting | Description | Recommended Values |
|---------|-------------|-------------------|
| `max_batch_size` | Max values per variable in single request | `25-100` depending on query complexity |
| `use_batching` | Enable automatic batching | `True` (recommended) |
| `show_progress` | Display batch progress | `True` for interactive use |

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

TrafaPy includes the following dependencies:

**Runtime Dependencies:**
- requests
- pandas

**Development/Testing Dependencies (not distributed):**
- pytest
- pytest-cov
- pytest-mock

All dependency licenses are available in the `LICENSES/` directory.

## Links

- **Official API Documentation**: [Trafikanalys Open Data API](https://www.trafa.se/sidor/oppen-data-api/)
- **Data Catalog**: [Trafikanalys Statistics](https://www.trafa.se/sidor/statistikportalen/)
- **GitHub Repository**: [TrafaPy on GitHub](https://github.com/xemarap/trafapy)

---

**TrafaPy** - Making Swedish transport data accessible to everyone 🚗📊🚂