import pygame

# game size window
COLUMNS = 10 
ROWS = 20
CELL_SIZE = 35
GAME_WIDTH, GAME_HEIGHT = COLUMNS * CELL_SIZE, ROWS* CELL_SIZE

# side bar size
SIDEBAR_WIDTH = 200
PREVIEW_HEIGHT_FRACTION = 0.7
SCORE_HEIGHT_FRACTION = 1 - PREVIEW_HEIGHT_FRACTION

# window
PADDING = 20
WINDOW_WIDTH = GAME_WIDTH + SIDEBAR_WIDTH + PADDING * 3
WINDOW_HEIGHT =  GAME_HEIGHT + PADDING * 2

# colors
YELLOW = "#f1e60d"
RED = "#e51b20"
BLUE = "#204b9b"
GREEN = "#65b32e"
PURPLE = "#7b217f"
CYAN = "#6cc6d9"
ORANGE = "#f07e13"
GRAY = "#1C1C1C"
LINE_COLOR = "#FFFFFF"