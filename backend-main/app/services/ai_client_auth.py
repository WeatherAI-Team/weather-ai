# app/services/ai_client_auth.py
# backend-ai(FastAPI) 서버 호출 시 공통으로 붙이는 내부 인증 헤더.
# backend-ai/app/security.py 의 AI_INTERNAL_SECRET 과 값이 같아야 한다.
import os

AI_INTERNAL_SECRET = os.getenv("AI_INTERNAL_SECRET")

if not AI_INTERNAL_SECRET:
    raise RuntimeError(
        "AI_INTERNAL_SECRET 환경변수가 설정되지 않았습니다. "
        "backend-main/.env 에 AI_INTERNAL_SECRET 값을 설정하세요 "
        "(backend-ai/.env 의 값과 동일해야 합니다)."
    )

AI_SERVER_HEADERS = {"X-Internal-Secret": AI_INTERNAL_SECRET}
