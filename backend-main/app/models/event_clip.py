from datetime import datetime, timezone
from app import db

def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)

class EventClip(db.Model):
    __tablename__ = 'event_clips'

    id         = db.Column(db.BigInteger, primary_key=True)
    event_id   = db.Column(db.BigInteger, nullable=False)
    clip_url   = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now)