# app/security.py
# backend-main만 호출할 수 있도록 서버 간 공유 시크릿을 검증한다.
import os
from fastapi import Header, HTTPException, status

AI_INTERNAL_SECRET = os.getenv("AI_INTERNAL_SECRET")

if not AI_INTERNAL_SECRET:
    raise RuntimeError(
        "AI_INTERNAL_SECRET 환경변수가 설정되지 않았습니다. "
        "backend-ai/.env 에 AI_INTERNAL_SECRET 값을 설정하세요 "
        "(backend-main/.env 의 값과 동일해야 합니다)."
    )


async def verify_internal_secret(x_internal_secret: str = Header(default=None)):
    if x_internal_secret != AI_INTERNAL_SECRET:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
