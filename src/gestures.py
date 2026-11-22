"""Hand gesture logic, free of camera and model code so it can be unit tested.

Landmarks follow MediaPipe's 21-point hand model, as (x, y) pairs normalized to
the image: 0 = wrist, 4 = thumb tip, 8 = index tip, 9 = middle finger base,
12/16/20 = middle/ring/pinky tips.
"""

import math

WRIST, THUMB_TIP, INDEX_TIP, MIDDLE_MCP = 0, 4, 8, 9
FINGER_TIPS = (8, 12, 16, 20)

# Pinch: thumb-index distance relative to hand size, with hysteresis so a
# borderline pinch does not fire twice.
PINCH_ON = 0.30
PINCH_OFF = 0.45

# Fist: average fingertip-to-wrist distance relative to hand size.
FIST_ON = 1.10

# Only the central part of the image maps to the board, so the edge columns
# are reachable without the hand leaving the frame.
X_MIN, X_MAX = 0.20, 0.80


def distance(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def hand_size(landmarks):
    """Wrist to middle finger base: stable whether the hand is open or closed."""
    return max(distance(landmarks[WRIST], landmarks[MIDDLE_MCP]), 1e-6)


def pinch_ratio(landmarks):
    return distance(landmarks[THUMB_TIP], landmarks[INDEX_TIP]) / hand_size(landmarks)


def fist_ratio(landmarks):
    wrist = landmarks[WRIST]
    mean_tip = sum(distance(landmarks[t], wrist) for t in FINGER_TIPS) / len(FINGER_TIPS)
    return mean_tip / hand_size(landmarks)


def is_fist(landmarks):
    return fist_ratio(landmarks) < FIST_ON


def hand_x(landmarks):
    """Horizontal hand position, taken at the middle finger base."""
    return landmarks[MIDDLE_MCP][0]


def x_to_column(x, columns):
    t = (x - X_MIN) / (X_MAX - X_MIN)
    t = min(max(t, 0.0), 1.0)
    return min(int(t * columns), columns - 1)


class PinchDetector:
    """Turns the pinch ratio into one event per pinch (rising edge)."""

    def __init__(self):
        self.pinched = False

    def update(self, ratio):
        if not self.pinched and ratio < PINCH_ON:
            self.pinched = True
            return True
        if self.pinched and ratio > PINCH_OFF:
            self.pinched = False
        return False

    def reset(self):
        self.pinched = False


class OneEuroFilter:
    """Low-pass filter that smooths jitter at rest but follows fast moves.

    Casiez et al., "1 Euro Filter", CHI 2012.
    """

    def __init__(self, min_cutoff=1.0, beta=0.5, d_cutoff=1.0):
        self.min_cutoff = min_cutoff
        self.beta = beta
        self.d_cutoff = d_cutoff
        self.x_prev = None
        self.dx_prev = 0.0
        self.t_prev = None

    @staticmethod
    def _alpha(cutoff, dt):
        tau = 1.0 / (2 * math.pi * cutoff)
        return 1.0 / (1.0 + tau / dt)

    def __call__(self, x, t):
        if self.x_prev is None:
            self.x_prev, self.t_prev = x, t
            return x
        dt = max(t - self.t_prev, 1e-6)
        dx = (x - self.x_prev) / dt
        a_d = self._alpha(self.d_cutoff, dt)
        dx_hat = a_d * dx + (1 - a_d) * self.dx_prev
        cutoff = self.min_cutoff + self.beta * abs(dx_hat)
        a = self._alpha(cutoff, dt)
        x_hat = a * x + (1 - a) * self.x_prev
        self.x_prev, self.dx_prev, self.t_prev = x_hat, dx_hat, t
        return x_hat

    def reset(self):
        self.x_prev = None
        self.dx_prev = 0.0
        self.t_prev = None
