# extensions/charts/routes.py
import os, json
from flask import Blueprint, render_template, jsonify, request, current_app
from .fyers_fetcher import fetch_ohlc
from .indicators import attach_indicators
from .signal_store import read_signals

import os
bp = Blueprint(
    "charts_ext",
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), "../templates"),
    static_folder=os.path.join(os.path.dirname(__file__), "../static"),
    static_url_path="/charts_static"
)

@bp.route('/charts')
def charts_page():
    # Use standalone template to avoid conflicts with base.html
    return render_template('charts_standalone.html')

@bp.route("/signals")
def signals_page():
    return render_template("signals.html")

@bp.route("/api/ohlc/<path:symbol>")
def api_ohlc(symbol):
    interval = request.args.get("interval", "5minute")
    duration = int(request.args.get("duration", "240"))
    data = fetch_ohlc(symbol, interval=interval, duration_minutes=duration)
    return jsonify(data)

@bp.route("/api/indicators/<path:symbol>")
def api_indicators(symbol):
    interval = request.args.get("interval", "5minute")
    duration = int(request.args.get("duration", "240"))
    emas = request.args.get("ema", "")  # comma separated
    rsi = request.args.get("rsi", None)
    emas_list = [int(x) for x in emas.split(",") if x.strip().isdigit()] if emas else []
    rsi_period = int(rsi) if rsi and rsi.isdigit() else None
    ohlc = fetch_ohlc(symbol, interval=interval, duration_minutes=duration)
    indicators = attach_indicators(ohlc, emas=emas_list, rsi_period=rsi_period)
    return jsonify({"ohlc": ohlc, "indicators": indicators})

@bp.route("/api/signals", methods=["GET"])
def api_signals():
    """
    Serve live signals from logs/signals.json with optional ?symbol= filtering.
    """
    symbol = request.args.get("symbol", None)
    try:
        signals = read_signals()
    except FileNotFoundError:
        return jsonify({"status": "error", "message": "signals.json not found"}), 404
    except json.JSONDecodeError:
        return jsonify({"status": "error", "message": "Malformed signals.json"}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

    if symbol:
        signals = [s for s in signals if s.get("symbol", "").upper() == symbol.upper()]

    return jsonify({"status": "success", "data": signals})


@bp.route("/api/search")
def api_search():
    q = request.args.get('q', '').strip().upper()
    idx_path = os.path.join(current_app.root_path, "..", "config", "instrument_index.json")
    results = []
    try:
        if os.path.exists(idx_path):
            with open(idx_path,'r', encoding='utf-8') as f:
                index = json.load(f)
            for entry in index:
                if q == "" or q in entry.get('name','').upper() or q in entry.get('symbol','').upper():
                    results.append(entry)
    except Exception:
        pass
    if not results and q:
        results = [{"name": q, "symbol": q}]
    return jsonify(results)
# =====================================================
# API endpoint: Fetch OHLC candles from Fyers
# =====================================================
from flask import request, jsonify
from .fyers_fetcher import fetch_ohlc

@bp.route("/api/fyers_ohlc", methods=["GET"])
def fyers_ohlc():
    """
    Endpoint to fetch OHLC data for a given symbol and interval.
    Example: /api/fyers_ohlc?symbol=NSE:NIFTY50-INDEX&interval=5minute
    """
    symbol = request.args.get("symbol", "NSE:NIFTY50-INDEX")
    interval = request.args.get("interval", "5minute")

    try:
        candles = fetch_ohlc(symbol, interval)
        return jsonify({"status": "success", "data": candles})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

from flask_socketio import SocketIO, emit
from flask import Blueprint
import threading, json
from charts_extension.charts.fyers_stream import run_stream


socketio = SocketIO(cors_allowed_origins="*")
fyers_socket = Blueprint('fyers_socket', __name__)

def start_fyers_stream():
    # use your existing fyers_stream.py instead of old SDK
    run_stream()


@fyers_socket.route("/start_stream")
def start_stream():
    threading.Thread(target=start_fyers_stream).start()
    return {"status": "Stream started"}