import math
import random

import pygame

from ..config import WIDTH, HEIGHT, BG_COLOR


_star_positions = []
_saturn_surf = None
_planet_surf = None


def generate():
    global _star_positions, _saturn_surf, _planet_surf
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

    # Pixel art planet surface at the bottom
    pixel = 8
    planet_h = 400
    surf = pygame.Surface((WIDTH, planet_h), pygame.SRCALPHA)

    pl_cx = WIDTH // 2
    pl_radius = 1500
    pl_cy_below = pl_radius

    palette = [
        (60, 48, 38),
        (72, 58, 46),
        (85, 68, 54),
        (50, 40, 32),
        (38, 30, 24),
    ]

    for by in range(0, planet_h, pixel):
        rel_y = pl_cy_below - by
        if rel_y > pl_radius:
            continue
        half = int(math.sqrt(max(0, pl_radius * pl_radius - rel_y * rel_y)))
        half = (half // pixel) * pixel
        x1 = max(0, (pl_cx - half) // pixel * pixel)
        x2 = min(WIDTH, ((pl_cx + half) // pixel) * pixel + pixel)
        if x2 <= x1:
            continue

        depth = by / planet_h
        base_idx = min(3, int(depth * 4))

        for bx in range(x1, x2, pixel):
            seed = (bx // pixel) * 7 + (by // pixel) * 13
            var = seed % 7
            if var == 0 and depth > 0.4:
                c = palette[4]
            elif var == 1 or var == 4:
                c = palette[base_idx + 1] if base_idx < 3 else palette[3]
            else:
                c = palette[base_idx]
            surf.fill(c, (bx, by, pixel, pixel))

    craters = [
        (pl_cx - 260, planet_h - 70, 32),
        (pl_cx + 140, planet_h - 110, 24),
        (pl_cx - 80, planet_h - 170, 16),
        (pl_cx + 380, planet_h - 60, 12),
        (pl_cx - 420, planet_h - 100, 20),
        (pl_cx + 520, planet_h - 140, 14),
        (pl_cx - 180, planet_h - 230, 18),
        (pl_cx + 280, planet_h - 200, 10),
    ]
    for crx, cry, crr in craters:
        pygame.draw.circle(surf, (38, 30, 24), (crx, cry), crr)

    _planet_surf = surf


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

    if _planet_surf:
        screen.blit(_planet_surf, (0, HEIGHT - _planet_surf.get_height()))
