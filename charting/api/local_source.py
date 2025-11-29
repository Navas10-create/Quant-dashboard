# charting/api/local_source.py
import os, json
from .datasource import IDataSource, DataSourceError
from flask import current_app

class LocalSource(IDataSource):
    def __init__(self, base_dir=None):
        self.base_dir = base_dir or current_app.root_path

    def get_ohlcv(self, symbol: str, interval: str = "1", limit: int = 1000):
        # Look for file: static/data/{symbol}_{interval}.json or static/data/{symbol}.json
        possible = [
            os.path.join(self.base_dir, "static", "data", f"{symbol}_{interval}.json"),
            os.path.join(self.base_dir, "static", "data", f"{symbol}.json")
        ]
        for p in possible:
            if os.path.exists(p):
                try:
                    with open(p, "r") as f:
                        payload = json.load(f)
                    # Accept two possible formats:
                    # 1) {"candles": [[ts, o,h,l,c,vol], ...]}
                    # 2) [{time:,open:,high:,low:,close:,volume:}, ...]
                    if isinstance(payload, dict) and "candles" in payload:
                        bars = []
                        for c in payload["candles"][-limit:]:
                            bars.append({"time": int(c[0]//1000), "open": c[1], "high": c[2], "low": c[3], "close": c[4], "volume": c[5]})
                        return bars
                    elif isinstance(payload, list):
                        # ensure time is in seconds
                        return payload[-limit:]
                    else:
                        raise DataSourceError("Unsupported local JSON format")
                except Exception as e:
                    raise DataSourceError(f"LocalSource read error: {e}")
        raise DataSourceError("Local file not found")
