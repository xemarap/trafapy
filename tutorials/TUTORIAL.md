# Trafapy Quick Start Tutorial

Welcome to Trafapy! This tutorial will get you up and running with the Swedish Transport Statistics API in just a few minutes.

## What is Trafapy?

Trafapy is a Python wrapper for the Trafikanalys API, which provides access to comprehensive Swedish transport statistics. You can retrieve data on vehicles, traffic, accidents, and transport patterns across Sweden.

## Installation

```bash
pip install trafapy
```

## Basic Setup

```python
from trafapy import TrafikanalysClient

# Create a client
trafa = TrafikanalysClient(
    language="sv",          # 'sv' for Swedish, 'en' for English
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
    ar=['2020', '2021', '2022', '2023'],  # Multiple years
    drivmedel='all',                       # All fuel types
    reglan=['01'],                         # Stockholm County
    nyregunder=''                          # New registrations
)

df = trafa.get_data_as_dataframe(product_code, query)
print(f"Retrieved {len(df)} rows")
print(df.head())
```

### Get All Available Values

```python
# Get all available years automatically
all_years = trafa.get_all_available_values(product_code, "ar")
print(f"Available years: {all_years}")

# Get all municipalities in Stockholm County
stockholm_municipalities = [
    mun for mun in trafa.get_all_available_values(product_code, "regkom") 
    if mun.startswith("01")  # Stockholm County codes start with "01"
]
print(f"Stockholm municipalities: {stockholm_municipalities[:5]}...")  # Show first 5
```

## Step 4: Cache Management

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

### 4. Handle Large Datasets
For large queries, consider chunking by year or region.

### 5. Explore Before Querying
Always explore variables and options first:
```python
# 1. List products
# 2. Explore variables
# 3. Check variable options
# 4. Build and preview query
# 5. Fetch data
```

For a list with possible API calls and structures for each dataproduct, please visit [Trafikanalys API Documentation](https://www.trafa.se/sidor/api-dokumentation/)

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

## Next Steps

- Explore the full [API documentation](https://www.trafa.se/sidor/oppen-data-api/)
- Check out the complete variable lists for each product
- Combine multiple products for comprehensive analyses
- Use pandas for data analysis and visualization
- Set up automated data collection pipelines

Happy analyzing! 🚗📊