# tests/test_ai_detection_http_client.py

import requests

from app.services.keras_detection_service import run_keras_first_detection
from app.services.yolo_detection_service import run_yolo_detection


def test_keras_http_failure(monkeypatch):
    def fake_post(*args, **kwargs):
        raise requests.RequestException("AI server down")

    monkeypatch.setattr("requests.post", fake_post)

    result = run_keras_first_detection("test.jpg")

    assert result["stage"] == "keras"
    assert result["used"] is False
    assert result["possible_risk"] is True


def test_yolo_http_failure(monkeypatch):
    def fake_post(*args, **kwargs):
        raise requests.RequestException("AI server down")

    monkeypatch.setattr("requests.post", fake_post)

    result = run_yolo_detection("test.jpg")

    assert result["stage"] == "yolo"
    assert result["used"] is False
    assert result["dangerous_vehicle_detected"] is False
    assert result["objects"] == []
    assert result["dangerous_objects"] == []

def test_yolo_http_success(monkeypatch):
    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "yolo_boxes": [
                    {
                        "class_name": "Gas_Truck",
                        "confidence": 91.0,
                        "box_coords": [10, 20, 100, 200],
                    }
                ],
                "yolo_detected": True,
            }

    def fake_post(*args, **kwargs):
        return FakeResponse()

    monkeypatch.setattr("requests.post", fake_post)

    result = run_yolo_detection("test.jpg")

    assert result["used"] is True
    assert result["dangerous_vehicle_detected"] is True
    assert result["dangerous_objects"][0]["label"] == "Gas_Truck"

def test_keras_http_success(monkeypatch):
    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "weather": "heavy_rain",
                "confidence": 92.0,
                "is_danger": True,
                "has_danger_car": True,
                "danger_confidence": 88.0,
            }

    def fake_post(*args, **kwargs):
        return FakeResponse()

    monkeypatch.setattr("requests.post", fake_post)

    result = run_keras_first_detection("test.jpg")

    assert result["stage"] == "keras"
    assert result["used"] is True
    assert result["possible_risk"] is True
    assert result["confidence"] == 0.92
    assert result["label"] == "heavy_rain"
    assert result["danger_confidence"] == 0.88