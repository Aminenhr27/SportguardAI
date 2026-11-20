"""
SportGuard AI - Suivi du squat avec MediaPipe (API Tasks)

Place ce fichier dans : vision/squat_tracker.py
Lancement (depuis la racine du projet, venv actif) :
    python vision/squat_tracker.py

Touche  q  pour terminer : le résultat est envoyé à l'API.
"""

import math
import time
import urllib.request
from collections import deque
from pathlib import Path

import cv2
import mediapipe as mp
import requests
from mediapipe.tasks.python import BaseOptions, vision
from mediapipe.tasks.python.vision import drawing_utils

# ---------- Réglages ----------
ATHLETE_ID = 1
API_URL = "http://127.0.0.1:8000"
MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
    "pose_landmarker_lite/float16/latest/pose_landmarker_lite.task"
)
MODEL_PATH = Path(__file__).parent / "pose_landmarker_lite.task"

UP_ANGLE = 160  # jambe quasi tendue
DOWN_ANGLE = 110  # genou assez plié pour compter une répétition
GOOD_DEPTH = 90  # profondeur "parfaite"

# Indices MediaPipe : (hanche, genou, cheville)
LEFT_LEG = (23, 25, 27)
RIGHT_LEG = (24, 26, 28)


def angle_at(a, b, c):
    """Angle (en degrés) au point b formé par a-b-c. Points en pixels (x, y)."""
    ba = (a[0] - b[0], a[1] - b[1])
    bc = (c[0] - b[0], c[1] - b[1])
    norm = math.hypot(*ba) * math.hypot(*bc)
    if norm == 0:
        return None
    cos = (ba[0] * bc[0] + ba[1] * bc[1]) / norm
    return math.degrees(math.acos(max(-1.0, min(1.0, cos))))


def depth_score(min_angle):
    """100 si le genou descend à 90° ou moins, puis -2.5 points par degré en plus."""
    if min_angle <= GOOD_DEPTH:
        return 100.0
    return max(0.0, 100.0 - (min_angle - GOOD_DEPTH) * 2.5)


def pick_leg(landmarks):
    """Choisit le côté (gauche ou droit) le mieux visible par la caméra."""

    def visibility(leg):
        return sum((landmarks[i].visibility or 0) for i in leg) / 3

    return LEFT_LEG if visibility(LEFT_LEG) >= visibility(RIGHT_LEG) else RIGHT_LEG


def knee_angle(landmarks, width, height):
    leg = pick_leg(landmarks)
    if min((landmarks[i].visibility or 0) for i in leg) < 0.5:
        return None  # jambe pas assez visible
    points = [(landmarks[i].x * width, landmarks[i].y * height) for i in leg]
    return angle_at(*points)


class SquatCounter:
    """Compte les squats : debout (> 160°) -> en bas (< 110°) -> debout."""

    def __init__(self):
        self.state = "up"
        self.reps = 0
        self.rep_min = None
        self.rep_angles = []
        self.rep_scores = []

    def update(self, angle):
        """Retourne True quand une répétition vient d'être terminée."""
        if self.state == "up":
            if angle < DOWN_ANGLE:
                self.state = "down"
                self.rep_min = angle
        else:
            self.rep_min = min(self.rep_min, angle)
            if angle > UP_ANGLE:
                self.state = "up"
                self.reps += 1
                self.rep_angles.append(self.rep_min)
                self.rep_scores.append(depth_score(self.rep_min))
                self.rep_min = None
                return True
        return False

    def summary(self):
        if self.reps == 0:
            return None
        return {
            "reps": self.reps,
            "avg_min_angle": round(float(sum(self.rep_angles) / self.reps), 1),
            "posture_score": round(float(sum(self.rep_scores) / self.reps), 1),
        }


def ensure_model():
    if MODEL_PATH.exists():
        return
    print("Téléchargement du modèle MediaPipe (une seule fois)...")
    urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
    print("Modèle téléchargé :", MODEL_PATH)


def send_result(summary):
    payload = {"athlete_id": ATHLETE_ID, "exercise": "squat", **summary}
    try:
        r = requests.post(f"{API_URL}/movements", json=payload, timeout=10)
    except requests.exceptions.ConnectionError:
        print("API injoignable : lance uvicorn puis réessaie.")
        return
    if r.status_code == 200:
        print("Analyse enregistrée :", r.json())
    else:
        print("Erreur API :", r.status_code, r.text)


def put_text(frame, text, y, color=(0, 255, 0)):
    cv2.putText(frame, text, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)


def main():
    try:
        requests.get(f"{API_URL}/health", timeout=3)
    except requests.exceptions.RequestException:
        print("API injoignable : lance d'abord uvicorn app.main:app --reload")
        return
    ensure_model()
    options = vision.PoseLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=str(MODEL_PATH)),
        running_mode=vision.RunningMode.VIDEO,
        num_poses=1,
    )

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Impossible d'ouvrir la webcam.")
        return

    counter = SquatCounter()
    recent = deque(maxlen=5)  # lissage de l'angle sur 5 images
    start = time.monotonic()
    last_ts = -1

    with vision.PoseLandmarker.create_from_options(options) as landmarker:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            frame = cv2.flip(frame, 1)
            height, width = frame.shape[:2]

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            ts = max(int((time.monotonic() - start) * 1000), last_ts + 1)
            last_ts = ts
            result = landmarker.detect_for_video(mp_image, ts)

            angle_text = "Angle genou : --"
            if result.pose_landmarks:
                landmarks = result.pose_landmarks[0]
                drawing_utils.draw_landmarks(
                    frame, landmarks, vision.PoseLandmarksConnections.POSE_LANDMARKS
                )
                raw = knee_angle(landmarks, width, height)
                if raw is not None:
                    recent.append(raw)
                    angle = sum(recent) / len(recent)
                    counter.update(angle)
                    angle_text = f"Angle genou : {int(angle)}"

            put_text(frame, f"Repetitions : {counter.reps}", 30)
            put_text(frame, angle_text, 60)
            if counter.rep_scores:
                put_text(frame, f"Derniere rep : {int(counter.rep_scores[-1])}/100", 90)
            cv2.imshow("SportGuard AI - Squat (q pour terminer)", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    cap.release()
    cv2.destroyAllWindows()

    summary = counter.summary()
    if summary is None:
        print("Aucune répétition détectée : rien n'est envoyé.")
        return
    print("Résumé :", summary)
    send_result(summary)


if __name__ == "__main__":
    main()