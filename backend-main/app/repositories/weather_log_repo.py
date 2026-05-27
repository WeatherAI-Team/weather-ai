# app/repositories/weather_log_repo.py

from app import db
from app.models.weather_log import WeatherLog


class WeatherLogRepository:
    def create_weather_log(self, data: dict):
        weather_log = WeatherLog(**data)
        db.session.add(weather_log)
        db.session.flush()

        return weather_log