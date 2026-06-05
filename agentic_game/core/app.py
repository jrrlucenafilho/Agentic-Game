"""Application shell: owns the window, shows the menu, and dispatches to
local play or the online client."""

from __future__ import annotations

import pygame

from ..config import HEIGHT, WIDTH
from ..systems import audio
from .game import Game
from .menu import run_menu


def main() -> None:
    pygame.mixer.pre_init(audio.SAMPLE_RATE, -16, 2, 512)
    pygame.init()
    audio.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Agentic Battle - Slime Arena")
    clock = pygame.time.Clock()
    fonts = (
        pygame.font.Font(None, 72),
        pygame.font.Font(None, 48),
        pygame.font.Font(None, 28),
    )

    while True:
        choice = run_menu(screen, clock, fonts)
        if choice == "quit":
            break
        if choice == "local":
            result = Game(screen=screen).run()
        else:
            # Imported lazily so local play never needs the network stack.
            from ..network.client import run_online_client
            result = run_online_client(screen, clock, fonts)
        if result == "quit":
            break

    pygame.quit()
