import json
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import plotly.utils

from models import SavedCity
import services.openweather as weather_api


def _normalize_forecast_days(days):
    if days is None:
        return 5
    return max(1, min(int(days), 5))


def build_forecast_dataframe(raw_data, days=5):
    if not raw_data:
        return None

    rows = []
    for item in raw_data:
        dt = datetime.fromtimestamp(item["dt"])
        rows.append(
            {
                "date": dt,
                "date_str": dt.strftime("%Y-%m-%d"),
                "hour_str": dt.strftime("%d.%m %H:%M"),
                "temp": item["main"]["temp"],
                "feels_like": item["main"]["feels_like"],
                "humidity": item["main"]["humidity"],
                "pressure": item["main"]["pressure"],
                "wind": item["wind"]["speed"],
                "clouds": item.get("clouds", {}).get("all", 0),
            }
        )

    if not rows:
        return None

    df = pd.DataFrame(rows)
    allowed_dates = df["date_str"].drop_duplicates().tolist()[: _normalize_forecast_days(days)]
    filtered = df[df["date_str"].isin(allowed_dates)].copy()
    return filtered if not filtered.empty else None


def get_forecast_dataframe(city_id, days=5):
    city = SavedCity.query.get(city_id)
    if city is None:
        return None

    raw_data = weather_api.get_forecast_raw(city.city_name)
    return build_forecast_dataframe(raw_data, days)


def get_forecast_dataframe_by_name(city_name, days=5, raw_data=None):
    if raw_data is None:
        raw_data = weather_api.get_forecast_raw(city_name)
    return build_forecast_dataframe(raw_data, days)


def build_temp_hourly_chart(df):
    if df is None or df.empty:
        return None

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["hour_str"].tolist(),
            y=df["temp"].round(1).tolist(),
            mode="lines+markers",
            name="Температура",
            line=dict(color="#2563EB", width=2),
        )
    )
    fig.update_layout(
        title="Як змінюватиметься температура",
        xaxis_title="День і час",
        yaxis_title="Температура (°C)",
        xaxis=dict(type="category", tickangle=-45),
        template="plotly_white",
        margin=dict(l=20, r=20, t=40, b=80),
    )
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)


def build_humidity_hourly_chart(df):
    if df is None or df.empty:
        return None

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["hour_str"].tolist(),
            y=df["humidity"].tolist(),
            mode="lines+markers",
            name="Вологість",
            line=dict(color="#0EA5E9", width=2),
        )
    )
    fig.update_layout(
        title="Як змінюватиметься вологість",
        xaxis_title="День і час",
        yaxis_title="Вологість (%)",
        xaxis=dict(type="category", tickangle=-45),
        template="plotly_white",
        margin=dict(l=20, r=20, t=40, b=80),
    )
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)


def build_pressure_hourly_chart(df):
    if df is None or df.empty:
        return None

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["hour_str"].tolist(),
            y=df["pressure"].tolist(),
            mode="lines+markers",
            name="Тиск",
            line=dict(color="#7C3AED", width=2),
        )
    )
    fig.update_layout(
        title="Як змінюватиметься тиск",
        xaxis_title="День і час",
        yaxis_title="Тиск (гПа)",
        xaxis=dict(type="category", tickangle=-45),
        template="plotly_white",
        margin=dict(l=20, r=20, t=40, b=80),
    )
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)


def build_forecast_minmax_chart(df):
    if df is None or df.empty:
        return None

    daily = (
        df.groupby("date_str")
        .agg(temp_min=("temp", "min"), temp_max=("temp", "max"))
        .reset_index()
    )
    if daily.empty:
        return None

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=daily["date_str"].tolist(),
            y=daily["temp_max"].round(1).tolist(),
            mode="lines+markers",
            name="Найтепліше",
            line=dict(color="#DC2626", width=2),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=daily["date_str"].tolist(),
            y=daily["temp_min"].round(1).tolist(),
            mode="lines+markers",
            name="Найхолодніше",
            line=dict(color="#2563EB", width=2),
            fill="tonexty",
            fillcolor="rgba(37, 99, 235, 0.12)",
        )
    )
    fig.update_layout(
        title="Межі температури по днях",
        xaxis_title="День",
        yaxis_title="Температура (°C)",
        template="plotly_white",
        margin=dict(l=20, r=20, t=40, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)


def build_feels_like_chart(df):
    if df is None or df.empty:
        return None

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["hour_str"].tolist(),
            y=df["temp"].round(1).tolist(),
            mode="lines+markers",
            name="Фактична температура",
            line=dict(color="#2563EB", width=2),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df["hour_str"].tolist(),
            y=df["feels_like"].round(1).tolist(),
            mode="lines+markers",
            name="Відчувається як",
            line=dict(color="#F59E0B", width=2),
        )
    )
    fig.update_layout(
        title="Реальна температура і як вона відчувається",
        xaxis_title="День і час",
        yaxis_title="Температура (°C)",
        xaxis=dict(type="category", tickangle=-45),
        template="plotly_white",
        margin=dict(l=20, r=20, t=40, b=80),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)


