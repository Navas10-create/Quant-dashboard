# charting/api/fyers_source.py
import os, requests, time
from .datasource import IDataSource, DataSourceError

class FyersSource(IDataSource):
    def __init__(self):
        self.token = os.getenv("FYERS_TOKEN")  # set FYERS_TOKEN as env
        # NOTE: endpoint and param names may vary by Fyers account region; update as needed
        self.endpoint = "https://api.fyers.in/data-api/v1/history"  # example; verify with Fyers docs

    def get_ohlcv(self, symbol: str, interval: str = "1", limit: int = 1000):
        if not self.token:
            raise DataSourceError("No FYERS_TOKEN set")
        headers = {"Authorization": f"Bearer {self.token}"}
        params = {"symbol": symbol, "resolution": interval, "count": limit}
        try:
            r = requests.get(self.endpoint, headers=headers, params=params, timeout=8)
            r.raise_for_status()
            data = r.json()
            # Fyers response format needs mapping — adapt if necessary
            if "candles" in data:
                return [{"time": int(c[0]//1000), "open": c[1], "high": c[2], "low": c[3], "close": c[4], "volume": c[5]} for c in data["candles"]]
            raise DataSourceError("Fyers returned no candles")
        except Exception as e:
            raise DataSourceError(f"FyersSource error: {e}")
