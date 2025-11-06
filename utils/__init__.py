"""
Utilities package for Stock Scanner API.

Provides logging, caching, validation, error handling, and other utilities.
"""

from utils.logging import logger, setup_logging
from utils.cache import CacheManager, cache
from utils.errors import (
    StockScannerError,
    CacheError,
    ValidationError,
    DhanAPIError,
    DataFetchError,
)
from utils.validators import (
    validate_symbol,
    validate_price,
    validate_quantity,
    validate_date,
)

__all__ = [
    # Logging
    "logger",
    "setup_logging",
    # Cache
    "CacheManager",
    "cache",
    # Errors
    "StockScannerError",
    "CacheError",
    "ValidationError",
    "DhanAPIError",
    "DataFetchError",
    # Validators
    "validate_symbol",
    "validate_price",
    "validate_quantity",
    "validate_date",
]