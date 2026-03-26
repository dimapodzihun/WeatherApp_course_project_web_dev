import requests
from flask import current_app
from datetime import datetime

BASE_URL = "https://api.openweathermap.org/data/2.5"
GEO_URL = "http://api.openweathermap.org/geo/1.0"


_COUNTRY_NAMES_UK = {
    "UA": "Україна", "US": "США", "GB": "Велика Британія", "DE": "Німеччина",
    "FR": "Франція", "PL": "Польща", "IT": "Італія", "ES": "Іспанія",
    "JP": "Японія", "CN": "Китай", "IN": "Індія", "BR": "Бразилія",
    "CA": "Канада", "AU": "Австралія", "RU": "Росія", "TR": "Туреччина",
    "NL": "Нідерланди", "BE": "Бельгія", "SE": "Швеція", "NO": "Норвегія",
    "FI": "Фінляндія", "DK": "Данія", "AT": "Австрія", "CH": "Швейцарія",
    "CZ": "Чехія", "SK": "Словаччина", "HU": "Угорщина", "RO": "Румунія",
    "BG": "Болгарія", "HR": "Хорватія", "RS": "Сербія", "GR": "Греція",
    "PT": "Португалія", "MX": "Мексика", "AR": "Аргентина", "CL": "Чилі",
    "CO": "Колумбія", "PE": "Перу", "EG": "Єгипет", "ZA": "ПАР",
    "NG": "Нігерія", "KE": "Кенія", "SA": "Саудівська Аравія",
    "AE": "ОАЕ", "IL": "Ізраїль", "IR": "Іран", "PK": "Пакистан",
    "BD": "Бангладеш", "TH": "Таїланд", "VN": "В'єтнам", "ID": "Індонезія",
    "MY": "Малайзія", "PH": "Філіппіни", "KR": "Південна Корея",
    "LT": "Литва", "LV": "Латвія", "EE": "Естонія", "MD": "Молдова",
    "BY": "Білорусь", "KZ": "Казахстан", "GE": "Грузія", "AM": "Вірменія",
    "AZ": "Азербайджан", "UZ": "Узбекистан",
}


def get_country_name(country_code):
    return _COUNTRY_NAMES_UK.get(country_code, country_code)


def get_city_suggestions(query):
    """Повертає список підказок міст через Geocoding API."""
    api_key = current_app.config['OPENWEATHER_API_KEY']
    url = f"{GEO_URL}/direct?q={query}&limit=5&appid={api_key}"
    try:
        response = requests.get(url, timeout=4)
        response.raise_for_status()
        results = []
        seen = set()
        for item in response.json():
            city_uk = item.get('local_names', {}).get('uk') or item.get('name', '')
            name_en = item.get('name', '')
            code = item.get('country', '')
            country_name = get_country_name(code)
            key = (name_en.lower(), code.lower())
            if key in seen:
                continue
            seen.add(key)
            results.append({
                'display': f"{city_uk}, {country_name}",
                'name_en': name_en,
                'country': code,
            })
        return results
    except Exception:
        return []

def _get_weekday_name(weekday_int):
    days = ['Пн', 'Вв', 'Ср', 'Чт', 'Пт', 'Сб', 'Нд']
    return days[weekday_int]

def get_current_weather(city_name):
    api_key = current_app.config['OPENWEATHER_API_KEY']
    url = f"{BASE_URL}/weather?q={city_name}&appid={api_key}&units=metric&lang=ua"
    
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        return {
            'city': data['name'],
            'country': data['sys']['country'],
            'country_name': get_country_name(data['sys']['country']),
            'temperature': round(data['main']['temp']),
            'feels_like': round(data['main']['feels_like']),
            'humidity': data['main']['humidity'],
            'pressure': data['main']['pressure'],
            'wind_speed': round(data['wind']['speed'], 1),
            'description': data['weather'][0]['description'].capitalize(),
            'icon': data['weather'][0]['icon'],
            'updated_at': datetime.now().strftime('%H:%M')
        }
    except requests.exceptions.HTTPError:
        if response.status_code == 404:
            return {'error': 'Місто не знайдено'}
        return {'error': 'Помилка API OpenWeather'}
    except Exception:
        return {'error': 'Помилка з\'єднання'}

