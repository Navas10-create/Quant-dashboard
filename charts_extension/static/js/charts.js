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

        // Clear old content
        while (container.firstChild) {
            container.removeChild(container.firstChild);
        }

        // Remove old chart if exists
        if (this.chart) {
            console.log('[LWCharts] Removing old chart instance');
            this.chart.remove();
            this.chart = null;
        }

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

            // Create chart instance
            this.chart = LightweightCharts.createChart(container, {
                width: container.clientWidth,
                height: Math.max(480, Math.floor(container.clientHeight || 600)),
                layout,
                grid: {
                    vertlines: { color: '#222' },
                    horzlines: { color: '#222' }
                },
                timeScale: {
                    timeVisible: true,
                    secondsVisible: false
                }
            });

            // Add candlestick series
            this.candleSeries = this.chart.addCandlestickSeries({
                upColor: '#26a69a',
                downColor: '#ef5350',
                borderUpColor: '#26a69a',
                borderDownColor: '#ef5350',
                wickUpColor: '#26a69a',
                wickDownColor: '#ef5350'
            });

            console.log('[LWCharts] ✓ Chart initialized successfully');
            this.showStatus('Chart ready', 'success');

            // Handle window resize
            window.removeEventListener('resize', this.onResize);
            window.addEventListener('resize', this.onResize.bind(this));

            return true;
        } catch (error) {
            console.error('[LWCharts] ERROR initializing chart:', error);
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

            // Fetch OHLC data from API
            const response = await fetch(
                `/api/ohlc?symbol=${encodeURIComponent(sym)}&interval=${interval}&limit=200`,
                { signal: this.currentFetchController.signal }
            );

            if (!response.ok) {
                throw new Error(`API error: ${response.status}`);
            }

            const responseData = await response.json();
const data = responseData.data || responseData;


            if (!Array.isArray(data) || data.length === 0) {
                console.warn('[LWCharts] No data received from API');
                this.showStatus('No data available for this symbol', 'error');
                return;
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
            this.showStatus(`Loaded ${candles.length} candles for ${sym}`, 'success');

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

    onResize: function() {
        if (!this.chart) return;
        const container = document.getElementById('chartContainer');
        if (!container) return;
        this.chart.applyOptions({
            width: container.clientWidth,
            height: Math.max(480, Math.floor(container.clientHeight || 600))
        });
        this.chart.timeScale().fitContent();
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
