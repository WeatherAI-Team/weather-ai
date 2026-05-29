from datetime import datetime, timezone
from sqlalchemy import Enum
from app import db

def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)

class Member(db.Model):
    __tablename__ = 'members'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # 1. 기본 정보
    
    login_id = db.Column(db.String(50), unique=True, nullable=True) # 소셜 로그인 시 null일 수 있음
    password = db.Column(db.String(255), nullable=True)             # 소셜 로그인 시 null일 수 있음
    
    # 2. 프로필 정보
    email = db.Column(db.String(100), unique=True, nullable=False)
    real_name = db.Column(db.String(50), nullable=True)
    nickname = db.Column(db.String(50), nullable=False)
    profile_img_url = db.Column(db.Text, nullable=True)
    
    # 3. 권한 및 상태
    # Enum 설정 (admin, manager, user)
    role = db.Column(Enum('admin', 'manager', 'user', name='user_roles'), default='user')
    active = db.Column(db.Boolean, default=True)

    # 4. 알림 설정
    noti_email = db.Column(db.Boolean, default=True, nullable=False, server_default='1')
    noti_sms   = db.Column(db.Boolean, default=False, nullable=False, server_default='0')
    noti_app   = db.Column(db.Boolean, default=True, nullable=False, server_default='1')

    
    # 5. 시간 기록 (Audit)
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)
    last_login_at = db.Column(db.DateTime, nullable=True)
    deleted_at = db.Column(db.DateTime, nullable=True) # Soft Delete용

    # 비밀번호 재설정 
    password_reset_token = db.Column(db.String(255), nullable=True)
    password_reset_token_expires_at = db.Column(db.DateTime, nullable=True)
    password_changed_at = db.Column(db.DateTime, nullable=True)
    def __repr__(self):
        return f'<Member {self.nickname}>'
    
    def soft_delete(self):
        self.active = False
        self.deleted_at = utc_now()

    # 탈퇴한 회원인지 확인할 때 쓰는 메서드야.
    # deleted_at에 값이 있으면 탈퇴한 회원이라고 볼 수 있어.
    def is_deleted(self):
        return self.deleted_at is not None

# --- 여기서부터 새로 추가하는 코드 ---
class EventLog(db.Model):
    __tablename__ = 'event_logs'
    id = db.Column(db.Integer, primary_key=True)
    event_type = db.Column(db.String(50))  # 예: 폭우, 사고 등
    risk_level = db.Column(db.Integer)      # 위험도 (1~10)
    message = db.Column(db.Text)            # 알림 내용
    created_at = db.Column(db.DateTime, default=utc_now)

