// charting/static/charting/js/chart_core.js
// NOTE: Uses LightweightCharts already loaded on page

const ChartCore = (function(){
  let chart, candleSeries, symbol;
  let overlayCanvas, overlayCtx;
  let currentInterval = "1";

  async function fetchBars(sym, interval){
    const url = `/chart/data?symbol=${encodeURIComponent(sym)}&interval=${encodeURIComponent(interval)}&limit=1000`;
    const r = await fetch(url);
    if(!r.ok){
      const err = await r.json().catch(()=>({message:"fetch failed"}));
      throw new Error(err.message || "failed to fetch");
    }
    const payload = await r.json();
    if(payload.status !== "ok") throw new Error(payload.message || "no data");
    return payload.bars;
  }

  function createOverlay(){
    overlayCanvas = document.getElementById('overlay');
    const chartEl = document.getElementById('chart');
    overlayCanvas.width = chartEl.clientWidth;
    overlayCanvas.height = chartEl.clientHeight;
    overlayCanvas.style.width = chartEl.clientWidth + "px";
    overlayCanvas.style.height = chartEl.clientHeight + "px";
    overlayCanvas.style.pointerEvents = "none";
    overlayCtx = overlayCanvas.getContext('2d');
  }

  function resize(){
    const chartEl = document.getElementById('chart');
    chart.resize(chartEl.clientWidth, chartEl.clientHeight);
    overlayCanvas.width = chartEl.clientWidth * window.devicePixelRatio;
    overlayCanvas.height = chartEl.clientHeight * window.devicePixelRatio;
    overlayCanvas.style.width = chartEl.clientWidth + "px";
    overlayCanvas.style.height = chartEl.clientHeight + "px";
    overlayCtx.scale(window.devicePixelRatio, window.devicePixelRatio);
  }

  function applyIndicatorsUI(){
    document.getElementById('btnSMA').addEventListener('click', async ()=>{
      const bars = await fetchBars(symbol, currentInterval);
      const sma = Indicators.SMA(bars.map(b=>b.close), 20);
      const map = bars.map((b,i)=>({time:b.time, value: sma[i] || null})).filter(d=>d.value!==null);
      const s = chart.addLineSeries({ color: 'orange', lineWidth: 2 });
      s.setData(map);
    });
    document.getElementById('btnEMA').addEventListener('click', async ()=>{
      const bars = await fetchBars(symbol, currentInterval);
      const ema = Indicators.EMA(bars.map(b=>b.close), 20);
      const map = bars.map((b,i)=>({time:b.time, value: ema[i] || null})).filter(d=>d.value!==null);
      const s = chart.addLineSeries({ color: 'cyan', lineWidth: 2 });
      s.setData(map);
    });
    document.getElementById('btnRSI').addEventListener('click', async ()=>{
      const bars = await fetchBars(symbol, currentInterval);
      const rsi = Indicators.RSI(bars.map(b=>b.close), 14);
      // render rsi in a separate pane: for now overlay as histogram series of small height by rescaling
      const map = bars.map((b,i)=>({time:b.time, value: rsi[i] || null})).filter(d=>d.value!==null);
      const s = chart.addHistogramSeries({ priceFormat: { type: 'volume' }, color: '#7f7' });
      s.setData(map);
    });

    // timeframe selector
    document.getElementById('tfSelect').addEventListener('change', async (e)=>{
      currentInterval = e.target.value;
      await load(symbol, currentInterval);
    });

    // drawing tools
    document.getElementById('btnTrend').addEventListener('click', ()=>{
      DrawingTools.startTool('trendline', chart, candleSeries);
    });
    document.getElementById('btnFibs').addEventListener('click', ()=>{
      DrawingTools.startTool('fibonacci', chart, candleSeries);
    });
  }

  async function load(sym, interval){
    symbol = sym;
    try{
      const bars = await fetchBars(sym, interval);
      const formatted = bars.map(b=>({ time: b.time, open: b.open, high: b.high, low: b.low, close: b.close }));
      candleSeries.setData(formatted);
      // clear overlays if any
      DrawingTools.redrawAll();
    }catch(err){
      console.error("Load error", err);
      // optionally show UI notification
    }
  }

  function initUI(){
    const chartEl = document.getElementById('chart');
    chart = LightweightCharts.createChart(chartEl, {
      layout: { backgroundColor: "#ffffff", textColor: "#333" },
      timeScale: { timeVisible: true, secondsVisible: false },
      rightPriceScale: { scaleMargins: { top: 0.1, bottom: 0.1 } }
    });
    candleSeries = chart.addCandlestickSeries();
    createOverlay();
    window.addEventListener('resize', resize);
    applyIndicatorsUI();
    DrawingTools.init(overlayCanvas, overlayCtx, chart); // initialize drawing tools
  }

  return {
    init: async function(conf){
      initUI();
      symbol = conf.symbol || 'NIFTY';
      currentInterval = conf.interval || '1';
      await load(symbol, currentInterval);
    },
    reload: function(){ load(symbol, currentInterval); }
  };
})();
