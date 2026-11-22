from settings import *
from sys import exit
import argparse

# components
from game import Game
from score import Score
from preview import Preview
from controls import KeyboardInput

from random import choice


def parse_args():
    parser = argparse.ArgumentParser(description="Tetris, com teclado ou com a mão")
    parser.add_argument(
        "--camera",
        help="ativa o controle por mão: índice da câmera (ex.: 1) ou URL do stream "
        "(ex.: http://192.168.0.17:4747/video)",
    )
    parser.add_argument(
        "--rotate", type=int, choices=[0, 90, 180, 270], default=0,
        help="gira a imagem da câmera (celular em pé costuma pedir 90)",
    )
    parser.add_argument(
        "--no-mirror", action="store_true", help="não espelha a imagem da câmera"
    )
    return parser.parse_args()


class Main:
    def __init__(self, args):

        # input sources
        self.hand = None
        inputs = [KeyboardInput()]
        if args.camera is not None:
            from hand_input import HandInput

            self.hand = HandInput(
                args.camera,
                COLUMNS,
                MODEL_DIR / "hand_landmarker.task",
                rotate=args.rotate,
                mirror=not args.no_mirror,
            )
            inputs.append(self.hand)

        # general
        pygame.init()
        width = WINDOW_WIDTH + (CAMERA_PANEL_WIDTH + PADDING if self.hand else 0)
        self.display_surface = pygame.display.set_mode((width, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()
        pygame.display.set_caption("Tetris")

        # shapes
        self.next_shapes = [choice(list(TETROMINOS.keys())) for shape in range(3)]

        # components
        self.game = Game(self.get_next_shape, self.update_score, inputs)
        self.score = Score()
        self.preview = Preview()
        self.camera_font = pygame.font.Font(GRAPHICS_DIR / "Russo_One.ttf", 15)

        # audio
        self.music = pygame.mixer.Sound(SOUND_DIR / "music.wav")
        self.music.set_volume(0.07)
        self.music.play(-1)

    def update_score(self, lines, score, level):
        self.score.lines = lines
        self.score.score = score
        self.score.level = level

    def get_next_shape(self):
        next_shape = self.next_shapes.pop(0)
        self.next_shapes.append(choice(list(TETROMINOS.keys())))
        return next_shape

    def draw_camera(self):
        rect = pygame.Rect(WINDOW_WIDTH, PADDING, CAMERA_PANEL_WIDTH, GAME_HEIGHT)
        pygame.draw.rect(self.display_surface, LINE_COLOR, rect, 2, 2)

        frame = self.hand.preview_frame()
        if frame is not None:
            h, w = frame.shape[:2]
            scale = min((rect.width - 8) / w, (rect.height - 60) / h)
            # numpy frames are (row, col); pygame surfaces are (x, y)
            surface = pygame.surfarray.make_surface(frame.swapaxes(0, 1))
            surface = pygame.transform.smoothscale(
                surface, (int(w * scale), int(h * scale))
            )
            self.display_surface.blit(
                surface, surface.get_rect(midtop=(rect.centerx, rect.top + 4))
            )

        fps, latency = self.hand.stats()
        lines = [
            f"camera {fps:4.1f} fps | {latency:3.0f} ms",
            "mao = mover   pinca = girar",
            "punho = descer",
        ]
        for i, text in enumerate(reversed(lines)):
            label = self.camera_font.render(text, True, LINE_COLOR)
            self.display_surface.blit(
                label, label.get_rect(midbottom=(rect.centerx, rect.bottom - 8 - 22 * i))
            )

    def run(self):
        try:
            while True:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        return

                # display
                self.display_surface.fill(GRAY)

                # components
                self.game.run()
                self.score.run()
                self.preview.run(self.next_shapes)
                if self.hand:
                    self.draw_camera()

                # updating the game
                pygame.display.update()
                self.clock.tick(60)
        finally:
            if self.hand:
                self.hand.close()
            pygame.quit()


if __name__ == "__main__":
    main = Main(parse_args())
    main.run()
    exit()
