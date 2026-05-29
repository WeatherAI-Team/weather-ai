# Flask에서 필요한 도구들을 가져와.
# Blueprint는 API 주소를 묶어주는 도구야.
# request는 사용자가 보낸 값을 읽을 때 써.
# jsonify는 Python 데이터를 JSON으로 바꿔줘.
# current_app은 서버에서 에러 로그를 남길 때 써.
# f-026 AI chatbot
from flask import Blueprint, request, jsonify, current_app
import time 
# 챗봇 기능을 처리하는 ChatbotService를 가져와.
from ..services.chatbot_service import ChatbotService


# 챗봇 API 묶음을 만들어.
# 이 파일의 API 주소는 /api/chatbot 으로 시작해.
chatbot_bp = Blueprint("chatbot", __name__, url_prefix="/api/chatbot")

# ChatbotService를 만들어.
# 이제 API에서 챗봇 답변 기능을 사용할 수 있어.
chatbot_service = ChatbotService()


@chatbot_bp.route("/message", methods=["POST"])
def send_message():
    # 이 함수는 POST /api/chatbot/message 요청이 들어오면 실행돼.
    # 쉽게 말하면 사용자가 챗봇에게 메시지를 보낼 때 실행되는 함수야.
    
    # 요청 처리 시간을 재기 시작해.
    start_time = time.perf_counter()
    print("[CHATBOT] 요청 들어옴", flush=True)
    # 사용자가 보낸 JSON 데이터를 가져와.
    # 예: {"message": "강남대로 위험해?"}
    data = request.get_json(silent=True) or {}
    print("[CHATBOT] JSON 읽음", time.perf_counter() - start_time, flush=True)
    # message 값을 꺼내.
    message = data.get("message", "")

    # message가 문자열이 아니면 잘못된 요청으로 처리해.
    # 예: {"message": 123} 같은 요청 방지
    if not isinstance(message, str):
        return jsonify({
            "success": False,
            "message": "message는 문자열이어야 합니다.",
            "data": None
        }), 400
    
    # 앞뒤 공백을 제거해.
    message = message.strip()
    print("[CHATBOT] message 정리 완료:", message, time.perf_counter() - start_time, flush=True)

    # 빈 메시지면 굳이 service까지 보내지 않고 바로 안내해.
    if not message:
        return jsonify({
            "success": False,
            "message": "질문 내용을 입력해 주세요.",
            "data": None
        }), 400

    # 질문이 너무 길면 처리하지 않고 안내해.
    if len(message) > 300:
        return jsonify({
            "success": False,
            "message": "질문은 300자 이내로 입력해 주세요.",
            "data": None
        }), 400
    
    try:
        print("[CHATBOT] create_response 시작", time.perf_counter() - start_time, flush=True)
        # Service에게 챗봇 답변을 만들어 달라고 부탁해.
        result = chatbot_service.create_response(message)
        print("[CHATBOT] create_response 끝", time.perf_counter() - start_time, flush=True)

        response = jsonify({
            "success": True,
            "message": "챗봇 응답 생성 성공",
            "data": result
        })

        print("[CHATBOT] jsonify 끝", time.perf_counter() - start_time, flush=True)

        return response, 200

    except Exception:
        current_app.logger.exception("챗봇 응답 생성 중 오류 발생")

        return jsonify({
            "success": False,
            "message": "챗봇 응답 생성 중 오류가 발생했습니다.",
            "data": None
        }), 500