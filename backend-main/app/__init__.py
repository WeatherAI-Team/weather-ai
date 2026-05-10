from flask import Flask
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_socketio import SocketIO
import os
from dotenv import load_dotenv

load_dotenv()

jwt = JWTManager()
db = SQLAlchemy()
socketio = SocketIO()

def create_app():
    app = Flask(__name__)

    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret-key")
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    jwt.init_app(app)

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
    from .routes.member_route import member_bp
    app.register_blueprint(member_bp)

    from .api.cctv_api import cctv_bp
    app.register_blueprint(cctv_bp, url_prefix='/api')

    from .api.auth.kakao_auth_api import kakao_auth_bp
    from .api.auth.naver_auth import naver_auth_bp
    app.register_blueprint(kakao_auth_bp)
    app.register_blueprint(naver_auth_bp)

    # 관리자 라우트 (dev에서 가져옴)
    from .api.admin_routes import admin_bp
    app.register_blueprint(admin_bp, url_prefix='/api/admin')

    from . import socket_events

    with app.app_context():
        from .models.member import Member, EventLog
        db.create_all()

    return app