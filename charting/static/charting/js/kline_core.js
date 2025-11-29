// charting/static/charting/js/kline_core.js
(async function() {
  const cfg = window.CHART_CONFIG || {};
  const symbol = cfg.symbol || 'NIFTY';
  const endpoint = cfg.dataEndpoint || `/chart/data?symbol=${symbol}&interval=1&limit=1000`;

  const root = document.getElementById('chart-root');

  // Create chart widget
  const chart = init('chart-root', { 
    styles: { 
      grid: { horizontal: '#f3f6f9', vertical: '#f3f6f9' },
      background: '#ffffff'
    }
  });

  // create series (candles + volume below)
  const main = chart.createTechnicalIndicator('Candle');
  chart.createTechnicalIndicator('VOL', { panel: 'VOL' });

  // helper: normalize bars returned by backend
  function normalizeBars(bars) {
    // expect bars: [{time:unix_s, open, high, low, close, volume}, ...]
    return bars.map(b => ({
      time: (typeof b.time === 'number' && b.time > 1e10) ? Math.floor(b.time / 1000) : b.time, // normalize ms->s if needed
      open: b.open,
      high: b.high,
      low: b.low,
      close: b.close,
      volume: b.volume || 0
    }));
  }

  async function fetchData(sym, interval = '1') {
    const url = `/chart/data?symbol=${encodeURIComponent(sym)}&interval=${encodeURIComponent(interval)}&limit=2000`;
    try {
      const res = await fetch(url, { credentials: 'same-origin' });
      if (!res.ok) throw new Error('no-data');
      const payload = await res.json();
      if (payload.status && payload.status === 'error') throw new Error(payload.message || 'error');
      // payload.bars is expected by our router
      const bars = payload.bars || payload;
      document.getElementById('dataSourceBadge').innerText = 'loaded';
      return normalizeBars(bars);
    } catch (err) {
      console.warn('Primary fetch failed, attempting direct fallback:', err);
      document.getElementById('dataSourceBadge').innerText = 'fallback';
      // Optionally try /proxy/fyers/<symbol> if implemented on server
      try {
        const fyres = await fetch(`/proxy/fyers/${encodeURIComponent(sym)}`);
        if (!fyres.ok) throw new Error('fyers failed');
        const data = await fyres.json();
        return normalizeBars(data);
      } catch (e) {
        console.error('All data sources failed', e);
        return [];
      }
    }
  }

  async function load(sym, interval) {
    const bars = await fetchData(sym, interval);
    if (!bars || bars.length === 0) {
      // show placeholder
      chart.applyNewData([]);
      return;
    }
    chart.applyNewData(bars);
    // optional: add some built-in indicators
    // SMA(20)
    chart.createTechnicalIndicator('SMA', { params: [20] });
    chart.createTechnicalIndicator('EMA', { params: [50] });
    chart.createTechnicalIndicator('MACD');
  }

  // initial load
  await load(symbol, document.getElementById('tfSelect').value || '1');

  // UI events
  document.getElementById('tfSelect').addEventListener('change', async (e) => {
    await load(symbol, e.target.value);
  });
  document.getElementById('btnReload').addEventListener('click', async () => {
    await load(symbol, document.getElementById('tfSelect').value);
  });

  // Expose chart controls to console for debugging
  window._KLINE_CHART = chart;
})();
