"""GeoSimAI Application Entry Point."""

import os
from flask import Flask, send_from_directory
from flask_cors import CORS

from src.config import Config
from src.api.routes import api_bp


def create_app() -> Flask:
    """Application factory for GeoSimAI."""
    static_folder = os.path.join(os.path.dirname(__file__), "src", "static")
    app = Flask(__name__, static_folder=static_folder)
    CORS(app)

    # Register API blueprint
    app.register_blueprint(api_bp)

    @app.route("/")
    def index():
        """Serve frontend single-page application."""
        return send_from_directory(static_folder, "index.html")

    @app.route("/<path:path>")
    def static_proxy(path):
        """Serve static files."""
        return send_from_directory(static_folder, path)

    return app


if __name__ == "__main__":
    app = create_app()
    print("=" * 60)
    print("GeoSimAI Web Application starting...")
    print(f"URL: http://{Config.HOST}:{Config.PORT}")
    print("=" * 60)
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
