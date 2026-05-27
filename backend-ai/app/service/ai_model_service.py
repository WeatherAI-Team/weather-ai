# app/service/ai_model_service.py
import os
import asyncio
import subprocess
from collections import Counter
os.environ['KERAS_BACKEND'] = 'torch'

import cv2
import numpy as np
import datetime
from fastapi import UploadFile

import keras
from ultralytics import YOLO

CLASS_NAMES = ['heavy_rain', 'heavy_snow', 'sun']
DANGER_CLASSES = ['heavy_rain', 'heavy_snow', 'fog']

STATIC_DIR = os.getenv('STATIC_DIR', 'static')


class AIModelService:

    def __init__(self):
        print("[AI] 모델 로딩 중...")
        self.keras_model = keras.models.load_model('weather_danger_finetuned_model.keras')
        self.yolo_model = YOLO('best.pt')
        print("[AI] 모든 모델 로딩 완료!")

        self.is_analyzing = False
        self.stop_requested = False

    def stop_analysis(self):
        self.stop_requested = True
        self.is_analyzing = False
        print("[AI] 분석 중지 요청됨")

    def _reset_state(self):
        self.is_analyzing = True
        self.stop_requested = False

    def _convert_to_h264(self, input_path: str) -> str:
        output_path = os.path.splitext(input_path)[0] + '_converted.mp4'
        try:
            result = subprocess.run([
                'ffmpeg', '-i', input_path,
                '-vcodec', 'libx264',
                '-acodec', 'aac',
                '-y',
                output_path
            ], capture_output=True, text=True, timeout=120)

            if result.returncode == 0:
                print(f"[AI] ✅ ffmpeg 변환 완료: {output_path}")
                return output_path
            else:
                print(f"[AI] ⚠️ ffmpeg 변환 실패, 원본 사용: {result.stderr}")
                return input_path
        except Exception as e:
            print(f"[AI] ⚠️ ffmpeg 없음 또는 오류, 원본 사용: {e}")
            return input_path

    # ════════════════════════════════════════
    # 케라스: 기상 + 위험차량 1차 분류
    # ════════════════════════════════════════
    def _predict_weather(self, frame: np.ndarray) -> dict:
        img = cv2.resize(frame, (224, 224))
        img = img / 255.0
        img = np.expand_dims(img, axis=0)

        pred_weather, pred_danger = self.keras_model.predict(img, verbose=0)

        class_idx = np.argmax(pred_weather[0])
        class_name = CLASS_NAMES[class_idx]
        weather_confidence = float(pred_weather[0][class_idx])

        danger_score = float(pred_danger[0][0])
        has_danger_car = danger_score >= 0.5

        result = {
            'weather': class_name,
            'confidence': round(weather_confidence * 100, 1),
            'is_danger': class_name in DANGER_CLASSES,
            'has_danger_car': has_danger_car,
            'danger_confidence': round(danger_score * 100, 1)
        }

        print(f"[AI] 케라스 기상: {class_name} | 신뢰도: {round(weather_confidence*100,1)}% | 위험차량: {has_danger_car}")
        return result

    # ════════════════════════════════════════
    # YOLO: 악천후 + 위험차량 감지 시에만 실행
    # ════════════════════════════════════════
    def _run_yolo(self, frame: np.ndarray, keras_result: dict) -> list:
        yolo_boxes = []

        if keras_result['is_danger']:
            print(f"[AI] 🚨 악천후 + 위험차량 감지 → YOLO 정밀 분석 시작")
            yolo_results = self.yolo_model(frame, verbose=False)

            for box in yolo_results[0].boxes:
                coords = box.xyxy[0].tolist()
                conf = float(box.conf[0])
                cls_id = int(box.cls[0])
                cls_name = self.yolo_model.names[cls_id]

                yolo_boxes.append({
                    'class_name': cls_name,
                    'confidence': round(conf * 100, 1),
                    'box_coords': [round(c, 1) for c in coords]
                })

                cv2.rectangle(frame,
                    (int(coords[0]), int(coords[1])),
                    (int(coords[2]), int(coords[3])),
                    (0, 0, 255), 3)
                cv2.putText(frame,
                    f"{cls_name} {round(conf*100)}%",
                    (int(coords[0]), int(coords[1]) - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

            if yolo_boxes:
                best_box = max(yolo_boxes, key=lambda x: x['confidence'])
                print(f"[AI] YOLO 대표 차종: {best_box['class_name']} ({best_box['confidence']}%)")

            print(f"[AI] YOLO 탐지 결과: {[b['class_name'] for b in yolo_boxes]}")
        else:
            print(f"[AI] YOLO 스킵 (악천후: {keras_result['is_danger']}, 위험차량: {keras_result['has_danger_car']})")

        return yolo_boxes

    # ════════════════════════════════════════
    # 이미지 분석
    # ════════════════════════════════════════
    async def detect_image(self, file: UploadFile) -> dict:
        print(f"[AI] 이미지 분석 요청: {file.filename}")
        file_bytes = await file.read()
        np_arr = np.frombuffer(file_bytes, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        if frame is None:
            raise ValueError("이미지 디코딩 실패.")

        keras_result = self._predict_weather(frame)
        yolo_boxes = self._run_yolo(frame, keras_result)

        # 이미지에서 신뢰도 가장 높은 차종 하나
        if yolo_boxes:
            best_box = max(yolo_boxes, key=lambda x: x['confidence'])
            dominant_vehicle = f"{best_box['class_name']} ({best_box['confidence']}%)"
        else:
            dominant_vehicle = None

        result = {
            **keras_result,
            'yolo_boxes': yolo_boxes,
            'detected_vehicle': dominant_vehicle,
            'yolo_detected': len(yolo_boxes) > 0
        }
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

        if frame is None:
            raise ValueError("이미지 디코딩 실패.")

        keras_result = self._predict_weather(frame)
        yolo_boxes = self._run_yolo(frame, keras_result)

        if yolo_boxes:
            best_box = max(yolo_boxes, key=lambda x: x['confidence'])
            dominant_vehicle = f"{best_box['class_name']} ({best_box['confidence']}%)"
        else:
            dominant_vehicle = None

        weather_label = f"{keras_result['weather']} ({keras_result['confidence']}%)"
        danger_label = f"Danger Car: DETECTED ({keras_result['danger_confidence']}%)" if keras_result['has_danger_car'] else "Danger Car: None"
        weather_color = (0, 0, 255) if keras_result['is_danger'] else (0, 255, 0)
        danger_color = (0, 0, 255) if keras_result['has_danger_car'] else (0, 255, 0)

        cv2.putText(frame, weather_label, (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.2, weather_color, 2)
        cv2.putText(frame, danger_label, (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 1.2, danger_color, 2)

        results_dir = os.path.join(STATIC_DIR, 'results')
        os.makedirs(results_dir, exist_ok=True)
        now_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        local_path = os.path.join(results_dir, f"weather_{now_str}.jpg")
        cv2.imwrite(local_path, frame)

        print(f"[AI] 이미지 저장 완료: {local_path}")
        return {
            **keras_result,
            'yolo_boxes': yolo_boxes,
            'detected_vehicle': dominant_vehicle,
            'yolo_detected': len(yolo_boxes) > 0,
            'local_path': local_path
        }

    # ════════════════════════════════════════
    # 영상 분석 + 저장
    # ════════════════════════════════════════
    async def analyze_and_save_video(self, user_id: int, file: UploadFile, original_filename: str) -> dict:
        print(f"[AI] 영상 분석 요청: {file.filename}")
        self._reset_state()

        temp_dir = os.path.join(STATIC_DIR, 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        now_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        ext = os.path.splitext(file.filename)[1].lower() or '.mp4'

        safe_filename = f"upload_{now_str}{ext}"
        temp_input = os.path.join(temp_dir, safe_filename)

        with open(temp_input, 'wb') as f:
            f.write(await file.read())

        converted_path = None

        try:
            converted_path = self._convert_to_h264(temp_input)
            read_path = converted_path

            cap = cv2.VideoCapture(read_path)

            if not cap.isOpened():
                raise ValueError("영상 파일을 열 수 없습니다.")

            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            print(f"[AI] 영상 총 프레임 수: {total_frames} | FPS: {fps}")

            cap.release()
            cap = cv2.VideoCapture(read_path)

            weather_counts = {c: 0 for c in CLASS_NAMES}
            confidence_sum = {c: 0.0 for c in CLASS_NAMES}
            danger_car_frames = 0
            analyzed_frame_count = 0
            frame_count = 0
            vehicle_counter = Counter()
            vehicle_confidence = {}  # 차종별 신뢰도 리스트

            while True:
                if self.stop_requested:
                    print("[AI] 분석 중지됨")
                    break

                ret, frame = cap.read()
                if not ret:
                    break

                if frame is None:
                    frame_count += 1
                    continue

                if frame_count % 5 == 0:
                    keras_result = self._predict_weather(frame)
                    weather_counts[keras_result['weather']] += 1
                    confidence_sum[keras_result['weather']] += keras_result['confidence']

                    if keras_result['has_danger_car']:
                        danger_car_frames += 1

                    yolo_boxes = self._run_yolo(frame, keras_result)
                    for box in yolo_boxes:
                        vehicle_counter[box['class_name']] += 1
                        if box['class_name'] not in vehicle_confidence:
                            vehicle_confidence[box['class_name']] = []
                        vehicle_confidence[box['class_name']].append(box['confidence'])

                    analyzed_frame_count += 1
                frame_count += 1

            cap.release()
            self.is_analyzing = False

            if analyzed_frame_count == 0:
                return {
                    'weather': 'unknown',
                    'confidence': 0.0,
                    'is_danger': False,
                    'has_danger_car': False,
                    'detected_vehicle': None,
                    'weather_counts': weather_counts,
                    'message': '분석 실패: 영상에서 프레임을 읽을 수 없습니다.'
                }

            dominant_weather = max(weather_counts, key=weather_counts.get)
            is_danger = dominant_weather in DANGER_CLASSES
            has_danger_car = (danger_car_frames / max(1, analyzed_frame_count)) >= 0.2
            dominant_count = weather_counts[dominant_weather]
            avg_confidence = round(confidence_sum[dominant_weather] / max(1, dominant_count), 1)

            # 가장 많이 나온 차종 + 평균 신뢰도
            if vehicle_counter:
                dominant_vehicle_name = vehicle_counter.most_common(1)[0][0]
                avg_vehicle_conf = round(
                    sum(vehicle_confidence[dominant_vehicle_name]) / len(vehicle_confidence[dominant_vehicle_name]), 1
                )
                dominant_vehicle = f"{dominant_vehicle_name} ({avg_vehicle_conf}%)"
            else:
                dominant_vehicle = None

            print(f"[AI] 영상 분석 완료 | 최종 기상: {dominant_weather} ({avg_confidence}%) | 위험차량: {has_danger_car} | 대표 차종: {dominant_vehicle}")

            return {
                'weather': dominant_weather,
                'confidence': avg_confidence,
                'is_danger': is_danger,
                'has_danger_car': has_danger_car,
                'danger_confidence': round(danger_car_frames / max(1, analyzed_frame_count) * 100, 1),
                'detected_vehicle': dominant_vehicle,
                'weather_counts': weather_counts,
                'message': '중지됨' if self.stop_requested else '분석 완료'
            }

        finally:
            for path in [temp_input, converted_path]:
                if path and os.path.exists(path):
                    try:
                        os.remove(path)
                    except:
                        pass

    # ════════════════════════════════════════
    # CCTV 실시간 스트리밍 (async generator)
    # ════════════════════════════════════════
    async def get_cctv_stream(self, rtsp_url: str):
        print(f"[AI] CCTV 스트리밍 시작: {rtsp_url}")
        self._reset_state()

        loop = asyncio.get_event_loop()
        cap = await loop.run_in_executor(None, cv2.VideoCapture, rtsp_url)

        if not cap.isOpened():
            print(f"[AI] ❌ CCTV 연결 실패: {rtsp_url}")
            return

        frame_count = 0
        weather_label = 'Analyzing...'
        danger_label = 'Analyzing...'
        weather_color = (255, 255, 255)
        danger_color = (255, 255, 255)

        try:
            while True:
                if self.stop_requested:
                    print("[AI] CCTV 스트리밍 중지됨")
                    break

                ret, frame = await loop.run_in_executor(None, cap.read)
                if not ret or frame is None:
                    break

                if frame_count % 5 == 0:
                    keras_result = self._predict_weather(frame)
                    weather_label = f"{keras_result['weather']} ({keras_result['confidence']}%)"
                    danger_label = f"Danger Car: DETECTED ({keras_result['danger_confidence']}%)" if keras_result['has_danger_car'] else "Danger Car: None"
                    weather_color = (0, 0, 255) if keras_result['is_danger'] else (0, 255, 0)
                    danger_color = (0, 0, 255) if keras_result['has_danger_car'] else (0, 255, 0)

                    self._run_yolo(frame, keras_result)

                cv2.putText(frame, weather_label, (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.2, weather_color, 2)
                cv2.putText(frame, danger_label, (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 1.2, danger_color, 2)

                _, buffer = cv2.imencode('.jpg', frame)
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

                frame_count += 1
                await asyncio.sleep(0)

        finally:
            cap.release()
            self.is_analyzing = False
            print(f"[AI] CCTV 스트리밍 종료")