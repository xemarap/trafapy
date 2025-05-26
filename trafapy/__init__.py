"""
Trafikanalys API Python Wrapper

A Python package for interacting with the Trafikanalys API.
"""

__version__ = "0.1.0"

from .client import TrafikanalysClient
from .cache_utils import APICache, DEFAULT_CACHE_DIR