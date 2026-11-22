import pygame
from pathlib import Path

# Asset paths, relative to this file so the game runs from any working directory
BASE_DIR = Path(__file__).resolve().parent.parent
GRAPHICS_DIR = BASE_DIR / "graphics"
SOUND_DIR = BASE_DIR / "sound"

# Game size
COLUMNS = 10
ROWS = 20
CELL_SIZE = 40
GAME_WIDTH, GAME_HEIGHT = COLUMNS * CELL_SIZE, ROWS * CELL_SIZE

# side bar size
SIDEBAR_WIDTH = 200
PREVIEW_HEIGHT_FRACTION = 0.7
SCORE_HEIGHT_FRACTION = 1 - PREVIEW_HEIGHT_FRACTION

# window
PADDING = 20
WINDOW_WIDTH = GAME_WIDTH + SIDEBAR_WIDTH + PADDING * 3
WINDOW_HEIGHT = GAME_HEIGHT + PADDING * 2

# camera panel, shown to the right of the sidebar when hand control is on
CAMERA_PANEL_WIDTH = 300
MODEL_DIR = BASE_DIR / "models"
TARGET_COLUMN_COLOR = (255, 255, 255, 35)

# game behaviour
UPDATE_START_SPEED = 500
MOVE_WAIT_TIME = 200
ROTATE_WAIT_TIME = 200
BLOCK_OFFSET = pygame.Vector2(COLUMNS // 2, -1)

# Colors
YELLOW = "#f1e60d"
RED = "#e51b20"
BLUE = "#204b9b"
GREEN = "#65b32e"
PURPLE = "#7b217f"
CYAN = "#6cc6d9"
ORANGE = "#f07e13"
GRAY = "#1C1C1C"
LINE_COLOR = "#FFFFFF"

# shapes
TETROMINOS = {
    "T": {"shape": [(0, 0), (-1, 0), (1, 0), (0, -1)], "color": PURPLE},
    "O": {"shape": [(0, 0), (0, -1), (1, 0), (1, -1)], "color": YELLOW},
    "J": {"shape": [(0, 0), (0, -1), (0, 1), (-1, 1)], "color": BLUE},
    "L": {"shape": [(0, 0), (0, -1), (0, 1), (1, 1)], "color": ORANGE},
    "I": {"shape": [(0, 0), (0, -1), (0, -2), (0, 1)], "color": CYAN},
    "S": {"shape": [(0, 0), (-1, 0), (0, -1), (1, -1)], "color": GREEN},
    "Z": {"shape": [(0, 0), (1, 0), (0, -1), (-1, -1)], "color": RED},
}

SCORE_DATA = {1: 40, 2: 100, 3: 300, 4: 1200}
