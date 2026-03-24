from __future__ import annotations

from typing import Optional

from sqlalchemy import func

from models import WeatherHistory, db

try:
    from sklearn.tree import DecisionTreeClassifier #модель машинного навчання
except Exception:  # pragma: no cover
    DecisionTreeClassifier = None


_MODEL_CACHE = {
    "signature": None,
    "model": None,
    "samples": 0,
}

_LABELS_UA = {
    "comfortable": "Комфортно",
    "moderate": "Помірно",
    "uncomfortable": "Некомфортно",
}


def invalidate_model_cache():
    _MODEL_CACHE["signature"] = None
    _MODEL_CACHE["model"] = None
    _MODEL_CACHE["samples"] = 0


def _history_signature():
    count_value, max_recorded_at = db.session.query(
        func.count(WeatherHistory.id),
        func.max(WeatherHistory.recorded_at),
    ).one()
    return (
        int(count_value or 0),
        max_recorded_at.isoformat() if max_recorded_at else None,
    )


def _extract_features(temperature, humidity, pressure, wind_speed):
    if None in (temperature, humidity, pressure, wind_speed):
        return None
    return [float(temperature), float(humidity), float(pressure), float(wind_speed)]


def rule_based_comfort_class(temperature, humidity, pressure, wind_speed):
    score = 100
    score -= abs(float(temperature) - 22) * 2.2
    score -= max(float(wind_speed) - 4, 0) * 4
    score -= max(float(humidity) - 70, 0) * 0.7
    score -= max(1000 - float(pressure), 0) * 0.03

    if score >= 75:
        return "comfortable"
    if score >= 50:
        return "moderate"
    return "uncomfortable"


def _train_model_if_needed():
    signature = _history_signature()
    if _MODEL_CACHE["signature"] == signature:
        return _MODEL_CACHE["model"]

    _MODEL_CACHE["signature"] = signature
    _MODEL_CACHE["model"] = None
    _MODEL_CACHE["samples"] = signature[0]

    if DecisionTreeClassifier is None or signature[0] < 12:
        return None

    records = WeatherHistory.query.order_by(WeatherHistory.recorded_at.asc()).all()
    features = []
    labels = []
    for row in records:
        item = _extract_features(row.temperature, row.humidity, row.pressure, row.wind_speed)
        if item is None:
            continue
        features.append(item)
        labels.append(
            rule_based_comfort_class(
                row.temperature,
                row.humidity,
                row.pressure,
                row.wind_speed,
            )
        )

    if len(features) < 12 or len(set(labels)) < 2:
        return None

    model = DecisionTreeClassifier(
        max_depth=4,
        min_samples_leaf=3,
        random_state=42,
    )
    model.fit(features, labels)
    _MODEL_CACHE["model"] = model
    _MODEL_CACHE["samples"] = len(features)
    return model


def predict_comfort(weather: dict) -> Optional[dict]:
    if not weather or "error" in weather:
        return None

    features = _extract_features(
        weather.get("temperature"),
        weather.get("humidity"),
        weather.get("pressure"),
        weather.get("wind_speed"),
    )
    if features is None:
        return None

    rule_label = rule_based_comfort_class(*features)
    model = _train_model_if_needed()

    if model is None:
        return {
            "slug": rule_label,
            "label": _LABELS_UA[rule_label],
            "confidence": None,
            "source": "rules",
            "samples": _MODEL_CACHE["samples"],
        }

    predicted = model.predict([features])[0]
    confidence = None
    if hasattr(model, "predict_proba"):
        probabilities = model.predict_proba([features])[0]
        confidence = round(float(max(probabilities)) * 100)

    return {
        "slug": predicted,
        "label": _LABELS_UA.get(predicted, predicted),
        "confidence": confidence,
        "source": "ml",
        "samples": _MODEL_CACHE["samples"],
    }


def enrich_weather_with_comfort(weather: dict) -> dict:
    if not weather or "error" in weather:
        return weather
    enriched = dict(weather)
    enriched["comfort_ml"] = predict_comfort(weather)
    return enriched
