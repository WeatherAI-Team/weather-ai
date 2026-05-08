from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_socketio import SocketIO
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

db = SQLAlchemy()
socketio = SocketIO() # 내가 쓴거 

def create_app():
    app = Flask(__name__)
    CORS(app)

    # DB 주소 설정
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    # 추가: 웹소켓 초기화 (cors_allowed_origins는 프론트엔드 주소에 맞춰 설정)
    socketio.init_app(app, cors_allowed_origins="*")

    # 블루프린트 등록
    from .api.member_api import member_bp
    app.register_blueprint(member_bp, url_prefix='/api/member')

    # cctv 블루프린트
    from .api.cctv_api import cctv_bp
    app.register_blueprint(cctv_bp, url_prefix='/api')

    # 관리자 라우트 임포트 (내가 쓴거) 
    from .admin_routes import admin_bp 
    app.register_blueprint(admin_bp, url_prefix='/api/admin')

    # 테이블 자동 생성 (이게 있어야 실행 시 테이블이 만들어져!)
    from .models.member import Member, EventLog
    with app.app_context():
        db.create_all()

    return app
