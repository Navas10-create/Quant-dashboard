Charting module for Quant-dashboard
==================================

Installation:
1. Copy this folder into your repo root as `charting/`.
2. Ensure lightweight-charts JS is present: charting/static/charting/js/lightweight-charts.standalone.production.js
3. In app.py register the blueprint:
   from charting.blueprint import chart_bp
   csrf.exempt(chart_bp)   # optional
   app.register_blueprint(chart_bp)
4. Restart Flask.

Usage:
- Visit /charts/<SYMBOL> (e.g., /charts/NIFTY)
- Default data flow: local JSON -> OpenAlgo history -> Fyers
- To populate local JSON: run charting/scripts/daily_updater.py NIFTY

Extending:
- Add more indicators in charting/static/charting/js/indicators.js
- Improve drawing overlay: add selection, drag, persistence
- For real-time: implement WebSocket to server that streams tick updates and call series.update()
