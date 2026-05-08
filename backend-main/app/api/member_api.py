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

# GET http://localhost:5000/api/member/1
@member_bp.route('/<int:member_id>', methods=['GET'])
def get_profile(member_id):
    result = member_service.get_member_info(member_id)
    
    if result["success"]:
        return jsonify(result), 200
    return jsonify(result), 404