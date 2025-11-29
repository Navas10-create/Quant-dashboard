"""
OpenAlgo Strategy Templates - Drop-in Python file
Contains multiple ready-to-use strategy templates designed for OpenAlgo Analyse (Sandbox) Mode.

HOW TO USE
1. Place this file in your OpenAlgo strategies folder or import its classes into your strategy runner.
2. Each strategy exposes a Strategy class with init/on_bar/on_tick hooks (match your OpenAlgo strategy lifecycle).
3. Update the BROKER_API placeholders to use your OpenAlgo sandbox/client objects (e.g., `client = openalgo.api.sandbox_client()`)
4. Configure strategy parameters at the top of each class or via your strategy config.

DISCLAIMER
These templates are intended as drop-in starting points for simulated testing only. Adapt order API calls to your OpenAlgo client.
"""

import math
import time
from dataclasses import dataclass
from typing import Dict, Any, Optional

# -------------------------------
# Helper utilities (shared)
# -------------------------------

def now_ts():
    return int(time.time())

@dataclass
class SimOrder:
    order_id: str
    symbol: str
    side: str
    qty: int
    price: float
    filled: int = 0
    status: str = "PLACED"
    placed_at: int = None


class SandboxAPI:
    """Placeholder class. Replace with your OpenAlgo sandbox client instance.
    Methods implemented are intentionally simple so they can be mapped to OpenAlgo's client API.
    """
    def __init__(self, client=None):
        self.client = client
        self.order_counter = 0
        self.orders = {}
        self.balance = 1_000_000  # default sandbox cash

    def get_balance(self):
        return self.balance

    def place_order(self, symbol, side, qty, price=None, order_type='MARKET', tag=None):
        self.order_counter += 1
        oid = f"S{self.order_counter:06d}"
        o = SimOrder(order_id=oid, symbol=symbol, side=side, qty=qty, price=price or 0.0, placed_at=now_ts())
        self.orders[oid] = o
        # Return a simplified order receipt
        return {"order_id": oid, "status": "PLACED"}

    def cancel_order(self, order_id):
        if order_id in self.orders:
            self.orders[order_id].status = 'CANCELLED'
            return True
        return False

    def simulate_fill(self, order_id, fill_qty, fill_price):
        o = self.orders.get(order_id)
        if not o:
            return None
        o.filled += fill_qty
        if o.filled >= o.qty:
            o.status = 'FILLED'
        else:
            o.status = 'PARTIALLY_FILLED'
        return o

# Instantiate a default sandbox API object; replace with actual OpenAlgo sandbox client
BROKER_API = SandboxAPI()

# Execution utility to apply slippage and fees
def apply_slippage_and_fees(requested_price: float, side: str, slippage_ticks: float, tick_size: float, commission_per_trade: float):
    # slippage_ticks can be fractional; positive means worse price for taker
    slippage_amount = slippage_ticks * tick_size
    if side.upper() == 'BUY':
        executed_price = requested_price + slippage_amount
    else:
        executed_price = requested_price - slippage_amount
    executed_price = round(executed_price, 2)
    # subtract commission later in PnL accounting
    return executed_price

