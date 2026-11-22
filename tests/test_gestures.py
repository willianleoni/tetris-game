"""Tests for the gesture logic, with synthetic hand landmarks."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from gestures import (  # noqa: E402
    OneEuroFilter,
    PinchDetector,
    is_fist,
    pinch_ratio,
    x_to_column,
)


def make_hand(open_fingers=True, pinch=False, cx=0.5):
    """21 landmarks for an upright hand centred at cx; hand size (0 -> 9) is 0.2."""
    pts = [(cx, 0.8)] * 21
    pts[9] = (cx, 0.6)  # middle finger base
    reach = 0.42 if open_fingers else 0.12  # fingertip distance from the wrist
    for i, tip in enumerate((8, 12, 16, 20)):
        pts[tip] = (cx - 0.06 + 0.04 * i, 0.8 - reach)
    pts[4] = (cx - 0.10, 0.65)  # thumb tip, away from the index
    if pinch:
        pts[4] = (pts[8][0] + 0.01, pts[8][1])
    return pts


def test_open_hand_is_not_a_fist():
    assert not is_fist(make_hand(open_fingers=True))


def test_closed_hand_is_a_fist():
    assert is_fist(make_hand(open_fingers=False))


def test_pinch_ratio_small_when_pinching():
    assert pinch_ratio(make_hand(pinch=True)) < 0.3
    assert pinch_ratio(make_hand(pinch=False)) > 0.45


def test_pinch_fires_once_per_pinch():
    detector = PinchDetector()
    events = [detector.update(r) for r in (0.8, 0.2, 0.2, 0.35, 0.2, 0.8, 0.2)]
    # 0.35 sits inside the hysteresis band, so the pinch is still held
    assert events == [False, True, False, False, False, False, True]


def test_x_to_column_covers_board_with_margins():
    assert x_to_column(0.0, 10) == 0
    assert x_to_column(0.2, 10) == 0
    assert x_to_column(0.53, 10) == 5  # middle of column 5, away from the 4|5 boundary
    assert x_to_column(0.8, 10) == 9
    assert x_to_column(1.0, 10) == 9


def test_one_euro_smooths_jitter():
    f = OneEuroFilter(min_cutoff=1.0, beta=0.0)
    out = [f(0.5 + (0.02 if i % 2 else -0.02), i / 30) for i in range(60)]
    # raw signal swings 0.04 peak to peak; filtered output much less
    assert max(out[30:]) - min(out[30:]) < 0.02
