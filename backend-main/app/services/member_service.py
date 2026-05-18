from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from ..repositories.member_repo import MemberRepository
from .auth_utils import create_access_token
from ..models.member import Member

class MemberService:
    def __init__(self):
        self.member_repo = MemberRepository()

    # 일반 회원가입
    def register_member(self, data):
        login_id = data.get("login_id")
        password = data.get("password")
        email = data.get("email")
        nickname = data.get("nickname")

        if not login_id or not password or not email or not nickname:
            return {"success": False, "message": "아이디, 비밀번호, 이메일, 닉네임은 필수입니다."}

        if self.member_repo.find_by_login_id(login_id):
            return {"success": False, "message": "이미 존재하는 아이디입니다."}

        if self.member_repo.find_by_email(email):
            return {"success": False, "message": "이미 사용 중인 이메일입니다."}

        hashed_pw = generate_password_hash(password)
        new_member = Member(
            login_id=login_id,
            password=hashed_pw,
            email=email,
            nickname=nickname,
            profile_img_url=None,
            role="user",
            active=True,
            provider="local",
            social_id=None,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            last_login_at=None,
            deleted_at=None,
        )
        self.member_repo.save(new_member)
        return {
            "success": True,
            "message": f"{new_member.nickname}님 가입 성공!",
            "data": self.to_public_dict(new_member)
        }

    # 일반 로그인
    def login_member(self, data):
        login_id = data.get("login_id")
        password = data.get("password")

        if not login_id or not password:
            return {"success": False, "message": "아이디와 비밀번호를 입력해주세요."}

        member = self.member_repo.find_by_login_id(login_id)
        if not member:
            return {"success": False, "message": "아이디 또는 비밀번호가 올바르지 않습니다."}
        if member.deleted_at is not None:
            return {"success": False, "message": "탈퇴한 회원입니다."}
        if member.active is False:
            return {"success": False, "message": "비활성화된 계정입니다."}
        if not member.password:
            return {"success": False, "message": "소셜 로그인 계정입니다."}
        if not check_password_hash(member.password, password):
            return {"success": False, "message": "아이디 또는 비밀번호가 올바르지 않습니다."}

        self.member_repo.update_last_login(member)
        access_token = create_access_token({"sub": str(member.id)})
        return {
            "success": True,
            "message": "로그인 성공",
            "access_token": access_token,
            "token_type": "bearer",
            "data": self.to_public_dict(member)
        }

    # 소셜 로그인 (dev에서 가져옴)
    def social_login_or_register(self, data):
        member = self.member_repo.find_by_email(data['email'])
        if not member:
            member = Member(
                login_id=f"{data['provider']}_{data['social_id'][:10]}",
                password="SOCIAL_AUTH_USER",
                email=data['email'],
                nickname=data['nickname'],
                role='user',
                provider=data['provider']
            )
            self.member_repo.save(member)
            message = f"{member.nickname}님, 첫 소셜 가입을 환영합니다!"
        else:
            message = f"{member.nickname}님, 로그인되었습니다."

        access_token = create_access_token({"sub": str(member.id)})
        return {
            "success": True,
            "message": message,
            "access_token": access_token,
            "token_type": "bearer",
            "data": {"id": member.id, "nickname": member.nickname, "email": member.email}
        }

    # 회원 정보 조회
    def get_member_info(self, member_id):
        member = self.member_repo.find_by_id(member_id)
        if not member or member.deleted_at is not None:
            return {"success": False, "message": "존재하지 않는 회원입니다."}
        return {"success": True, "data": self.to_public_dict(member)}

    def to_public_dict(self, member):
        return {
            "id": member.id,
            "login_id": member.login_id,
            "email": member.email,
            "nickname": member.nickname,
            "profile_img_url": member.profile_img_url,
            "role": str(member.role),
            "active": member.active,
            "provider": member.provider,
            "social_id": member.social_id,
            "created_at": member.created_at.isoformat() if member.created_at else None,
            "updated_at": member.updated_at.isoformat() if member.updated_at else None,
            "last_login_at": member.last_login_at.isoformat() if member.last_login_at else None,
        }
    
    def find_login_id(self, data):
        email = data.get("email")

        if not email:
            return {
                "success": False,
                "message": "이메일을 입력해주세요."
            }

        member = self.member_repo.find_by_email(email)

        if not member or member.deleted_at is not None:
            return {
                "success": False,
                "message": "해당 이메일로 가입된 회원이 없습니다."
            }

        return {
            "success": True,
            "message": "아이디를 찾았습니다.",
            "login_id": member.login_id
        
        }
    
    
        