# extensions/charts/signal_store.py
import logging
logger = logging.getLogger(__name__)

import json, os, tempfile
from typing import Dict, Any

SIGNAL_PATH = "logs/signals.json"
os.makedirs(os.path.dirname(SIGNAL_PATH), exist_ok=True)

def read_signals():
    if not os.path.exists(SIGNAL_PATH):
        return []
    try:
        with open(SIGNAL_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"Failed to read signals: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error reading signals: {e}")
        return []


def write_signals_atomic(signals_list):
    # atomically write entire list
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(SIGNAL_PATH))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(signals_list, f, ensure_ascii=False, indent=2)
        os.replace(tmp, SIGNAL_PATH)
        return True
    except Exception:
        try:
            os.remove(tmp)
        except:
            pass
        return False

def append_signal(signal: Dict[str, Any]):
    """
    Append single signal atomically. Signal example:
    {"symbol":"NSE:NIFTY50-INDEX","side":"BUY","time": 169... or "2025-11-11T10:03:00+05:30","price":21700.5,"note":"rsi<30"}
    """
    signals = read_signals()
    signals.append(signal)
    return write_signals_atomic(signals)
