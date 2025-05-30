# Trafapy Quick Start Tutorial

Welcome to Trafapy! This tutorial will get you up and running with the Swedish Transport Statistics API in just a few minutes.

## What is Trafapy?

Trafapy is a Python wrapper for the Trafikanalys API, which provides access to comprehensive Swedish transport statistics. You can retrieve data on vehicles, traffic, accidents, and transport patterns across Sweden.

## Installation

```bash
pip install git+https://github.com/xemarap/trafapy.git
```

## Basic Setup

```python
from trafapy import TrafikanalysClient

# Create a client
trafa = TrafikanalysClient(
    rate_limit_enabled=True,    # 'True' is default
    cache_enabled=True          # 'False' as default, but it is recommended to enable
)
```

## Step 1: Explore Available Data

### Find Products (Datasets)

```python
# List all available products
products = trafa.list_products()
print(f"Found {len(products)} products")
print(products[['code', 'label']].head())

# Search for specific topics
car_products = trafa.search_products("personbilar")  # Search for cars
bus_products = trafa.search_products("bussar")       # Search for buses
```

### Understand Product Structure

```python
# Let's work with passenger cars data
product_code = "t10026"  # Passenger cars

# See what variables are available
variables = trafa.explore_product_variables(product_code)
print("Available variables:")
print(variables[['name', 'label', 'type']].head(10))
```

## Step 2: Explore Variable Options

```python
# Check what years are available
year_options = trafa.explore_variable_options(product_code, "ar")
print("Available years:")
print(year_options[['name', 'label']].head())

# Check fuel types
fuel_options = trafa.explore_variable_options(product_code, "drivmedel")
print("\nAvailable fuel types:")
print(fuel_options[['name', 'label']].head())

# Check regions (counties)
region_options = trafa.explore_variable_options(product_code, "reglan")
print("\nAvailable regions:")
print(region_options[['name', 'label']].head())
```

## Step 3: Get Data

### Simple Query

```python
# Get new car registrations for 2023 in Stockholm County
query = trafa.build_query(
    product_code,
    ar=['2023'],           # Year 2023
    reglan=['01'],         # Stockholm County (code 01)
    nyregunder=''          # New registrations (measure, no filter)
)

# Preview the API query
trafa.preview_query(product_code, query)

# Get the data
df = trafa.get_data_as_dataframe(product_code, query)
print(f"Retrieved {len(df)} rows")
print(df.head())
```

### Advanced Query with Multiple Filters

```python
# Get car data by fuel type for multiple years
query = trafa.build_query(
    product_code,
    ar=['2020', '2021', '2022', '2023'],   # Multiple years
    reglan=['01'],                         # Stockholm County
    drivmedel='all',                       # All fuel types
    nyregunder=''                          # New registrations
)

df = trafa.get_data_as_dataframe(product_code, query)
print(f"Retrieved {len(df)} rows")
print(df.head())
```

### Get All Available Values

```python
# Get all municipalities in Stockholm County
stockholm_municipalities = [
    mun for mun in trafa.get_all_available_values(product_code, "regkom") 
    if mun.startswith("01")  # Stockholm County codes start with "01"
]
print(f"Stockholm municipalities: {stockholm_municipalities[:5]}...")  # Show first 5
```

## Step 4: Working with Large Datasets

### Understanding Automatic Batching

When you request a lot of data (many years, municipalities, or other variables), Trafapy automatically splits your query into smaller batches to avoid API limits. This happens transparently!

```python
# This query would be VERY large - Trafapy handles it automatically
large_query = trafa.build_query(
    product_code,
    ar='all',           # All available years
    reglan='all',       # All counties
    regkom='all',       # All municipalities (290+ values)  
    drivmedel='all',    # All fuel types (10+ values)
    nyregunder=''
)

# Trafapy automatically detects this is large and uses batching
print("🔍 Running large query with automatic batching...")
df = trafa.get_data_as_dataframe(product_code, large_query)
print(f"✅ Successfully retrieved {len(df):,} rows!")
```

