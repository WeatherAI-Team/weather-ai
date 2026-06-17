from app import db
from datetime import datetime

class CctvSource(db.Model):
    __tablename__ = "cctv_sources"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    cctv_id = db.Column(db.String(100), nullable=True)
    cctv_name = db.Column(db.String(255), nullable=False)
    road_name = db.Column(db.String(255), nullable=True)
    location_name = db.Column(db.String(255), nullable=True)
    latitude = db.Column(db.Numeric(10, 7), nullable=False)
    longitude = db.Column(db.Numeric(10, 7), nullable=False)
    stream_url = db.Column(db.Text, nullable=True)
    provider = db.Column(db.String(50), nullable=False, default="ITS")
    active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
