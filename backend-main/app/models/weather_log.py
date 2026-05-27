from datetime import datetime
from app import db


class WeatherLog(db.Model):
    __tablename__ = "weather_logs"

    id = db.Column(db.BigInteger, primary_key=True)

    cctv_source_id = db.Column(db.BigInteger, nullable=True)

    weather_type = db.Column(db.String, nullable=False)

    temperature = db.Column(db.Numeric, nullable=True)
    precipitation = db.Column(db.Numeric, nullable=True)
    snowfall = db.Column(db.Numeric, nullable=True)
    visibility = db.Column(db.Numeric, nullable=True)

    weather_risk_score = db.Column(db.Integer, nullable=False, default=0)

    source = db.Column(db.String, nullable=False, default="KMA")

    raw_data = db.Column(db.JSON, nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)