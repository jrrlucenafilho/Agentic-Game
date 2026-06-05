from __future__ import annotations

from typing import Tuple

import pygame

from ..config import HEIGHT, WHITE, WIDTH
from ..rendering import background as bg

OPTIONS: Tuple[Tuple[str, str], ...] = (
    ("Jogar Local", "local"),
    ("Jogar Online", "online"),
    ("Sair", "quit"),
)


def run_menu(screen, clock, fonts) -> str:
    """Show the main menu. Returns 'local', 'online' or 'quit'."""
    big, mid, small = fonts
    sel = 0
    bg.generate()

    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return "quit"
            if e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_UP, pygame.K_w):
                    sel = (sel - 1) % len(OPTIONS)
                elif e.key in (pygame.K_DOWN, pygame.K_s):
                    sel = (sel + 1) % len(OPTIONS)
                elif e.key in (pygame.K_RETURN, pygame.K_SPACE):
                    return OPTIONS[sel][1]
                elif e.key == pygame.K_ESCAPE:
                    return "quit"

        bg.draw(screen)
        title = big.render("AGENTIC BATTLE", True, WHITE)
        screen.blit(title, title.get_rect(center=(WIDTH // 2, HEIGHT // 3 - 20)))
        sub = small.render("Slime Arena", True, (150, 200, 255))
        screen.blit(sub, sub.get_rect(center=(WIDTH // 2, HEIGHT // 3 + 30)))

        for i, (label, _) in enumerate(OPTIONS):
            chosen = i == sel
            color = (255, 230, 120) if chosen else WHITE
            text = ("> " + label + " <") if chosen else label
            surf = mid.render(text, True, color)
            screen.blit(surf, surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 + i * 64)))

        hint = small.render(
            "W/S ou setas para escolher  -  ENTER para confirmar", True, (170, 170, 195)
        )
        screen.blit(hint, hint.get_rect(center=(WIDTH // 2, HEIGHT - 70)))
        pygame.display.flip()
        clock.tick(60)
