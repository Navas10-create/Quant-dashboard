# charting/blueprint.py
from flask import Blueprint, render_template, request, jsonify, current_app
from .api.router import MultiSourceRouter
from .api.datasource import DataSourceError

chart_bp = Blueprint("charting", __name__, template_folder="templates")
router = MultiSourceRouter()

@chart_bp.route("/charts/<symbol>")
def charts_page(symbol):
    # A friendly page that mounts the frontend UI
    return render_template("charting/chart_container.html", symbol=symbol)

@chart_bp.route("/chart/data")
def chart_data():
    symbol = request.args.get("symbol")
    interval = request.args.get("interval", "1")
    limit = int(request.args.get("limit", 1000))
    if not symbol:
        return jsonify({"status":"error","message":"symbol query param required"}), 400
    try:
        bars = router.get_ohlcv(symbol, interval, limit)
        return jsonify({"status":"ok","bars":bars})
    except DataSourceError as e:
        current_app.logger.error("chart data error: %s", e)
        return jsonify({"status":"error","message": str(e)}), 500
