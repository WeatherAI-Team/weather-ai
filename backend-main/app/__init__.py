from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    CORS(app)

    # DB 주소 설정
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    # 블루프린트 등록
    from .api.member_api import member_bp
    app.register_blueprint(member_bp, url_prefix='/api/member')

    # 테이블 자동 생성 (이게 있어야 실행 시 테이블이 만들어져!)
    with app.app_context():
        db.create_all()

    return app