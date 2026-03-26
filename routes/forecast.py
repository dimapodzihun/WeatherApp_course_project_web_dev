from flask import Blueprint, render_template, request, session

import services.openweather as weather_api
import services.weather_insights as weather_insights
import services.long_term_forecast as long_term_forecast
import services.weather_ml as weather_ml
from models import User, db
from utils import login_required

forecast_bp = Blueprint("forecast", __name__, url_prefix="/forecast")


def country_code_to_flag(country_code):
    if not country_code or len(country_code) != 2:
        return ""
    return chr(127397 + ord(country_code[0].upper())) + chr(127397 + ord(country_code[1].upper()))


@forecast_bp.route("/", methods=["GET"])
@login_required
def index():
    user = db.session.get(User, session["user_id"])
    saved_cities = user.saved_cities

    if not saved_cities:
        return render_template(
            "forecast/index.html",
            cities=[],
            selected_city="",
            selected_country="",
            selected_flag="",
            forecast=[],
            hourly=[],
        )

    city_name = request.args.get("city")
    if not city_name:
        city_name = saved_cities[0].city_name
    selected_city_obj = next((city for city in saved_cities if city.city_name == city_name), saved_cities[0])

    current_weather = weather_api.get_current_weather(city_name)
    current_weather = weather_ml.enrich_weather_with_comfort(current_weather)
    raw_forecast = weather_api.get_forecast_raw(city_name) or []
    forecast_5d = weather_api.build_forecast_5days_from_raw(raw_forecast) or []
    recommendations = weather_insights.build_personal_recommendations(current_weather, raw_forecast)
    alerts = weather_insights.build_weather_alerts(current_weather, raw_forecast)
    extended_summary = long_term_forecast.build_long_term_summary(
        selected_city_obj.id,
        seed_daily=forecast_5d,
    )

    selected_date = request.args.get("date")
    if selected_date:
        hourly_data = weather_api.build_hourly_for_date_from_raw(raw_forecast, selected_date)
    else:
        hourly_data = weather_api.build_hourly_today_from_raw(raw_forecast) or []

    return render_template(
        "forecast/index.html",
        cities=saved_cities,
        selected_city=city_name,
        selected_country=selected_city_obj.country_code,
        selected_flag=country_code_to_flag(selected_city_obj.country_code),
        current_weather=current_weather,
        selected_date=selected_date or (forecast_5d[0]["date_iso"] if forecast_5d else None),
        forecast=forecast_5d,
        hourly=hourly_data,
        recommendations=recommendations,
        alerts=alerts,
        extended_summary=extended_summary,
    )


@forecast_bp.route("/hourly", methods=["GET"])
@login_required
def hourly():
    city_name = request.args.get("city", "")
    date_str = request.args.get("date", "")
    weekday = request.args.get("weekday", "")

    if not city_name or not date_str:
        return ""

    slots = weather_api.get_hourly_for_date(city_name, date_str)
    return render_template("partials/hourly_slots.html", hourly=slots, weekday=weekday)
