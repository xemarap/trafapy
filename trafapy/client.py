
import requests
import pandas as pd
import logging
from typing import Dict, List, Union, Optional, Any

from .cache_utils import APICache, cached_api_request, DEFAULT_CACHE_DIR

logger = logging.getLogger(__name__)

class TrafikanalysClient:
    """
    Simplified client for the Trafikanalys API focused on retrieving data using known queries.
    """
    
    BASE_URL = "https://api.trafa.se/api"
    
    def __init__(self, language: str = "sv", debug: bool = False, 
                 cache_enabled: bool = False, cache_dir: str = DEFAULT_CACHE_DIR,
                 cache_expiry_seconds: int = 1800):  # Default: 30 minutes
        """
        Initialize the client.
        
        Args:
            language: Language for responses, 'sv' for Swedish or 'en' for English
            debug: Whether to print debug information
            cache_enabled: Whether to use caching
            cache_dir: Directory to store cache files
            cache_expiry_seconds: Cache expiry time in seconds
        """
        self.language = language
        self.debug = debug
        self.session = requests.Session()
        self.cache = APICache(
            cache_dir=cache_dir,
            expiry_seconds=cache_expiry_seconds,
            enabled=cache_enabled
        )
    
    def _make_request(self, url: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make an HTTP request and return the response as JSON.
        
        Args:
            url: Request URL
            params: Request parameters
            
        Returns:
            Response JSON data
        """
        response = self.session.get(url, params=params)
        
        if response.status_code != 200:
            if self.debug:
                print(f"Request failed with status code {response.status_code}")
                print(f"Response text: {response.text}")
            return {}
        
        return response.json()
    
    def list_products(self) -> pd.DataFrame:
        """
        List all available products.
        
        Returns:
            DataFrame with product information
        """
        url = f"{self.BASE_URL}/structure"
        
        # Use cached request
        data = cached_api_request(
            cache=self.cache,
            request_func=self._make_request,
            url=url,
            params={"lang": self.language},
            debug=self.debug
        )
        
        if not data or 'StructureItems' not in data:
            if self.debug:
                print("No products found in response")
            return pd.DataFrame()
        
        products = data['StructureItems']
        
        product_data = []
        for product in products:
            product_data.append({
                'code': product.get('Name', ''),
                'label': product.get('Label', ''),
                'description': product.get('Description', ''),
                'id': product.get('Id', ''),
                'unique_id': product.get('UniqueId', ''),
                'active_from': product.get('ActiveFrom', '')
            })
        
        return pd.DataFrame(product_data)
    
    def search_products(self, search_term):
        """
        Search for products in the Trafikanalys API.
    
        Args:
            search_term: Term to search for
            language: Language for responses, 'sv' for Swedish or 'en' for English
            debug: Whether to print debug information
        
        Returns:
            DataFrame with matching products
        """
        products = self.list_products()
    
        if products.empty:
            return products
    
        # Search in label and description
        search_term = search_term.lower()
        mask = (
            products['label'].str.lower().str.contains(search_term, na=False) | 
            products['description'].str.lower().str.contains(search_term, na=False)
        )
    
        return products[mask]
    
    def _build_query(self, product_code: str, variables: Dict[str, Union[str, List[str]]]) -> str:
        """
        Build a query string for the API.
        
        Args:
            product_code: The product code (e.g., "t10016")
            variables: Dictionary of variables and values (e.g., {"ar": ["2020", "2021"]})
            
        Returns:
            Query string
        """
        query_parts = [product_code]
        
        for var_name, var_values in variables.items():
            if isinstance(var_values, list) and var_values:
                # Multiple values
                values_str = ",".join(str(v) for v in var_values)
                query_parts.append(f"{var_name}:{values_str}")
            elif var_values:
                # Single value
                query_parts.append(f"{var_name}:{var_values}")
            else:
                # No filter, just include the variable
                query_parts.append(var_name)
        
        return "|".join(query_parts)
    
    def _get_data(self, query: str) -> Dict[str, Any]:
        """
        Get data from the API.
        
        Args:
            query: Query string
            
        Returns:
            API response data
        """
        url = f"{self.BASE_URL}/data"
        
        if self.debug:
            print(f"Making request to: {url}?query={query}&lang={self.language}")
        
        # Use cached request
        data = cached_api_request(
            cache=self.cache,
            request_func=self._make_request,
            url=url,
            params={"query": query, "lang": self.language},
            debug=self.debug
        )
        
        if self.debug and 'Rows' in data:
            print(f"Got {len(data['Rows'])} rows from API")
            
            # Print column information if available
            if 'Header' in data and 'Column' in data['Header']:
                columns = data['Header']['Column']
                print(f"Found {len(columns)} columns in response")
                for col in columns[:5]:  # Show first 5 columns
                    print(f"  - {col.get('Name')}: {col.get('Value')} ({col.get('Type')})")
                
                if len(columns) > 5:
                    print(f"  - ... and {len(columns) - 5} more columns")
            
        return data
    
    def _get_structure(self, query: str = "") -> Dict[str, Any]:
        """
        Get structure information from the API.
        
        Args:
            query: Query string (optional)
            
        Returns:
            API response data
        """
        url = f"{self.BASE_URL}/structure"
        params = {"lang": self.language}
        
        if query:
            params["query"] = query
        
        if self.debug:
            param_str = "&".join(f"{k}={v}" for k, v in params.items())
            print(f"Making request to: {url}?{param_str}")
        
        # Use cached request
        return cached_api_request(
            cache=self.cache,
            request_func=self._make_request,
            url=url,
            params=params,
            debug=self.debug
        )
    
    def _process_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a row from the API response.
        
        Args:
            row: API response row
            
        Returns:
            Processed row data
        """
        processed = {}
        
        if 'Cell' in row:
            cells = row['Cell']
            
            if isinstance(cells, list):
                for cell in cells:
                    if isinstance(cell, dict):
                        col_name = cell.get('Column')
                        value = cell.get('Value')
                        
                        if col_name:
                            processed[col_name] = value
            elif isinstance(cells, dict):
                col_name = cells.get('Column')
                value = cells.get('Value')
                
                if col_name:
                    processed[col_name] = value
        
        return processed
    
    def _data_to_dataframe(self, data: Dict[str, Any]) -> pd.DataFrame:
        """
        Convert API data to a DataFrame.
        
        Args:
            data: API response data
            
        Returns:
            DataFrame with the data
        """
        if not data or 'Rows' not in data or not data['Rows']:
            if self.debug:
                print("No rows in data")
            return pd.DataFrame()
        
        rows = data['Rows']
        
        if self.debug:
            print(f"Processing {len(rows)} rows")
            
        processed_rows = [self._process_row(row) for row in rows]
        
        # Filter out empty rows
        processed_rows = [row for row in processed_rows if row]
        
        if self.debug:
            print(f"Processed {len(processed_rows)} rows")
            if processed_rows:
                print(f"Columns in first row: {list(processed_rows[0].keys())}")
        
        return pd.DataFrame(processed_rows)
    
    def get_data_as_dataframe(self, product_code: str, variables: Dict[str, Union[str, List[str]]]) -> pd.DataFrame:
        """
        Get data from the API as a DataFrame.
        
        Args:
            product_code: The product code (e.g., "t10016")
            variables: Dictionary of variables and values (e.g., {"ar": ["2020", "2021"]})
            
        Returns:
            DataFrame with the data
        """
        query = self._build_query(product_code, variables)
        
        if self.debug:
            print(f"Query: {query}")
        
        data = self._get_data(query)
        return self._data_to_dataframe(data)
    
    def clear_cache(self, older_than_seconds: Optional[int] = None) -> int:
        """
        Clear the cache.
        
        Args:
            older_than_seconds: Only clear files older than this many seconds
            
        Returns:
            Number of files deleted
        """
        return self.cache.clear_cache(older_than_seconds)
    
    def get_cache_info(self) -> Dict[str, Any]:
        """
        Get information about the cache.
        
        Returns:
            Dictionary with cache information
        """
        return self.cache.get_cache_info()
    


    """
    Functions for exploring variables and filter options in the Trafikanalys API.
    """ 

    def explore_product_variables(self, product_code: str) -> pd.DataFrame:
        """
        Explore the available variables for a product code in the Trafikanalys API.
        
        Args:
            product_code: The product code (e.g., "t10011")
            
        Returns:
            DataFrame with variable information (name, label, type, description)
        """
        # Use cached request through the API structure
        data = self._get_structure(query=product_code)
        
        if self.debug:
            print(f"API response structure: {list(data.keys())}")
        
        # Extract variables from the structure
        variables = []
        
        if 'StructureItems' not in data:
            if self.debug:
                print("No 'StructureItems' in API response")
            return pd.DataFrame()
        
        def process_item(item, parent_hierarchy=None):
            """Process an item and its children recursively."""
            item_type = item.get('Type', '')
            item_name = item.get('Name', '')
            
            # Process depending on type
            if item_type == 'D':  # Variable
                variables.append({
                    'name': item_name,
                    'label': item.get('Label', ''),
                    'type': 'Variable',
                    'description': item.get('Description', ''),
                    'data_type': item.get('DataType', ''),
                    'has_filter_options': True,
                    'parent_hierarchy': parent_hierarchy
                })
            elif item_type == 'M':  # Measure
                variables.append({
                    'name': item_name,
                    'label': item.get('Label', ''),
                    'type': 'Measure',
                    'description': item.get('Description', ''),
                    'data_type': item.get('DataType', ''),
                    'has_filter_options': False,
                    'parent_hierarchy': parent_hierarchy
                })
            elif item_type == 'H':  # Hierarchy
                # Add the hierarchy itself as a "group" type
                variables.append({
                    'name': item_name,
                    'label': item.get('Label', ''),
                    'type': 'Hierarchy',
                    'description': item.get('Description', ''),
                    'data_type': item.get('DataType', ''),
                    'has_filter_options': False,
                    'parent_hierarchy': parent_hierarchy
                })
                
                # Process children of the hierarchy
                if 'StructureItems' in item and item['StructureItems']:
                    for child_item in item['StructureItems']:
                        process_item(child_item, item_name)  # Pass current hierarchy as parent
        
        # Process both cases: When items are inside the product and when they're at top level
        for item in data['StructureItems']:
            # Check if this is our product
            if item.get('Name') == product_code and item.get('Type') == 'P':
                if self.debug:
                    print(f"Found product: {item.get('Label')}")
                
                # Look for variables inside the product
                if 'StructureItems' in item and item['StructureItems']:
                    for var_item in item['StructureItems']:
                        process_item(var_item)
                        
            # Also check for variables at top level (with our product code as parent)
            elif item.get('ParentName') == product_code:
                process_item(item)
        
        if not variables and self.debug:
            print("No variables found for this product")
            
            # Print some details about what we found to help diagnose
            print(f"Total StructureItems: {len(data['StructureItems'])}")
            for idx, item in enumerate(data['StructureItems'][:5]):  # Show first 5 items
                print(f"Item {idx}: Name={item.get('Name')}, Type={item.get('Type')}, ParentName={item.get('ParentName')}")
        
        return pd.DataFrame(variables)


    def explore_variable_options(self, product_code: str, variable_name: str) -> pd.DataFrame:
        """
        Explore the available filter options for a variable in a product.
        
        Args:
            product_code: The product code (e.g., "t10011")
            variable_name: The variable name (e.g., "ar" for year)
            
        Returns:
            DataFrame with filter options (name, label, description)
        """
        # First try direct access to the variable (this works for most variables including those in hierarchies)
        direct_query = f"{product_code}|{variable_name}"
        
        # Get the structure for the product + variable directly
        url = f"{self.BASE_URL}/structure"
        params = {"query": direct_query, "lang": self.language}
        
        if self.debug:
            print(f"Making request to: {url}?query={direct_query}&lang={self.language}")
            
        # Use cached request
        data = cached_api_request(
            cache=self.cache,
            request_func=self._make_request,
            url=url,
            params=params,
            debug=self.debug
        )
        
        # Extract filter options from the structure
        filter_options = []
        
        if 'StructureItems' not in data:
            if self.debug:
                print("No 'StructureItems' in direct API response, trying hierarchical approach")
            # If direct access fails, try the hierarchical approach
            return self._explore_variable_options_hierarchical(product_code, variable_name)
        
        # First, try to find the variable in the top-level items
        variable_found = False
        
        for item in data['StructureItems']:
            if item.get('Name') == variable_name:
                variable_found = True
                if self.debug:
                    print(f"Found variable: {item.get('Label')}")
                
                if 'StructureItems' in item and item['StructureItems']:
                    self._process_filter_options(item['StructureItems'], filter_options)
                break
        
        # If not found in top-level, search inside the product item and hierarchies
        if not variable_found:
            # Recursive function to find variable in nested structure
            def find_variable(items):
                for item in items:
                    if item.get('Name') == variable_name:
                        if self.debug:
                            print(f"Found variable: {item.get('Label')}")
                        
                        if 'StructureItems' in item and item['StructureItems']:
                            self._process_filter_options(item['StructureItems'], filter_options)
                        return True
                    
                    # Look in children
                    if 'StructureItems' in item and item['StructureItems']:
                        if find_variable(item['StructureItems']):
                            return True
                
                return False
            
            for item in data['StructureItems']:
                if 'StructureItems' in item and item['StructureItems']:
                    if find_variable(item['StructureItems']):
                        variable_found = True
                        break
        
        if not variable_found:
            if self.debug:
                print(f"Variable {variable_name} not found in direct API response, trying hierarchical approach")
            # If variable not found with direct approach, try hierarchical
            return self._explore_variable_options_hierarchical(product_code, variable_name)
        
        if not filter_options and self.debug:
            print("No filter options found for this variable")
        
        return pd.DataFrame(filter_options)


    def _process_filter_options(self, items: List[Dict], filter_options: List[Dict]) -> None:
        """
        Process filter option items and add them to the filter_options list.
        
        Args:
            items: List of filter option items
            filter_options: List to add filter options to
        """
        for option in items:
            if option.get('Type') in ['DV', 'F']:  # DV = variable value, F = filter
                filter_options.append({
                    'name': option.get('Name', ''),
                    'label': option.get('Label', ''),
                    'description': option.get('Description', ''),
                    'option_type': 'Filter' if option.get('Type') == 'F' else 'Value',
                    'unique_id': option.get('UniqueId', '')
                })

    def preview_query(self, product_code: str, query_dict: Dict[str, Any]) -> str:
        """
        Preview the API query that would be generated from the provided parameters.
        
        Args:
            product_code: The product code (e.g., "t10011")
            query_dict: Dictionary with selected variables and filters
            
        Returns:
            The API query string
        """
        query = self._build_query(product_code, query_dict)
        
        print(f"\nAPI Query Preview:")
        print(f"https://api.trafa.se/api/data?query={query}")
        
        return query
    
    def _explore_variable_options_hierarchical(self, product_code: str, variable_name: str) -> pd.DataFrame:
        """
        Explore variable options using a hierarchical approach as fallback.
        
        Args:
            product_code: The product code
            variable_name: The variable name
            
        Returns:
            DataFrame with filter options
        """
        # First, check if this is part of a hierarchy by getting the product structure
        data = self._get_structure(query=product_code)
        
        # Find hierarchy path to the variable
        hierarchy_path = None
        
        def find_variable_in_structure(items, parent_path=None):
            """Find a variable in the structure and return its hierarchy path."""
            path = parent_path[:] if parent_path else []
            
            for item in items:
                item_type = item.get('Type', '')
                item_name = item.get('Name', '')
                
                if item_name == variable_name and item_type in ['D', 'M']:
                    return path
                
                if item_type == 'H':
                    # Add this hierarchy to the path
                    new_path = path + [item_name]
                    
                    # Look in children
                    if 'StructureItems' in item and item['StructureItems']:
                        result = find_variable_in_structure(item['StructureItems'], new_path)
                        if result:
                            return result
            
            return None
        
        if 'StructureItems' in data:
            for item in data['StructureItems']:
                if item.get('Type') == 'P' and item.get('Name') == product_code:
                    if 'StructureItems' in item and item['StructureItems']:
                        hierarchy_path = find_variable_in_structure(item['StructureItems'])
        
        if not hierarchy_path:
            if self.debug:
                print(f"No hierarchy path found for variable {variable_name}")
            return pd.DataFrame()
        
        # Build the query string based on hierarchy path
        query = product_code
        for h in hierarchy_path:
            query += f"|{h}"
        query += f"|{variable_name}"
        
        if self.debug:
            print(f"Using hierarchical query: {query}")
        
        # Get the structure for the product + hierarchy + variable
        url = f"{self.BASE_URL}/structure"
        params = {"query": query, "lang": self.language}
        
        # Use cached request
        data = cached_api_request(
            cache=self.cache,
            request_func=self._make_request,
            url=url,
            params=params,
            debug=self.debug
        )
        
        # Extract filter options from the structure
        filter_options = []
        
        if 'StructureItems' not in data:
            if self.debug:
                print("No 'StructureItems' in hierarchical API response")
            return pd.DataFrame()
        
        # First, try to find the variable in the top-level items
        variable_found = False
        
        for item in data['StructureItems']:
            if item.get('Name') == variable_name:
                variable_found = True
                if self.debug:
                    print(f"Found variable in hierarchical response: {item.get('Label')}")
                
                if 'StructureItems' in item and item['StructureItems']:
                    self._process_filter_options(item['StructureItems'], filter_options)
                break
        
        # If not found in top-level, search recursively
        if not variable_found:
            def find_variable(items):
                for item in items:
                    if item.get('Name') == variable_name:
                        if self.debug:
                            print(f"Found variable in hierarchical response: {item.get('Label')}")
                        
                        if 'StructureItems' in item and item['StructureItems']:
                            self._process_filter_options(item['StructureItems'], filter_options)
                        return True
                    
                    # Look in children
                    if 'StructureItems' in item and item['StructureItems']:
                        if find_variable(item['StructureItems']):
                            return True
                
                return False
            
            for item in data['StructureItems']:
                if 'StructureItems' in item and item['StructureItems']:
                    if find_variable(item['StructureItems']):
                        variable_found = True
                        break
        
        if not variable_found and self.debug:
            print(f"Variable {variable_name} not found in hierarchical API response")
        
        if not filter_options and self.debug:
            print("No filter options found for this variable")
        
        return pd.DataFrame(filter_options)


    """
    Functions for automating queries for the Trafikanalys API.
    """ 

    def get_all_available_values(self, product_code: str, variable_name: str, exclude_totals: bool = True) -> List[str]:
        """
        Get all available values for any variable in a product.
        
        Args:
            product_code: The product code (e.g., "t10026")
            variable_name: The variable name (e.g., "ar", "drivmedel", "reglan")
            exclude_totals: Whether to exclude total values like 't1'
            
        Returns:
            List of available values as strings
        """
        # Get filter options for the variable
        options_df = self.explore_variable_options(product_code, variable_name)
        
        if options_df.empty:
            if self.debug:
                print(f"No options found for variable {variable_name} in product {product_code}")
            return []
        
        # Extract values
        values = []
        for _, row in options_df.iterrows():
            value_name = row['name']
            
            # Skip total values if requested
            if exclude_totals and value_name in ['t1', 'totalt', 'total']:
                continue
                
            # Skip special filter options for years
            if variable_name == 'ar' and value_name in ['senaste', 'forra']:
                continue
                
            values.append(value_name)
        
        # Sort years in ascending order if this is the year variable
        if variable_name == 'ar':
            # Filter to only numeric years and sort
            numeric_years = [year for year in values if year.isdigit() and len(year) == 4]
            numeric_years.sort()
            values = numeric_years
        
        if self.debug:
            print(f"Found {len(values)} available values for {variable_name} in {product_code}: {values}")
        
        return values

    def build_query(self, product_code: str, **kwargs) -> Dict[str, Union[str, List[str]]]:
        """
        Build a query with automated fetching of available values.
        
        Args:
            product_code: The product code
            **kwargs: Variable configurations where:
                    - key is variable name
                    - value can be:
                    - 'all': get all available values
                    - list of specific values
                    - empty string for no filter
                    - single string value
        
        Returns:
            Dictionary with query parameters
        
        Example:
            query = client.build_query(
                "t10026",
                ar='all',        # Get all available years
                drivmedel='all', # Get all fuel types
                reglan=['01'],   # Specific region
                nyregunder=''    # No filter (measure)
            )
        """
        query_dict = {}
        
        for variable_name, value_spec in kwargs.items():
            if value_spec == 'all':
                query_dict[variable_name] = self.get_all_available_values(product_code, variable_name)
            elif isinstance(value_spec, list):
                query_dict[variable_name] = value_spec
            else:
                query_dict[variable_name] = value_spec
        
        if self.debug:
            print("Built automated query:")
            for key, value in query_dict.items():
                if isinstance(value, list) and len(value) > 5:
                    print(f"  {key}: [{value[0]}, {value[1]}, ..., {value[-2]}, {value[-1]}] ({len(value)} values)")
                else:
                    print(f"  {key}: {value}")
        
        return query_dict