# -------------------------------
# Strategy 1: Momentum Breakout (volume + ATR sizing)
# - Uses ATR for volatility regime and position sizing
# - Uses volume surge as filter
# - Market orders simulated with slippage
# -------------------------------
class MomentumBreakoutStrategy:
    PARAMETERS = {
        'atr_period': 14,
        'atr_multiplier_stop': 1.5,
        'volume_surge_multiplier': 2.0,
        'risk_per_trade_pct': 0.01,  # 1% of equity
        'tick_size': 0.05,
        'slippage_ticks': 1.0,
        'commission': 40.0,  # per trade/exchange approx
        'min_qty': 1,
    }

    def __init__(self, symbol:str, client:Optional[SandboxAPI]=None, params:Optional[Dict]=None):
        self.symbol = symbol
        self.client = client or BROKER_API
        if params:
            self.PARAMETERS.update(params)
        self.state = {}
        self.atr = None
        self.avg_vol = None

    def compute_atr(self, highs, lows, closes, period):
        # simple ATR calculation; expects lists with newest at end
        trs = []
        for i in range(1, len(closes)):
            tr = max(highs[i] - lows[i], abs(highs[i] - closes[i-1]), abs(lows[i] - closes[i-1]))
            trs.append(tr)
        if len(trs) < period:
            return sum(trs)/len(trs) if trs else 0.0
        return sum(trs[-period:]) / period

    def on_bar(self, bar_history):
        """bar_history: list of dicts with keys ['t','open','high','low','close','volume'] sorted oldest->newest
        This method should be called each bar.
        """
        if len(bar_history) < 20:
            return
        highs = [b['high'] for b in bar_history]
        lows = [b['low'] for b in bar_history]
        closes = [b['close'] for b in bar_history]
        volumes = [b['volume'] for b in bar_history]

        atr = self.compute_atr(highs, lows, closes, self.PARAMETERS['atr_period'])
        self.atr = atr
        self.avg_vol = sum(volumes[-20:])/20

        last = bar_history[-1]
        prev = bar_history[-2]

        # breakout condition: close above previous high and volume surge
        breakout_up = last['close'] > max(h['high'] for h in bar_history[-5:-1])
        breakout_down = last['close'] < min(h['low'] for h in bar_history[-5:-1])
        vol_surge = last['volume'] > (self.PARAMETERS['volume_surge_multiplier'] * self.avg_vol)

        if breakout_up and vol_surge:
            self.enter_trade('BUY', last['close'])
        elif breakout_down and vol_surge:
            self.enter_trade('SELL', last['close'])

    def enter_trade(self, side, price):
        equity = self.client.get_balance()
        risk_amt = equity * self.PARAMETERS['risk_per_trade_pct']
        stop_dist = self.atr * self.PARAMETERS['atr_multiplier_stop'] if self.atr else 10
        # approximate point value = 1 for index futures; adapt per symbol
        contract_risk = max(1e-6, stop_dist)
        qty = max(self.PARAMETERS['min_qty'], int(risk_amt / contract_risk))

        # simulate market order + slippage
        exec_price = apply_slippage_and_fees(price, side, self.PARAMETERS['slippage_ticks'], self.PARAMETERS['tick_size'], self.PARAMETERS['commission'])
        res = self.client.place_order(symbol=self.symbol, side=side, qty=qty, price=exec_price, order_type='MARKET')
        print(f"[Momentum] Placed {side} {qty}@{exec_price} for {self.symbol} (risk {risk_amt:.2f}, stop {stop_dist:.2f}) -> {res}")

# -------------------------------
# Strategy 2: Mean Reversion (VWAP + RSI) with limit execution and partial-fill retry
# - Uses VWAP to detect deviations; uses RSI as confirmation
# - Places limit orders at better-than-market price and has timeout+retry
# -------------------------------
class MeanReversionVWAPStrategy:
    PARAMETERS = {
        'rsi_period': 14,
        'rsi_oversold': 30,
        'rsi_overbought': 70,
        'vwap_lookback': 60,
        'limit_offset_ticks': 2.0,
        'timeout_secs': 10,
        'tick_size': 0.05,
        'commission': 30.0,
        'min_qty': 1,
    }

    def __init__(self, symbol:str, client:Optional[SandboxAPI]=None, params:Optional[Dict]=None):
        self.symbol = symbol
        self.client = client or BROKER_API
        if params:
            self.PARAMETERS.update(params)
        self.open_orders = {}

    def compute_vwap(self, bars):
        # bars: list oldest->newest
        pv = 0.0
        vol = 0.0
        for b in bars:
            typical = (b['high'] + b['low'] + b['close'])/3.0
            pv += typical * b['volume']
            vol += b['volume']
        return pv/vol if vol>0 else bars[-1]['close']

    def compute_rsi(self, closes, period):
        if len(closes) < period+1:
            return 50
        gains = 0.0
        losses = 0.0
        for i in range(-period, 0):
            diff = closes[i] - closes[i-1]
            if diff>0: gains += diff
            else: losses += abs(diff)
        avg_gain = gains/period
        avg_loss = losses/period if losses>0 else 1e-6
        rs = avg_gain/avg_loss
        rsi = 100 - (100/(1+rs))
        return rsi

    def on_bar(self, bar_history):
        if len(bar_history) < self.PARAMETERS['vwap_lookback'] + 5:
            return
        lookback = self.PARAMETERS['vwap_lookback']
        vwap = self.compute_vwap(bar_history[-lookback:])
        closes = [b['close'] for b in bar_history]
        rsi = self.compute_rsi(closes, self.PARAMETERS['rsi_period'])
        last = bar_history[-1]

        # price far above vwap and RSI overbought -> short via limit
        deviation = (last['close'] - vwap)/vwap
        if deviation > 0.002 and rsi > self.PARAMETERS['rsi_overbought']:
            # place limit slightly better than current
            limit_price = last['close'] - self.PARAMETERS['limit_offset_ticks']*self.PARAMETERS['tick_size']
            self.place_limit_with_retry('SELL', limit_price, qty=self.PARAMETERS['min_qty'])
        elif deviation < -0.002 and rsi < self.PARAMETERS['rsi_oversold']:
            limit_price = last['close'] + self.PARAMETERS['limit_offset_ticks']*self.PARAMETERS['tick_size']
            self.place_limit_with_retry('BUY', limit_price, qty=self.PARAMETERS['min_qty'])

    def place_limit_with_retry(self, side, price, qty=1):
        res = self.client.place_order(symbol=self.symbol, side=side, qty=qty, price=price, order_type='LIMIT')
        oid = res.get('order_id')
        self.open_orders[oid] = {'placed': now_ts(), 'side': side, 'price': price, 'qty': qty}
        # Simulate waiting; in a real runner you'd have an on_order_update hook
        start = now_ts()
        # naive loop to demonstrate retry logic; in production use event-driven
        while now_ts() - start < self.PARAMETERS['timeout_secs']:
            # Here, integrate with market data to decide if it's filled; we'll simulate progressive fill
            time.sleep(0.5)
        # After timeout, if not filled, cancel and optionally re-place at market
        self.client.cancel_order(oid)
        print(f"[MeanRev] Timeout reached for order {oid} price {price}; cancelled and skipping")

