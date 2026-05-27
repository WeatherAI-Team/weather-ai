# app/repositories/detection_object_repo.py
from app import db
from app.models.detection_object import DetectionObject


class DetectionObjectRepository:
    def create_detection_object(self, data: dict):
        detection_object = DetectionObject(**data)
        db.session.add(detection_object)

        return detection_object

    def create_detection_objects(self, objects: list[dict]):
        created = []

        for data in objects:
            created.append(self.create_detection_object(data))

        return created