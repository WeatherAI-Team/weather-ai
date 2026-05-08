# app/service/ai_model_service.py
import os
os.environ['KERAS_BACKEND'] = 'torch'

import cv2
import numpy as np
import datetime
from fastapi import UploadFile

import keras

CLASS_NAMES = ['fog', 'heavy_rain', 'heavy_snow', 'sun']
DANGER_CLASSES = ['fog', 'heavy_rain', 'heavy_snow']


class AIModelService:

    def __init__(self):
        print("[AI] 모델 로딩 중...")
        self.model = keras.models.load_model('weather_final_model_finetuned.h5')
        print("[AI] 모델 로딩 완료!")

    # ════════════════════════════════════════
    # 단일 프레임 기상 분류
    # ════════════════════════════════════════

    def _predict_weather(self, frame: np.ndarray) -> dict:
        img = cv2.resize(frame, (224, 224))
        img = img / 255.0
        img = np.expand_dims(img, axis=0)

        pred = self.model.predict(img, verbose=0)
        class_idx = np.argmax(pred[0])
        class_name = CLASS_NAMES[class_idx]
        confidence = float(pred[0][class_idx])

        result = {
            'weather': class_name,
            'confidence': round(confidence * 100, 1),
            'is_danger': class_name in DANGER_CLASSES
        }

        print(f"[AI] 기상 분류: {class_name} | 신뢰도: {round(confidence * 100, 1)}% | 악천후: {result['is_danger']}")
        return result

    # ════════════════════════════════════════
    # 이미지 분석
    # ════════════════════════════════════════

    async def detect_image(self, file: UploadFile) -> dict:
        print(f"[AI] 이미지 분석 요청: {file.filename}")
        file_bytes = await file.read()
        np_arr = np.frombuffer(file_bytes, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        result = self._predict_weather(frame)
        print(f"[AI] 이미지 분석 완료: {result}")
        return result

    # ════════════════════════════════════════
    # 이미지 분석 + 저장
    # ════════════════════════════════════════

    async def detect_and_save_image(self, user_id: int, file: UploadFile, original_filename: str) -> dict:
        print(f"[AI] 이미지 분석+저장 요청: {original_filename}")
        file_bytes = await file.read()
        np_arr = np.frombuffer(file_bytes, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        result = self._predict_weather(frame)

        label = f"{result['weather']} ({result['confidence']}%)"
        color = (0, 0, 255) if result['is_danger'] else (0, 255, 0)
        cv2.putText(frame, label, (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.2, color, 2)

        os.makedirs('static/results', exist_ok=True)
        now_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        local_path = f"static/results/weather_{now_str}.jpg"
        cv2.imwrite(local_path, frame)

        print(f"[AI] 이미지 저장 완료: {local_path}")
        return {**result, 'local_path': local_path}

    # ════════════════════════════════════════
    # 영상 분석 + 저장
    # ════════════════════════════════════════

    async def analyze_and_save_video(self, user_id: int, file: UploadFile, original_filename: str) -> dict:
        print(f"[AI] 영상 분석 요청: {file.filename}")
        os.makedirs('static/temp', exist_ok=True)
        now_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        ext = os.path.splitext(file.filename)[1].lower() or '.mp4'
        temp_input = f"static/temp/temp_{now_str}{ext}"

        with open(temp_input, 'wb') as f:
            f.write(await file.read())

        try:
            cap = cv2.VideoCapture(temp_input)
            weather_counts = {c: 0 for c in CLASS_NAMES}
            frame_count = 0

            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                if frame_count % 5 == 0:
                    result = self._predict_weather(frame)
                    weather_counts[result['weather']] += 1
                frame_count += 1

            cap.release()

            dominant_weather = max(weather_counts, key=weather_counts.get)
            is_danger = dominant_weather in DANGER_CLASSES

            print(f"[AI] 영상 분석 완료 | 최종 기상: {dominant_weather} | 분포: {weather_counts}")

            return {
                'weather': dominant_weather,
                'is_danger': is_danger,
                'weather_counts': weather_counts,
                'message': '분석 완료'
            }

        finally:
            if os.path.exists(temp_input):
                os.remove(temp_input)

    # ════════════════════════════════════════
    # CCTV 실시간 스트리밍
    # ════════════════════════════════════════

    def get_cctv_stream(self, rtsp_url: str):
        print(f"[AI] CCTV 스트리밍 시작: {rtsp_url}")
        cap = cv2.VideoCapture(rtsp_url)
        frame_count = 0
        label = 'Analyzing...'
        color = (255, 255, 255)

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_count % 5 == 0:
                result = self._predict_weather(frame)
                label = f"{result['weather']} ({result['confidence']}%)"
                color = (0, 0, 255) if result['is_danger'] else (0, 255, 0)

            cv2.putText(frame, label, (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.2, color, 2)

            _, buffer = cv2.imencode('.jpg', frame)
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
            frame_count += 1

        cap.release()
        print(f"[AI] CCTV 스트리밍 종료")