def build_radar_chart(df):
    if df is None or df.empty:
        return None

    first = df.iloc[0]
    categories = ["Температура", "Вологість", "Вітер", "Тиск", "Хмарність"]

    n_temp = max(0, min(100, (first["temp"] + 30) / 0.8))
    n_hum = first["humidity"]
    n_wind = max(0, min(100, first["wind"] * 3.333))
    n_press = max(0, min(100, first["pressure"] - 950))
    n_clouds = first["clouds"]

    values = [n_temp, n_hum, n_wind, n_press, n_clouds, n_temp]
    labels = [
        f'{round(first["temp"], 1)} °C',
        f'{int(first["humidity"])} %',
        f'{round(first["wind"], 1)} м/с',
        f'{int(first["pressure"])} гПа',
        f'{int(first["clouds"])} %',
        f'{round(first["temp"], 1)} °C',
    ]
    categories_closed = categories + [categories[0]]

    fig = go.Figure()
    fig.add_trace(
        go.Scatterpolar(
            r=values,
            theta=categories_closed,
            fill="toself",
            name="Показники",
            text=labels,
            hoverinfo="text",
            marker=dict(color="#8B5CF6"),
        )
    )
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=False, range=[0, 100])),
        title="Погода найближчим часом",
        template="plotly_white",
        margin=dict(l=40, r=40, t=40, b=40),
    )
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)


def build_compare_temp_chart(city1, city2, days=5, raw_data1=None, raw_data2=None):
    df1 = get_forecast_dataframe_by_name(city1, days, raw_data=raw_data1)
    df2 = get_forecast_dataframe_by_name(city2, days, raw_data=raw_data2)
    if df1 is None or df2 is None or df1.empty or df2.empty:
        return None

    daily1 = df1.groupby("date_str").agg({"temp": "max"}).reset_index()
    daily2 = df2.groupby("date_str").agg({"temp": "max"}).reset_index()

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=daily1["date_str"].tolist(),
            y=daily1["temp"].round(1).tolist(),
            mode="lines+markers",
            name=city1,
            line=dict(color="#2563EB", width=2),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=daily2["date_str"].tolist(),
            y=daily2["temp"].round(1).tolist(),
            mode="lines+markers",
            name=city2,
            line=dict(color="#059669", width=2),
        )
    )
    fig.update_layout(
        title="Порівняння найвищої температури по днях",
        xaxis_title="День",
        yaxis_title="Температура (°C)",
        template="plotly_white",
        margin=dict(l=20, r=20, t=40, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)


def build_compare_current_bar(w1, w2):
    if not w1 or not w2:
        return None

    fig = go.Figure(
        data=[
            go.Bar(
                name=w1["city"],
                x=["Температура (°C)", "Вологість (%)", "Вітер (м/с)"],
                y=[w1["temperature"], w1["humidity"], w1["wind_speed"]],
                marker_color="#2563EB",
            ),
            go.Bar(
                name=w2["city"],
                x=["Температура (°C)", "Вологість (%)", "Вітер (м/с)"],
                y=[w2["temperature"], w2["humidity"], w2["wind_speed"]],
                marker_color="#059669",
            ),
        ]
    )
    fig.update_layout(
        barmode="group",
        title="Поточна погода в містах",
        template="plotly_white",
        margin=dict(l=20, r=20, t=40, b=40),
    )
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)


def build_compare_humidity_chart(city1, city2, days=5, raw_data1=None, raw_data2=None):
    df1 = get_forecast_dataframe_by_name(city1, days, raw_data=raw_data1)
    df2 = get_forecast_dataframe_by_name(city2, days, raw_data=raw_data2)
    if df1 is None or df2 is None or df1.empty or df2.empty:
        return None

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df1["hour_str"].tolist(),
            y=df1["humidity"].tolist(),
            mode="lines+markers",
            name=city1,
            line=dict(color="#3B82F6", width=2),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df2["hour_str"].tolist(),
            y=df2["humidity"].tolist(),
            mode="lines+markers",
            name=city2,
            line=dict(color="#10B981", width=2),
        )
    )
    fig.update_layout(
        title="Порівняння вологості за прогнозом",
        xaxis_title="День і час",
        yaxis_title="Вологість (%)",
        xaxis=dict(type="category", tickangle=-45),
        template="plotly_white",
        margin=dict(l=20, r=20, t=40, b=80),
    )
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)


def build_compare_radar(w1, w2):
    if not w1 or not w2:
        return None

    categories = ["Температура", "Вологість", "Вітер", "Тиск"]
    categories_closed = categories + [categories[0]]

    def norm(weather):
        n_temp = max(0, min(100, (weather["temperature"] + 30) / 0.8))
        n_hum = weather["humidity"]
        n_wind = max(0, min(100, weather["wind_speed"] * 3.333))
        n_press = max(0, min(100, weather["pressure"] - 950))
        return [n_temp, n_hum, n_wind, n_press, n_temp]

    def labels(weather):
        return [
            f'{weather["temperature"]} °C',
            f'{weather["humidity"]} %',
            f'{weather["wind_speed"]} м/с',
            f'{weather["pressure"]} гПа',
            f'{weather["temperature"]} °C',
        ]

    fig = go.Figure()
    fig.add_trace(
        go.Scatterpolar(
            r=norm(w1),
            theta=categories_closed,
            text=labels(w1),
            hoverinfo="text",
            fill="toself",
            name=w1["city"],
            marker=dict(color="#2563EB"),
        )
    )
    fig.add_trace(
        go.Scatterpolar(
            r=norm(w2),
            theta=categories_closed,
            text=labels(w2),
            hoverinfo="text",
            fill="toself",
            name=w2["city"],
            marker=dict(color="#059669"),
        )
    )
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=False, range=[0, 100])),
        title="Порівняння поточної погоди",
        template="plotly_white",
        margin=dict(l=40, r=40, t=40, b=40),
    )
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
