"""Flask app factory."""
from __future__ import annotations

from flask import Flask
from flask_cors import CORS


def create_app() -> Flask:
    app = Flask(__name__)
    CORS(app)

    from viewer.routes import bp
    app.register_blueprint(bp)

    return app


# Allow `flask --app viewer.app run`
app = create_app()
