from flask import Blueprint, render_template, request, session

from models import SavedCity, User, db
from services.history import build_city_card_data, record_city_history_if_due
from utils import login_required

cities_bp = Blueprint("cities", __name__, url_prefix="/cities")


@cities_bp.route("/save", methods=["POST"])
@login_required
def save_city():
    city_name = request.form.get("city_name")
    country_code = request.form.get("country_code", "")

    if not city_name:
        return "Missing city_name", 400

    existing = SavedCity.query.filter_by(
        user_id=session["user_id"],
        city_name=city_name,
        country_code=country_code,
    ).first()
    if not existing:
        new_city = SavedCity(
            user_id=session["user_id"],
            city_name=city_name,
            country_code=country_code,
        )
        db.session.add(new_city)
        db.session.commit()
        record_city_history_if_due(new_city, min_interval_minutes=0)

    return "", 200


@cities_bp.route("/all", methods=["GET"])
@login_required
def get_all_cities():
    user = db.session.get(User, session["user_id"])

    cities_data = []
    for city in reversed(user.saved_cities):
        latest_weather, _, _ = record_city_history_if_due(city)
        cities_data.append(build_city_card_data(city, latest_weather))

    return render_template("partials/cities_grid.html", cities=cities_data)


@cities_bp.route("/<int:city_id>/refresh", methods=["POST"])
@login_required
def refresh_city(city_id):
    city = SavedCity.query.get_or_404(city_id)

    if city.user_id != session["user_id"]:
        return "Unauthorized", 403

    history, _, weather = record_city_history_if_due(city, min_interval_minutes=0)
    if weather and "error" not in weather and history:
        city_data = build_city_card_data(city, history)
        return render_template("partials/city_card.html", city=city_data)

    return "Error updating", 500


@cities_bp.route("/<int:city_id>", methods=["DELETE"])
@login_required
def delete_city(city_id):
    city = SavedCity.query.get_or_404(city_id)

    if city.user_id != session["user_id"]:
        return "Unauthorized", 403

    db.session.delete(city)
    db.session.commit()
    return ""