**What you'll see:**
```
📊 Large query detected - retrieving data in 3 batches...
  📋 Batching variable 'regkom' (52 values)
  ✅ Created 3 batches (max 50 values per variable)
  🔄 Processing batch 1/3... ✅ 1,250 rows
  🔄 Processing batch 2/3... ✅ 1,250 rows  
  🔄 Processing batch 3/3... ✅ 160 rows
  🔗 Combining data from 3 successful batches... ✅
✅ Batch processing complete! Retrieved 2,660 total rows
```

### Controlling Batching Behavior

```python
# Configure batch size (how many values per variable in each batch)
trafa.configure_batching(max_batch_size=25)  # Smaller batches

# Check current settings
batch_info = trafa.get_batching_info()
print(f"Current max batch size: {batch_info['max_batch_size']}")

# Control progress messages
df = trafa.get_data_as_dataframe(product_code, query, show_progress=False)  # Quiet mode

# Disable batching entirely (not recommended for large queries)
df = trafa.get_data_as_dataframe(product_code, query, use_batching=False)
```

### When Does Batching Activate?

Batching automatically activates when any variable has more than 50 values (default). For example:

```python
# This will trigger batching:
query1 = trafa.build_query(product_code, regkom='all')  # All municipalities (290+ values)  

# These will NOT trigger batching:
query2 = trafa.build_query(product_code, ar=['2020', '2021', '2022'])  # Only 3 years
query3 = trafa.build_query(product_code, drivmedel='all')  # Only ~10 fuel types
```

## Step 5: Cache Management

```python
# Check cache status
cache_info = trafa.get_cache_info()
print(f"Cache files: {cache_info['file_count']}")
print(f"Cache size: {cache_info['total_size_mb']} MB")

# Clear old cache files (older than 1 hour)
deleted = trafa.clear_cache(older_than_seconds=3600)
print(f"Deleted {deleted} cache files")
```

## Tips and Best Practices

### 1. Use Caching
Always enable caching for repeated analyses to limit API calls:
```python
trafa = TrafikanalysClient(cache_enabled=True)
```

### 2. Preview Queries
Always preview your queries before fetching large datasets:
```python
trafa.preview_query(product_code, query)
```

### 3. Start Small
When exploring new data, start with a small subset:
```python
# Start with one year and one region
query = trafa.build_query(product_code, ar=['2023'], reglan=['01'])
```

### 4. Let Batching Handle Large Datasets
Don't worry about query size - let Trafapy's automatic batching handle it:

```python
# ✅ GOOD: Let Trafapy handle the complexity
query = trafa.build_query(
    product_code,
    ar='all',               # Let batching handle this
    reglan='all',           # And this
    regkom='all',           # This as well
    drivmedel='all'         # And this too!
)
df = trafa.get_data_as_dataframe(product_code, query)
```

### 5. Monitor Progress for Large Queries
Enable progress messages for large datasets:
```python
# See what's happening during batch processing
df = trafa.get_data_as_dataframe(product_code, query, show_progress=True)
```

### 6. Adjust Batch Size Based on Your Needs

```python
# For complex queries with many variables, use smaller batches
trafa.configure_batching(max_batch_size=25)

# For simple queries, you can use larger batches  
trafa.configure_batching(max_batch_size=100)

# For very slow connections, use smaller batches
trafa.configure_batching(max_batch_size=10)
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

### 7. Explore Before Querying
For a list with possible API calls and structures for each dataproduct, please visit [Trafikanalys API Documentation](https://www.trafa.se/sidor/api-dokumentation/)

Always explore variables and options first:
```python
# 1. List products
# 2. Explore variables
# 3. Check variable options
# 4. Build and preview query
# 5. Fetch data
```

### 8. Use Debug Mode When Stuck
Enable debug mode to understand what's happening:
```python
trafa = TrafikanalysClient(debug=True)
```

You'll see detailed information about:
- API requests being made
- Batching decisions and progress
- Rate limiting delays
- Cache hits and misses

## Real-World Example: Comprehensive Analysis

Here's a complete example showing how to analyze electric vehicle adoption across Sweden:

```python
# Initialize client with best practices
trafa = TrafikanalysClient(
    cache_enabled=True,
    rate_limit_enabled=True,
    debug=False  # Set to True if you want to see what's happening
)

