    # 4. 관리자용 사용자 목록 조회
    # 관리자용 사용자 목록 조회 함수
    # 쉽게 말하면 DB에서 회원들을 여러 명 가져오는 기능이야.

class MemberRepository:
    def find_all(self, page=1, per_page=10, keyword=None, role=None, active=None):
        # Member 테이블에서 삭제되지 않은 회원만 찾기 시작해.
        # deleted_at이 None이라는 뜻은 아직 삭제되지 않았다는 뜻이야.
        query = Member.query.filter(Member.deleted_at.is_(None))

        # keyword가 있으면 아이디, 이메일, 닉네임 중에서 검색해.
        # 예를 들어 keyword가 "정화"면 닉네임에 정화가 들어간 회원을 찾을 수 있어.
        if keyword:
            search = f"%{keyword}%"
            query = query.filter(
                or_(
                    Member.login_id.ilike(search),     # login_id에 keyword가 들어가는지 확인
                    Member.email.ilike(search),        # email에 keyword가 들어가는지 확인   
                    Member.nickname.ilike(search)      # nickname에 keyword가 들어가는지 확인
                )
            )

        # role 값이 있으면 해당 권한의 회원만 찾음.
        # 예: role=user 이면 일반 사용자만 조회
        # 예: role=admin 이면 관리자만 조회
        if role:
            query = query.filter(Member.role == role)

        # active 값이 있으면 활성/비활성 회원만 찾음.
        # active=True면 사용 중인 회원
        # active=False면 정지되었거나 비활성화된 회원
        if active is not None:
            query = query.filter(Member.active == active)

        # created_at 기준으로 최신 가입자부터 정렬해.
        # paginate는 페이지를 나눠서 가져오는 기능이야.
        # 예: 1페이지에 10명씩 보여주기
        return query.order_by(Member.created_at.desc()).paginate(
            page=page,               # 몇 번째 페이지인지
            per_page=per_page,       # 한 페이지에 몇 명 보여줄지   
            error_out=False          # 페이지가 없어도 에러 대신 빈 결과를 주게 함   
        )
    # 나중에 관리자 페이지에서 사용자 목록을 검색