# 요청에서 쿠키나 정보를 가져오기 위해 request를 가져와.
# 응답을 JSON으로 보내기 위해 jsonify를 가져와.
from flask import request, jsonify

# 데코레이터를 만들 때 원래 함수 이름을 유지하기 위해 가져와.
from functools import wraps

# JWT 토큰을 해석하기 위해 가져와.
from jose import jwt

# JWT 오류를 구분해서 처리하기 위해 가져와.
from jose.exceptions import ExpiredSignatureError, JWTError

# 환경변수에서 SECRET_KEY를 가져오기 위해 가져와.
import os


# 로그인할 때 토큰을 만들었던 SECRET_KEY와 같아야 해.
SECRET_KEY = os.getenv("SECRET_KEY", "your-fallback-secret-key")

# 프론트엔드와 약속한 쿠키 이름을 적어줘. (기본값으로 많이 쓰는 "access_token" 설정)
COOKIE_NAME = "access_token"


def login_required(f):
    # 로그인한 사용자만 API를 사용할 수 있게 막아주는 함수야.
    @wraps(f)
    def decorated(*args, **kwargs):
        # [수정] 요청 헤더 대신 브라우저 쿠키에서 토큰을 가져와.
        auth_token = request.cookies.get(COOKIE_NAME)

        # 토큰이 없으면 로그인하지 않은 상태야.
        if not auth_token:
            return jsonify({
                "success": False,
                "message": "토큰이 없습니다."
            }), 401

        try:
            # [수정] 쿠키 방식을 쓸 때는 보통 "Bearer " 접두사 없이 토큰값만 들어있으므로 split 과정이 필요 없어.
            # JWT 토큰을 해석해.
            # JWT 기본 만료 시간 검증을 그대로 사용해.
            payload = jwt.decode(
                auth_token,
                SECRET_KEY,
                algorithms=["HS256"]
            )

            # 토큰 안에 있는 사용자 ID를 request에 저장해.
            # 뒤의 API 함수에서 request.user_id로 사용할 수 있어.
            request.user_id = payload.get("sub")

            # 토큰 안에 있는 사용자 권한을 저장해.
            # 값이 없으면 일반 사용자로 처리해.
            request.user_role = payload.get("role", "user")

        except ExpiredSignatureError:
            # 토큰 시간이 지난 경우야.
            return jsonify({
                "success": False,
                "message": "토큰이 만료되었습니다."
            }), 401

        except JWTError as e:
            # 토큰이 잘못됐거나 변조된 경우야.
            print(f"[JWT ERROR] {e}")
            return jsonify({
                "success": False,
                "message": "유효하지 않은 토큰입니다."
            }), 401

        except Exception as e:
            # 예상하지 못한 서버 오류야.
            print(f"[LOGIN REQUIRED ERROR] {e}")
            return jsonify({
                "success": False,
                "message": "인증 처리 중 오류가 발생했습니다."
            }), 500

        # 모든 검사를 통과하면 원래 API 함수를 실행해.
        return f(*args, **kwargs)

    return decorated


def admin_required(f):
    # 관리자만 API를 사용할 수 있게 막아주는 함수야.
    @wraps(f)
    def decorated(*args, **kwargs):
        # [수정] 요청 헤더 대신 브라우저 쿠키에서 토큰을 가져와.
        auth_token = request.cookies.get(COOKIE_NAME)

        # 토큰이 없으면 로그인하지 않은 상태야.
        if not auth_token:
            return jsonify({
                "success": False,
                "message": "토큰이 없습니다."
            }), 401

        try:
            # JWT 토큰을 해석해.
            # 만료된 토큰은 자동으로 차단돼.
            payload = jwt.decode(
                auth_token,
                SECRET_KEY,
                algorithms=["HS256"]
            )

            # 토큰 안의 사용자 ID를 저장해.
            request.user_id = payload.get("sub")

            # 토큰 안의 권한을 저장해.
            request.user_role = payload.get("role", "user")

            # 관리자 권한인지 확인해.
            # 너희 기존 코드 기준으로 admin, manager만 관리자 취급해.
            if request.user_role not in ("admin", "manager"):
                return jsonify({
                    "success": False,
                    "message": "관리자 권한이 필요합니다."
                }), 403

        except ExpiredSignatureError:
            # 토큰 시간이 지난 경우야.
            return jsonify({
                "success": False,
                "message": "토큰이 만료되었습니다."
            }), 401

        except JWTError as e:
            # 토큰이 잘못됐거나 변조된 경우야.
            print(f"[JWT ERROR] {e}")
            return jsonify({
                "success": False,
                "message": "유효하지 않은 토큰입니다."
            }), 401

        except Exception as e:
            # 예상하지 못한 서버 오류야.
            print(f"[ADMIN REQUIRED ERROR] {e}")
            return jsonify({
                "success": False,
                "message": "권한 확인 중 오류가 발생했습니다."
            }), 500

        # 관리자 검사를 통과하면 원래 API 함수를 실행해.
        return f(*args, **kwargs)

    return decorated