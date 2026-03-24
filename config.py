import os
from dotenv import load_dotenv

# Завантажуємо змінні оточення з файлу .env
load_dotenv()

class Config:
    # URL для підключення до БД (PostgreSQL)
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    
    # Секретний ключ для сесій Flask
    SECRET_KEY = os.getenv('SECRET_KEY')
    
    # Ключ для OpenWeather API
    OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY')
    
    # Вимкнення непотрібної опції SQLAlchemy для економії ресурсів
    SQLALCHEMY_TRACK_MODIFICATIONS = False
