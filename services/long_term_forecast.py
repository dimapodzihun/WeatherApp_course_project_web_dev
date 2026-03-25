from datetime import datetime, timedelta

from models import SavedCity, WeatherHistory
import services.openweather as weather_api


_WEEKDAYS_UA = {
    "Mon": "Пн",
    "Tue": "Вт",
    "Wed": "Ср",
    "Thu": "Чт",
    "Fri": "Пт",
    "Sat": "Сб",
    "Sun": "Нд",
}


def _history_stats(city_id):
    rows = (
        WeatherHistory.query.filter_by(city_id=city_id)
        .order_by(WeatherHistory.recorded_at.asc())
        .all()
    )
    if not rows:
        return {
            "count": 0,
            "temp_avg": None,
            "temp_trend": 0.0,
            "humidity_avg": None,
        }

    temps = [float(row.temperature) for row in rows]
    humidities = [float(row.humidity) for row in rows]
    temp_avg = sum(temps) / len(temps)
    humidity_avg = sum(humidities) / len(humidities)
    temp_trend = (temps[-1] - temps[0]) / max(len(temps) - 1, 1) if len(temps) >= 2 else 0.0

    return {
        "count": len(rows),
        "temp_avg": temp_avg,
        "temp_trend": temp_trend,
        "humidity_avg": humidity_avg,
    }


def build_extended_outlook(city_id, horizon_days=14):
    city = SavedCity.query.get(city_id)
    if city is None:
        return []

    seed_daily = weather_api.get_forecast_5days(city.city_name) or []
    if not seed_daily:
        return []

    stats = _history_stats(city.id)
    seed_daily = seed_daily[: min(5, len(seed_daily))]
    temp_anchor = sum(item["temp_max"] for item in seed_daily) / len(seed_daily)
    temp_floor = sum(item["temp_min"] for item in seed_daily) / len(seed_daily)
    humidity_anchor = stats["humidity_avg"] if stats["humidity_avg"] is not None else 65.0
    descriptions = [item["description"] for item in seed_daily]
    trend = stats["temp_trend"]

    last_seed_date = datetime.strptime(seed_daily[-1]["date_iso"], "%Y-%m-%d").date()
    base_date = datetime.now().date()
    result = []

    for offset in range(1, horizon_days + 1):
        target_date = last_seed_date + timedelta(days=offset)
        weekly_wave = ((offset % 7) - 3) * 0.4
        history_bias = 0.0 if stats["temp_avg"] is None else (stats["temp_avg"] - temp_anchor) * 0.15
        projected_max = round(temp_anchor + weekly_wave + trend * offset * 0.35 + history_bias, 1)
        projected_min = round(temp_floor + weekly_wave * 0.7 + trend * offset * 0.25 + history_bias, 1)
        projected_humidity = max(30, min(95, round(humidity_anchor + (offset % 5 - 2) * 2)))
        confidence = max(42, 80 - offset)

        weekday_en = target_date.strftime("%a")
        result.append(
            {
                "date": target_date.strftime("%d.%m"),
                "date_iso": target_date.isoformat(),
                "weekday": _WEEKDAYS_UA.get(weekday_en, weekday_en),
                "temp_max": projected_max,
                "temp_min": projected_min,
                "humidity": projected_humidity,
                "description": descriptions[(offset - 1) % len(descriptions)],
                "confidence": confidence,
                "source": "Оціночний прогноз",
                "days_ahead": (target_date - base_date).days,
            }
        )

    return result


def build_long_term_summary(city_id):
    outlook_14 = build_extended_outlook(city_id, 14)
    outlook_30 = build_extended_outlook(city_id, 30)
    if not outlook_14 or not outlook_30:
        return {
            "outlook_14": [],
            "outlook_30": [],
            "avg_14": None,
            "avg_30": None,
            "trend_label": "Недостатньо даних",
        }

    avg_14 = round(sum(item["temp_max"] for item in outlook_14) / len(outlook_14), 1)
    avg_30 = round(sum(item["temp_max"] for item in outlook_30) / len(outlook_30), 1)

    if avg_30 >= avg_14 + 1:
        trend_label = "Далі, ймовірно, буде тепліше"
    elif avg_30 <= avg_14 - 1:
        trend_label = "Далі, ймовірно, буде холодніше"
    else:
        trend_label = "Суттєвих змін не очікується"

    return {
        "outlook_14": outlook_14,
        "outlook_30": outlook_30,
        "avg_14": avg_14,
        "avg_30": avg_30,
        "trend_label": trend_label,
    }
