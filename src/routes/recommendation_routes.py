import logging
from flask import Blueprint, request, jsonify
import requests
import os
from src.utils.preference_mapping import PREFERENCE_MAPPING, map_preference

recommendation_bp = Blueprint("recommendation_bp", __name__)

@recommendation_bp.route("/recommendations", methods=["POST"])
def get_recommendations():
    
    try:
        data = request.get_json() or {}
        city = data.get("city", "").strip()
        user_prefs = data.get("userPreferences", [])
        family_prefs = data.get("familyPreferences", [])
        # Or if you only have 'preferences', just treat them all the same.

        if not city:
            return jsonify({"error": "City is required"}), 400

        api_key = os.getenv("GOOGLE_PLACES_API_KEY")
        if not api_key:
            return jsonify({"error": "Google Places API key is not configured"}), 500

        # Combine user + family preferences for the actual Google search.
        # This ensures we don't miss places that match either group.
        all_prefs = user_prefs + family_prefs
        if not all_prefs:
            # If no prefs, default to something broad, e.g. "attractions in city"
            all_prefs = ["attractions"]

        # Build the OR query for the Places Text Search.
        mapped_terms = [map_preference(p) for p in all_prefs]
        query = " OR ".join(mapped_terms) + f" in {city}"

        logging.info(f"Google Places API query: {query}")

        url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        params = {
            "query": query,
            "key": api_key,
        }

        response = requests.get(url, params=params)
        if response.status_code != 200:
            logging.error(f"Google Places API returned {response.status_code}")
            return jsonify({"error": "Failed to fetch recommendations"}), 500

        results = response.json().get("results", [])


        def count_matches(place, prefs):
            score = 0
            place_name = place.get("name", "").lower()
            place_types = place.get("types", [])
            place_address = place.get("formatted_address", "").lower()
            for pref in prefs:
                pref_lower = pref.lower()
                # If the place name, address, or any type matches the preference string
                if (pref_lower in place_name) or (pref_lower in place_address) or any(pref_lower in t.lower() for t in place_types):
                    score += 1
            return score

        # We can define weights, e.g. user = 2, family = 1
        USER_WEIGHT = 1.5
        FAMILY_WEIGHT = 1

        # Build a new list with a "score" for each place
        scored_results = []
        for place in results:
            user_match_count = count_matches(place, user_prefs)
            family_match_count = count_matches(place, family_prefs)

            # You can also incorporate rating as part of the score:
            rating = place.get("rating", 0)
            # Weighted formula:
            place_score = (USER_WEIGHT * user_match_count) + (FAMILY_WEIGHT * family_match_count) + rating

            # Construct photo URL if available
            photos = place.get("photos", [])
            photo_url = None
            if photos:
                photo_ref = photos[0].get("photo_reference")
                if photo_ref:
                    photo_url = (
                        f"https://maps.googleapis.com/maps/api/place/photo?"
                        f"maxwidth=400&photoreference={photo_ref}&key={api_key}"
                    )

            scored_results.append({
                "place": place,
                "score": place_score,
                "photo_url": photo_url
            })

        # Sort by score descending
        scored_results.sort(key=lambda x: x["score"], reverse=True)

        # Slice top 10
        top_results = scored_results[:10]

        # Build final recommendations to return
        recommendations = []
        for item in top_results:
            place = item["place"]
            recommendations.append({
                "name": place.get("name"),
                "formatted_address": place.get("formatted_address"),
                "rating": place.get("rating"),
                "types": place.get("types"),
                "place_id": place.get("place_id"),
                "photo_url": item["photo_url"],
                "calculated_score": item["score"],  # Optional, just to see how it was ranked
            })

        return jsonify({"recommendations": recommendations}), 200

    except Exception as e:
        logging.exception("Error in get_recommendations:")
        return jsonify({"error": "An error occurred while processing your request"}), 500
