# app/models/detection_object.py

from datetime import datetime
from app import db


class DetectionObject(db.Model):
    __tablename__ = "detection_objects"

    id = db.Column(db.BigInteger, primary_key=True)
    event_id = db.Column(db.BigInteger, nullable=False)
    vehicle_type = db.Column(db.String, nullable=False)
    confidence = db.Column(db.Numeric, nullable=False)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    model_name = db.Column(db.String, nullable=True)
    is_risk_vehicle = db.Column(db.Boolean, nullable=False, default=False)