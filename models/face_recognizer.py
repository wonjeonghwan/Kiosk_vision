import torch
import face_recognition
import cv2
import numpy as np
from models.config import REQUIRED_FRAMES

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

face_stable_count = 0
temporary_encodings = []

def extract_face_embeddings(frame):
    global face_stable_count, temporary_encodings

    h, w, _ = frame.shape
    x1, y1, x2, y2 = w//3, h//4, 2*w//3, 3*h//4
    face_crop = frame[y1:y2, x1:x2]

    if face_crop is None or face_crop.size == 0:
        face_stable_count = max(0, face_stable_count - 1)
        temporary_encodings.clear()
        return None, (x1, y1, x2, y2), 0

    rgb_face = cv2.cvtColor(face_crop, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(rgb_face)
    encodings = face_recognition.face_encodings(rgb_face, face_locations)

    if encodings:
        largest_encoding = encodings[0]
        face_stable_count = min(REQUIRED_FRAMES, face_stable_count + 1)
        temporary_encodings.append(largest_encoding)

    progress = int((face_stable_count / REQUIRED_FRAMES) * 100)
    return largest_encoding if encodings else None, (x1, y1, x2, y2), progress
