"""
Utilities for caching API responses.
"""

import os
import json
import time
import hashlib
from typing import Dict, Any, Optional, Callable

# Default cache directory
DEFAULT_CACHE_DIR = os.path.join(os.path.expanduser("~"), ".trafapy_cache")

class APICache:
    """
    Cache for API responses to improve performance and reduce API load.
    """
    
    def __init__(self, cache_dir: str = DEFAULT_CACHE_DIR, 
                 expiry_seconds: int = 86400,  # Default: 1 day
                 enabled: bool = True):
        """
        Initialize the cache.
        
        Args:
            cache_dir: Directory to store cache files
            expiry_seconds: Cache expiry time in seconds
            enabled: Whether caching is enabled
        """
        self.cache_dir = cache_dir
        self.expiry_seconds = expiry_seconds
        self.enabled = enabled

    def _ensure_cache_dir_exists(self):
        """Ensure cache directory exists if caching is enabled."""
        if self.enabled and not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

    def generate_cache_key(self, url: str, params: Dict[str, Any]) -> str:
        """
        Generate a cache key for a request.
        
        Args:
            url: Request URL
            params: Request parameters
            
        Returns:
            Cache key
        """
        # Create a string representation of the request
        request_str = f"{url}?{json.dumps(params, sort_keys=True)}"
        
        # Hash the request string
        hash_obj = hashlib.md5(request_str.encode('utf-8'))
        return hash_obj.hexdigest()
    
    def get_cache_path(self, cache_key: str) -> str:
        """
        Get the file path for a cache key.
        
        Args:
            cache_key: Cache key
            
        Returns:
            Cache file path
        """
        return os.path.join(self.cache_dir, f"{cache_key}.json")
    
    def is_cache_valid(self, cache_key: str) -> bool:
        """
        Check if a cache file exists and is not expired.
        
        Args:
            cache_key: Cache key
            
        Returns:
            True if cache is valid, False otherwise
        """
        if not self.enabled:
            return False
        
        cache_path = self.get_cache_path(cache_key)
        
        if not os.path.exists(cache_path):
            return False
        
        # Check if file is expired
        file_mod_time = os.path.getmtime(cache_path)
        current_time = time.time()
        
        return (current_time - file_mod_time) < self.expiry_seconds
    
    def get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        Get data from cache.
        
        Args:
            cache_key: Cache key
            
        Returns:
            Cached data or None if not found
        """
        if not self.is_cache_valid(cache_key):
            return None
        
        cache_path = self.get_cache_path(cache_key)
        
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError, IOError):
            # If reading cache fails, return None
            return None
    
    def save_to_cache(self, cache_key: str, data: Dict[str, Any]) -> bool:
        """
        Save data to cache.
        
        Args:
            cache_key: Cache key
            data: Data to cache
            
        Returns:
            True if saving was successful, False otherwise
        """
        if not self.enabled:
            return False
        
        self._ensure_cache_dir_exists()  # Create only when needed

        cache_path = self.get_cache_path(cache_key)
        
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False)
            return True
        except (IOError, OSError):
            # If saving cache fails, return False
            return False
    
    def clear_cache(self, older_than_seconds: Optional[int] = None) -> int:
        """
        Clear cache files.
        
        Args:
            older_than_seconds: Only clear files older than this many seconds
            
        Returns:
            Number of files deleted
        """
        if not os.path.exists(self.cache_dir):
            return 0
        
        files = os.listdir(self.cache_dir)
        count = 0
        
        current_time = time.time()
        
        for file in files:
            if file.endswith('.json'):
                file_path = os.path.join(self.cache_dir, file)
                
                # If older_than_seconds is specified, check file age
                if older_than_seconds is not None:
                    file_mod_time = os.path.getmtime(file_path)
                    if (current_time - file_mod_time) < older_than_seconds:
                        continue
                
                try:
                    os.remove(file_path)
                    count += 1
                except OSError:
                    pass
        
        return count
    
    def get_cache_info(self) -> Dict[str, Any]:
        """
        Get information about the cache.

        Returns:
            Dictionary with cache information
        """
        if not self.enabled:
            return {
                "cache_dir": self.cache_dir,
                "enabled": False,
                "expiry_seconds": self.expiry_seconds,
                "file_count": 0,
                "total_size_bytes": 0,
                "total_size_mb": 0.0,
                "oldest_file_age_seconds": 0,
                "newest_file_age_seconds": 0
            }
        
        if not os.path.exists(self.cache_dir):
            # Don't create directory just for info
            return {
                "cache_dir": self.cache_dir,
                "enabled": True,
                "expiry_seconds": self.expiry_seconds,
                "file_count": 0,
                "total_size_bytes": 0,
                "total_size_mb": 0.0,
                "oldest_file_age_seconds": 0,
                "newest_file_age_seconds": 0
            }

        files = [f for f in os.listdir(self.cache_dir) if f.endswith('.json')]
        file_count = len(files)
        
        if file_count == 0:
            return {
                "cache_dir": self.cache_dir,
                "enabled": True,
                "expiry_seconds": self.expiry_seconds,
                "file_count": 0,
                "total_size_bytes": 0,
                "total_size_mb": 0.0,
                "oldest_file_age_seconds": 0,
                "newest_file_age_seconds": 0
            }
        
        total_size = 0
        oldest_time = float('inf')
        newest_time = 0
        current_time = time.time()
        
        for file in files:
            file_path = os.path.join(self.cache_dir, file)
            file_size = os.path.getsize(file_path)
            file_mod_time = os.path.getmtime(file_path)
            
            total_size += file_size
            oldest_time = min(oldest_time, file_mod_time)
            newest_time = max(newest_time, file_mod_time)
        
        return {
            "cache_dir": self.cache_dir,
            "enabled": True,
            "expiry_seconds": self.expiry_seconds,
            "file_count": file_count,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "oldest_file_age_seconds": round(current_time - oldest_time),
            "newest_file_age_seconds": round(current_time - newest_time)
        }


def cached_api_request(cache: APICache, request_func: Callable, url: str, params: Dict[str, Any], 
                       debug: bool = False) -> Dict[str, Any]:
    """
    Make an API request with caching.
    
    Args:
        cache: APICache instance
        request_func: Function to make the actual request
        url: Request URL
        params: Request parameters
        debug: Whether to print debug information
        
    Returns:
        API response data
    """
    cache_key = cache.generate_cache_key(url, params)
    
    # Try to get from cache first
    cached_data = cache.get_from_cache(cache_key)
    
    if cached_data is not None:
        if debug:
            print(f"Using cached response for {url}")
        return cached_data
    
    # Not in cache or expired, make the actual request
    if debug:
        print(f"Making API request to {url}")
    
    response_data = request_func(url, params)
    
    # Cache the response
    if response_data:
        success = cache.save_to_cache(cache_key, response_data)
        if debug and success:
            print(f"Saved response to cache with key {cache_key}")
    
    return response_data