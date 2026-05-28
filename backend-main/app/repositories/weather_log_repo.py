# app/repositories/weather_log_repo.py

from app import db
from app.models.weather_log import WeatherLog


class WeatherLogRepository:
    def create_weather_log(self, data: dict):
        weather_log = WeatherLog(**data)
        db.session.add(weather_log)
        db.session.commit()

        return weather_log

    def find_by_id(self, weather_log_id: int):
        return WeatherLog.query.filter(
            WeatherLog.id == weather_log_id
        ).first()

    def find_latest_by_cctv_source_id(self, cctv_source_id: int):
        return WeatherLog.query.filter(
            WeatherLog.cctv_source_id == cctv_source_id
        ).order_by(
            WeatherLog.created_at.desc()
        ).first()

    def find_latest(self):
        return WeatherLog.query.order_by(
            WeatherLog.created_at.desc()
        ).first()