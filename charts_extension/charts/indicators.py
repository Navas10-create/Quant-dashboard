# extensions/charts/indicators.py
import pandas as pd

def compute_ema(series, period):
    return series.ewm(span=period, adjust=False).mean()

def compute_rsi(series, period=14):
    delta = series.diff()
    up, down = delta.clip(lower=0), -1*delta.clip(upper=0)
    ma_up = up.ewm(com=period-1, adjust=False).mean()
    ma_down = down.ewm(com=period-1, adjust=False).mean()
    rs = ma_up / (ma_down.replace(0, 1e-8))
    rsi = 100 - (100 / (1 + rs))
    return rsi

def attach_indicators(ohlc_list, emas=None, rsi_period=None):
    """
    ohlc_list: list of dicts with 'date','open','high','low','close','volume'
    emas: list of integer periods [20,50]
    rsi_period: int or None
    returns: dict of arrays aligned with ohlc_list: {'ema_20': [...], 'rsi_14': [...]}
    """
    try:
        df = pd.DataFrame(ohlc_list)
        if df.empty:
            return {}
        df['close'] = pd.to_numeric(df['close'], errors='coerce')
        out = {}
        if emas:
            for p in emas:
                out[f'ema_{p}'] = compute_ema(df['close'], p).bfill().tolist()
        if rsi_period:
            out[f'rsi_{rsi_period}'] = compute_rsi(df['close'], rsi_period).fillna(50).tolist()
        return out
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Indicator calculation failed: {e}")
        return {}