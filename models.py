from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    """Модель користувача (відповідає таблиці users у БД)"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Зв'язок із збереженими містами (з каскадним видаленням)
    saved_cities = db.relationship('SavedCity', backref='user', lazy=True, cascade='all, delete-orphan')

class SavedCity(db.Model):
    """Модель збереженого міста (відповідає таблиці saved_cities у БД)"""
    __tablename__ = 'saved_cities'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    city_name = db.Column(db.String(100), nullable=False)
    country_code = db.Column(db.String(2), nullable=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Зв'язок з історією погоди (з каскадним видаленням)
    weather_history = db.relationship('WeatherHistory', backref='city', lazy=True, cascade='all, delete-orphan')

class WeatherHistory(db.Model):
    """Модель історії погоди (відповідає таблиці weather_history у БД)"""
    __tablename__ = 'weather_history'

    id = db.Column(db.Integer, primary_key=True)
    city_id = db.Column(db.Integer, db.ForeignKey('saved_cities.id', ondelete='CASCADE'), nullable=False)
    temperature = db.Column(db.Float, nullable=False)
    humidity = db.Column(db.Integer, nullable=False)
    pressure = db.Column(db.Integer, nullable=False)
    wind_speed = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(255), nullable=False)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)


# ── Автоматичне скидання sequence після кожного видалення ──────────────────

from sqlalchemy import event, text

def _reset_sequence(mapper, connection, target):
    """Скидає sequence таблиці до MAX(id)+1 після видалення рядка."""
    table = target.__tablename__
    seq   = f"{table}_id_seq"
    connection.execute(
        text(f"SELECT setval('{seq}', COALESCE((SELECT MAX(id) FROM {table}), 0) + 1, false)")
    )

for _model in (User, SavedCity, WeatherHistory):
    event.listen(_model, 'after_delete', _reset_sequence)
