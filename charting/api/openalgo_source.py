# charting/api/openalgo_source.py
import os, requests
from .datasource import IDataSource, DataSourceError

class OpenAlgoSource(IDataSource):
    def __init__(self):
        self.host = os.getenv("OPENALGO_HOST", "http://localhost:5000")
        self.key = os.getenv("OPENALGO_API_KEY", "")

    def get_ohlcv(self, symbol: str, interval: str = "1", limit: int = 1000):
        url = f"{self.host.rstrip('/')}/api/v1/history"
        try:
            r = requests.get(url, headers={"X-API-KEY": self.key}, params={"symbol": symbol, "interval": interval, "limit": limit}, timeout=8)
            r.raise_for_status()
            data = r.json()
            if "candles" in data:
                return [{"time": int(c[0]//1000), "open": c[1], "high": c[2], "low": c[3], "close": c[4], "volume": c[5]} for c in data["candles"]]
            # sometimes OpenAlgo may return raw list
            if isinstance(data, list):
                return data
            raise DataSourceError("OpenAlgo returned no candles")
        except Exception as e:
            raise DataSourceError(f"OpenAlgoSource error: {e}")
