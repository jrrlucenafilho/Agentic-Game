from __future__ import annotations

import math
import random
from typing import TYPE_CHECKING, List

import pygame

from ..config import (
    BLACKHOLE_LAUNCH_COLOR,
    BLACKHOLE_LIFETIME,
    BLACKHOLE_PULL_RANGE,
    BLACKHOLE_PULL_STRENGTH,
    BLACKHOLE_RADIUS,
    BLACKHOLE_TELEPORT_COLOR,
    HEIGHT,
    WIDTH,
)
from .particle import Particle, burst

if TYPE_CHECKING:
    from .player import Player


class BlackHole:
    """A swirling singularity that pulls players in.

    kind == "teleport": warps the player to a random spot on the map.
    kind == "launch":   slingshots the player off in a random direction.
    """

    def __init__(self, kind: str = "teleport") -> None:
        self.kind = kind
        margin = 160
        self.x = float(random.randint(margin, WIDTH - margin))
        self.y = float(random.randint(margin, HEIGHT - margin))
        self.radius = BLACKHOLE_RADIUS
        self.pull_range = BLACKHOLE_PULL_RANGE
        self.strength = BLACKHOLE_PULL_STRENGTH
        self.color = (
            BLACKHOLE_TELEPORT_COLOR if kind == "teleport" else BLACKHOLE_LAUNCH_COLOR
        )
        self.life = BLACKHOLE_LIFETIME
        self.spin = random.uniform(0, math.tau)
        self.done = False
        self.rect = pygame.Rect(0, 0, self.radius * 2, self.radius * 2)
        self.rect.center = (int(self.x), int(self.y))

    def update(self) -> List[Particle] | None:
        if self.done:
            return None
        self.spin += 0.14
        self.life -= 1
        if self.life <= 0:
            self.done = True
            # Collapse puff when the singularity evaporates.
            return burst(self.x, self.y, self.color, 22, speed=5, life=26, gravity=0.0, size=3)
        return None

    def pull(self, player: Player) -> None:
        dx = self.x - player.rect.centerx
        dy = self.y - player.rect.centery
        dist = math.hypot(dx, dy)
        if 0 < dist < self.pull_range:
            t = dist / self.pull_range
            force = self.strength * (1 - t)
            player.vx += force * dx / dist
            player.vy += force * dy / dist

    def contains_center(self, player: Player) -> bool:
        dx = self.x - player.rect.centerx
        dy = self.y - player.rect.centery
        return dx * dx + dy * dy <= self.radius * self.radius

    def draw(self, screen: pygame.Surface) -> None:
        if self.done:
            return
        cx, cy = int(self.x), int(self.y)

        # Faint gravity well.
        pr = self.pull_range
        well = pygame.Surface((pr * 2, pr * 2), pygame.SRCALPHA)
        pygame.draw.circle(well, (*self.color, 14), (pr, pr), pr)
        screen.blit(well, (cx - pr, cy - pr))

        # Accretion swirl: a few spiral arms made of fading dots.
        arms = 3
        steps = 16
        for a in range(arms):
            base = self.spin + a * (math.tau / arms)
            for i in range(steps):
                t = i / steps
                ang = base + t * 4.5
                r = self.radius + 3 + t * self.radius * 1.7
                px = cx + math.cos(ang) * r
                py = cy + math.sin(ang) * r
                alpha = int(210 * (1 - t))
                sz = max(1, int(4 * (1 - t)) + 1)
                dot = pygame.Surface((sz * 2, sz * 2), pygame.SRCALPHA)
                pygame.draw.circle(dot, (*self.color, alpha), (sz, sz), sz)
                screen.blit(dot, (px - sz, py - sz))

        # Glow + black event horizon + bright core.
        gr = self.radius * 2
        glow = pygame.Surface((gr * 2, gr * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*self.color, 70), (gr, gr), self.radius + 6)
        screen.blit(glow, (cx - gr, cy - gr))
        pygame.draw.circle(screen, self.color, (cx, cy), self.radius + 2)
        pygame.draw.circle(screen, (0, 0, 0), (cx, cy), self.radius)
        pygame.draw.circle(screen, (255, 255, 255), (cx, cy), max(2, self.radius // 5))
