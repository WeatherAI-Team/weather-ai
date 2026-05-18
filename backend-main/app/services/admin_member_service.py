from ..repositories.member_repo import MemberRepository


class AdminMemberService:
    def __init__(self):
        # 회원 DB 조회 기능을 사용하기 위해 MemberRepository를 준비해.
        self.member_repo = MemberRepository()

    # 관리자용 사용자 목록 조회
    # page: 몇 번째 페이지인지
    # per_page: 한 페이지에 몇 명 보여줄지
    # keyword: 검색어
    # role: user/admin/manager 같은 권한 필터
    # active: 활성 계정만 볼지 여부
    def get_member_list(self, page=1, per_page=10, keyword=None, role=None, active=None):
        # Repository에게 DB에서 회원 목록을 가져오라고 요청해.
        members_page = self.member_repo.find_all(
            page=page,
            per_page=per_page,
            keyword=keyword,
            role=role,
            active=active
        )

        # 프론트엔드가 보기 쉬운 JSON 형태로 정리해.
        return {
            "success": True,
            "data": {
                "members": [
                    self._member_to_dict(member)
                    for member in members_page.items
                ],
                "pagination": {
                    "page": members_page.page,
                    "per_page": members_page.per_page,
                    "total": members_page.total,
                    "pages": members_page.pages,
                    "has_next": members_page.has_next,
                    "has_prev": members_page.has_prev
                }
            }
        }

    # 관리자용 사용자 상세 조회
    def get_member_detail(self, member_id):
        # id로 회원 한 명을 찾음
        member = self.member_repo.find_by_id(member_id)

        # 회원이 없으면 실패 응답
        if not member:
            return {
                "success": False,
                "message": "존재하지 않는 회원입니다."
            }

        # 회원이 있으면 회원 정보를 반환
        return {
            "success": True,
            "data": self._member_to_dict(member)
        }

    # Member 객체를 JSON으로 바꿔주는 함수
    # 비밀번호는 절대 보내면 안 되기 때문에 password는 제외해.
    def _member_to_dict(self, member):
        return {
            "id": member.id,
            "login_id": member.login_id,
            "email": member.email,
            "nickname": member.nickname,
            "profile_img_url": member.profile_img_url,
            "role": member.role,
            "active": member.active,
            "provider": member.provider,
            "created_at": member.created_at.isoformat() if member.created_at else None,
            "updated_at": member.updated_at.isoformat() if member.updated_at else None,
            "last_login_at": member.last_login_at.isoformat() if member.last_login_at else None
        }
