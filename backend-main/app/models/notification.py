from datetime import datetime, timezone
from app import db


def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Notification(db.Model):
    __tablename__ = 'notifications'

    id          = db.Column(db.BigInteger, primary_key=True)
    target_type = db.Column(db.String(50),  nullable=True)   # 'ADMIN' | 'MEMBER'
    member_id   = db.Column(db.BigInteger,  nullable=True)   # members.id 참조
    event_id    = db.Column(db.BigInteger,  nullable=True)   # detection_events.id 참조
    title       = db.Column(db.String(500), nullable=True)
    content     = db.Column(db.Text,        nullable=True)
    risk_level  = db.Column(db.String(20),  nullable=True)   # 'HIGH' | 'MEDIUM' | 'LOW'
    status      = db.Column(db.String(20),  nullable=True, default='PENDING')  # 'PENDING'|'SENT'|'FAILED'|'READ'
    sent_at     = db.Column(db.DateTime,    nullable=True)
    read_at     = db.Column(db.DateTime,    nullable=True)
    created_at  = db.Column(db.DateTime,    default=utc_now)
