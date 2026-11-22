"""Tests for the input layer, run headless (no window, no audio)."""

import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pygame  # noqa: E402
import pytest  # noqa: E402

from controls import Commands  # noqa: E402
from settings import COLUMNS, WINDOW_HEIGHT, WINDOW_WIDTH  # noqa: E402


class FakeInput:
    """Input source whose commands the test sets directly."""

    def __init__(self):
        self.commands = Commands()

    def read(self):
        return self.commands


@pytest.fixture
def game(monkeypatch):
    pygame.init()
    pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    import game as game_module
    from game import Game

    # Game draws its first piece with random.choice; pin it to T so the
    # wall positions and the rotation below are deterministic
    monkeypatch.setattr(game_module, "choice", lambda seq: "T")
    fake = FakeInput()
    g = Game(lambda: "T", lambda *args: None, inputs=[fake])
    g.fake = fake
    yield g
    pygame.quit()


def pivot_column(game):
    return int(game.tetromino.blocks[0].pos.x)


def step_until_moves_stop(game, max_steps=50):
    """Run the input logic, letting the horizontal timer expire between steps."""
    for _ in range(max_steps):
        game.timers["horizontal move"].deactivate()
        before = pivot_column(game)
        game.input()
        if pivot_column(game) == before:
            return


def test_merge_combines_flags_and_keeps_first_target():
    merged = Commands(left=True, target_column=3).merge(
        Commands(rotate=True, target_column=7)
    )
    assert merged.left and merged.rotate
    assert not merged.right and not merged.soft_drop
    assert merged.target_column == 3


def test_target_column_slides_piece_to_the_left_wall(game):
    game.fake.commands = Commands(target_column=0)
    step_until_moves_stop(game)
    # T piece has a block left of the pivot, so the pivot stops at column 1
    assert pivot_column(game) == 1


def test_target_column_slides_piece_to_the_right_wall(game):
    game.fake.commands = Commands(target_column=COLUMNS - 1)
    step_until_moves_stop(game)
    assert pivot_column(game) == COLUMNS - 2


def test_target_column_stops_exactly_on_target(game):
    game.fake.commands = Commands(target_column=3)
    step_until_moves_stop(game)
    assert pivot_column(game) == 3


def test_left_right_override_target_column(game):
    start = pivot_column(game)
    game.fake.commands = Commands(right=True, target_column=0)
    game.input()
    assert pivot_column(game) == start + 1


def test_soft_drop_speeds_up_and_restores_fall(game):
    normal = game.timers["vertical move"].duration
    game.fake.commands = Commands(soft_drop=True)
    game.input()
    assert game.timers["vertical move"].duration < normal
    game.fake.commands = Commands()
    game.input()
    assert game.timers["vertical move"].duration == normal


def test_rotate_changes_block_positions(game):
    # move the piece away from the top edge before rotating
    for _ in range(3):
        game.tetromino.move_down()
    before = [tuple(b.pos) for b in game.tetromino.blocks]
    game.fake.commands = Commands(rotate=True)
    game.input()
    after = [tuple(b.pos) for b in game.tetromino.blocks]
    assert after != before
