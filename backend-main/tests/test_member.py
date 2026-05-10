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
        "name": "파이테스트",
        "password": "password123"
    })
    
    assert response.status_code == 201
    assert response.json['success'] is True

def test_get_member_profile(client):
    # 회원 조회 API 테스트 (ID 1번이 있다고 가정)
    response = client.get('/api/member/1')
    
    # 200(성공) 또는 404(없음) 중 하나가 와야 함
    assert response.status_code in [200, 404]