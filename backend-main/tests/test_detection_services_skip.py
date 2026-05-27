from app.services.keras_detection_service import run_keras_first_detection
from app.services.yolo_detection_service import run_yolo_detection


def test_keras_detection_skip_without_image():
    result = run_keras_first_detection(image_path=None)

    print(result)

    assert isinstance(result, dict)
    assert result["stage"] == "keras"
    assert result["used"] is False
    assert result["possible_risk"] is True


def test_yolo_detection_skip_without_image():
    result = run_yolo_detection(image_path=None)

    print(result)

    assert isinstance(result, dict)
    assert result["stage"] == "yolo"
    assert result["used"] is False
    assert result["dangerous_vehicle_detected"] is False
    assert "objects" in result
    assert "dangerous_objects" in result