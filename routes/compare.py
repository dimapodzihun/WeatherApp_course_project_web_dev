from flask import Blueprint, render_template, request
from utils import login_required
import services.openweather as weather_api
import services.charts_builder as charts_builder
import services.weather_insights as weather_insights
import services.weather_ml as weather_ml

compare_bp = Blueprint('compare', __name__, url_prefix='/compare')

@compare_bp.route('/', methods=['GET'])
@login_required
def index():
    return render_template('compare/index.html')

@compare_bp.route('/result', methods=['GET'])
@login_required
def result():
    city1 = request.args.get('city1', '').strip()
    city2 = request.args.get('city2', '').strip()
    
    if not city1 or not city2:
        return "<div class='text-[#DC2626] p-4 text-center'>Будь ласка, введіть обидва міста.</div>"
        
    w1, w2 = weather_api.get_two_cities(city1, city2)
    
    if not w1 or not w2:
        return "<div class='text-[#DC2626] bg-red-50 p-4 rounded-xl text-center'>Не вдалося отримати дані. Перевірте назву міста або спробуйте пізніше.</div>"
    
    if 'error' in w1 or 'error' in w2:
        err = w1.get('error', w2.get('error', 'Невідома помилка'))
        return f"<div class='text-[#DC2626] bg-red-50 p-4 rounded-xl text-center'>{err}</div>"
        
    w1 = weather_ml.enrich_weather_with_comfort(w1)
    w2 = weather_ml.enrich_weather_with_comfort(w2)

    f1 = weather_api.get_forecast_5days(city1) or []
    f2 = weather_api.get_forecast_5days(city2) or []
    
    comp_temp = charts_builder.build_compare_temp_chart(city1, city2)
    comp_hum = charts_builder.build_compare_humidity_chart(city1, city2)
    comp_current = charts_builder.build_compare_current_bar(w1, w2)
    compare_summary = weather_insights.build_compare_summary(w1, w2, f1, f2)
    alerts1 = weather_insights.build_weather_alerts(w1, weather_api.get_forecast_raw(city1) or [])
    alerts2 = weather_insights.build_weather_alerts(w2, weather_api.get_forecast_raw(city2) or [])
    
    return render_template(
        'partials/compare_result.html',
        w1=w1,
        w2=w2,
        f1=f1,
        f2=f2,
        comp_temp=comp_temp,
        comp_hum=comp_hum,
        comp_current=comp_current,
        compare_summary=compare_summary,
        alerts1=alerts1,
        alerts2=alerts2,
    )
