from flask import Blueprint, render_template, request, session

from models import SavedCity, User, db
import services.climate_analytics as climate_analytics
from utils import login_required

analytics_bp = Blueprint("analytics", __name__, url_prefix="/analytics")


@analytics_bp.route("/", methods=["GET"])
@login_required
def index():
    user = db.session.get(User, session["user_id"])
    saved_cities = user.saved_cities
    city_id = request.args.get("city_id", type=int)

    if not saved_cities:
        return render_template(
            "analytics/index.html",
            cities=[],
            selected_city_id=None,
            history_summary=climate_analytics.build_history_summary(None),
            climate_summary=climate_analytics.build_climate_summary(None),
            history_chart=None,
            metrics_chart=None,
            climate_chart=None,
        )

    if not city_id:
        city_id = saved_cities[0].id

    selected_city = SavedCity.query.get_or_404(city_id)
    if selected_city.user_id != session["user_id"]:
        return "", 403

    df = climate_analytics.get_history_dataframe_for_city(city_id)
    return render_template(
        "analytics/index.html",
        cities=saved_cities,
        selected_city_id=city_id,
        history_summary=climate_analytics.build_history_summary(df),
        climate_summary=climate_analytics.build_climate_summary(df),
        history_chart=climate_analytics.build_temperature_history_chart(df),
        metrics_chart=climate_analytics.build_history_metrics_chart(df),
        climate_chart=climate_analytics.build_climate_change_chart(df),
    )
