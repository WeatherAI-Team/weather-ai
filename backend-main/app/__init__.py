from flask import Flask
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_socketio import SocketIO

import os
from dotenv import load_dotenv
from .extensions import mail
load_dotenv()

jwt = JWTManager()
db = SQLAlchemy()
socketio = SocketIO(
    cors_allowed_origins="*",
    async_mode="threading"
)

def create_app():
    
    app = Flask(__name__)
    app.json.ensure_ascii = False
    app.config["JSON_AS_ASCII"] = False
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret-key")
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")  # 추가
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"   # 추가
    app.config["SESSION_COOKIE_SECURE"] = False      # 추가 (localhost라서 False)
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret-key")
    app.config["ITS_API_KEY"] = os.getenv("ITS_API_KEY")


    # 메일 설정
    app.config["MAIL_SERVER"] = os.getenv("MAIL_SERVER")
    app.config["MAIL_PORT"] = int(os.getenv("MAIL_PORT", 587))
    app.config["MAIL_USE_TLS"] = os.getenv("MAIL_USE_TLS", "True") == "True"
    app.config["MAIL_USE_SSL"] = os.getenv("MAIL_USE_SSL", "False") == "True"
    app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
    app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
    app.config["MAIL_DEFAULT_SENDER"] = os.getenv("MAIL_DEFAULT_SENDER")
    

    # 메일 확장 초기화
    mail.init_app(app)

    # 데이터베이스 확장 초기화
    db.init_app(app)

    jwt.init_app(app)


    # CORS: 프론트 주소만 허용
    CORS(
        app,
        resources={r"/api/*": {"origins": [
            "http://localhost:3000",
            "http://172.25.181.79:3000"
        ]}},
        supports_credentials=True,
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
    )

    # SocketIO (dev에서 가져옴)
    socketio.init_app(
        app, cors_allowed_origins="*",
        async_mode="threading"
    )

    # Blueprint 등록
    from .api.member_api import member_bp
    app.register_blueprint(member_bp)

    from .api.cctv_api import cctv_bp
    app.register_blueprint(cctv_bp, url_prefix='/api')
    
    from .api.weather_alert_api import weather_alert_bp

    from .api.auth.kakao_auth_api import kakao_auth_bp
    from .api.auth.naver_auth_api import naver_auth_bp
    from .api.auth.google_auth_api import google_auth_bp
    from .api.detection_api import detection_bp
    from .api.alert_api import alert_bp
    from .api.map_api import map_bp
    from .api.dashboard_api import dashboard_bp
    from .api.chatbot_api import chatbot_bp
    from .api.board_api import board_bp

    app.register_blueprint(kakao_auth_bp)
    app.register_blueprint(naver_auth_bp)
    app.register_blueprint(google_auth_bp)
    app.register_blueprint(detection_bp)
    app.register_blueprint(alert_bp)
    app.register_blueprint(map_bp)   
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(chatbot_bp)
    app.register_blueprint(weather_alert_bp)
    app.register_blueprint(board_bp)

    # 관리자 라우트 (dev에서 가져옴)
    from .api.admin_api import admin_bp
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    # 관리자 사용자 조회 API
    from .api.admin_member_api import admin_member_bp
    app.register_blueprint(admin_member_bp, url_prefix="/api/admin/members")
    # 알림 이력 API (notifications 테이블)
    from .api.notification_api import notification_bp
    app.register_blueprint(notification_bp)

    from . import socket_events

    with app.app_context():
        from .models.member import Member, EventLog
        from .models.detection_event import DetectionEvent
        from .models.board import Board, BoardComment
        from .models.notification import Notification

        db.create_all()

    return app