from flask import Blueprint, jsonify, request
from datetime import datetime

api_bp = Blueprint("api", __name__)

@api_bp.get("/api/data")
def get_sample_data():
    return jsonify(
        {
            "data": [
                {"id": 1, "name": "Sample Item 1", "value": 100},
                {"id": 2, "name": "Sample Item 2", "value": 200},
                {"id": 3, "name": "Sample Item 3", "value": 300},
            ],
            "total": 3,
            "timestamp": "2024-01-01T00:00:00Z",
        }
    )

@api_bp.get("/api/items/<int:item_id>")
def get_item(item_id: int):
    return jsonify(
        {
            "item": {
                "id": item_id,
                "name": f"Sample Item {item_id}",
                "value": item_id * 100,
            },
            "timestamp": "2024-01-01T00:00:00Z",
        }
    )

@api_bp.get("/health")
def health():
    # A simple health check endpoint
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
    })

@api_bp.post("/api/scan")
def scan():
    """
    Triggers a scan for given symbols, returns stubbed signal results.
    Accepts JSON: { "symbols": ["NSE:INFY", ...], "interval": "1d", "n": 100 }
    """
    data = request.json or {}
    symbols = data.get("symbols", [])
    interval = data.get("interval", "1d")
    n = data.get("n", 100)

    results = []
    for symbol in symbols:
        # Stubbed feature flags
        features = {
            "obv_bullish": True,
            "rsi_bullish": True,
            "mfi_bullish": True,
            "market_structure": False,
            "candlestick_bullish": False,
            "not_falling": True,
            "htf_uptrend": True,
            "ema_trend": True,
        }
        score = 8  # Stub score
        buy_signal = score >= 6

        results.append({
            "symbol": symbol,
            "score": score,
            "buy_signal": buy_signal,
        })

    return jsonify({
        "timestamp": datetime.utcnow().isoformat(),
        "results": results,
    })

@api_bp.post("/api/order")
def place_order():
    """
    Stubbed order placement endpoint.
    Expects JSON: {symbol, entry, sl, tp, quantity}
    """
    data = request.json or {}
    symbol = data.get("symbol")
    entry = data.get("entry")
    sl = data.get("sl")
    tp = data.get("tp")
    quantity = data.get("quantity", 1)

    # Stub order response
    return jsonify({
        "order_id": "ORD123456",
        "symbol": symbol,
        "entry": entry,
        "stop_loss": sl,
        "take_profit": tp,
        "quantity": quantity,
        "status": "placed",
        "timestamp": datetime.utcnow().isoformat(),
    })

@api_bp.get("/api/order/status/<order_id>")
def order_status(order_id):
    """
    Stubbed order status check.
    """
    # In actual implementation, query Dhan API
    return jsonify({
        "order_id": order_id,
        "status": "filled",
        "filled_quantity": 1,
        "filled_price": 2850.50,
        "timestamp": datetime.utcnow().isoformat(),
    })

@api_bp.get("/admin/cache/health")
def cache_health():
    # Stub cache health; replace with actual cache check
    return jsonify({
        "status": "healthy",
        "backend": "redis",
        "timestamp": datetime.utcnow().isoformat(),
    })

@api_bp.post("/admin/cache/clear")
def cache_clear():
    # Stub cache clear; replace with actual cache clear
    pattern = request.json.get("pattern")
    return jsonify({
        "cleared": True,
        "pattern": pattern,
        "timestamp": datetime.utcnow().isoformat(),
    })
