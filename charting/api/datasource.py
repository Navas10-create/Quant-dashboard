# charting/api/datasource.py
from abc import ABC, abstractmethod

class DataSourceError(Exception):
    pass

class IDataSource(ABC):
    @abstractmethod
    def get_ohlcv(self, symbol: str, interval: str = "1", limit: int = 1000):
        """Return list of bars: each bar = {"time": int (unix sec), "open":float,...,"volume":float}"""
        raise NotImplementedError
