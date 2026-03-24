import json

import pandas as pd
import plotly.graph_objects as go
import plotly.utils

from models import SavedCity, WeatherHistory


def build_history_dataframe(city_id):
    rows = (
        WeatherHistory.query.filter_by(city_id=city_id)
        .order_by(WeatherHistory.recorded_at.asc())
        .all()
    )
    if not rows:
        return None

    data = []
    for row in rows:
        data.append(
            {
                "recorded_at": row.recorded_at,
                "time_label": row.recorded_at.strftime("%d.%m %H:%M"),
                "temperature": float(row.temperature),
                "humidity": float(row.humidity),
                "pressure": float(row.pressure),
                "wind_speed": float(row.wind_speed),
            }
        )

    df = pd.DataFrame(data)
    return df if not df.empty else None


def get_history_dataframe_for_city(city_id):
    city = SavedCity.query.get(city_id)
    if city is None:
        return None
    return build_history_dataframe(city.id)


def build_history_summary(df):
    if df is None or df.empty:
        return {
            "samples": 0,
            "latest_temp": None,
            "temp_change": None,
            "humidity_change": None,
            "pressure_change": None,
            "trend_label": "Недостатньо даних",
            "period_start": "-",
            "period_end": "-",
        }

    latest = df.iloc[-1]
    first = df.iloc[0]
    temp_change = round(float(latest["temperature"] - first["temperature"]), 1)
    humidity_change = round(float(latest["humidity"] - first["humidity"]), 1)
    pressure_change = round(float(latest["pressure"] - first["pressure"]), 1)

    if temp_change >= 2:
        trend_label = "Теплішання"
    elif temp_change <= -2:
        trend_label = "Похолодання"
    else:
        trend_label = "Відносна стабільність"

    return {
        "samples": int(len(df)),
        "latest_temp": round(float(latest["temperature"]), 1),
        "temp_change": temp_change,
        "humidity_change": humidity_change,
        "pressure_change": pressure_change,
        "trend_label": trend_label,
        "period_start": df.iloc[0]["recorded_at"].strftime("%d.%m %H:%M"),
        "period_end": latest["recorded_at"].strftime("%d.%m %H:%M"),
    }


def build_climate_summary(df):
    if df is None or df.empty:
        return {
            "temp_anomaly": None,
            "humidity_anomaly": None,
            "wind_shift": None,
            "climate_signal": "Недостатньо даних",
        }

    baseline = df.head(min(5, len(df)))
    recent = df.tail(min(5, len(df)))
    temp_anomaly = round(float(recent["temperature"].mean() - baseline["temperature"].mean()), 1)
    humidity_anomaly = round(float(recent["humidity"].mean() - baseline["humidity"].mean()), 1)
    wind_shift = round(float(recent["wind_speed"].mean() - baseline["wind_speed"].mean()), 1)

    if temp_anomaly >= 1.5:
        climate_signal = "Позитивна температурна аномалія"
    elif temp_anomaly <= -1.5:
        climate_signal = "Негативна температурна аномалія"
    else:
        climate_signal = "Помітних аномалій не виявлено"

    return {
        "temp_anomaly": temp_anomaly,
        "humidity_anomaly": humidity_anomaly,
        "wind_shift": wind_shift,
        "climate_signal": climate_signal,
    }


def build_temperature_history_chart(df):
    if df is None or df.empty:
        return None

    rolling = df["temperature"].rolling(window=min(4, len(df)), min_periods=1).mean()
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["time_label"].tolist(),
            y=df["temperature"].round(1).tolist(),
            mode="lines+markers",
            name="Температура",
            line=dict(color="#2563EB", width=2),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df["time_label"].tolist(),
            y=rolling.round(1).tolist(),
            mode="lines",
            name="Ковзне середнє",
            line=dict(color="#F59E0B", width=2, dash="dash"),
        )
    )
    fig.update_layout(
        title="Історичний тренд температури",
        xaxis_title="Час спостереження",
        yaxis_title="Температура (°C)",
        xaxis=dict(type="category", tickangle=-45),
        template="plotly_white",
        margin=dict(l=20, r=20, t=40, b=80),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)


def build_history_metrics_chart(df):
    if df is None or df.empty:
        return None

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["time_label"].tolist(),
            y=df["humidity"].round(1).tolist(),
            mode="lines+markers",
            name="Вологість",
            line=dict(color="#0891B2", width=2),
            yaxis="y1",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df["time_label"].tolist(),
            y=df["pressure"].round(1).tolist(),
            mode="lines+markers",
            name="Тиск",
            line=dict(color="#7C3AED", width=2),
            yaxis="y2",
        )
    )
    fig.update_layout(
        title="Історичні зміни вологості та тиску",
        xaxis=dict(type="category", tickangle=-45, title="Час спостереження"),
        yaxis=dict(title="Вологість (%)"),
        yaxis2=dict(title="Тиск (гПа)", overlaying="y", side="right"),
        template="plotly_white",
        margin=dict(l=20, r=20, t=40, b=80),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)


def build_climate_change_chart(df):
    if df is None or df.empty:
        return None

    baseline_temp = df["temperature"].expanding().mean()
    anomaly_temp = (df["temperature"] - baseline_temp).round(2)
    rolling_humidity = df["humidity"].rolling(window=min(4, len(df)), min_periods=1).mean()

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=df["time_label"].tolist(),
            y=anomaly_temp.tolist(),
            name="Температурна аномалія",
            marker_color=["#DC2626" if value >= 0 else "#2563EB" for value in anomaly_temp.tolist()],
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df["time_label"].tolist(),
            y=rolling_humidity.round(1).tolist(),
            mode="lines+markers",
            name="Вологість, ковзне середнє",
            line=dict(color="#059669", width=2),
            yaxis="y2",
        )
    )
    fig.update_layout(
        title="Візуалізація кліматичних змін та аномалій",
        xaxis=dict(type="category", tickangle=-45, title="Час спостереження"),
        yaxis=dict(title="Температурна аномалія (°C)"),
        yaxis2=dict(title="Вологість (%)", overlaying="y", side="right"),
        template="plotly_white",
        margin=dict(l=20, r=20, t=40, b=80),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
