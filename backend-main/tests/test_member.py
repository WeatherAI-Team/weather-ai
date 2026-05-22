import pytest
from uuid import uuid4
from app import create_app, db
from app.models.member import Member

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_register_member(client):
    # 회원가입 API 테스트
    response = client.post('/api/member/register', json={
        "login_id": "pytest_user",
        "password": "password123",
        "email": "pytest_user@test.com",
        "nickname": "파이테스트",
        "real_name": "파이테스트"
    })
    data = response.get_json()
    print("회원가입 응답:", data)
    assert response.status_code == 201
    assert data["success"] is True

def test_get_my_profile(client):
    login_response = client.post("/api/member/login", json={
        "login_id": "test",
        "password": "2345"
    })

    login_data = login_response.get_json()
    access_token = login_data["access_token"]

    response = client.get(
        "/api/member/me",
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    data = response.get_json()
    print("내 프로필 조회 응답:", data)

    assert response.status_code == 200
    assert data["success"] is True

def test_login_member(client):
    # 이미 DB에 만들어 둔 테스트 회원 기준
    response = client.post("/api/member/login", json={
        "login_id": "test",
        "password": "2345"
    })

    data = response.get_json()
    print("로그인 응답:", data)

    assert response.status_code == 200
    assert data["success"] is True
    assert "access_token" in data
    assert "data" in data


def test_find_login_id(client):
    response = client.post("/api/member/find-id", json={
        "email": "test@email.com"
    })

    data = response.get_json()
    print("아이디 찾기 응답:", data)

    assert response.status_code == 200
    assert data["success"] is True
    assert data["login_id"] == "test"

def test_update_my_profile(client):
    login_response = client.post("/api/member/login", json={
        "login_id": "test",
        "password": "2345"
    })

    login_data = login_response.get_json()
    access_token = login_data["access_token"]

    response = client.put(
        "/api/member/me",
        headers={
            "Authorization": f"Bearer {access_token}"
        },
        json={
            "email": "test@email.com",
            "nickname": "수정된테스트",
            "real_name": "테스트",
            "profile_img_url": None
        }
    )

    data = response.get_json()
    print("회원정보 수정 응답:", data)

    assert response.status_code == 200
    assert data["success"] is True
    assert data["data"]["nickname"] == "수정된테스트"

def test_withdraw_my_account(client):
    suffix = uuid4().hex[:8]
    login_id = f"withdraw_{suffix}"
    password = "password123"
    email = f"{login_id}@test.com"

    register_response = client.post("/api/member/register", json={
        "login_id": login_id,
        "password": password,
        "email": email,
        "nickname": "탈퇴테스트",
        "real_name": "탈퇴테스트"
    })
    register_data = register_response.get_json()
    print("탈퇴 테스트 회원가입 응답:", register_data)

    assert register_response.status_code == 201
    assert register_data["success"] is True

    login_response = client.post("/api/member/login", json={
        "login_id": login_id,
        "password": password
    })
    login_data = login_response.get_json()
    print("탈퇴 테스트 로그인 응답:", login_data)

    assert login_response.status_code == 200
    assert login_data["success"] is True
    access_token = login_data["access_token"]

    response = client.patch(
        "/api/member/me/withdraw",
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )
    data = response.get_json()
    print("회원탈퇴 응답:", data)

    assert response.status_code == 200
    assert data["success"] is True
    assert data["message"] == "회원 탈퇴가 완료되었습니다."

    second_response = client.patch(
        "/api/member/me/withdraw",
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )
    second_data = second_response.get_json()
    print("회원탈퇴 재요청 응답:", second_data)

    assert second_response.status_code == 400
    assert second_data["success"] is False
    assert second_data["message"] == "이미 탈퇴 처리된 회원입니다."

    relogin_response = client.post("/api/member/login", json={
        "login_id": login_id,
        "password": password
    })
    relogin_data = relogin_response.get_json()
    print("탈퇴 후 로그인 응답:", relogin_data)

    assert relogin_response.status_code == 401
    assert relogin_data["success"] is False
    assert relogin_data["message"] == "비활성화된 계정입니다."

def test_find_login_id_social_account(client):
    suffix = uuid4().hex[:8]
    email = f"social_{suffix}@test.com"

    with client.application.app_context():
        social_member = Member(
            login_id=f"kakao_{suffix}",
            password=None,
            email=email,
            nickname="카카오테스트",
            real_name="카카오테스트",
            profile_img_url=None,
            role="user",
            active=True,
            provider="kakao",
            social_id=f"kakao_social_{suffix}",
            deleted_at=None,
        )

        db.session.add(social_member)
        db.session.commit()

    try:
        response = client.post("/api/member/find-id", json={
            "email": email
        })

        data = response.get_json()
        print("소셜 아이디 찾기 응답:", data)

        assert response.status_code == 200
        assert data["success"] is True
        assert data["account_type"] == "social"
        assert data["provider"] == "kakao"
        assert "login_id" not in data

    finally:
        with client.application.app_context():
            member = Member.query.filter_by(email=email).first()
            if member:
                db.session.delete(member)
                db.session.commit()

def test_kakao_login_without_email_does_not_create_fake_email(client, monkeypatch):
    
    class FakeTokenResponse:
        status_code = 200

        def json(self):
            return {
                "access_token": "fake_kakao_access_token"
            }

    class FakeUserResponse:
        status_code = 200

        def json(self):
            return {
                "id": 4896760811,
                "kakao_account": {
                    "profile": {
                        "nickname": "카카오테스트"
                    }
                    # email 없음
                }
            }

    def fake_post(*args, **kwargs):
        return FakeTokenResponse()

    def fake_get(*args, **kwargs):
        return FakeUserResponse()

    monkeypatch.setattr(
        "app.api.auth.kakao_auth_api.requests.post",
        fake_post
    )
    monkeypatch.setattr(
        "app.api.auth.kakao_auth_api.requests.get",
        fake_get
    )

    response = client.get("/api/auth/kakao/callback?code=fake_code")

    print("카카오 이메일 없음 응답 status:", response.status_code)
    print("redirect location:", response.headers.get("Location"))

    assert response.status_code == 302
    assert "error=kakao_email_missing" in response.headers.get("Location")

    with client.application.app_context():
        fake_email_member = Member.query.filter_by(
            email="kakao_4896760811@kakao.local"
        ).first()

        assert fake_email_member is None