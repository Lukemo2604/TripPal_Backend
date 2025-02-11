# src/routes/user_routes.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.utils.db import get_db
from bson import ObjectId

user_bp = Blueprint("user_bp", __name__)

@user_bp.route("/user", methods=["GET"])
@jwt_required()
def get_user():
    """Get the current user's data by JWT identity."""
    db = get_db()
    user_id = get_jwt_identity()  # This is str(user["_id"])

    user = db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        return jsonify({"error": "User not found"}), 404

    # Convert _id to string
    user["_id"] = str(user["_id"])
    # You might want to remove the password hash before sending to client
    user.pop("password", None)

    return jsonify(user), 200


@user_bp.route("/user", methods=["PATCH"])
@jwt_required()
def update_user():
    db = get_db()
    user_id = get_jwt_identity()
    data = request.json

    update_fields = {}

    # Existing fields:
    if "username" in data:
        update_fields["username"] = data["username"]
    if "email" in data:
        update_fields["email"] = data["email"]
    if "about" in data:
        update_fields["about"] = data["about"]
    if "preferences" in data:
        update_fields["preferences"] = data["preferences"]
    if "familyMembers" in data:
        update_fields["familyMembers"] = data["familyMembers"]

    # New fields:
    if "address" in data:
        update_fields["address"] = data["address"]
    if "phone" in data:
        update_fields["phone"] = data["phone"]
    if "postcode" in data:
        update_fields["postcode"] = data["postcode"]
    if "dob" in data:
        update_fields["dob"] = data["dob"]  # You can store as string or parse a date

    db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": update_fields}
    )

    return jsonify({"success": True}), 200

