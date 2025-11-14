import json, websocket, os, time
from dotenv import load_dotenv
from extensions import socketio

load_dotenv()

FYERS_ACCESS_TOKEN = os.getenv("FYERS_ACCESS_TOKEN")
FYERS_WS_URL = "wss://api.fyers.in/socket/v2/data"


SYMBOLS = [
    "NSE:NIFTY50-INDEX",
    "NSE:BANKNIFTY-INDEX"
]

def on_message(ws, message):
    try:
        data = json.loads(message)
        socketio.emit("chart_update", data)
        print("[TICK]", data)
    except Exception as e:
        print("[ERROR]", e, message)

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