# -------------------------------
# Strategy 3: Delta-aware Options Straddle (volatility breakout tester)
# - Designed to run in sandbox for NIFTY/BNF; selects ATM strikes and trades straddles
# - Includes IV rank gating and dynamic sizing
# NOTE: This template assumes you have access to option chain and IV data via your OpenAlgo client
# -------------------------------
class OptionsStraddleVolTest:
    PARAMETERS = {
        'iv_rank_threshold': 50,    # only test when IV rank above
        'lookback_iv_days': 90,
        'days_to_expiry_target': 10,
        'max_risk_pct': 0.02,  # 2% per straddle
        'slippage_ticks': 2.0,
        'tick_size': 0.05,
        'commission': 60.0,
        'min_qty': 1,
    }

    def __init__(self, underlying_symbol:str, client:Optional[SandboxAPI]=None, params:Optional[Dict]=None):
        self.underlying = underlying_symbol
        self.client = client or BROKER_API
        if params:
            self.PARAMETERS.update(params)

    def select_atm_strikes(self, spot_price, option_chain):
        # option_chain: list of dicts with strike, call_iv, put_iv, expiry_date
        # pick strike closest to spot and expiry ~ days_to_expiry_target
        target_days = self.PARAMETERS['days_to_expiry_target']
        # naive selection: pick first expiry within target_days +- 2
        best = None
        for opt in option_chain:
            days = (opt['expiry_date'] - int(time.time()))/86400
            if abs(days - target_days) < 3:
                if best is None or abs(opt['strike'] - spot_price) < abs(best['strike']-spot_price):
                    best = opt
        return best

    def compute_iv_rank(self, iv_history):
        # iv_history: list of recent IV values
        if not iv_history:
            return 50
        cur = iv_history[-1]
        lo = min(iv_history)
        hi = max(iv_history)
        if hi==lo: return 50
        return 100 * (cur - lo)/(hi-lo)

    def on_tick(self, market_snapshot):
        """market_snapshot should provide: spot_price, option_chain, iv_history_for_underlying
        This gets called frequently (per tick) in Analyze Mode using live/paper data.
        """
        spot = market_snapshot['spot_price']
        iv_hist = market_snapshot['iv_history']
        iv_rank = self.compute_iv_rank(iv_hist)
        if iv_rank < self.PARAMETERS['iv_rank_threshold']:
            return
        # select ATM expiry
        chain = market_snapshot['option_chain']
        atm = self.select_atm_strikes(spot, chain)
        if not atm:
            return

        # compute sizing
        equity = self.client.get_balance()
        risk_per_trade = equity * self.PARAMETERS['max_risk_pct']
        # approximate premium per straddle = (call_bid+put_bid)*lot_size; we mock as mid
        approx_premium = (atm['call_mid'] + atm['put_mid'])
        lot_size = atm.get('lot_size', 1)
        if approx_premium*lot_size==0: return
        qty = max(self.PARAMETERS['min_qty'], int(risk_per_trade / (approx_premium * lot_size)))

        # place simulated market orders for both legs
        # place call
        call_symbol = atm['call_symbol']
        put_symbol = atm['put_symbol']
        call_price = apply_slippage_and_fees(atm['call_mid'], 'BUY', self.PARAMETERS['slippage_ticks'], self.PARAMETERS['tick_size'], self.PARAMETERS['commission'])
        put_price = apply_slippage_and_fees(atm['put_mid'], 'BUY', self.PARAMETERS['slippage_ticks'], self.PARAMETERS['tick_size'], self.PARAMETERS['commission'])
        res_c = self.client.place_order(symbol=call_symbol, side='BUY', qty=qty*lot_size, price=call_price, order_type='MARKET')
        res_p = self.client.place_order(symbol=put_symbol, side='BUY', qty=qty*lot_size, price=put_price, order_type='MARKET')
        print(f"[Straddle] Placed {qty} straddles: CALL {call_symbol}@{call_price} PUT {put_symbol}@{put_price} (IVrank {iv_rank:.1f}) -> {res_c},{res_p}")

