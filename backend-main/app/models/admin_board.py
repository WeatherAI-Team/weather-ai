from datetime import datetime, timezone
from app import db

def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)

class AdminBoard(db.Model):
    __tablename__ = 'admin_boards'

    id             = db.Column(db.BigInteger, primary_key=True)
    event_id       = db.Column(db.BigInteger, nullable=True)
    admin_id       = db.Column(db.Integer,    nullable=True)
    title          = db.Column(db.String(200), nullable=False)
    content        = db.Column(db.Text,        nullable=False)
    risk_score     = db.Column(db.Integer,     nullable=False, default=0)
    risk_level     = db.Column(db.String(20),  nullable=False, default='INTEREST')
    weather_type   = db.Column(db.String(20),  nullable=False, default='UNKNOWN')
    vehicle_type   = db.Column(db.String(20),  nullable=False, default='UNKNOWN')
    event_status   = db.Column(db.String(20),  nullable=False, default='UNCONFIRMED')
    pinned         = db.Column(db.Boolean,     nullable=False, default=False)
    active         = db.Column(db.Boolean,     nullable=False, default=True)
    created_by_llm = db.Column(db.Boolean,     nullable=False, default=True)
    created_at     = db.Column(db.DateTime,    default=utc_now)
    updated_at     = db.Column(db.DateTime,    default=utc_now, onupdate=utc_now)
    deleted_at     = db.Column(db.DateTime,    nullable=True)