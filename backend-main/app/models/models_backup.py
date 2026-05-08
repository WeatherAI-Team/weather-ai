from . import db
from datetime import datetime

# 사용자 정보 테이블
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    role = db.Column(db.String(20), default='user')  # 'admin' 또는 'user'

# 과거 알림 내역 저장 테이블
class EventLog(db.Model):
    __tablename__ = 'event_logs'
    id = db.Column(db.Integer, primary_key=True)
    event_type = db.Column(db.String(50))  # 예: 폭우, 강풍, 사고 등
    risk_level = db.Column(db.Integer)      # 위험도 (1~10)
    message = db.Column(db.Text)            # 알림 내용
    created_at = db.Column(db.DateTime, default=datetime.utcnow)