from werkzeug.security import generate_password_hash
from ..repositories.member_repo import MemberRepository
from ..models.member import Member
from datetime import datetime
import os
from jose import jwt
from datetime import timedelta

# JWT 설정 (조장님과 상의해서 .env에 넣는 것을 권장합니다)
SECRET_KEY = os.getenv("SECRET_KEY", "your-fallback-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24시간

class MemberService:
    def __init__(self):
        self.member_repo = MemberRepository()

    # 1. 토큰 생성 내부 메서드
    def _create_access_token(self, member_id: int):
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode = {"sub": str(member_id), "exp": expire}
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    # 2. 일반 회원가입
    def register_member(self, data):
        if self.member_repo.find_by_login_id(data['login_id']):
            return {"success": False, "message": "이미 존재하는 아이디입니다."}

        hashed_pw = generate_password_hash(data['password'])
        new_member = Member(
            login_id=data['login_id'],
            password=hashed_pw,
            email=data['email'],
            nickname=data['nickname'],
            role='user',
            provider='local' # 일반 가입 구분
        )
        
        self.member_repo.save(new_member)
        return {"success": True, "message": f"{new_member.nickname}님 가입 성공!"}

    # 3. 구글/소셜 로그인 및 자동 가입
    def social_login_or_register(self, data):
        """
        data: {'email': '...', 'nickname': '...', 'provider': 'google', 'social_id': '...'}
        """
        # 이메일로 기존 유저 확인
        member = self.member_repo.find_by_email(data['email'])

        if not member:
            # 신규 소셜 유저 가입
            member = Member(
                login_id=f"{data['provider']}_{data['social_id'][:10]}",
                password="SOCIAL_AUTH_USER", # 비밀번호 로그인 방지용 더미값
                email=data['email'],
                nickname=data['nickname'],
                role='user',
                provider=data['provider']
            )
            self.member_repo.save(member)
            message = f"{member.nickname}님, 첫 소셜 가입을 환영합니다!"
        else:
            message = f"{member.nickname}님, 로그인되었습니다."

        # 우리 서비스 전용 JWT 토큰 발급
        access_token = self._create_access_token(member.id)

        return {
            "success": True,
            "message": message,
            "access_token": access_token, # 프론트에 전달할 토큰
            "token_type": "bearer",
            "data": {
                "id": member.id,
                "nickname": member.nickname,
                "email": member.email
            }
        }

    # 4. 회원 정보 조회
    def get_member_info(self, member_id):
        member = self.member_repo.find_by_id(member_id)
        
        if not member:
            return {"success": False, "message": "존재하지 않는 회원입니다."}
        
        return {
            "success": True,
            "data": {
                "id": member.id,
                "login_id": member.login_id,
                "email": member.email,
                "nickname": member.nickname,
                "role": member.role,
                "provider": member.provider,
                "created_at": member.created_at.isoformat() if member.created_at else None
            }
        }