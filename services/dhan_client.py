"""
Dhan API client integration.
Handles order placement and tracking via Dhan broker API.
"""

import logging
import requests
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class DhanClient:
    """
    Dhan broker API client for order placement and management.
    API Documentation: https://dhanhq.co/docs/
    """
    
    BASE_URL = "https://api.dhan.co"
    
    def __init__(self, client_id: str, access_token: str):
        """
        Initialize Dhan API client.
        
        Args:
            client_id: Dhan client ID
            access_token: Dhan API access token
        """
        self.client_id = client_id
        self.access_token = access_token
        self.headers = {
            "access-token": access_token,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    def place_super_order(self, symbol: str, entry: float, sl: float, tp: float, quantity: int = 1) -> Dict[str, Any]:
        """
        Places a super order (BUY + target + stoploss).
        
        Args:
            symbol: Trading symbol
            entry: Entry price
            sl: Stop loss price
            tp: Take profit price
            quantity: Quantity to trade
            
        Returns:
            Order response with order_id and status
        """
        try:
            # Prepare order payload
            # Note: Actual Dhan API may have different structure
            # This is a template based on common broker API patterns
            payload = {
                "dhanClientId": self.client_id,
                "transactionType": "BUY",
                "exchangeSegment": "NSE_EQ",
                "productType": "INTRADAY",
                "orderType": "LIMIT",
                "validity": "DAY",
                "securityId": symbol,
                "quantity": quantity,
                "price": entry,
                "triggerPrice": 0,
                # Additional fields for SL and TP
                "stopLoss": sl,
                "takeProfit": tp
            }
            
            response = requests.post(
                f"{self.BASE_URL}/v2/orders",
                json=payload,
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Order placed successfully for {symbol}: {data}")
                return {
                    "order_id": data.get("orderId", "UNKNOWN"),
                    "symbol": symbol,
                    "entry": entry,
                    "stop_loss": sl,
                    "take_profit": tp,
                    "quantity": quantity,
                    "status": "placed",
                    "response": data
                }
            else:
                logger.error(f"Order placement failed: {response.status_code} - {response.text}")
                return {
                    "order_id": None,
                    "symbol": symbol,
                    "entry": entry,
                    "status": "failed",
                    "error": response.text
                }
        except Exception as e:
            logger.error(f"Exception during order placement: {e}")
            return {
                "order_id": None,
                "symbol": symbol,
                "entry": entry,
                "status": "error",
                "error": str(e)
            }

    def get_order_status(self, order_id: str) -> Optional[Dict[str, Any]]:
        """
        Get Dhan order status.
        
        Args:
            order_id: Order ID to check
            
        Returns:
            Order status information or None if failed
        """
        try:
            response = requests.get(
                f"{self.BASE_URL}/v2/orders/{order_id}",
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "order_id": order_id,
                    "status": data.get("orderStatus", "UNKNOWN"),
                    "filled_quantity": data.get("filledQty", 0),
                    "filled_price": data.get("averagePrice", 0),
                    "order_type": data.get("orderType"),
                    "transaction_type": data.get("transactionType"),
                    "raw_response": data
                }
            else:
                logger.error(f"Failed to get order status: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Exception getting order status: {e}")
            return None

    def get_positions(self) -> Optional[list]:
        """
        Get all open positions.
        
        Returns:
            List of positions or None if failed
        """
        try:
            response = requests.get(
                f"{self.BASE_URL}/v2/positions",
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get positions: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Exception getting positions: {e}")
            return None

    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an order.
        
        Args:
            order_id: Order ID to cancel
            
        Returns:
            True if successful, False otherwise
        """
        try:
            response = requests.delete(
                f"{self.BASE_URL}/v2/orders/{order_id}",
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                logger.info(f"Order {order_id} cancelled successfully")
                return True
            else:
                logger.error(f"Failed to cancel order: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Exception cancelling order: {e}")
            return False
