"""Hand tracking input source: camera + MediaPipe Hand Landmarker in a thread.

The game loop never waits for the camera. The worker thread keeps the latest
gesture state and annotated frame; ``read()`` and ``preview_frame()`` just
copy them under a lock.
"""

import threading
import time
import urllib.request
from pathlib import Path

import cv2
import mediapipe as mp
from mediapipe.tasks import python as mp_tasks
from mediapipe.tasks.python import vision

from controls import Commands
from gestures import (
    OneEuroFilter,
    PinchDetector,
    hand_x,
    is_fist,
    pinch_ratio,
    x_to_column,
)

MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
    "hand_landmarker/float16/latest/hand_landmarker.task"
)

ROTATIONS = {
    0: None,
    90: cv2.ROTATE_90_CLOCKWISE,
    180: cv2.ROTATE_180,
    270: cv2.ROTATE_90_COUNTERCLOCKWISE,
}

# MediaPipe hand skeleton, for drawing
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (5, 9), (9, 10), (10, 11), (11, 12),
    (9, 13), (13, 14), (14, 15), (15, 16),
    (13, 17), (17, 18), (18, 19), (19, 20), (0, 17),
]


def ensure_model(path: Path) -> Path:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        print(f"Baixando o modelo de mão para {path} ...")
        urllib.request.urlretrieve(MODEL_URL, path)
    return path


def open_camera(source):
    """``source`` is a device index ("1") or a stream URL (DroidCam over Wi-Fi)."""
    if isinstance(source, str) and source.isdigit():
        source = int(source)
    if isinstance(source, int):
        cap = cv2.VideoCapture(source, cv2.CAP_DSHOW)
        if not cap.isOpened():
            cap = cv2.VideoCapture(source)
    else:
        cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        raise RuntimeError(f"Não consegui abrir a câmera: {source!r}")
    return cap


class HandInput:
    def __init__(self, source, columns, model_path, rotate=0, mirror=True):
        self.columns = columns
        self.rotation = ROTATIONS[rotate]
        self.mirror = mirror

        self.cap = open_camera(source)
        options = vision.HandLandmarkerOptions(
            base_options=mp_tasks.BaseOptions(
                model_asset_path=str(ensure_model(Path(model_path)))
            ),
            running_mode=vision.RunningMode.VIDEO,
            num_hands=1,
            min_hand_detection_confidence=0.6,
            min_hand_presence_confidence=0.6,
            min_tracking_confidence=0.5,
        )
        self.landmarker = vision.HandLandmarker.create_from_options(options)

        self.x_filter = OneEuroFilter(min_cutoff=1.2, beta=3.0)
        self.pinch = PinchDetector()

        # state shared with the game thread
        self.lock = threading.Lock()
        self.target_column = None
        self.soft_drop = False
        self.rotate_pending = False
        self.frame = None
        self.fps = 0.0
        self.latency_ms = 0.0

        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    # --- game side -------------------------------------------------------

    def read(self) -> Commands:
        with self.lock:
            rotate, self.rotate_pending = self.rotate_pending, False
            return Commands(
                rotate=rotate,
                soft_drop=self.soft_drop,
                target_column=self.target_column,
            )

    def preview_frame(self):
        """Latest annotated frame (RGB numpy array) or None."""
        with self.lock:
            return self.frame

    def stats(self):
        with self.lock:
            return self.fps, self.latency_ms

    def close(self):
        self.running = False
        self.thread.join(timeout=1)
        self.cap.release()
        self.landmarker.close()

    # --- worker side -----------------------------------------------------

    def _loop(self):
        start = time.perf_counter()
        last_ts = -1
        fps_t0, fps_n = time.perf_counter(), 0
        while self.running:
            ok, frame = self.cap.read()
            if not ok:
                time.sleep(0.01)
                continue
            t_capture = time.perf_counter()

            if self.rotation is not None:
                frame = cv2.rotate(frame, self.rotation)
            if self.mirror:
                frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # VIDEO mode needs strictly increasing timestamps
            ts = max(int((t_capture - start) * 1000), last_ts + 1)
            last_ts = ts
            result = self.landmarker.detect_for_video(
                mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb), ts
            )

            landmarks = None
            if result.hand_landmarks:
                landmarks = [(p.x, p.y) for p in result.hand_landmarks[0]]

            self._update_state(landmarks, t_capture)
            self._annotate(rgb, landmarks)

            fps_n += 1
            now = time.perf_counter()
            if now - fps_t0 >= 1.0:
                fps, fps_t0, fps_n = fps_n / (now - fps_t0), now, 0
            else:
                fps = None

            with self.lock:
                self.frame = rgb
                self.latency_ms = (now - t_capture) * 1000
                if fps is not None:
                    self.fps = fps

    def _update_state(self, landmarks, t):
        if landmarks is None:
            self.x_filter.reset()
            self.pinch.reset()
            with self.lock:
                self.target_column = None
                self.soft_drop = False
            return

        x = self.x_filter(hand_x(landmarks), t)
        column = x_to_column(x, self.columns)
        fist = is_fist(landmarks)
        # a closed fist also brings thumb and index together; don't count it as a pinch
        pinched = False if fist else self.pinch.update(pinch_ratio(landmarks))

        with self.lock:
            self.target_column = column
            self.soft_drop = fist
            if pinched:
                self.rotate_pending = True

    def _annotate(self, rgb, landmarks):
        h, w = rgb.shape[:2]
        if landmarks is None:
            cv2.putText(rgb, "mostre a mao", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 200, 0), 2)
            return
        pts = [(int(x * w), int(y * h)) for x, y in landmarks]
        for a, b in HAND_CONNECTIONS:
            cv2.line(rgb, pts[a], pts[b], (0, 255, 120), 2)
        for p in pts:
            cv2.circle(rgb, p, 4, (255, 255, 255), -1)
        # pinch points highlighted
        color = (255, 60, 60) if self.pinch.pinched else (255, 220, 0)
        cv2.circle(rgb, pts[4], 7, color, -1)
        cv2.circle(rgb, pts[8], 7, color, -1)
