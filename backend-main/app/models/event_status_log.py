# app/models/event_status_log.py

from datetime import datetime
from app import db


class EventStatusLog(db.Model):
    __tablename__ = "event_status_logs"

    id = db.Column(db.BigInteger, primary_key=True)
    event_id = db.Column(db.BigInteger, nullable=False)
    changed_by = db.Column(db.Integer, nullable=True)

    previous_status = db.Column(db.String, nullable=True)
    new_status = db.Column(db.String, nullable=False)
    memo = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)