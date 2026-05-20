# Flask에서 필요한 도구들을 가져와.
# Blueprint는 API 주소를 묶어주는 도구야.
# request는 사용자가 보낸 값을 읽을 때 써.
# jsonify는 Python 데이터를 JSON으로 바꿔줘.
# f-026 AI chatbot
from flask import Blueprint, request, jsonify

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

    # 사용자가 보낸 JSON 데이터를 가져와.
    # 예: {"message": "강남대로 위험해?"}
    data = request.get_json()

    # JSON 데이터가 없으면 빈 딕셔너리로 바꿔줘.
    if data is None:
        data = {}

    # JSON 안에서 message 값을 꺼내.
    # message가 없으면 빈 문자열로 처리해.
    message = data.get("message", "")

    # Service에게 챗봇 답변을 만들어 달라고 부탁해.
    result = chatbot_service.create_response(message)

    # 결과를 JSON 형태로 프론트에게 보내줘.
    return jsonify({
        "success": True,
        "message": "챗봇 응답 생성 성공",
        "data": result
    }), 200