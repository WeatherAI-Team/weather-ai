from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_socketio import SocketIO
import os
from dotenv import load_dotenv

load_dotenv()

# [1] db 객체 생성 (초기화는 함수 안에서)
db = SQLAlchemy()
socketio = SocketIO() # 내가 쓴거 

def create_app():
    app = Flask(__name__)
    CORS(app)

    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # [2] db를 앱에 연결
    db.init_app(app)
    # 추가: 웹소켓 초기화 (cors_allowed_origins는 프론트엔드 주소에 맞춰 설정)
    socketio.init_app(app, cors_allowed_origins="*")

    # [3] 블루프린트 등록 (반드시 여기서 import)
    from .routes.member_route import member_bp
    app.register_blueprint(member_bp)

    # [4] 테이블 자동 생성 및 모델 로드 (순환 참조 방지의 핵심 위치)
    # cctv 블루프린트
    from .api.cctv_api import cctv_bp
    app.register_blueprint(cctv_bp, url_prefix='/api')

    # 관리자 라우트 임포트 (내가 쓴거) 
    from .api.admin_routes import admin_bp
    app.register_blueprint(admin_bp, url_prefix='/api/admin')

    from .import socket_events 

    # 테이블 자동 생성 (이게 있어야 실행 시 테이블이 만들어져!)
    from .models.member import Member, EventLog
    with app.app_context():
        # 파일명이 member.py라면 아래처럼 작성
        from .models.member import Member 
        db.create_all()

    return app
