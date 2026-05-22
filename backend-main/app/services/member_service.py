from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from ..repositories.member_repo import MemberRepository
from .auth_utils import create_access_token
from ..models.member import Member
import os
import secrets
from datetime import datetime, timedelta
from .mail_service import send_password_reset_email

class MemberService:
    def __init__(self):
        self.member_repo = MemberRepository()

    # 일반 회원가입
    def register_member(self, data):
        login_id = data.get("login_id")
        password = data.get("password")
        real_name = data.get("real_name")
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
            real_name=real_name,
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
        if member.provider not in (None, "local"):
            return {
                "success": False,
                "message": "소셜 로그인 계정입니다. 해당 소셜 로그인으로 접속해주세요."
        }
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
        if member.active is False:
            return {"success": False, "message": "비활성화된 계정입니다."}

        return {"success": True, "data": self.to_public_dict(member)}

    def to_public_dict(self, member):
        return {
            "id": member.id,
            "login_id": member.login_id,
            "email": member.email,
            "nickname": member.nickname,
            "real_name": member.real_name,
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

        if not member or member.deleted_at is not None or member.active is False:
            return {
                "success": False,
                "message": "해당 이메일로 가입된 회원이 없습니다."
            }

        # 소셜 로그인 계정은 내부 login_id를 보여주지 않음
        if member.provider not in (None, "local"):
            provider_name_map = {
                "kakao": "카카오",
                "naver": "네이버",
                "google": "구글",
            }

            provider_name = provider_name_map.get(member.provider, member.provider)

            return {
                "success": True,
                "account_type": "social",
                "provider": member.provider,
                "message": f"해당 이메일은 {provider_name} 소셜 로그인으로 가입된 계정입니다. {provider_name} 로그인으로 접속해주세요."
            }

        return {
            "success": True,
            "account_type": "local",
            "message": "아이디를 찾았습니다.",
            "login_id": member.login_id
        }
    
     # 비밀번호 재설정 링크 요청
    def request_password_reset(self, data):
        email = data.get("email")

        if not email:
            return {
                "success": False,
                "message": "이메일을 입력해주세요."
            }

        member = self.member_repo.find_by_email(email)

        # 보안상 이메일 존재 여부를 직접 알려주지 않는 게 좋음
        generic_response = {
            "success": True,
            "message": "해당 이메일로 가입된 계정이 있다면 비밀번호 재설정 링크를 전송했습니다."
        }

        if not member or member.deleted_at is not None or member.active is False:
            return generic_response

        # 소셜 로그인 회원은 비밀번호 재설정 대상에서 제외
        if member.provider not in (None, "local"):
            return generic_response

        # URL에 넣어도 안전한 랜덤 토큰 생성
        token = secrets.token_urlsafe(32)

        # 15분 뒤 만료
        expires_at = datetime.now() + timedelta(minutes=15)

        self.member_repo.update_password_reset_token(
            member=member,
            token=token,
            expires_at=expires_at
        )

        # 나중에는 실제 이메일 발송으로 교체
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        reset_link = f"{frontend_url}/reset-password?token={token}"

        # 실제 이메일 발송
        email_sent = send_password_reset_email(
            recipient_email=member.email,
            nickname=member.nickname,
            reset_link=reset_link
        )

        if email_sent:
            print(f"[MAIL SUCCESS] 비밀번호 재설정 메일 발송 완료: {member.email}")
        else:
            print(f"[MAIL FAIL] 비밀번호 재설정 메일 발송 실패: {member.email}")
        
        return {
            "success": True,
            "message": "해당 이메일로 가입된 계정이 있다면 비밀번호 재설정 링크를 전송했습니다."
        }


    # 새 비밀번호로 변경
    def reset_password(self, token, new_password):  # token은 controller에서 URL파라미터로 분리

        # 비밀번호 유효성 검사 추후 변경 가능
        if not new_password or len(new_password) < 8:
            return {
                "success": False,
                "message": "비밀번호는 8자 이상이어야 합니다."
            }

        member = self.member_repo.find_by_password_reset_token(token)

        if not member or not member.password_reset_token_expires_at:
            return {
                "success": False,
                "message": "유효하지 않은 재설정 링크입니다."
            }

        # 소셜 로그인 유저 차단
        if member.provider in ("kakao", "google"):
            return {
                "success": False,
                "message": "소셜 로그인 계정은 비밀번호를 변경할 수 없습니다."
            }

        # 토큰 만료 확인
        if member.password_reset_token_expires_at < datetime.utcnow():
            return {
                "success": False,
                "message": "재설정 링크가 만료되었습니다."
            }

        hashed_password = generate_password_hash(new_password)

        self.member_repo.update_password_after_reset(
            member=member,
            hashed_password=hashed_password
        )

        return {
            "success": True,
            "message": "비밀번호가 성공적으로 변경되었습니다."
        }
    
    # 회원정보 수정
    def update_member_info(self, member_id, data):
        member = self.member_repo.find_by_id(member_id)

        if not member or member.deleted_at is not None:
            return {
                "success": False,
                "message": "존재하지 않는 회원입니다."
            }

        email = data.get("email", member.email)
        nickname = data.get("nickname", member.nickname)
        real_name = data.get("real_name", member.real_name)
        profile_img_url = data.get("profile_img_url", member.profile_img_url)

        if not email or not nickname:
            return {
                "success": False,
                "message": "이메일과 닉네임은 필수입니다."
            }

        # 이메일을 변경하려는 경우 중복 검사
        if email != member.email:
            same_email_member = self.member_repo.find_by_email(email)

            if same_email_member:
                return {
                    "success": False,
                    "message": "이미 사용 중인 이메일입니다."
                }

        updated_member = self.member_repo.update_member_info(
            member=member,
            email=email,
            nickname=nickname,
            real_name=real_name,
            profile_img_url=profile_img_url
        )

        return {
            "success": True,
            "message": "회원정보가 수정되었습니다.",
            "data": self.to_public_dict(updated_member)
        }
    
    # 로그인한 회원 비밀번호 변경
    def change_password(self, member_id, data):
        current_password = data.get("current_password")
        new_password = data.get("new_password")

        if not current_password or not new_password:
            return {
                "success": False,
                "message": "현재 비밀번호와 새 비밀번호를 입력해주세요."
            }

        if len(new_password) < 8:
            return {
                "success": False,
                "message": "새 비밀번호는 8자 이상이어야 합니다."
            }

        member = self.member_repo.find_by_id(member_id)

        if not member or member.deleted_at is not None:
            return {
                "success": False,
                "message": "존재하지 않는 회원입니다."
            }

        # 소셜 로그인 계정은 비밀번호 변경 불가
        if member.provider not in (None, "local"):
            return {
                "success": False,
                "message": "소셜 로그인 계정은 비밀번호를 변경할 수 없습니다."
            }

        if not member.password or not check_password_hash(member.password, current_password):
            return {
                "success": False,
                "message": "현재 비밀번호가 일치하지 않습니다."
            }

        hashed_password = generate_password_hash(new_password)

        self.member_repo.update_password(
            member=member,
            hashed_password=hashed_password
        )

        return {
            "success": True,
            "message": "비밀번호가 변경되었습니다."
        }

    # 회원 탈퇴 - active만 false 처리
    def withdraw_member(self, member_id):
        member = self.member_repo.find_by_id(member_id)

        if not member:
            return{
                "success": False,
                "message": "존재하지 않는 회원입니다."

            }
        if member.active is False:
            return{
                "success": False,
                "message": "이미 탈퇴 처리된 회원입니다."
            }
        self.member_repo.deactivate_member(member)

        return{
                "success": True,
                "message": "회원 탈퇴가 완료되었습니다."
            }