# -------------------------------
# Strategy 4: Regime-Switching Adaptive Strategy
# - Detects volatility & liquidity regimes and switches between momentum and mean-revert
# - Keeps conservative sizing under high-volatility
# -------------------------------
class RegimeAdaptiveStrategy:
    PARAMETERS = {
        'vol_high_threshold': 1.5,  # multiplier vs long-term atr
        'liquidity_spread_threshold': 0.5,  # in ticks
        'base_size': 1,
        'reduced_size_factor': 0.4,
        'tick_size': 0.05,
        'commission': 40.0,
        'slippage_ticks_high_vol': 2.0,
        'slippage_ticks_low_vol': 0.8,
    }

    def __init__(self, symbol:str, client:Optional[SandboxAPI]=None, params:Optional[Dict]=None):
        self.symbol = symbol
        self.client = client or BROKER_API
        if params:
            self.PARAMETERS.update(params)
        self.long_atr = None

    def update_long_atr(self, atr_series):
        if not atr_series: return
        self.long_atr = sum(atr_series)/len(atr_series)

    def classify_regime(self, current_atr, bid_ask_spread):
        vol_mult = current_atr / (self.long_atr or max(current_atr,1))
        high_vol = vol_mult > self.PARAMETERS['vol_high_threshold']
        illiquid = (bid_ask_spread / self.PARAMETERS['tick_size']) > self.PARAMETERS['liquidity_spread_threshold']
        return {'high_vol': high_vol, 'illiquid': illiquid}

    def on_bar(self, bar_history, market_meta):
        # market_meta expected to contain current_atr and bid_ask_spread
        current_atr = market_meta.get('current_atr', 0.0)
        spread = market_meta.get('bid_ask_spread', 0.0)
        regime = self.classify_regime(current_atr, spread)
        # choose behavior
        if regime['high_vol']:
            size = max(1, int(self.PARAMETERS['base_size'] * self.PARAMETERS['reduced_size_factor']))
            slippage = self.PARAMETERS['slippage_ticks_high_vol']
            # be conservative - prefer mean-revert or smaller trend plays
            self._attempt_mean_revert(bar_history, size, slippage)
        else:
            size = self.PARAMETERS['base_size']
            slippage = self.PARAMETERS['slippage_ticks_low_vol']
            self._attempt_momentum(bar_history, size, slippage)

    def _attempt_mean_revert(self, bars, size, slippage_ticks):
        last = bars[-1]
        mid = (last['high']+last['low'])/2.0
        # naive mean-revert: if price 0.4% above moving avg -> short
        window = 20
        ma = sum(b['close'] for b in bars[-window:])/window
        if last['close'] > ma * 1.004:
            exec_price = apply_slippage_and_fees(last['close'], 'SELL', slippage_ticks, self.PARAMETERS['tick_size'], self.PARAMETERS['commission'])
            self.client.place_order(symbol=self.symbol, side='SELL', qty=size, price=exec_price, order_type='MARKET')
            print(f"[Regime] High-vol mean-revert SELL {size}@{exec_price}")

    def _attempt_momentum(self, bars, size, slippage_ticks):
        last = bars[-1]
        # naive momentum: check if last close > 5-period high
        if last['close'] > max(b['high'] for b in bars[-6:-1]):
            exec_price = apply_slippage_and_fees(last['close'], 'BUY', slippage_ticks, self.PARAMETERS['tick_size'], self.PARAMETERS['commission'])
            self.client.place_order(symbol=self.symbol, side='BUY', qty=size, price=exec_price, order_type='MARKET')
            print(f"[Regime] Low-vol momentum BUY {size}@{exec_price}")

# -------------------------------
# End of templates
# -------------------------------

# Exported helpers for convenience
strategy_classes = {
    'momentum_breakout': MomentumBreakoutStrategy,
    'mean_reversion_vwap': MeanReversionVWAPStrategy,
    'options_straddle_vol': OptionsStraddleVolTest,
    'regime_adaptive': RegimeAdaptiveStrategy,
}

if __name__ == '__main__':
    print('This module contains OpenAlgo strategy templates. Import the classes into your runner.')
