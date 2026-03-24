from datetime import datetime, timedelta

from models import db, WeatherHistory
import services.openweather as weather_api
import services.weather_ml as weather_ml


def record_city_history_if_due(saved_city, min_interval_minutes=10, weather=None):
    last = (
        WeatherHistory.query.filter_by(city_id=saved_city.id)
        .order_by(WeatherHistory.recorded_at.desc())
        .first()
    )
    threshold = datetime.utcnow() - timedelta(minutes=min_interval_minutes)

    if last and last.recorded_at >= threshold:
        return last, False, weather

    if weather is None:
        weather = weather_api.get_current_weather(saved_city.city_name)

    if not weather or "error" in weather:
        return last, False, weather

    history = WeatherHistory(
        city_id=saved_city.id,
        temperature=weather["temperature"],
        humidity=weather["humidity"],
        pressure=weather["pressure"],
        wind_speed=weather["wind_speed"],
        description=weather["description"],
    )
    db.session.add(history)
    db.session.commit()
    weather_ml.invalidate_model_cache()
    return history, True, weather


def build_city_card_data(saved_city, history_entry):
    return {
        "id": saved_city.id,
        "name": saved_city.city_name,
        "country": saved_city.country_code,
        "country_name": weather_api.get_country_name(saved_city.country_code),
        "temperature": int(history_entry.temperature) if history_entry else None,
        "description": history_entry.description if history_entry else "Немає даних",
        "updated_at": history_entry.recorded_at.strftime("%H:%M") if history_entry else None,
    }
