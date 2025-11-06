"""
Data validation utilities.

Provides validation functions for common data types used throughout the application.
"""

import re
from datetime import datetime
from typing import Tuple

from utils.errors import ValidationError


def validate_symbol(symbol: str) -> bool:
    """
    Validate stock symbol format.

    Valid formats:
    - NSE:INFY
    - BSE:RELIANCE
    - NIFTY50 (index)

    Args:
        symbol: Symbol string to validate

    Returns:
        True if valid, raises ValidationError otherwise

    Raises:
        ValidationError: If symbol format invalid
    """
    if not isinstance(symbol, str):
        raise ValidationError(
            f"Symbol must be string, got {type(symbol).__name__}",
            field="symbol",
        )

    symbol = symbol.strip().upper()

    # Pattern: EXCHANGE:SYMBOL or INDEX
    # Examples: NSE:INFY, BSE:RELIANCE, NIFTY50
    pattern = r"^([A-Z]{3,}:[A-Z0-9]{1,20}|[A-Z0-9]+)$"

    if not re.match(pattern, symbol):
        raise ValidationError(
            f"Invalid symbol format: {symbol}. Expected: EXCHANGE:SYMBOL (e.g., NSE:INFY)",
            field="symbol",
            details={"provided": symbol},
        )

    return True


def validate_price(price: float, min_price: float = 0.01, max_price: float = 1000000) -> bool:
    """
    Validate price value.

    Args:
        price: Price to validate
        min_price: Minimum allowed price
        max_price: Maximum allowed price

    Returns:
        True if valid, raises ValidationError otherwise

    Raises:
        ValidationError: If price invalid
    """
    if not isinstance(price, (int, float)):
        raise ValidationError(
            f"Price must be numeric, got {type(price).__name__}",
            field="price",
        )

    if price < min_price:
        raise ValidationError(
            f"Price {price} is below minimum {min_price}",
            field="price",
            details={"provided": price, "minimum": min_price},
        )

    if price > max_price:
        raise ValidationError(
            f"Price {price} exceeds maximum {max_price}",
            field="price",
            details={"provided": price, "maximum": max_price},
        )

    return True


def validate_quantity(quantity: int, min_qty: int = 1, max_qty: int = 1000000) -> bool:
    """
    Validate quantity value.

    Args:
        quantity: Quantity to validate
        min_qty: Minimum allowed quantity
        max_qty: Maximum allowed quantity

    Returns:
        True if valid, raises ValidationError otherwise

    Raises:
        ValidationError: If quantity invalid
    """
    if not isinstance(quantity, int):
        raise ValidationError(
            f"Quantity must be integer, got {type(quantity).__name__}",
            field="quantity",
        )

    if quantity < min_qty:
        raise ValidationError(
            f"Quantity {quantity} is below minimum {min_qty}",
            field="quantity",
            details={"provided": quantity, "minimum": min_qty},
        )

    if quantity > max_qty:
        raise ValidationError(
            f"Quantity {quantity} exceeds maximum {max_qty}",
            field="quantity",
            details={"provided": quantity, "maximum": max_qty},
        )

    return True


def validate_date(date_str: str, date_format: str = "%Y-%m-%d") -> Tuple[bool, datetime]:
    """
    Validate date string format.

    Args:
        date_str: Date string to validate
        date_format: Expected date format (default: YYYY-MM-DD)

    Returns:
        Tuple of (is_valid, datetime_object)

    Raises:
        ValidationError: If date invalid
    """
    if not isinstance(date_str, str):
        raise ValidationError(
            f"Date must be string, got {type(date_str).__name__}",
            field="date",
        )

    try:
        date_obj = datetime.strptime(date_str.strip(), date_format)
        return True, date_obj
    except ValueError as e:
        raise ValidationError(
            f"Invalid date format: {date_str}. Expected format: {date_format}",
            field="date",
            details={"provided": date_str, "expected_format": date_format},
        )


def validate_score(score: int, min_score: int = 0, max_score: int = 12) -> bool:
    """
    Validate confirmation score (0-12).

    Args:
        score: Confirmation score
        min_score: Minimum allowed score
        max_score: Maximum allowed score

    Returns:
        True if valid, raises ValidationError otherwise

    Raises:
        ValidationError: If score invalid
    """
    if not isinstance(score, int):
        raise ValidationError(
            f"Score must be integer, got {type(score).__name__}",
            field="score",
        )

    if score < min_score or score > max_score:
        raise ValidationError(
            f"Score {score} out of range [{min_score}, {max_score}]",
            field="score",
            details={"provided": score, "min": min_score, "max": max_score},
        )

    return True


def validate_order_id(order_id: str) -> bool:
    """
    Validate Dhan order ID format.

    Expected format: ORD123456 (or similar alphanumeric)

    Args:
        order_id: Order ID to validate

    Returns:
        True if valid, raises ValidationError otherwise

    Raises:
        ValidationError: If order ID invalid
    """
    if not isinstance(order_id, str):
        raise ValidationError(
            f"Order ID must be string, got {type(order_id).__name__}",
            field="order_id",
        )

    if not order_id.strip():
        raise ValidationError(
            "Order ID cannot be empty",
            field="order_id",
        )

    if len(order_id) > 50:
        raise ValidationError(
            f"Order ID too long: {len(order_id)} > 50 chars",
            field="order_id",
            details={"provided": order_id},
        )

    return True


def validate_entry(entry_price: float, stop_loss: float, take_profit: float) -> bool:
    """
    Validate entry signal prices (entry, SL, TP).

    Rules:
    - entry_price > stop_loss (for long)
    - entry_price < take_profit (for long)
    - All prices must be positive

    Args:
        entry_price: Entry price
        stop_loss: Stop loss price
        take_profit: Take profit price

    Returns:
        True if valid, raises ValidationError otherwise

    Raises:
        ValidationError: If prices invalid
    """
    # Validate individual prices
    validate_price(entry_price)
    validate_price(stop_loss)
    validate_price(take_profit)

    # Check relationships
    if stop_loss >= entry_price:
        raise ValidationError(
            f"Stop loss ({stop_loss}) must be below entry ({entry_price})",
            field="stop_loss",
            details={
                "entry_price": entry_price,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
            },
        )

    if take_profit <= entry_price:
        raise ValidationError(
            f"Take profit ({take_profit}) must be above entry ({entry_price})",
            field="take_profit",
            details={
                "entry_price": entry_price,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
            },
        )

    return True


def validate_required_fields(data: dict, required_fields: list[str]) -> bool:
    """
    Validate that required fields are present in dictionary.

    Args:
        data: Dictionary to check
        required_fields: List of required field names

    Returns:
        True if all required fields present, raises ValidationError otherwise

    Raises:
        ValidationError: If any required field missing
    """
    if not isinstance(data, dict):
        raise ValidationError(
            f"Data must be dictionary, got {type(data).__name__}",
            field="data",
        )

    missing_fields = [field for field in required_fields if field not in data]

    if missing_fields:
        raise ValidationError(
            f"Missing required fields: {', '.join(missing_fields)}",
            field="required_fields",
            details={"missing": missing_fields, "expected": required_fields},
        )

    return True