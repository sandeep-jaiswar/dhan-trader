"""
Custom exception classes for Stock Scanner.

Provides hierarchical error handling for different failure scenarios.
"""


class StockScannerError(Exception):
    """
    Base exception for Stock Scanner.

    All custom exceptions inherit from this.
    """

    def __init__(self, message: str, error_code: str = None, details: dict = None):
        """
        Initialize exception.

        Args:
            message: Human-readable error message
            error_code: Machine-readable error code (e.g., 'CACHE_001')
            details: Additional error context as dictionary
        """
        self.message = message
        self.error_code = error_code or "UNKNOWN"
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self) -> str:
        """Return formatted error message."""
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message

    def to_dict(self) -> dict:
        """Convert exception to dictionary for API responses."""
        return {
            "error": self.__class__.__name__,
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
        }


class CacheError(StockScannerError):
    """
    Error related to cache operations.

    Raised when Redis/KV operations fail.
    """

    def __init__(self, message: str, error_code: str = "CACHE_001", details: dict = None):
        """Initialize cache error."""
        super().__init__(message, error_code, details)


class ValidationError(StockScannerError):
    """
    Error related to data validation.

    Raised when input data doesn't meet requirements.
    """

    def __init__(self, message: str, field: str = None, details: dict = None):
        """
        Initialize validation error.

        Args:
            message: Validation error message
            field: Name of field that failed validation
            details: Additional validation details
        """
        if field:
            details = details or {}
            details["field"] = field
        super().__init__(message, "VALIDATION_001", details)


class DhanAPIError(StockScannerError):
    """
    Error related to Dhan API operations.

    Raised when Dhan API calls fail.
    """

    def __init__(
        self,
        message: str,
        status_code: int = None,
        response_body: dict = None,
        error_code: str = "DHAN_001",
    ):
        """
        Initialize Dhan API error.

        Args:
            message: Error message
            status_code: HTTP status code from Dhan
            response_body: Response body from Dhan API
            error_code: Error code prefix (default: DHAN_001)
        """
        details = {
            "status_code": status_code,
            "response_body": response_body,
        }
        super().__init__(message, error_code, details)
        self.status_code = status_code
        self.response_body = response_body

    @property
    def is_retryable(self) -> bool:
        """Check if error is retryable (5xx errors, timeouts)."""
        return self.status_code and 500 <= self.status_code < 600


class DataFetchError(StockScannerError):
    """
    Error related to fetching stock data.

    Raised when data fetching from external sources fails.
    """

    def __init__(
        self,
        message: str,
        source: str = None,
        symbol: str = None,
        error_code: str = "DATA_001",
    ):
        """
        Initialize data fetch error.

        Args:
            message: Error message
            source: Data source that failed (e.g., 'tvdatafeed', 'nselib')
            symbol: Stock symbol that failed
            error_code: Error code prefix
        """
        details = {
            "source": source,
            "symbol": symbol,
        }
        super().__init__(message, error_code, details)
        self.source = source
        self.symbol = symbol


class StrategyError(StockScannerError):
    """
    Error related to strategy signal detection.

    Raised when strategy calculation or signal detection fails.
    """

    def __init__(
        self,
        message: str,
        symbol: str = None,
        error_code: str = "STRATEGY_001",
        details: dict = None,
    ):
        """
        Initialize strategy error.

        Args:
            message: Error message
            symbol: Stock symbol where error occurred
            error_code: Error code prefix
            details: Additional details
        """
        if symbol:
            details = details or {}
            details["symbol"] = symbol
        super().__init__(message, error_code, details)


class SignalProcessingError(StockScannerError):
    """
    Error related to signal processing and order placement.

    Raised when signal cannot be processed or order placement fails.
    """

    def __init__(
        self,
        message: str,
        signal_id: str = None,
        order_id: str = None,
        error_code: str = "SIGNAL_001",
        details: dict = None,
    ):
        """
        Initialize signal processing error.

        Args:
            message: Error message
            signal_id: ID of signal that failed
            order_id: ID of order that failed
            error_code: Error code prefix
            details: Additional details
        """
        details = details or {}
        if signal_id:
            details["signal_id"] = signal_id
        if order_id:
            details["order_id"] = order_id
        super().__init__(message, error_code, details)