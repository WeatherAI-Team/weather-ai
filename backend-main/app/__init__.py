from flask import Flask
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os
from dotenv import load_dotenv


jwt = JWTManager()

# .env 파일 로드
load_dotenv()

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret-key")
    # DB 주소 설정
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    jwt.init_app(app)
    
    CORS(
    app,
    resources={r"/api/*": {"origins": "http://localhost:3000"}},
    supports_credentials=True,
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


    # 블루프린트 등록
    from .api.member_api import member_bp
    app.register_blueprint(member_bp, url_prefix='/api/member')

    # cctv 블루프린트
    from .api.cctv_api import cctv_bp
    app.register_blueprint(cctv_bp, url_prefix='/api')

    # 카카오 네이버 블루프린트
    from .api.auth.kakao_auth_api import kakao_auth_bp
    from .api.auth.naver_auth import naver_auth_bp

    app.register_blueprint(kakao_auth_bp)
    app.register_blueprint(naver_auth_bp)

    # 테이블 자동 생성 (이게 있어야 실행 시 테이블이 만들어짐!)
    with app.app_context():
        db.create_all()

    return app