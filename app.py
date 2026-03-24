from flask import Flask
from config import Config
from models import db

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Ініціалізація бази даних (без db.create_all(), адже таблиці існують)
    db.init_app(app)

    # Реєстрація Blueprint-ів
    from routes.auth import auth_bp
    app.register_blueprint(auth_bp)
    
    from routes.weather import weather_bp
    app.register_blueprint(weather_bp)
    
    from routes.cities import cities_bp
    app.register_blueprint(cities_bp)
    
    from routes.forecast import forecast_bp
    app.register_blueprint(forecast_bp)
    
    from routes.charts import charts_bp
    app.register_blueprint(charts_bp)
    
    from routes.compare import compare_bp
    app.register_blueprint(compare_bp)

    from routes.analytics import analytics_bp
    app.register_blueprint(analytics_bp)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
