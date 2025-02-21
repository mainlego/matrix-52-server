# create_app.py
from flask import Flask
from flask_cors import CORS
from app.routes import api


def create_app():
    app = Flask(__name__)


    # Register blueprints
    app.register_blueprint(api, url_prefix='/api')

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)