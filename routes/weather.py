from datetime import datetime

from flask import Blueprint, render_template, request, session

import services.openweather as weather_api
import services.weather_ml as weather_ml
from models import User, db
from services.history import record_city_history_if_due

weather_bp = Blueprint("weather", __name__)


@weather_bp.route("/")
def index():
    saved_cities = []
    current_weather = None

    if "user_id" in session:
        user = db.session.get(User, session["user_id"])
        if user:
            saved_cities = user.saved_cities
            if saved_cities:
                first_city = saved_cities[0]
                current_weather = weather_api.get_current_weather(first_city.city_name)
                if current_weather and "error" not in current_weather:
                    record_city_history_if_due(first_city, weather=current_weather)
                    current_weather = weather_ml.enrich_weather_with_comfort(current_weather)

    return render_template(
        "dashboard/index.html",
        saved_cities=saved_cities,
        current_weather=current_weather,
        current_date=datetime.now().strftime("%d.%m.%Y"),
    )


@weather_bp.route("/weather/current")
def current_weather_htmx():
    if "user_id" not in session:
        return ""

    user = db.session.get(User, session["user_id"])
    if not user or not user.saved_cities:
        return ""

    first_city = user.saved_cities[0]
    weather = weather_api.get_current_weather(first_city.city_name)

    if weather and "error" not in weather:
        record_city_history_if_due(first_city, weather=weather)
        weather = weather_ml.enrich_weather_with_comfort(weather)
        return render_template("partials/main_weather_block.html", current_weather=weather)
    return ""


@weather_bp.route("/search")
def search():
    query = request.args.get("q", "").strip()
    if len(query) < 3:
        return ""

    weather = weather_api.get_current_weather(query)

    if weather and "error" in weather:
        return f"""
        <div class="text-[#DC2626] text-sm mt-2 text-center p-3 bg-red-50 rounded-lg">
            {weather['error']}
        </div>
        """

    weather = weather_ml.enrich_weather_with_comfort(weather)
    return render_template("partials/weather_card.html", weather=weather, is_main_current=False)


@weather_bp.route("/auth/hint")
def auth_hint():
    return render_template("partials/auth_hint.html")


@weather_bp.route("/search/suggestions")
def search_suggestions():
    query = request.args.get("q", "").strip()
    if len(query) < 2:
        return ""
    suggestions = weather_api.get_city_suggestions(query)
    if not suggestions:
        return ""
    return render_template("partials/search_suggestions.html", suggestions=suggestions)
