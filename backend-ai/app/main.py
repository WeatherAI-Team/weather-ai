from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# 데이터 규격을 정의해 (팀원들이 이걸 보고 프론트/메인 서버를 짜게 됨)
class DetectionResult(BaseModel):
    label: str
    confidence: float
    box: list[int]

@app.get("/")
def read_root():
    return {"message": "AI 서버 정상 작동 중!"}

@app.post("/predict")
def predict():
    # 실제로는 여기서 모델을 돌리겠지만, 지금은 가짜(Mock) 데이터를 반환해
    print("[AI Server] 추론 요청 수신!")
    
    mock_result = {
        "label": "Korean Wild Boar",
        "confidence": 0.98,
        "box": [100, 200, 300, 400]
    }
    
    return {"status": "success", "data": mock_result}