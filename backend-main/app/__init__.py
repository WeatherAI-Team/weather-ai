from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os
from dotenv import load_dotenv

load_dotenv()

# [1] db 객체 생성 (초기화는 함수 안에서)
db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    CORS(app)

    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # [2] db를 앱에 연결
    db.init_app(app)

    # [3] 블루프린트 등록 (반드시 여기서 import)
    from .routes.member_route import member_bp
    app.register_blueprint(member_bp)

    # [4] 테이블 자동 생성 및 모델 로드 (순환 참조 방지의 핵심 위치)
    # cctv 블루프린트
    from .api.cctv_api import cctv_bp
    app.register_blueprint(cctv_bp, url_prefix='/api')

    # 테이블 자동 생성 (이게 있어야 실행 시 테이블이 만들어져!)
    with app.app_context():
        # 파일명이 member.py라면 아래처럼 작성
        from .models.member import Member 
        db.create_all()
    return app