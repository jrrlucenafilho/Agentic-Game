import math
import random

import pygame

from ..config import WIDTH, HEIGHT
from ..entities.platform import Platform
from ..entities.player import Player


def create_platforms():
    platforms = []
    margin = 120
    min_dist = 200
    target = random.randint(10, 16)
    for _ in range(target * 5):
        if len(platforms) >= target:
            break
        x = random.randint(margin, WIDTH - margin)
        y = random.randint(80, HEIGHT - 80)
        too_close = any(
            math.sqrt((x - p.x) ** 2 + (y - p.y) ** 2) < min_dist + max(p.rx, p.ry)
            for p in platforms
        )
        if too_close:
            continue
        if random.random() < 0.45:
            radius = random.randint(28, 55)
            platforms.append(Platform(x, y, "circle", radius))
        else:
            rx = random.randint(50, 100)
            ry = random.randint(28, 55)
            angle = random.uniform(0, math.pi)
            platforms.append(Platform(x, y, "ellipse", rx, ry, angle))
    if len(platforms) < 4:
        for x, y in [
            (WIDTH // 3, HEIGHT // 3),
            (2 * WIDTH // 3, HEIGHT // 3),
            (WIDTH // 2, 2 * HEIGHT // 3),
        ]:
            platforms.append(Platform(x, y, "circle", 45))
    return platforms


def init_players(platforms):
    def spawn_top(plat):
        angle = -math.pi / 2
        r = plat.get_boundary_radius(angle)
        cx = plat.x + math.cos(angle) * (r + 18)
        cy = plat.y + math.sin(angle) * (r + 18)
        return cx - 12, cy - 12

    by_x = sorted(platforms, key=lambda p: p.x)
    idx1 = max(0, len(by_x) // 4 - 1)
    idx2 = min(len(by_x) - 1, 3 * len(by_x) // 4)
    p1_x, p1_y = spawn_top(by_x[idx1])
    p2_x, p2_y = spawn_top(by_x[idx2])

    return [
        Player(
            p1_x, p1_y, (255, 107, 107),
            {
                "left": pygame.K_a,
                "right": pygame.K_d,
                "up": pygame.K_w,
                "down": pygame.K_s,
                "shoot": pygame.K_f,
                "melee": pygame.K_g,
            },
            "P1",
        ),
        Player(
            p2_x, p2_y, (78, 205, 196),
            {
                "left": pygame.K_LEFT,
                "right": pygame.K_RIGHT,
                "up": pygame.K_UP,
                "down": pygame.K_DOWN,
                "shoot": pygame.K_l,
                "melee": pygame.K_k,
            },
            "P2",
        ),
    ]
