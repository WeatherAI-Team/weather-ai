from flask import Flask

from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_socketio import SocketIO
import os
from dotenv import load_dotenv

load_dotenv()


db = SQLAlchemy()
socketio = SocketIO()

def create_app():
    app = Flask(__name__)

    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret-key")
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")  # 추가
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"   # 추가
    app.config["SESSION_COOKIE_SECURE"] = False      # 추가 (localhost라서 False)
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret-key")

    db.init_app(app)


    # CORS: 프론트 주소만 허용
    CORS(
        app,
        resources={r"/api/*": {"origins": "http://localhost:3000"}},
        supports_credentials=True,
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
    )

    # SocketIO (dev에서 가져옴)
    socketio.init_app(app, cors_allowed_origins="*")

    # Blueprint 등록
    from .api.member_api import member_bp
    app.register_blueprint(member_bp)

    from .api.cctv_api import cctv_bp
    app.register_blueprint(cctv_bp, url_prefix='/api')

    from .api.auth.kakao_auth_api import kakao_auth_bp
    from .api.auth.naver_auth_api import naver_auth_bp
    from .api.auth.google_auth_api import google_auth_bp
    from .api.detection_api import detection_bp
    from .api.alert_api import alert_bp
    from .api.map_api import map_bp
    from .api.dashboard_api import dashboard_bp
    from .api.chatbot_api import chatbot_bp

    app.register_blueprint(kakao_auth_bp)
    app.register_blueprint(naver_auth_bp)
    app.register_blueprint(google_auth_bp)
    app.register_blueprint(detection_bp)
    app.register_blueprint(alert_bp)
    app.register_blueprint(map_bp)   
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(chatbot_bp)
    
    # 관리자 라우트 (dev에서 가져옴)
    from .api.admin_api import admin_bp
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    # 관리자 사용자 조회 API
    # f-006 사용자 목록/상세 조회
    from .api.admin_member_api import admin_member_bp
    app.register_blueprint(admin_member_bp, url_prefix="/api/admin/members")

    from . import socket_events

    with app.app_context():
        from .models.member import Member, EventLog
        # 탐지 이벤트 모델을 가져와.
        # Flask가 detection_events 테이블 구조를 알 수 있게 해.
        from .models.detection_event import DetectionEvent
        
        db.create_all()

    return app