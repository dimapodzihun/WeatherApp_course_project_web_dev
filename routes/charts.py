from flask import Blueprint, render_template, request, session

import services.charts_builder as charts_builder
from models import SavedCity, User, db
from utils import login_required

charts_bp = Blueprint("charts", __name__, url_prefix="/charts")


def _normalize_days(days):
    if days in (1, 3, 5):
        return days
    if days is None:
        return 5
    return max(1, min(days, 5))


@charts_bp.route("/", methods=["GET"])
@login_required
def index():
    user = db.session.get(User, session["user_id"])
    saved_cities = user.saved_cities

    city_id = request.args.get("city_id", type=int)
    days = _normalize_days(request.args.get("days", type=int, default=5))

    if not saved_cities:
        return render_template(
            "charts/index.html",
            cities=[],
            selected_city_id=None,
        )

    if not city_id:
        city_id = saved_cities[0].id

    selected_city = SavedCity.query.get_or_404(city_id)
    if selected_city.user_id != session["user_id"]:
        return "", 403

    raw_data = charts_builder.weather_api.get_forecast_raw(selected_city.city_name)
    forecast_df = charts_builder.build_forecast_dataframe(raw_data, days)

    return render_template(
        "charts/index.html",
        cities=saved_cities,
        selected_city_id=city_id,
        days=days,
        temp_hourly_chart=charts_builder.build_temp_hourly_chart(forecast_df),
        humidity_chart=charts_builder.build_humidity_hourly_chart(forecast_df),
        pressure_chart=charts_builder.build_pressure_hourly_chart(forecast_df),
        forecast_minmax_chart=charts_builder.build_forecast_minmax_chart(forecast_df),
    )


@charts_bp.route("/data", methods=["GET"])
@login_required
def data():
    city_id = request.args.get("city_id", type=int)
    days = _normalize_days(request.args.get("days", type=int, default=5))

    if not city_id:
        return ""

    selected_city = SavedCity.query.get_or_404(city_id)
    if selected_city.user_id != session["user_id"]:
        return "", 403

    raw_data = charts_builder.weather_api.get_forecast_raw(selected_city.city_name)
    forecast_df = charts_builder.build_forecast_dataframe(raw_data, days)

    return render_template(
        "partials/charts_content.html",
        temp_hourly_chart=charts_builder.build_temp_hourly_chart(forecast_df),
        humidity_chart=charts_builder.build_humidity_hourly_chart(forecast_df),
        pressure_chart=charts_builder.build_pressure_hourly_chart(forecast_df),
        forecast_minmax_chart=charts_builder.build_forecast_minmax_chart(forecast_df),
    )
