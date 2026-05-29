import random

import pygame

from ..config import WIDTH, HEIGHT, BG_COLOR


_star_positions = []
_saturn_surf = None


def generate():
    global _star_positions, _saturn_surf
    _star_positions = []
    for _ in range(250):
        x = random.randint(0, WIDTH)
        y = random.randint(0, HEIGHT)
        r = random.random()
        if r < 0.6:
            size = 1
        elif r < 0.85:
            size = 2
        else:
            size = 3
        bright = random.randint(80, 255)
        _star_positions.append((x, y, size, bright))

    pw, ph = 32, 24
    surf = pygame.Surface((pw, ph), pygame.SRCALPHA)
    body_c = (220, 190, 140)
    ring_c = (200, 180, 140, 140)
    dark_c = (180, 150, 110)
    cx, cy = pw // 2 - 1, ph // 2

    pygame.draw.circle(surf, body_c, (cx, cy), 7)
    pygame.draw.circle(surf, (200, 170, 120), (cx, cy), 7, 1)
    pygame.draw.rect(surf, dark_c, (cx - 6, cy - 2, 12, 1))
    pygame.draw.rect(surf, dark_c, (cx - 5, cy + 2, 10, 1))
    pygame.draw.ellipse(surf, ring_c, (cx - 12, cy - 4, 24, 8), 1)

    _saturn_surf = pygame.transform.scale(surf, (pw * 4, ph * 4))
    _saturn_surf.set_alpha(50)


def draw(screen):
    screen.fill(BG_COLOR)
    for x, y, size, bright in _star_positions:
        shade = (bright, bright, bright)
        if size == 1:
            screen.set_at((x, y), shade)
        elif size == 2:
            pygame.draw.rect(screen, shade, (x, y, 2, 2))
        else:
            pygame.draw.rect(screen, shade, (x, y, 3, 3))

    if _saturn_surf:
        sx = WIDTH - _saturn_surf.get_width() - 60
        sy = 60
        screen.blit(_saturn_surf, (sx, sy))
