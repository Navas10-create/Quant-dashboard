#!/usr/bin/env python3
"""
charts_extension - OpenAlgo Charting and Fyers Integration Package

Provides REST API endpoints, WebSocket streaming, technical indicators,
and signal management for trading dashboards and chart analysis.

This is the main package initialization file.
"""

from flask_socketio import SocketIO

socketio = SocketIO(cors_allowed_origins="*")


def init_charts_extension(app):
    """
    Initialize charts extension with Flask application.
    
    This function registers the charts blueprint with the Flask app
    and initializes all charting APIs.
    
    Args:
        app: Flask application instance
        
    Returns:
        bool: True if initialization successful, False otherwise
        
    Example:
        from flask import Flask
        from charts_extension import init_charts_extension
        
        app = Flask(__name__)
        init_charts_extension(app)
    """
    try:
        from .charts.routes import bp
        app.register_blueprint(bp, url_prefix='/api')
        print("[Charts Extension] ✓ Successfully registered blueprint at /api")
        return True
    except ImportError as e:
        print(f"[Charts Extension] ✗ Import failed: {e}")
        return False
    except Exception as e:
        print(f"[Charts Extension] ✗ Registration failed: {e}")
        return False


__all__ = ['socketio', 'init_charts_extension']