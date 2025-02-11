# src/routes/auth_routes.py
from flask import Blueprint, request, jsonify
from src.utils.db import get_db
from src.utils.hash import hash_password, check_password
from flask_jwt_extended import create_access_token
from bson import ObjectId
import datetime

auth_bp = Blueprint("auth_bp", __name__)

@auth_bp.route("/register", methods=["POST"])
def register():
    """Register a new user and store in MongoDB."""
    data = request.json
    email = data.get("email")
    password = data.get("password")
    name = data.get("name", "")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    db = get_db()
    existing_user = db.users.find_one({"email": email})
    if existing_user:
        return jsonify({"error": "User already exists"}), 400

    hashed = hash_password(password)
    user = {
        "email": email,
        "password": hashed,  # store hashed password
        "name": name,
        "preferences": [],
        "familyMembers": [],
        # Could store an array of references to trips in separate collection
        # But we'll keep it minimal here
    }

    result = db.users.insert_one(user)
    user_id = str(result.inserted_id)

    # Optionally create JWT upon registration
    access_token = create_access_token(
        identity=user_id,
        expires_delta=datetime.timedelta(days=1)
    )
    return jsonify({"token": access_token, "userId": user_id}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    """User login. Return JWT if credentials are valid."""
    data = request.json
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400

    db = get_db()
    user = db.users.find_one({"email": email})
    if not user:
        return jsonify({"error": "Invalid credentials"}), 401

    # Compare the password
    if not check_password(password, user["password"]):
        return jsonify({"error": "Invalid credentials"}), 401

    # If valid, create JWT
    user_id = str(user["_id"])
    access_token = create_access_token(
        identity=user_id,
        expires_delta=datetime.timedelta(days=1)  # 1 day token
    )
    return jsonify({"token": access_token, "userId": user_id}), 200
