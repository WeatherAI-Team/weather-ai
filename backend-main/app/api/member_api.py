from flask import Blueprint, request, jsonify
from ..services.member_service import MemberService

member_bp = Blueprint('member', __name__)
member_service = MemberService()

@member_bp.route('/register', methods=['POST'])
def register():
    data = request.json
    print(f"DEBUG: 프론트에서 온 데이터 -> {data}")  # <--- 이 줄만 추가!
    result = member_service.register_member(data)
    
    if result["success"]:
        return jsonify(result), 201
    return jsonify(result), 400

@member_bp.route("", methods=["GET"])
def get_members():
    # 주소 뒤에 붙은 page 값을 가져와.
    # 없으면 기본값으로 1을 사용해.
    # 예: /api/member?page=2
    page = request.args.get("page",1,type=int)

    # 한 페이지에 몇 명 보여줄지 정해.
    # 없으면 기본값으로 10명을 보여줘.
    # 예: /api/member?per_page=20
    per_page = request.args.get("per_page", 10, type=int)


    # 검색어를 가져와.
    # 예: /api/member?keyword=정화
    keyword = request.args.get("keyword")
    
    # 권한 검색값을 가져와.
    # 예: /api/member?role=user
    role = request.args.get("role")

    # active 검색값을 가져와.
    # 주소에서는 문자열로 들어와서 아래에서 True/False로 바꿔줘야 해.
    # 예: /api/member?active=true
    active_param = request.args.get("active")

    # active 값을 처음에는 None으로 둬.
    # None이라는 뜻은 active 조건으로 검색하지 않겠다는 뜻이야.
    active = None


    # 만약 active=true 또는 active=false가 들어왔다면
    # 문자열을 진짜 True/False 값으로 바꿔줘.
    if active_param is not None:
        active = active_param.lower() == "true"
    
    # service에게 회원 목록을 가져오라고 요청해.
    result = member_service.get_member_list(
        page=page,
        per_page=per_page,
        keyword=keyword,
        role=role,
        active=active
    )
    
    # 결과를 JSON으로 프론트엔드나 사용자에게 보내줘.
    return jsonify(result), 200 









# GET http://localhost:5000/api/member/1
@member_bp.route('/<int:member_id>', methods=['GET'])
def get_profile(member_id):
    result = member_service.get_member_info(member_id)
    
    if result["success"]:
        return jsonify(result), 200
    return jsonify(result), 404