# app/utils/auth_utils.py (예시 경로)
from jose import jwt
from datetime import datetime, timedelta, timezone
import os

# JWT 서명/검증에 쓰는 유일한 SECRET_KEY. 다른 파일에서는 반드시 이 값을 import해서 쓴다.
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError(
        "SECRET_KEY 환경변수가 설정되지 않았습니다. backend-main/.env 에 SECRET_KEY 값을 설정하세요."
    )

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES) # datetime.utcnow()는 Python 3.12부터 deprecated 경고가 뜨고, UTC 시간은 timezone-aware 방식인 datetime.now(timezone.utc)를 쓰는 것을 권장
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> dict:
    """토큰을 디코딩해 payload를 반환한다. 만료/변조 시 jose 예외를 그대로 던진다."""
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])