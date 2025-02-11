# app.py
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv
import os

# Import your database init function
from src.utils.db import init_db

# Import your blueprints
from src.routes.auth_routes import auth_bp
from src.routes.user_routes import user_bp
from src.routes.trip_routes import trip_bp

load_dotenv()  # loads variables from .env (e.g., MONGO_URI, JWT_SECRET_KEY)

def create_app():
    app = Flask(__name__)

    # 1) Configure app
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "dev-secret-key")
    app.config["MONGO_URI"] = os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017/trippal")

    # 2) Initialize the database
    init_db(app.config["MONGO_URI"])

    # 3) Set up JWT
    jwt = JWTManager(app)

    # 4) Enable CORS (allow all origins for /api/*)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # 5) Register blueprints with an /api prefix
    app.register_blueprint(auth_bp, url_prefix="/api")
    app.register_blueprint(user_bp, url_prefix="/api")
    app.register_blueprint(trip_bp, url_prefix="/api")

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)

