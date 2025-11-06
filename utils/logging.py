"""
Logging configuration and utilities.

Sets up structured JSON logging for all application components.
Integrates with Sentry for error tracking in production.
"""

import logging
import sys
import os
from typing import Optional

try:
    from pythonjsonlogger import jsonlogger
except ImportError:
    jsonlogger = None

import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.logging import LoggingIntegration


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging.

    Falls back to standard format if pythonjsonlogger unavailable.
    """

    def __init__(self, use_json: bool = True):
        """
        Initialize formatter.

        Args:
            use_json: If True, use JSON format; else use standard format
        """
        self.use_json = use_json and jsonlogger is not None

        if self.use_json:
            super().__init__()
            self.formatter = jsonlogger.JsonFormatter()
        else:
            fmt = (
                "%(asctime)s - %(name)s - %(levelname)s - "
                "[%(filename)s:%(lineno)d] - %(message)s"
            )
            super().__init__(fmt)

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record.

        Args:
            record: Log record to format

        Returns:
            Formatted log string
        """
        if self.use_json:
            # Add custom fields to record
            record.service = "stock-scanner"
            record.environment = os.getenv("ENVIRONMENT", "development")
            return self.formatter.format(record)
        else:
            return super().format(record)


def setup_logging(
    level: str = None,
    json_format: bool = True,
    sentry_dsn: str = None,
    sentry_env: str = None,
) -> logging.Logger:
    """
    Configure logging for the application.

    Sets up:
    - Structured JSON logging to stdout
    - Logging level based on environment
    - Sentry integration for error tracking (production only)

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
               Defaults to DEBUG in dev, INFO in prod
        json_format: If True, use JSON format for logs
        sentry_dsn: Sentry DSN for error tracking
        sentry_env: Sentry environment tag

    Returns:
        Configured root logger instance
    """
    # Determine log level
    if level is None:
        env = os.getenv("ENVIRONMENT", "development")
        level = "DEBUG" if env == "development" else "INFO"

    log_level = getattr(logging, level.upper(), logging.INFO)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers to prevent duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)

    # Set formatter
    formatter = JSONFormatter(use_json=json_format)
    console_handler.setFormatter(formatter)

    # Add handler to root logger
    root_logger.addHandler(console_handler)

    # Configure Sentry if DSN provided
    if sentry_dsn:
        sentry_sdk.init(
            dsn=sentry_dsn,
            environment=sentry_env or os.getenv("ENVIRONMENT", "development"),
            traces_sample_rate=0.1 if sentry_env == "production" else 1.0,
            integrations=[
                FlaskIntegration(),
                LoggingIntegration(
                    level=logging.INFO,  # Capture info and above as breadcrumbs
                    event_level=logging.ERROR,  # Send errors as events
                ),
            ],
        )
        root_logger.info("Sentry error tracking initialized")

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module.

    Args:
        name: Module name (usually __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


# Initialize logger on module import
logger: logging.Logger = get_logger(__name__)

# Configure logging on app startup
if os.getenv("ENVIRONMENT") != "testing":
    setup_logging(
        level=os.getenv("LOG_LEVEL", "INFO"),
        json_format=True,
        sentry_dsn=os.getenv("SENTRY_DSN"),
        sentry_env=os.getenv("ENVIRONMENT", "development"),
    )