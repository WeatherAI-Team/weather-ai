import pytest
from app import create_app

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
        "nickname": "파이테스트"
    })
    data = response.get_json()
    print("회원가입 응답:", data)
    assert response.status_code == 200
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
    # 이미 DB에 존재하는 이메일 기준
    response = client.post("/api/member/find-id", json={
        "email": "test@email.com"
    })

    data = response.get_json()
    print("아이디 찾기 응답:", data)

    assert response.status_code == 200
    assert data["success"] is True
    assert data["login_id"] == "test"


