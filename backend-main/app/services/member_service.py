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