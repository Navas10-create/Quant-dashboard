# charting/api/router.py
from .local_source import LocalSource
from .openalgo_source import OpenAlgoSource
from .fyers_source import FyersSource
from .datasource import DataSourceError

class MultiSourceRouter:
    def __init__(self, app=None):
        self.app = app
        # order is important: local -> openalgo -> fyers
        self.sources = [LocalSource(), OpenAlgoSource(), FyersSource()]

    def get_ohlcv(self, symbol, interval="1", limit=1000):
        errors = []
        for s in self.sources:
            try:
                bars = s.get_ohlcv(symbol, interval, limit)
                # basic validation
                if not bars or not isinstance(bars, list):
                    raise DataSourceError("empty or invalid data")
                return bars
            except DataSourceError as e:
                errors.append(str(e))
                continue
        raise DataSourceError("All sources failed: " + " | ".join(errors))
