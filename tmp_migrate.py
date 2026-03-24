import os
import sys

# Добавляем путь к weather_app
sys.path.insert(0, r"d:\університет\курсові\курсовий проект 2 курс (2 семестр)\web_dev\course_work_web_development\weather_app")

from app import create_app
from models import db
from sqlalchemy import text

app = create_app()
with app.app_context():
    try:
        db.session.execute(text("ALTER TABLE weather_history ADD COLUMN icon VARCHAR(10) DEFAULT '01d'"))
        db.session.execute(text("ALTER TABLE weather_history ADD COLUMN feels_like FLOAT DEFAULT 0.0"))
        db.session.commit()
        print("Columns 'icon' and 'feels_like' added successfully.")
    except Exception as e:
        print(f"Error adding columns (they might already exist): {e}")
        db.session.rollback()
