# src/routes/recommendation_routes.py
import logging
from flask import Blueprint, request, jsonify
import requests
import os

recommendation_bp = Blueprint("recommendation_bp", __name__)

# Map common preferences to search query terms.
preference_mapping = {
    "drinking": "bar OR pub OR nightclub",
    "hiking": "hiking trails OR nature park",
    "museum": "museum OR art gallery",
    "cafe": "cafe OR coffee shop",
    "shopping": "shopping mall OR boutique OR market",
    "sports": "stadium OR sports arena OR gym",
    "dining": "restaurant OR fine dining OR casual dining",
    "nature": "botanical garden OR park OR nature reserve",
    "historical": "historical site OR landmark OR heritage site",
    "entertainment": "theater OR cinema OR concert hall OR comedy club",
    "family": "family friendly OR amusement park OR zoo",
    "romantic": "romantic restaurant OR scenic viewpoint OR love nest",
    "art": "art gallery OR exhibition OR museum",
    "nightlife": "night club OR lounge OR live music",
    "local": "local market OR cultural center OR street food",
    "fitness": "gym OR fitness center OR yoga studio",
    "spa": "spa OR wellness center OR massage parlor",
    "science": "science museum OR planetarium OR discovery center",
    "bookstore": "bookstore OR library",
    "concert": "concert venue OR live music",
    "theater": "theater OR performing arts center",
    "outdoors": "outdoor adventure OR hiking trails OR picnic park",
    "food": "food market OR gourmet food shop OR culinary school",
    "cultural": "cultural center OR heritage site OR folk museum",
    # You can add more mappings here.
}


def map_preferences(preferences):
    """Return a list of search terms based on user preferences."""
    return [preference_mapping.get(pref.lower(), pref) for pref in preferences]

@recommendation_bp.route("/recommendations", methods=["POST"])
def get_recommendations():
    """
    Expects a JSON payload:
    {
      "city": "New York",
      "preferences": ["drinking", "museum"],
      "dislikes": ["hiking"]
    }
    """
    try:
        data = request.get_json() or {}
        city = data.get("city", "").strip()
        preferences = data.get("preferences", [])
        dislikes = data.get("dislikes", [])

        if not city:
            return jsonify({"error": "City is required"}), 400

        api_key = os.getenv("GOOGLE_PLACES_API_KEY")
        if not api_key:
            return jsonify({"error": "Google Places API key is not configured"}), 500

        mapped_terms = map_preferences(preferences)
        query = " OR ".join(mapped_terms) + " in " + city

        logging.info(f"Google Places API query: {query}")

        url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        params = {
            "query": query,
            "key": api_key,
        }

        response = requests.get(url, params=params)
        if response.status_code != 200:
            logging.error(f"Google Places API returned {response.status_code}")
            return jsonify({"error": "Failed to fetch recommendations from Google Places API"}), 500

        results = response.json().get("results", [])

        # Optional: Filter out results based on dislikes (omitted for brevity).
        filtered_results = results

        # Build the recommendations list.
        recommendations = []
        for place in filtered_results[:10]:
            # Construct photo URL if available.
            photos = place.get("photos", [])
            photo_url = None
            if photos:
                photo_reference = photos[0].get("photo_reference")
                if photo_reference:
                    photo_url = (
                        f"https://maps.googleapis.com/maps/api/place/photo?"
                        f"maxwidth=400&photoreference={photo_reference}&key={api_key}"
                    )
            recommendations.append({
                "name": place.get("name"),
                "formatted_address": place.get("formatted_address"),
                "rating": place.get("rating"),
                "types": place.get("types"),
                "place_id": place.get("place_id"),
                "photo_url": photo_url
            })

        return jsonify({"recommendations": recommendations}), 200

    except Exception as e:
        logging.exception("Error in get_recommendations:")
        return jsonify({"error": "An error occurred while processing your request"}), 500
