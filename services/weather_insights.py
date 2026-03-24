from __future__ import annotations


def _safe_get(seq, index, default=None):
    try:
        return seq[index]
    except (IndexError, TypeError):
        return default


def build_personal_recommendations(current_weather, raw_forecast=None):
    if not current_weather or "error" in current_weather:
        return []

    recommendations = []
    temp = current_weather.get("temperature")
    wind = current_weather.get("wind_speed")
    humidity = current_weather.get("humidity")
    description = (current_weather.get("description") or "").lower()

    if temp is not None:
        if temp <= 0:
            recommendations.append("На вулиці морозно, варто вдягнути теплий верхній одяг, шапку та рукавички.")
        elif temp <= 10:
            recommendations.append("Погода прохолодна, краще взяти куртку або светр.")
        elif temp >= 28:
            recommendations.append("Очікується спека, варто мати воду та уникати тривалого перебування на сонці.")

    if wind is not None and wind >= 10:
        recommendations.append("Вітер досить сильний, легкий одяг і парасоля можуть бути незручними.")

    if humidity is not None and humidity >= 80:
        recommendations.append("Вологість висока, тому надворі може відчуватися сирість.")

    if any(word in description for word in ("дощ", "злива", "гроза", "сніг")):
        recommendations.append("Є ознаки опадів, тому варто взяти парасолю або водозахисний одяг.")

    upcoming = raw_forecast or []
    next_slots = upcoming[:4]
    if any("rain" in slot for slot in next_slots):
        recommendations.append("У найближчі години можливий дощ, краще не планувати тривалі прогулянки без парасолі.")
    if any("snow" in slot for slot in next_slots):
        recommendations.append("У найближчі години можливий сніг, дорога може бути слизькою.")

    if not recommendations:
        recommendations.append("Погодні умови загалом стабільні, спеціальних обмежень для активностей немає.")

    return recommendations[:4]


def build_weather_alerts(current_weather, raw_forecast=None):
    alerts = []
    if not current_weather or "error" in current_weather:
        return alerts

    raw_forecast = raw_forecast or []
    temp_now = current_weather.get("temperature")
    wind_now = current_weather.get("wind_speed", 0)
    desc_now = (current_weather.get("description") or "").lower()

    if wind_now >= 15:
        alerts.append("Сильний вітер зараз. Варто бути обережним на відкритій місцевості.")

    if any(word in desc_now for word in ("гроза", "злива")):
        alerts.append("Зараз спостерігаються небезпечні опади. За можливості залишайтеся в приміщенні.")

    next_slots = raw_forecast[:6]
    if next_slots:
        temps = [slot["main"]["temp"] for slot in next_slots if slot.get("main")]
        if temps and temp_now is not None and min(temps) <= temp_now - 5:
            alerts.append("У найближчі години прогнозується помітне зниження температури.")

        max_wind = max((slot.get("wind", {}).get("speed", 0) for slot in next_slots), default=0)
        if max_wind >= 12:
            alerts.append("У прогнозі є періоди сильного вітру в найближчі години.")

        if any(slot.get("rain") for slot in next_slots):
            alerts.append("У найближчі години можливі опади.")
        if any(slot.get("snow") for slot in next_slots):
            alerts.append("У найближчі години можливий сніг або ожеледиця.")

    return alerts[:4]


def build_compare_summary(w1, w2, forecast1=None, forecast2=None):
    if not w1 or not w2 or "error" in w1 or "error" in w2:
        return []

    summary = []

    warmer = w1 if w1["temperature"] >= w2["temperature"] else w2
    summary.append(f"Зараз тепліше у місті {warmer['city']}.")

    calmer = w1 if w1["wind_speed"] <= w2["wind_speed"] else w2
    summary.append(f"Менш вітряна погода зараз у місті {calmer['city']}.")

    drier = w1 if w1["humidity"] <= w2["humidity"] else w2
    summary.append(f"Сухіше повітря зараз у місті {drier['city']}.")

    f1_first = _safe_get(forecast1, 0)
    f2_first = _safe_get(forecast2, 0)
    if f1_first and f2_first:
        better_day = w1["city"] if f1_first["temp_max"] >= f2_first["temp_max"] else w2["city"]
        summary.append(f"За найближчим денним прогнозом тепліше буде у місті {better_day}.")

    score1 = _comfort_score(w1)
    score2 = _comfort_score(w2)
    if score1 != score2:
        better_city = w1["city"] if score1 > score2 else w2["city"]
        summary.append(f"За сукупністю умов комфортнішою для прогулянки виглядає погода у місті {better_city}.")

    return summary[:5]


def _comfort_score(weather):
    score = 100
    temp = weather.get("temperature", 20)
    wind = weather.get("wind_speed", 0)
    humidity = weather.get("humidity", 50)

    score -= abs(temp - 22) * 2
    score -= max(wind - 4, 0) * 3
    score -= max(humidity - 70, 0) * 0.5
    return round(score, 1)
