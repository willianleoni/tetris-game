"""Input sources for the game.

Every source (keyboard now, hand tracking later) turns what the player is doing
into a ``Commands`` snapshot once per frame. ``Game`` merges the snapshots of
all sources, so the keyboard keeps working alongside any other controller.
"""

from dataclasses import dataclass

import pygame


@dataclass
class Commands:
    """What the player wants to do in the current frame."""

    left: bool = False
    right: bool = False
    rotate: bool = False
    soft_drop: bool = False
    # Absolute column the piece should slide to (used by hand tracking).
    # Ignored while left/right is requested.
    target_column: int | None = None

    def merge(self, other: "Commands") -> "Commands":
        return Commands(
            left=self.left or other.left,
            right=self.right or other.right,
            rotate=self.rotate or other.rotate,
            soft_drop=self.soft_drop or other.soft_drop,
            target_column=(
                self.target_column
                if self.target_column is not None
                else other.target_column
            ),
        )


class KeyboardInput:
    """Arrow keys: left/right move, up rotates, down drops faster."""

    def read(self) -> Commands:
        keys = pygame.key.get_pressed()
        return Commands(
            left=keys[pygame.K_LEFT],
            right=keys[pygame.K_RIGHT],
            rotate=keys[pygame.K_UP],
            soft_drop=keys[pygame.K_DOWN],
        )
