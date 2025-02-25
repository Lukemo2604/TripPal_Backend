from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.utils.db import get_db
from bson import ObjectId

trip_bp = Blueprint("trip_bp", __name__)

@trip_bp.route("/trips", methods=["POST"])
@jwt_required()
def create_trip():
    """Create a new trip for the logged-in user."""
    db = get_db()
    user_id = get_jwt_identity()
    data = request.json

    # Build the trip document according to your schema
    trip = {
        "userId": ObjectId(user_id),
        "location": data.get("location"),
        "startDate": data.get("startDate"),
        "endDate": data.get("endDate"),
        "flights": data.get("flights"),
        "accommodation": data.get("accommodation"),
        "familyAttending": data.get("familyAttending", []),  # default to empty array if not provided
        "budget": data.get("budget"),
        "notes": data.get("notes"),
        "itinerary": data.get("itinerary", [])  # also default to empty array
    }

    result = db.trips.insert_one(trip)
    # Convert ObjectIds to strings for JSON response
    trip["_id"] = str(result.inserted_id)
    trip["userId"] = str(trip["userId"])

    return jsonify(trip), 201


@trip_bp.route("/trips", methods=["GET"])
@jwt_required()
def get_trips():
    """Get all trips for the logged-in user."""
    db = get_db()
    user_id = get_jwt_identity()

    trips_cursor = db.trips.find({"userId": ObjectId(user_id)})
    trips = []
    for t in trips_cursor:
        t["_id"] = str(t["_id"])
        t["userId"] = str(t["userId"])
        trips.append(t)

    return jsonify(trips), 200


@trip_bp.route("/trips/<trip_id>", methods=["PATCH"])
@jwt_required()
def update_trip(trip_id):
    """Update fields of an existing trip."""
    db = get_db()
    user_id = get_jwt_identity()
    data = request.json

    # Attempt to update only the trip that belongs to this user
    result = db.trips.update_one(
        {"_id": ObjectId(trip_id), "userId": ObjectId(user_id)},
        {"$set": data}
    )

    if result.modified_count == 0:
        # Either trip doesn't exist, or user doesn't own it, or no fields actually changed
        return jsonify({"error": "No trip updated"}), 404

    # Re-fetch the updated trip so we can return it
    updated_trip = db.trips.find_one({"_id": ObjectId(trip_id)})
    if not updated_trip:
        return jsonify({"error": "Trip not found after update"}), 404

    updated_trip["_id"] = str(updated_trip["_id"])
    updated_trip["userId"] = str(updated_trip["userId"])

    return jsonify(updated_trip), 200


@trip_bp.route("/trips/<trip_id>", methods=["DELETE"])
@jwt_required()
def delete_trip(trip_id):
    """Delete a trip if it belongs to the logged-in user."""
    db = get_db()
    user_id = get_jwt_identity()

    result = db.trips.delete_one({"_id": ObjectId(trip_id), "userId": ObjectId(user_id)})
    if result.deleted_count == 0:
        return jsonify({"error": "No trip deleted"}), 404

    return jsonify({"success": True}), 200

