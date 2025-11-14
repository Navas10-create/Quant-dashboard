import json, os
from database.token_db_enhanced import BrokerSymbolCache

print("🔍 Reading symbols from BrokerSymbolCache...")

try:
    cache = BrokerSymbolCache()

    # this method only loads data; doesn't return it
    cache.load_all_symbols(broker='fyers')

    # now extract the loaded cache from the correct property
    symbols = None
    for attr in ['cache', 'symbols', 'data', '_cache', '_symbols']:
        if hasattr(cache, attr):
            candidate = getattr(cache, attr)
            if isinstance(candidate, (dict, list)) and len(candidate) > 0:
                symbols = candidate
                print(f"✅ Found symbol data in cache attribute: {attr}")
                break

    if symbols is None:
        print("⚠️ Could not locate symbols in BrokerSymbolCache object.")
        symbols = {}

    data = []

    # handle dict vs list formats
    if isinstance(symbols, dict):
        for key, value in symbols.items():
            if isinstance(value, dict):
                name = value.get("name") or key
                symbol = value.get("symbol") or value.get("fyers_symbol") or key
            else:
                name, symbol = str(value), key
            if name and symbol:
                data.append({"name": name, "symbol": symbol})
    elif isinstance(symbols, list):
        for entry in symbols:
            name = entry.get("name") or entry.get("symbol")
            symbol = entry.get("symbol") or entry.get("fyers_symbol")
            if name and symbol:
                data.append({"name": name, "symbol": symbol})

    os.makedirs("config", exist_ok=True)
    out_path = os.path.join("config", "instrument_index.json")

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print(f"✅ Exported {len(data)} symbols to {out_path}")

except Exception as e:
    print("⚠️ Error while exporting symbols:", e)
