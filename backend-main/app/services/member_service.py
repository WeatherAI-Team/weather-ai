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
    
    # 사용자 목록을 가져오는 서비스 함수
    # api 파일에서 요청을 받으면 이 함수가 실행돼.
    def get_member_list(self, page=1, per_page=10, keyword=None, role=None, active=None):
        # repository에게 실제 DB 조회를 부탁해.
        # 쉽게 말하면 "DB에서 회원 목록 좀 가져와줘"라고 시키는 부분이야.
        members_page = self.member_repo.find_all(
            page=page,
            per_page=per_page,
            keyword=keyword,
            role=role,
            active=active
        )

        # 조회한 회원 목록을 JSON으로 보내기 좋은 형태로 정리해.
        return {
            "success" : True,    # 요청 성공
            "data" : {
                # members_page.items에는 실제 회원 데이터들이 들어있어.
                # 한 명 한 명을 _member_to_dict 함수로 보기 좋게 바꿔.
                "members" : [
                    self._member_to_dict(member)
                    for member in members_page.items
                ],


                # pagination은 페이지 정보야.
                # 프론트에서 "다음 페이지", "이전 페이지" 버튼 만들 때 필요해.
                "pagination": {
                    "page": members_page.page,              # 현재 페이지 번호
                    "per_page": members_page.per_page,      # 한 페이지에 몇 명인지  
                    "total": members_page.total,            # 전체 회원 수
                    "pages":members_page.pages,             # 전체 페이지 수
                    "has_next": members_page.has_next,      # 다음 페이지가 있는지
                    "has_prev": members_page.has_prev       # 이전 페이지가 있는지
                }
            }
        }
      
    # 회원 객체를 JSON으로 바꾸는 함수
    # DB에서 가져온 Member는 그대로 응답하기 어렵기 때문에 dict로 바꿔주는 거야.
    def _member_to_dict(self,member):
        return{
            "id": member.id,
            "login_id": member.login_id,
            "email": member.email,
            "nickname": member.nickname,
            "profile_img_url": member.profile_img_url,
            "role": member.role,
            "active": member.active,
            "provider": member.provider,                # local, google, kakao 등 로그인 방식

            # 날짜는 JSON으로 바로 보내기 어려워서 문자열로 바꿔줘.
            "created_at":member.created_at.isoformat() if member.created_at else None,
            "updated_at": member.updated_at.isoformat() if member.updated_at else None,
            "last_login_at": member.last_login_at.isoformat() if member.last_login_at else None
        }