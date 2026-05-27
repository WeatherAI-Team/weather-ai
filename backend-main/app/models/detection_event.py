# app에서 db를 가져와.
# db는 Flask가 데이터베이스랑 대화할 수 있게 도와주는 도구야.
# f-021 탐지 결과 조회/필터링
from app import db


class DetectionEvent(db.Model):
    # 이 클래스는 Supabase DB의 detection_events 테이블과 연결돼.
    # 쉽게 말하면 DB 테이블을 파이썬 코드로 표현한 거야.
    __tablename__ = "detection_events"

    # 탐지 이벤트의 고유 번호야.
    # 이벤트마다 번호가 하나씩 달라.
    id = db.Column(db.BigInteger, primary_key=True)

    # 어떤 CCTV에서 발생한 이벤트인지 알려주는 번호야.
    cctv_source_id = db.Column(db.BigInteger, nullable=True)

    # 어떤 날씨 기록과 연결된 이벤트인지 알려주는 번호야.
    weather_log_id = db.Column(db.BigInteger, nullable=True)

    # 이벤트 제목이야.
    # 예: "폭우 상황 위험 차량 감지"
    event_title = db.Column(db.String, nullable=True)

    # 이벤트가 발생한 위치 이름이야.
    # 예: "강남대로", "올림픽대로"
    location_name = db.Column(db.String, nullable=True)

    # 위도야.
    # 지도에서 세로 위치를 표시할 때 필요해.
    latitude = db.Column(db.Numeric, nullable=True)

    # 경도야.
    # 지도에서 가로 위치를 표시할 때 필요해.
    longitude = db.Column(db.Numeric, nullable=True)

    # 날씨 종류야.
    # 예: rain, snow
    weather_type = db.Column(db.String, nullable=True)

    # 일반 차량 개수야.
    normal_vehicle_count = db.Column(db.Integer, nullable=True)

    # 위험 차량 개수야.
    risk_vehicle_count = db.Column(db.Integer, nullable=True)

    # 교통 밀도 점수야.
    # 차가 얼마나 많은지 점수로 나타낸 값이라고 보면 돼.
    traffic_density_score = db.Column(db.Integer, nullable=True)

    # 가장 많이 보이는 주요 차량 종류야.
    # 예: car, bus, heavy_truck
    main_vehicle_type = db.Column(db.String, nullable=True)

    # 위험도 점수야.
    # 숫자가 높을수록 더 위험하다고 볼 수 있어.
    risk_score = db.Column(db.Integer, nullable=True)

    # 위험도 단계야.
    # 예: low, medium, high
    risk_level = db.Column(db.String, nullable=True)

    # 이벤트 상태야.
    # 예: pending, confirmed, resolved
    event_status = db.Column(db.String, nullable=True)

    # LLM이 만든 제목이야.
    llm_title = db.Column(db.String, nullable=True)

    # LLM이 만든 요약 내용이야.
    llm_summary = db.Column(db.Text, nullable=True)

    # 관리자가 적는 메모야.
    admin_memo = db.Column(db.Text, nullable=True)

    # 실제 탐지가 발생한 시간이야.
    detected_at = db.Column(db.DateTime, nullable=True)

    # 이 데이터가 처음 만들어진 시간이야.
    created_at = db.Column(db.DateTime, nullable=True)

    # 이 데이터가 마지막으로 수정된 시간이야.
    updated_at = db.Column(db.DateTime, nullable=True)

    # 낮/밤 같은 시간 유형이야.
    # 예: day, night
    time_type = db.Column(db.String, nullable=True)

    # 어떤 AI 모델이 탐지했는지 적는 칸이야.
    model_name = db.Column(db.String, nullable=True)

    # 전체 차량 개수야.
    total_vehicle_count = db.Column(db.Integer, nullable=True)

    # 탐지 신뢰도야.
    # AI가 얼마나 확실하게 탐지했는지 나타내는 값이야.
    detection_confidence = db.Column(db.Numeric, nullable=True)

    # 점수 필터를 통과했는지 여부야.
    # True면 위험도 기준을 통과했다는 뜻이야.
    score_filter_passed = db.Column(db.Boolean, nullable=True)

    # LLM 검증 결과야.
    # 예: approved, rejected
    llm_decision = db.Column(db.String, nullable=True)

    # LLM이 그렇게 판단한 이유야.
    llm_reason = db.Column(db.Text, nullable=True)

    # 알림이 필요한지 여부야.
    # True면 관리자나 사용자에게 알려야 하는 이벤트야.
    alert_required = db.Column(db.Boolean, nullable=True)

    # 오탐 의심 여부야.
    # True면 실제 위험이 아닐 수도 있다는 뜻이야.
    false_positive_suspected = db.Column(db.Boolean, nullable=True)
