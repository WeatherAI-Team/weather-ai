from werkzeug.security import generate_password_hash
from ..repositories.member_repo import MemberRepository
from ..models.member import Member

class MemberService:
    def __init__(self):
        self.member_repo = MemberRepository()

    def register_member(self, data):
        # 1. 이미 존재하는 아이디인지 확인
        if self.member_repo.find_by_login_id(data['login_id']):
            return {"success": False, "message": "이미 존재하는 아이디입니다."}

        # 2. 비밀번호 암호화 및 객체 생성
        hashed_pw = generate_password_hash(data['password'])
        new_member = Member(
            login_id=data['login_id'],
            password=hashed_pw,
            email=data['email'],
            nickname=data['nickname'],
            role='user'
        )
        
        # 3. DB 저장
        self.member_repo.save(new_member)
        return {"success": True, "message": f"{new_member.nickname}님 가입 성공!"}


    def get_member_info(self, member_id):
        # Repository에서 member_id로 조회
        member = self.member_repo.find_by_id(member_id)
        
        if not member:
            return {"success": False, "message": "존재하지 않는 회원입니다."}
        
        # password 제외하고 필요한 정보만 반환
        return {
            "success": True,
            "data": {
                "id": member.id,
                "login_id": member.login_id,
                "email": member.email,
                "nickname": member.nickname,
                "role": member.role,
                "provider": member.provider,
                "created_at": member.created_at.isoformat()
            }
        }