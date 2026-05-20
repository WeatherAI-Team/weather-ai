from flask_mail import Message
from ..extensions import mail



def send_password_reset_email(recipient_email, nickname, reset_link):
    """
    비밀번호 재설정 이메일 발송
    성공 시 True, 실패 시 False 반환
    """
    try:
        subject = "[Weather AI] 비밀번호 재설정 안내"

        text_body = f"""
안녕하세요, {nickname}님.

비밀번호 재설정 요청이 접수되었습니다.
아래 링크를 클릭하여 새 비밀번호를 설정해주세요.

{reset_link}

이 링크는 15분 후 만료됩니다.
본인이 요청하지 않았다면 이 메일은 무시하셔도 됩니다.

감사합니다.
Weather AI
""".strip()

        html_body = f"""
        <div style="font-family: Arial, sans-serif; line-height: 1.6;">
            <h2>[Weather AI] 비밀번호 재설정 안내</h2>
            <p>안녕하세요, <strong>{nickname}</strong>님.</p>
            <p>비밀번호 재설정 요청이 접수되었습니다.</p>
            <p>아래 버튼을 눌러 새 비밀번호를 설정해주세요.</p>

            <p style="margin: 24px 0;">
                <a href="{reset_link}"
                   style="
                       display: inline-block;
                       padding: 12px 20px;
                       background-color: #2563eb;
                       color: white;
                       text-decoration: none;
                       border-radius: 6px;
                       font-weight: bold;
                   ">
                    비밀번호 재설정하기
                </a>
            </p>

            <p>버튼이 동작하지 않으면 아래 링크를 직접 복사해 접속해주세요.</p>
            <p>{reset_link}</p>

            <hr style="margin: 24px 0;">
            <p style="color: #666;">
                이 링크는 15분 후 만료됩니다.<br>
                본인이 요청하지 않았다면 이 메일은 무시하셔도 됩니다.
            </p>
        </div>
        """

        msg = Message(
            subject=subject,
            recipients=[recipient_email],
            body=text_body,
            html=html_body
        )

        mail.send(msg)
        return True

    except Exception as e:
        print(f"[MAIL ERROR] 비밀번호 재설정 메일 발송 실패: {e}")
        return False