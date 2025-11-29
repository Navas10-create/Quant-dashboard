// ============================================
// LIGHTWEIGHT CHARTS - NAMESPACE ISOLATION
// ============================================
// This prevents conflicts with OpenAlgo's legacy chart engine

window.LWCharts = {
    // State variables (namespaced to prevent collisions)
    chart: null,
    candleSeries: null,
    pollTimer: null,
    lastFetchAt: 0,
    clientCache: {},
    currentFetchController: null,

    // Constants
    POLL_MS: 10000,  // 10 seconds
    CACHE_TTL: 30,   // 30 seconds

    // ============ Utility Functions ============

    debounce(fn, ms = 200) {
        let t;
        return (...args) => {
            clearTimeout(t);
            t = setTimeout(() => fn(...args), ms);
        };
    },

    nowSec() {
        return Math.floor(Date.now() / 1000);
    },

    toSec(maybeTs) {
        if (typeof maybeTs === 'number') {
            if (maybeTs > 1e12) return Math.floor(maybeTs / 1000);
            return Math.floor(maybeTs);
        }
        if (typeof maybeTs === 'string') {
            return Math.floor(new Date(maybeTs).getTime() / 1000);
        }
        return this.nowSec();
    },

    // ============ Chart Initialization ============

   initChart(dark = true) {
  console.log('[LWCharts] Initializing chart...');
  const container = document.getElementById('chartContainer');
  
  if (!container) {
    console.error('[LWCharts] ERROR: chartContainer element not found!');
    this.showStatus('ERROR: Chart container not found', 'error');
    return false;
  }

  // ⚠️ KEY FIX: Set container size FIRST
  if (!container.style.height || container.style.height === '0px') {
    container.style.height = '600px';
    container.style.width = '100%';
  }

  // Remove old chart if exists
  if (this.chart) {
    console.log('[LWCharts] Removing old chart instance');
    try {
      this.chart.remove();
    } catch (e) {
      console.warn('[LWCharts] Error removing chart:', e);
    }
    this.chart = null;
    this.candleSeries = null;
  }

  // Clear container content
  container.innerHTML = '';

  // Verify LightweightCharts is available
  if (typeof LightweightCharts === 'undefined') {
    console.error('[LWCharts] ERROR: LightweightCharts library not loaded!');
    this.showStatus('ERROR: Chart library failed to load', 'error');
    return false;
  }

  try {
    // Define layout based on dark mode
    const layout = dark
      ? {
          background: { color: '#15171b' },
          textColor: '#d8d8d8'
        }
      : {
          background: { color: '#ffffff' },
          textColor: '#111'
        };

    console.log('[LWCharts] Creating chart with dimensions:', container.clientWidth, 'x', container.clientHeight);

    // Create chart instance
    this.chart = LightweightCharts.createChart(container, {
      width: container.clientWidth || 800,
      height: Math.max(480, container.clientHeight || 600),
      layout,
      timeScale: {
        timeVisible: true,
        secondsVisible: false,
        rightOffset: 12,
        fixLeftEdge: false,
        fixRightEdge: false
      },
      watermark: {
        visible: false
      }
    });

    if (!this.chart) {
      throw new Error('createChart returned null or undefined');
    }

    console.log('[LWCharts] Chart object created:', typeof this.chart);
    console.log('[LWCharts] addCandlestickSeries available?', typeof this.chart.addCandlestickSeries);

    // Verify method exists before calling
    if (typeof this.chart.addCandlestickSeries !== 'function') {
      throw new Error('addCandlestickSeries is not a function on chart object');
    }

    this.candleSeries = this.chart.addCandlestickSeries({
      upColor: '#26a69a',
      downColor: '#ef5350',
      borderUpColor: '#26a69a',
      borderDownColor: '#ef5350',
      wickUpColor: '#26a69a',
      wickDownColor: '#ef5350'
    });

    this.chart.timeScale().fitContent();
    console.log('[LWCharts] ✓ Chart initialized successfully');
    this.showStatus('Chart ready', 'success');

    // Handle window resize
    window.removeEventListener('resize', this.onResize.bind(this));
    window.addEventListener('resize', this.onResize.bind(this));

    return true;

  } catch (error) {
    console.error('[LWCharts] ERROR initializing chart:', error);
    console.error('[LWCharts] Stack:', error.stack);
    this.chart = null;
    this.candleSeries = null;
    this.showStatus('ERROR: ' + error.message, 'error');
    return false;
  }
},


    // ============ Chart Update ============

    async setCandles(sym, interval, showSignals = true, incremental = false) {
        if (!sym) {
            console.warn('[LWCharts] No symbol provided');
            this.showStatus('Please select a symbol', 'error');
            return;
        }

        if (!this.chart || !this.candleSeries) {
            console.log('[LWCharts] Chart not initialized, initializing...');
            if (!this.initChart()) {
                return;
            }
        }

        const cacheKey = `${sym}:${interval}`;
        const now = this.nowSec();

        // Abort any pending fetch
        if (this.currentFetchController) {
            this.currentFetchController.abort();
        }

        this.currentFetchController = new AbortController();

        try {
            this.showStatus('Loading chart data...', 'loading');

            // PRIMARY: Try /api/ohlc endpoint
let data = null;
let dataSource = 'API';

try {
  console.log('[LWCharts] Attempting to fetch from /api/ohlc...');
  const response = await fetch(
    `/api/ohlc?symbol=${encodeURIComponent(sym)}&interval=${interval}&limit=200`,
    { signal: this.currentFetchController.signal }
  );

  if (response.ok) {
    const responseData = await response.json();
    data = responseData.data || responseData;
    console.log('[LWCharts] ✓ Data received from /api/ohlc:', data?.length || 0, 'candles');
    dataSource = 'API Endpoint';
  } else {
    throw new Error(`API returned status ${response.status}`);
  }
} catch (apiError) {
  console.warn('[LWCharts] /api/ohlc failed:', apiError.message);
  
  // FALLBACK: Try Fyers API directly
  console.log('[LWCharts] Attempting Fyers API fallback...');
  try {
    data = await this.fetchFromFyers(sym, interval);
    if (data && data.length > 0) {
      console.log('[LWCharts] ✓ Data received from Fyers API:', data.length, 'candles');
      dataSource = 'Fyers API';
    }
  } catch (fyersError) {
    console.warn('[LWCharts] Fyers API fallback failed:', fyersError.message);
    data = null;
  }
}
            // Transform API data to chart format
            const candles = data.map(bar => ({
                time: this.toSec(bar.timestamp || bar.time),
                open: parseFloat(bar.open),
                high: parseFloat(bar.high),
                low: parseFloat(bar.low),
                close: parseFloat(bar.close)
            }));

            // Set data on chart
            this.candleSeries.setData(candles);

            // Auto-scale
            this.chart.timeScale().fitContent();

            // Cache data
            this.clientCache[cacheKey] = {
                data: candles,
                timestamp: now
            };

            console.log('[LWCharts] ✓ Chart data updated:', candles.length, 'candles');
            this.showStatus(`Loaded ${candles.length} candles for ${sym} (from ${dataSource})`, 'success');

        } catch (error) {
            if (error.name !== 'AbortError') {
                console.error('[LWCharts] ERROR fetching data:', error);
                this.showStatus('ERROR: ' + error.message, 'error');
            }
        } finally {
            this.currentFetchController = null;
        }
    },

    // ============ Event Handlers ============

onResize() {
    if (!this.chart) return;
    const container = document.getElementById('chartContainer');
    if (!container) return;
       this.chart.applyOptions({
        width: container.clientWidth,
        height: Math.max(480, Math.floor(container.clientHeight || 600))
    });

    this.chart.timeScale().fitContent();
},

// ============ Fyers API Fallback ============
async fetchFromFyers(symbol, interval) {
  try {
    console.log('[LWCharts] Fetching from Fyers for symbol:', symbol);

    const intervalMap = {
      '1': 1,
      '5': 5,
      '15': 15,
      '30': 30,
      '60': 60,
      'D': 1440
    };

    const fyersInterval = intervalMap[interval] || 5;

    const response = await fetch('/api/fyers-data', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        symbol: symbol,
        interval: fyersInterval,
        limit: 200
      })
    });

    if (!response.ok) {
      throw new Error(`Fyers API returned ${response.status}`);
    }

    const result = await response.json();
    
    if (result.data && Array.isArray(result.data)) {
      return result.data;
    } else if (Array.isArray(result)) {
      return result;
    } else {
      throw new Error('Invalid Fyers response format');
    }

  } catch (error) {
    console.error('[LWCharts] Fyers fallback error:', error);
    throw error;
  }
},

    // ============ UI Helpers ============

    showStatus(message, type = 'loading') {
        const statusEl = document.getElementById('statusMessage');
        if (!statusEl) return;

        statusEl.textContent = message;
        statusEl.className = `status-message ${type}`;
        statusEl.style.display = 'block';

        if (type === 'success' || type === 'error') {
            setTimeout(() => {
                statusEl.style.display = 'none';
            }, 3000);
        }
    },

    // ============ Initialization ============

    init() {
        console.log('[LWCharts] Initializing event listeners...');

        // Initialize chart on first load
        this.initChart(true);

        // Bind button events
        const searchBtn = document.getElementById('searchBtn');
        const loadBtn = document.getElementById('loadBtn');
        const symbolSelect = document.getElementById('symbolSelect');
        const intervalSelect = document.getElementById('intervalSelect');
        const showSignals = document.getElementById('showSignals');
// === Autocomplete Search Dropdown for Instruments ===
const searchBox = document.getElementById("searchBox");
const dropdown = document.getElementById("search-dropdown");
let timer;

if (searchBox) {
    searchBox.addEventListener("input", () => {
        clearTimeout(timer);
        const query = searchBox.value.trim();
        if (query.length < 2) { dropdown.innerHTML = ""; dropdown.style.display = "none"; return; }
        timer = setTimeout(() => {
            fetch(`/api/search?q=${encodeURIComponent(query)}`)
                .then(res => res.json())
                .then(results => {
                    dropdown.innerHTML = "";
                    results.slice(0, 25).forEach(inst => {
                        const div = document.createElement("div");
                        div.textContent = inst.symbol || inst.name || '';
                        div.className = 'search-item';
                        div.addEventListener('click', () => {
                            searchBox.value = div.textContent;
                            dropdown.innerHTML = "";
                            dropdown.style.display = "none";
                        });
                        dropdown.appendChild(div);
                    });
                    dropdown.style.display = (dropdown.children.length > 0) ? 'block' : 'none';
                })
                .catch(err => {
                    console.error('[LWCharts] Search error:', err);
                    dropdown.innerHTML = "";
                    dropdown.style.display = "none";
                });
        }, 300);
    });
}

// Button handlers
if (searchBtn) {
    searchBtn.addEventListener('click', () => {
        const symbol = document.getElementById('searchBox').value.trim();
        if (symbol) {
            const interval = intervalSelect?.value || '5';
            const signals = showSignals?.checked || false;
            this.setCandles(symbol, interval, signals);
        }
    });
}

if (loadBtn) {
    loadBtn.addEventListener('click', () => {
        const symbol = symbolSelect?.value;
        if (symbol) {
            const interval = intervalSelect?.value || '5';
            const signals = showSignals?.checked || false;
            this.setCandles(symbol, interval, signals);
        }
    });
}

// Auto-load on symbol change
if (symbolSelect) {
    symbolSelect.addEventListener('change', (e) => {
        if (e.target.value) {
            const interval = intervalSelect?.value || '5';
            const signals = showSignals?.checked || false;
            this.setCandles(e.target.value, interval, signals);
        }
    });
}

console.log('[LWCharts] ✓ Ready');
    }
};

// Start when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.LWCharts.init();
    });
} else {
    window.LWCharts.init();
}