def get_forecast_5days(city_name):
    raw_forecast = get_forecast_raw(city_name)
    if not raw_forecast:
        return None
    return build_forecast_5days_from_raw(raw_forecast)


def build_forecast_5days_from_raw(raw_data):
    if not raw_data:
        return None

    daily_forecasts = {}

    for item in raw_data:
        dt = datetime.fromtimestamp(item['dt'])
        date_str = dt.strftime('%Y-%m-%d')

        if date_str not in daily_forecasts:
            daily_forecasts[date_str] = {
                'temps': [],
                'description': item['weather'][0]['description'].capitalize(),
                'icon': item['weather'][0]['icon'],
                'date': dt.strftime('%d.%m'),
                'weekday': _get_weekday_name(dt.weekday())
            }

        daily_forecasts[date_str]['temps'].append(item['main']['temp'])

        if dt.hour in (12, 13, 14, 15):
            daily_forecasts[date_str]['description'] = item['weather'][0]['description'].capitalize()
            daily_forecasts[date_str]['icon'] = item['weather'][0]['icon']

    result = []
    for date_key, d in list(daily_forecasts.items())[:5]:
        result.append({
            'date': d['date'],
            'date_iso': date_key,
            'weekday': d['weekday'],
            'temp_max': round(max(d['temps'])),
            'temp_min': round(min(d['temps'])),
            'description': d['description'],
            'icon': d['icon']
        })

    return result

def get_forecast_raw(city_name):
    api_key = current_app.config['OPENWEATHER_API_KEY']
    url = f"{BASE_URL}/forecast?q={city_name}&appid={api_key}&units=metric&lang=ua"
    
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        return data['list']
    except Exception:
        return None


def build_hourly_today_from_raw(raw_data):
    if not raw_data:
        return None

    result = []
    today = datetime.now().date()

    for item in raw_data:
        dt = datetime.fromtimestamp(item['dt'])
        if dt.date() == today:
            result.append({
                'time': dt.strftime('%H:%M'),
                'temperature': round(item['main']['temp']),
                'icon': item['weather'][0]['icon'],
                'description': item['weather'][0]['description']
            })
        elif dt.date() > today:
            if len(result) < 8:
                result.append({
                    'time': dt.strftime('%H:%M'),
                    'temperature': round(item['main']['temp']),
                    'icon': item['weather'][0]['icon'],
                    'description': item['weather'][0]['description']
                })
            else:
                break

    return result


def build_hourly_for_date_from_raw(raw_data, date_str):
    if not raw_data:
        return []

    result = []
    for item in raw_data:
        dt = datetime.fromtimestamp(item['dt'])
        if dt.strftime('%Y-%m-%d') == date_str:
            result.append({
                'time': dt.strftime('%H:%M'),
                'temperature': round(item['main']['temp']),
                'icon': item['weather'][0]['icon'],
                'description': item['weather'][0]['description']
            })
    return result

def get_hourly_today(city_name):
    raw_forecast = get_forecast_raw(city_name)
    if not raw_forecast:
        return None
    return build_hourly_today_from_raw(raw_forecast)

def get_hourly_for_date(city_name, date_str):
    """Повертає погодинний прогноз для конкретної дати (формат YYYY-MM-DD)."""
    raw_forecast = get_forecast_raw(city_name)
    if not raw_forecast:
        return []
    return build_hourly_for_date_from_raw(raw_forecast, date_str)


def get_two_cities(city1, city2):
    import concurrent.futures
    app = current_app._get_current_object()

    def fetch_with_context(city):
        with app.app_context():
            return get_current_weather(city)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future1 = executor.submit(fetch_with_context, city1)
        future2 = executor.submit(fetch_with_context, city2)

        return (future1.result(), future2.result())


def get_two_forecasts_raw(city1, city2):
    import concurrent.futures
    app = current_app._get_current_object()

    def fetch_with_context(city):
        with app.app_context():
            return get_forecast_raw(city)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future1 = executor.submit(fetch_with_context, city1)
        future2 = executor.submit(fetch_with_context, city2)

        return (future1.result(), future2.result())