# Analyze electric vehicle registrations
product_code = "t10026"

# Build a comprehensive query
ev_query = trafa.build_query(
    product_code,
    ar='all',                   # All available years
    reglan='all',               # All counties
    regkom='all',               # All municipalities
    drivmedel=['103'],          # Electric vehicles only
    nyregunder=''               # New registrations
)

print("🔍 Analyzing electric vehicle registrations across Sweden...")
print("⚡ This is a large query - automatic batching will be used")

# Get the data (batching happens automatically)
df = trafa.get_data_as_dataframe(product_code, ev_query, show_progress=True)

print(f"\n📊 Analysis complete!")
print(f"Retrieved {len(df):,} records of electric vehicle registrations")
print(f"Years covered: {sorted(df['ar'].unique())}")
print(f"Counties covered: {len(df['reglan'].unique())}")
```

## Common Product Codes

| Code | Description |
|------|-------------|
| t10026 | Passenger cars |
| t10011 | Buses |
| t10013 | Trucks |
| t10014 | Motorcycles |
| t1004 | Road traffic injuries |
| t0603 | Railway transport |
| t0802 | Maritime traffic |

## Common Variable Names

| Variable | Description |
|----------|-------------|
| ar | Year |
| reglan | County |
| regkom | Municipality |
| drivmedel | Fuel type |
| nyregunder | New registrations |
| itrfslut | Vehicles in traffic |
| avregunder | Deregistrations |

## Error Handling

```python
try:
    df = trafa.get_data_as_dataframe(product_code, query)
    print(f"Success! Got {len(df)} rows")
except Exception as e:
    print(f"Error: {e}")
    # Check if product code and variables are correct
    variables = trafa.explore_product_variables(product_code)
    print("Available variables:", variables['name'].tolist())
```

## Debugging and Troubleshooting
When things don't work as expected, TrafaPy's debug mode is your best friend! Enable it to see exactly what's happening behind the scenes.

### Enable Debug Mode
```python
# Create client with debug mode enabled
trafa = TrafikanalysClient(debug=True)  # Enable detailed logging
```
What does debug show?

- API request URLs being made
- Cache hits and misses  
- Response structure details
- Number of rows/columns received
- Rate limiting delays
- Batching decisions and progress

Sample debug output:
```html
Making request to: https://api.trafa.se/api/structure?lang=sv
Got 45 products from API
Making request to: https://api.trafa.se/api/structure?query=t10026&lang=sv
API response structure: ['StructureItems', 'DataCount', 'ValidatedRequestType']
Found product: Personbilar
📊 Large query detected - retrieving data in 2 batches...
  📋 Batching variable 'regkom' (52 values)
Rate limiting: waiting 1.00 seconds
Making request to: https://api.trafa.se/api/data?query=t10026|ar:2023|regkom:0114,0115,0117&lang=sv
Got 150 rows from API
Processing 150 rows
Processed 150 rows
```

## Summary: Trafapy Makes Large Queries Easy

**The key takeaway**: Don't worry about query complexity or size. Trafapy's automatic batching means you can:

- ✅ Request `'all'` for any variable
- ✅ Combine multiple large variables
- ✅ Get comprehensive datasets without manual chunking
- ✅ See progress in real-time
- ✅ Trust that results are complete and deduplicated

Focus on your analysis, not API limitations!

## Next Steps

- Explore the full [API documentation](https://www.trafa.se/sidor/oppen-data-api/)
- Check out the complete variable lists for each product
- Combine multiple products for comprehensive analyses
- Use pandas for data analysis and visualization
- Set up automated data collection pipelines

Happy analyzing! 🚗📊