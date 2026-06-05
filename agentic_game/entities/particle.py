from __future__ import annotations

import math
import random
from typing import List, Tuple

import pygame


class Particle:
    def __init__(
        self,
        x: float,
        y: float,
        color: tuple[int, int, int],
        vx: float | None = None,
        vy: float | None = None,
        life: int = 30,
        gravity: float = 0.2,
        size: int = 4,
    ) -> None:
        self.x = x
        self.y = y
        self.vx = random.uniform(-4, 4) if vx is None else vx
        self.vy = random.uniform(-4, 4) if vy is None else vy
        self.life = life
        self.max_life = life
        self.gravity = gravity
        self.size = size
        self.color = color

    def update(self) -> bool:
        self.x += self.vx
        self.y += self.vy
        self.vy += self.gravity
        self.life -= 1
        return self.life > 0

    def draw(self, screen: pygame.Surface) -> None:
        alpha = max(0, int(255 * (self.life / self.max_life)))
        s = self.size
        surf = pygame.Surface((s, s), pygame.SRCALPHA)
        surf.fill((*self.color, alpha))
        screen.blit(surf, (self.x - s / 2, self.y - s / 2))


def burst(
    x: float,
    y: float,
    color: Tuple[int, int, int],
    count: int,
    speed: float = 4.0,
    life: int = 20,
    gravity: float = 0.15,
    size: int = 3,
) -> List[Particle]:
    """Particles flying outward in every direction (impacts, jumps)."""
    parts: List[Particle] = []
    for _ in range(count):
        ang = random.uniform(0, 2 * math.pi)
        spd = random.uniform(0.3, 1.0) * speed
        parts.append(
            Particle(x, y, color, math.cos(ang) * spd, math.sin(ang) * spd, life, gravity, size)
        )
    return parts


def directional(
    x: float,
    y: float,
    color: Tuple[int, int, int],
    dx: float,
    dy: float,
    count: int,
    spread: float = 0.5,
    speed: float = 4.0,
    life: int = 16,
    gravity: float = 0.05,
    size: int = 3,
) -> List[Particle]:
    """Particles sprayed along a (dx, dy) direction (muzzle, sword, thrust)."""
    base = math.atan2(dy, dx)
    parts: List[Particle] = []
    for _ in range(count):
        ang = base + random.uniform(-spread, spread)
        spd = random.uniform(0.4, 1.0) * speed
        parts.append(
            Particle(x, y, color, math.cos(ang) * spd, math.sin(ang) * spd, life, gravity, size)
        )
    return parts
