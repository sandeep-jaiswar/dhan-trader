from flask import Blueprint, jsonify, request
from datetime import datetime, timezone

from services import StockDataFetcher, IndicatorCalculator, StrategyEngine
from utils.validators import validate_symbol
from utils.cache import cache

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
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

@api_bp.post("/api/scan")
def scan():
    """
    Triggers a scan for given symbols, returns stubbed signal results.
    Accepts JSON: { "symbols": ["NSE:INFY", ...] }
    """
    payload = request.json or {}
    symbols = payload.get("symbols", [])
    interval = payload.get("interval", "1d")
    n = int(payload.get("n", 200))

    if not isinstance(symbols, list):
        return jsonify({"error": "symbols must be a list"}), 400

    results = []

    for symbol in symbols:
        try:
            # Validate symbol format
            try:
                validate_symbol(symbol)
            except Exception as e:
                results.append({"symbol": symbol, "error": f"invalid symbol: {e}"})
                continue

            # Try cache first
            cache_key = f"scan:{symbol}:{interval}:{n}"
            try:
                cached = cache.get(cache_key)
            except Exception:
                cached = None

            if cached:
                results.append({"symbol": symbol, "cached": True, **cached})
                continue

            # Fetch OHLCV
            data = StockDataFetcher.fetch(symbol, interval=interval, n=n)
            if not data:
                results.append({"symbol": symbol, "error": "no data"})
                continue

            opens = data.get("open", [])
            highs = data.get("high", [])
            lows = data.get("low", [])
            closes = data.get("close", [])
            volumes = data.get("volume", [])

            # Basic sanity checks
            if not closes or len(closes) < 10:
                results.append({"symbol": symbol, "error": "insufficient data"})
                continue

            # Compute indicators
            rsi_vals = IndicatorCalculator.rsi(closes)
            mfi_vals = IndicatorCalculator.mfi(highs, lows, closes, volumes)
            obv_vals = IndicatorCalculator.obv(closes, volumes)
            ema_fast = IndicatorCalculator.ema(closes, 12)
            ema_slow = IndicatorCalculator.ema(closes, 26)
            htf_up = IndicatorCalculator.is_uptrend(closes)
            candle_bull = IndicatorCalculator.detect_bullish_candle(opens, highs, lows, closes, len(closes) - 1)

            last_rsi = next((v for v in reversed(rsi_vals) if v is not None), None)
            last_mfi = next((v for v in reversed(mfi_vals) if v is not None), None)
            last_obv = obv_vals[-1] if obv_vals else None
            prev_obv = obv_vals[-2] if len(obv_vals) >= 2 else None
            last_fast = next((v for v in reversed(ema_fast) if v is not None), None)
            last_slow = next((v for v in reversed(ema_slow) if v is not None), None)

            # Build features for strategy
            features = {
                "obv_bullish": (prev_obv is not None and last_obv is not None and last_obv > prev_obv),
                "rsi_bullish": (last_rsi is not None and last_rsi < 40),
                "mfi_bullish": (last_mfi is not None and last_mfi < 40),
                "market_structure": (closes[-1] > sum(closes[-10:]) / min(10, len(closes))),
                "candlestick_bullish": bool(candle_bull),
                "not_falling": (closes[-1] >= closes[-3] if len(closes) >= 3 else True),
                "htf_uptrend": bool(htf_up),
                "ema_trend": (last_fast is not None and last_slow is not None and last_fast > last_slow),
            }

            score = StrategyEngine.compute_score(features)
            buy_signal = StrategyEngine.detect_long_signal(features)

            result = {
                "score": score,
                "buy_signal": bool(buy_signal),
                "features": features,
                "last": {
                    "close": closes[-1],
                    "rsi": last_rsi,
                    "mfi": last_mfi,
                }
            }

            # Cache the result (best-effort)
            try:
                cache.set(cache_key, result, ttl_hours=1)
            except Exception:
                # Non-fatal if cache fails
                logger = None

            results.append({"symbol": symbol, **result})

        except Exception as e:
            results.append({"symbol": symbol, "error": str(e)})

    return jsonify({
        "timestamp": datetime.now(timezone.utc).isoformat(),
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
        "timestamp": datetime.now(timezone.utc).isoformat(),
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
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

@api_bp.get("/admin/cache/health")
def cache_health():
    # Stub cache health; replace with actual cache check
    return jsonify({
        "status": "healthy",
        "backend": "redis",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

@api_bp.post("/admin/cache/clear")
def cache_clear():
    """Clear cache entries."""
    data = request.json or {}
    pattern = data.get("pattern")
    return jsonify({
        "cleared": True,
        "pattern": pattern,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
