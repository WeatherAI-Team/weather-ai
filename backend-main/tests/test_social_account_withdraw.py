import pytest
from uuid import uuid4

from app import create_app, db
from app.models.member import Member
from app.models.member_social_account import MemberSocialAccount


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_withdraw_deactivates_social_accounts(client):
    suffix = uuid4().hex[:8]
    login_id = f"social_withdraw_{suffix}"
    password = "password123"
    email = f"{login_id}@test.com"

    register_response = client.post("/api/member/register", json={
        "login_id": login_id,
        "password": password,
        "email": email,
        "nickname": "소셜탈퇴테스트",
        "real_name": "소셜탈퇴테스트"
    })

    register_data = register_response.get_json()
    print("회원가입 응답:", register_data)

    assert register_response.status_code == 201
    assert register_data["success"] is True

    member_id = register_data["data"]["id"]

    with client.application.app_context():
        social_account = MemberSocialAccount(
            member_id=member_id,
            provider="kakao",
            social_id=f"kakao_{suffix}",
            email=email,
            deleted_at=None
        )

        db.session.add(social_account)
        db.session.commit()

    login_response = client.post("/api/member/login", json={
        "login_id": login_id,
        "password": password
    })

    login_data = login_response.get_json()
    print("로그인 응답:", login_data)

    assert login_response.status_code == 200
    assert login_data["success"] is True

    access_token = login_data["access_token"]

    withdraw_response = client.patch(
        "/api/member/me/withdraw",
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    withdraw_data = withdraw_response.get_json()
    print("회원탈퇴 응답:", withdraw_data)

    assert withdraw_response.status_code == 200
    assert withdraw_data["success"] is True

    with client.application.app_context():
        member = Member.query.filter_by(id=member_id).first()
        social = MemberSocialAccount.query.filter_by(member_id=member_id).first()

        print("member.active:", member.active)
        print("social.deleted_at:", social.deleted_at)

        assert member.active is False
        assert social.deleted_at is not None