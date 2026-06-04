# app/service/ai_model_service.py
from dotenv import load_dotenv
load_dotenv()

import os
import asyncio
import subprocess
import time
from collections import Counter
import psycopg2

os.environ['KERAS_BACKEND'] = 'torch'

import cv2
import numpy as np
import datetime
from fastapi import UploadFile

import keras
from ultralytics import YOLO

CLASS_NAMES = ['fog', 'heavy_rain', 'heavy_snow', 'sun']
DANGER_CLASSES = ['fog', 'heavy_rain', 'heavy_snow']

STATIC_DIR = os.getenv('STATIC_DIR', 'static')
DATABASE_URL = os.getenv('DATABASE_URL')
print(f"[DB] DATABASE_URL: {DATABASE_URL}")

VEHICLE_TYPE_MAP = {
    'Gas_Truck':   'gas_truck',
    'RMC':         'rmc',
    'cargo_truck': 'cargo_truck',

}


class AIModelService:

    def __init__(self):
        print("[AI] 모델 로딩 중...")
        self.keras_model = keras.models.load_model('weather_classifier_finetuned_model.keras')
        self.yolo_model = YOLO('best.pt')
        print("[AI] 모든 모델 로딩 완료!")

        self.is_analyzing = False
        self.stop_requested = False
        self.last_save_time = None
        self.save_interval = 5

    def stop_analysis(self):
        self.stop_requested = True
        self.is_analyzing = False
        print("[AI] 분석 중지 요청됨")

    def _reset_state(self):
        self.is_analyzing = True
        self.stop_requested = False

    def _get_db(self):
        return psycopg2.connect(DATABASE_URL)

    def _save_detection_event(self, keras_result: dict, yolo_boxes: list, cctv_source_id: int = None) -> int:
        try:
            conn = self._get_db()
            cur = conn.cursor()

            risk_vehicle_count = len(yolo_boxes)
            detection_confidence = keras_result['confidence'] / 100.0

            if detection_confidence >= 0.9 and risk_vehicle_count >= 3:
                risk_level = 'EMERGENCY'
            elif detection_confidence >= 0.8 and risk_vehicle_count >= 2:
                risk_level = 'SERIOUS'
            elif detection_confidence >= 0.7 and risk_vehicle_count >= 1:
                risk_level = 'WARNING'
            elif detection_confidence >= 0.6:
                risk_level = 'CAUTION'
            else:
                risk_level = 'INTEREST'

            if yolo_boxes:
                best_box = max(yolo_boxes, key=lambda x: x['confidence'])
                main_vehicle_type = VEHICLE_TYPE_MAP.get(best_box['class_name'], 'SPECIAL_VEHICLE')
            else:
                main_vehicle_type = None

            cur.execute("""
                INSERT INTO detection_events (
                    cctv_source_id, weather_type, model_name, detected_at,
                    risk_vehicle_count, total_vehicle_count, main_vehicle_type,
                    detection_confidence, risk_level, alert_required, event_status,
                    created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                RETURNING id
            """, (
                cctv_source_id,
                keras_result['weather'].upper(),
                'YOLO11m',
                datetime.datetime.now(),
                risk_vehicle_count,
                risk_vehicle_count,
                main_vehicle_type,
                detection_confidence,
                risk_level,
                keras_result['is_danger'] and risk_vehicle_count > 0,
                'UNCONFIRMED',
            ))

            event_id = cur.fetchone()[0]
            conn.commit()
            cur.close()
            conn.close()

            print(f"[DB] ✅ detection_events 저장 완료 | event_id: {event_id}")
            return event_id

        except Exception as e:
            print(f"[DB] ❌ detection_events 저장 실패: {e}")
            return None

    def _save_detection_objects(self, event_id: int, yolo_boxes: list):
        if not event_id or not yolo_boxes:
            return
        try:
            conn = self._get_db()
            cur = conn.cursor()

            for box in yolo_boxes:
                vehicle_type = VEHICLE_TYPE_MAP.get(box['class_name'], 'SPECIAL_VEHICLE')
                cur.execute("""
                    INSERT INTO detection_objects (
                        event_id, is_risk_vehicle, vehicle_type, model_name, confidence, created_at
                    ) VALUES (%s, %s, %s, %s, %s, NOW())
                """, (
                    event_id, True, vehicle_type, 'YOLO11m', box['confidence'] / 100.0,
                ))

            conn.commit()
            cur.close()
            conn.close()
            print(f"[DB] ✅ detection_objects 저장 완료 | {len(yolo_boxes)}개")

        except Exception as e:
            print(f"[DB] ❌ detection_objects 저장 실패: {e}")

    def _convert_to_h264(self, input_path: str) -> str:
        output_path = os.path.splitext(input_path)[0] + '_converted.mp4'
        try:
            result = subprocess.run([
                'ffmpeg', '-i', input_path,
                '-vcodec', 'libx264', '-acodec', 'aac', '-y', output_path
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

    def _predict_weather(self, frame: np.ndarray) -> dict:
        img = cv2.resize(frame, (224, 224))
        img = img / 255.0
        img = np.expand_dims(img, axis=0)

        pred_weather = self.keras_model.predict(img, verbose=0)

        class_idx = np.argmax(pred_weather[0])
        class_name = CLASS_NAMES[class_idx]
        weather_confidence = float(pred_weather[0][class_idx])

        result = {
            'weather': class_name,
            'confidence': round(weather_confidence * 100, 1),
            'is_danger': class_name in DANGER_CLASSES,
        }

        print(f"[AI] 케라스 기상: {class_name} | 신뢰도: {round(weather_confidence*100,1)}%")
        return result

    def _run_yolo(self, frame: np.ndarray, keras_result: dict) -> list:
        yolo_boxes = []

        if keras_result['is_danger'] and keras_result['confidence'] >= 40.0:  # 배포 시 60.0으로 변경
            print(f"[AI] 🚨 신뢰도 {keras_result['confidence']}% → YOLO 위험차량 탐지 시작")
            yolo_results = self.yolo_model(frame, verbose=False, conf=0.4)

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
            print(f"[AI] YOLO 스킵 (날씨: {keras_result['weather']} | 신뢰도: {keras_result['confidence']}%)")

        return yolo_boxes

    def _save_clip(self, video_path: str, trigger_frame: int, fps: float, duration_sec: int = 3) -> str | None:
        try:
            clips_dir = os.path.join(STATIC_DIR, 'clips')
            os.makedirs(clips_dir, exist_ok=True)

            now_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            clip_path = os.path.join(clips_dir, f"clip_{now_str}.mp4")

            start_sec = max(0, (trigger_frame - int(fps * 1.5)) / fps)

            result = subprocess.run([
                'ffmpeg',
                '-ss', str(start_sec),
                '-i', video_path,
                '-t', str(duration_sec),
                '-vcodec', 'libx264',
                '-acodec', 'aac',
                '-y',
                clip_path
            ], capture_output=True, text=True, timeout=60)

            if result.returncode == 0:
                print(f"[AI] 클립 저장 완료: {clip_path}")
                return clip_path
            else:
                print(f"[AI] 클립 저장 실패: {result.stderr}")
                return None

        except Exception as e:
            print(f"[AI] 클립 저장 실패: {e}")
            return None

    # ════════════════════════════════════════
    # 이미지 분석 (저장 없이 결과만)
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

        if yolo_boxes:
            best_box = max(yolo_boxes, key=lambda x: x["confidence"])
            dominant_vehicle = f"{best_box['class_name']} ({best_box['confidence']}%)"
        else:
            dominant_vehicle = None

        result = {
            **keras_result,
            "has_danger_car": len(yolo_boxes) > 0,
            "yolo_boxes": yolo_boxes,
            "detected_vehicle": dominant_vehicle,
            "yolo_detected": len(yolo_boxes) > 0,
            "event_id": None,
        }

        print(f"[AI] 이미지 분석 완료: {result}")
        return result

    # ════════════════════════════════════════
    # 이미지 분석 + 저장 (DB 연동)
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
        danger_label = "Danger Car: DETECTED" if len(yolo_boxes) > 0 else "Danger Car: None"
        weather_color = (0, 0, 255) if keras_result['is_danger'] else (0, 255, 0)
        danger_color = (0, 0, 255) if len(yolo_boxes) > 0 else (0, 255, 0)

        cv2.putText(frame, weather_label, (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.2, weather_color, 2)
        cv2.putText(frame, danger_label, (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 1.2, danger_color, 2)

        results_dir = os.path.join(STATIC_DIR, 'results')
        os.makedirs(results_dir, exist_ok=True)
        now_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        local_path = os.path.join(results_dir, f"weather_{now_str}.jpg")
        cv2.imwrite(local_path, frame)

        event_id = self._save_detection_event(keras_result, yolo_boxes)
        if event_id:
            self._save_detection_objects(event_id, yolo_boxes)

        print(f"[AI] 이미지 저장 완료: {local_path}")
        return {
            **keras_result,
            'has_danger_car': len(yolo_boxes) > 0,
            'yolo_boxes': yolo_boxes,
            'detected_vehicle': dominant_vehicle,
            'yolo_detected': len(yolo_boxes) > 0,
            'local_path': local_path,
            'event_id': event_id
        }

    # ════════════════════════════════════════
    # 영상 분석 (저장 없이 결과만)
    # ════════════════════════════════════════
    async def analyze_video_only(self, file: UploadFile, original_filename: str = "video.mp4") -> dict:
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
            vehicle_confidence = {}
            all_yolo_boxes = []
            first_danger_frame = None

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

                    yolo_boxes = self._run_yolo(frame, keras_result)

                    if len(yolo_boxes) > 0:
                        danger_car_frames += 1
                        all_yolo_boxes.extend(yolo_boxes)
                        if first_danger_frame is None:
                            first_danger_frame = frame_count

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
                    'danger_confidence': 0.0,
                    'detected_vehicle': None,
                    'yolo_boxes': [],
                    'weather_counts': weather_counts,
                    'analyzed_frames': 0,
                    'total_frames': total_frames,
                    'fps': fps,
                    'clip_path': None,
                    'original_filename': original_filename,
                    'message': '분석 실패: 영상에서 프레임을 읽을 수 없습니다.',
                }

            dominant_weather = max(weather_counts, key=weather_counts.get)
            is_danger = dominant_weather in DANGER_CLASSES
            has_danger_car = (danger_car_frames / max(1, analyzed_frame_count)) >= 0.2
            dominant_count = weather_counts[dominant_weather]
            avg_confidence = round(
                confidence_sum[dominant_weather] / max(1, dominant_count), 1,
            )

            if vehicle_counter:
                dominant_vehicle_name = vehicle_counter.most_common(1)[0][0]
                avg_vehicle_conf = round(
                    sum(vehicle_confidence[dominant_vehicle_name]) /
                    len(vehicle_confidence[dominant_vehicle_name]), 1,
                )
                dominant_vehicle = f"{dominant_vehicle_name} ({avg_vehicle_conf}%)"
            else:
                dominant_vehicle = None

            clip_path = None
            if first_danger_frame is not None and has_danger_car:
                clip_path = self._save_clip(
                    video_path=read_path,
                    trigger_frame=first_danger_frame,
                    fps=fps,
                    duration_sec=3,
                )

            print(
                f"[AI] 영상 분석 완료 | 최종 기상: {dominant_weather} "
                f"({avg_confidence}%) | 위험차량: {has_danger_car} | 대표 차종: {dominant_vehicle}"
            )

            return {
                'weather': dominant_weather,
                'confidence': avg_confidence,
                'is_danger': is_danger,
                'has_danger_car': has_danger_car,
                'danger_confidence': round(
                    danger_car_frames / max(1, analyzed_frame_count) * 100, 1,
                ),
                'detected_vehicle': dominant_vehicle,
                'yolo_boxes': all_yolo_boxes,
                'yolo_detected': len(all_yolo_boxes) > 0,
                'weather_counts': weather_counts,
                'analyzed_frames': analyzed_frame_count,
                'total_frames': total_frames,
                'fps': fps,
                'clip_path': clip_path,
                'original_filename': original_filename,
                'message': '중지됨' if self.stop_requested else '분석 완료',
            }

        finally:
            for path in [temp_input, converted_path]:
                if path and os.path.exists(path):
                    try:
                        os.remove(path)
                    except:
                        pass

    # ════════════════════════════════════════
    # 영상 분석 + 저장 (DB 연동)
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
            vehicle_confidence = {}
            all_yolo_boxes = []

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

                    yolo_boxes = self._run_yolo(frame, keras_result)
                    if len(yolo_boxes) > 0:
                        danger_car_frames += 1
                        all_yolo_boxes.extend(yolo_boxes)

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

            if vehicle_counter:
                dominant_vehicle_name = vehicle_counter.most_common(1)[0][0]
                avg_vehicle_conf = round(
                    sum(vehicle_confidence[dominant_vehicle_name]) / len(vehicle_confidence[dominant_vehicle_name]), 1
                )
                dominant_vehicle = f"{dominant_vehicle_name} ({avg_vehicle_conf}%)"
            else:
                dominant_vehicle = None

            final_keras_result = {
                'weather': dominant_weather,
                'confidence': avg_confidence,
                'is_danger': is_danger,
            }
            event_id = self._save_detection_event(final_keras_result, all_yolo_boxes)
            if event_id:
                self._save_detection_objects(event_id, all_yolo_boxes)

            print(f"[AI] 영상 분석 완료 | 최종 기상: {dominant_weather} ({avg_confidence}%) | 위험차량: {has_danger_car} | 대표 차종: {dominant_vehicle}")

            return {
                'weather': dominant_weather,
                'confidence': avg_confidence,
                'is_danger': is_danger,
                'has_danger_car': has_danger_car,
                'danger_confidence': round(danger_car_frames / max(1, analyzed_frame_count) * 100, 1),
                'detected_vehicle': dominant_vehicle,
                'weather_counts': weather_counts,
                'event_id': event_id,
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
                    weather_color = (0, 0, 255) if keras_result['is_danger'] else (0, 255, 0)

                    yolo_boxes = self._run_yolo(frame, keras_result)
                    has_danger = len(yolo_boxes) > 0
                    danger_label = "⚠️ 위험차량 감지됨" if has_danger else "✅ 위험차량 없음"
                    danger_color = (0, 0, 255) if has_danger else (0, 255, 0)

                    if has_danger:
                        now = time.time()
                        if not self.last_save_time or (now - self.last_save_time) >= self.save_interval:
                            self.last_save_time = now
                        else:
                            print(f"[DB] 스킵 (마지막 저장 후 {int(now - self.last_save_time)}초 경과)")

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