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
  "shopping": "shopping mall OR boutique",
  "sports": "stadium OR sports arena",
  "dining": "restaurant OR dining",
  "nature": "park OR botanical garden",
    "beach": "beach OR seaside",
    "amusement": "amusement park OR theme park",
    "zoo": "zoo OR aquarium",
    "theater": "theater OR opera house",
    "concert": "concert hall OR music venue",
    "spa": "spa OR wellness center",
    "casino": "casino OR gambling",
    "library": "library OR bookstore",
    "gym": "gym OR fitness center",
    "church": "church OR temple",
    "mosque": "mosque OR religious site",
    "synagogue": "synagogue OR religious site",
    "park": "park OR garden",
    "lake": "lake OR reservoir",
    "river": "river OR stream",
    "mountain": "mountain OR peak",
    "waterfall": "waterfall OR cascade",
    "cave": "cave OR cavern",
    "forest": "forest OR woodland",
    "desert": "desert OR dunes",
    "volcano": "volcano OR crater",
    "waterpark": "waterpark OR splash pad",
    "skating": "skating rink OR ice rink",
    "skiing": "ski resort OR ski slope",
    "snowboarding": "snowboarding OR snow park",
    "surfing": "surfing OR beach",
    "scuba": "scuba diving OR snorkeling",
    "fishing": "fishing OR angling",
    "boating": "boating OR sailing",
    "kayaking": "kayaking OR canoeing",
    "rafting": "rafting OR tubing",
    "biking": "biking OR cycling",
    "horseback": "horseback riding OR equestrian",
    "golf": "golf course OR driving range",
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

        # Get Google Places API key from environment variables.
        api_key = os.getenv("GOOGLE_PLACES_API_KEY")
        if not api_key:
            return jsonify({"error": "Google Places API key is not configured"}), 500

        # Map the preferences to search terms.
        mapped_terms = map_preferences(preferences)
        # Build a text search query: e.g., "bar OR pub OR nightclub OR museum in New York"
        query = " OR ".join(mapped_terms) + " in " + city

        logging.info(f"Google Places API query: {query}")

        # Call the Google Places Text Search API.
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

        # Optional: Filter out places that match any disliked search terms.
        filtered_results = []
        if dislikes:
            mapped_dislikes = [preference_mapping.get(dislike.lower(), dislike) for dislike in dislikes]
            for place in results:
                types = place.get("types", [])
                # Skip if any mapped dislike appears in the place's types.
                if any(any(dislike_term.lower() in t.lower() for t in types) for dislike_term in mapped_dislikes):
                    continue
                filtered_results.append(place)
        else:
            filtered_results = results

        # Return up to 10 recommendations with selected fields.
        recommendations = []
        for place in filtered_results[:10]:
            recommendations.append({
                "name": place.get("name"),
                "formatted_address": place.get("formatted_address"),
                "rating": place.get("rating"),
                "types": place.get("types"),
                "place_id": place.get("place_id")
            })

        return jsonify({"recommendations": recommendations}), 200

    except Exception as e:
        logging.exception("Error in get_recommendations:")
        return jsonify({"error": "An error occurred while processing your request"}), 500
