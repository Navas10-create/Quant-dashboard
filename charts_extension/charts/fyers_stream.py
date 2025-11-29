import json, os, time

import logging
logger = logging.getLogger(__name__)

try:
    import websocket
except ImportError:
    raise ImportError("websocket-client required: pip install websocket-client")

from dotenv import load_dotenv
def emit_update(data):
    """Emit chart update through socketio"""
    try:
        from extensions import socketio
        socketio.emit("chart_update", data)
    except ImportError:
        print("[Stream] SocketIO not available")


load_dotenv()

FYERS_ACCESS_TOKEN = os.getenv("FYERS_ACCESS_TOKEN")
FYERS_WS_URL = "wss://api.fyers.in/socket/v2/data"


SYMBOLS = [
    "NSE:NIFTY50-INDEX",
    "NSE:BANKNIFTY-INDEX"
]

def emit_update(data):
    """Emit chart update - imported inside function to avoid circular dependency"""
    try:
        from extensions import socketio
        socketio.emit("chart_update", data)
    except ImportError:
        logger.warning("SocketIO not available")

def on_message(ws, message):
    try:
        data = json.loads(message)
        emit_update(data)
    except Exception as e:
        logger.error(f"Error occurred: {e}")


def on_error(ws, error):
    print("[WebSocket Error]", error)

def on_close(ws, code, msg):
    print("[WebSocket Closed]", code, msg)
    time.sleep(5)
    run_stream()

def on_open(ws):
    print("[WebSocket Opened] Subscribing to symbols...")
    payload = {
        "T": "subscribe",
        "instruments": SYMBOLS,
        "token": FYERS_ACCESS_TOKEN
    }
    ws.send(json.dumps(payload))

def run_stream():
    print("[Stream] Connecting to Fyers WebSocket...")
    ws = websocket.WebSocketApp(
        FYERS_WS_URL,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    ws.run_forever()
import threading

def run_stream_threaded():
    """Run WebSocket stream in background thread"""
    thread = threading.Thread(target=run_stream, daemon=True)
    thread.start()
    return thread
def on_message(ws, message):
    try:
        data = json.loads(message)
        emit_update(data)  # Use new function
        print("[TICK]", data)
    except Exception as e:
        print("[ERROR]", e, message)
