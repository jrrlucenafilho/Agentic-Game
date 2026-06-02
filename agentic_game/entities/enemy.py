from __future__ import annotations

import math
import random
from typing import List

import pygame

from ..config import WIDTH, HEIGHT, UFO_GREEN, WHITE, MISS
from .particle import Particle
from .player import Player


class UFOBeam:
    def __init__(self, x: float, y: float, target_x: float, target_y: float) -> None:
        dx = target_x - x
        dy = target_y - y
        dist = math.hypot(dx, dy)
        self.x = float(x)
        self.y = float(y)
        speed = 12
        self.vx = (dx / dist) * speed if dist > 0 else 0
        self.vy = (dy / dist) * speed if dist > 0 else 0
        self.rect = pygame.Rect(0, 0, 10, 10)
        self.done = False

    def update(self, players: List[Player]) -> object:
        self.x += self.vx
        self.y += self.vy
        self.rect.center = (int(self.x), int(self.y))
        for player in players:
            if player.alive and self.rect.colliderect(player.rect):
                return player
        if (
            self.x < -100
            or self.x > WIDTH + 100
            or self.y < -100
            or self.y > HEIGHT + 100
        ):
            self.done = True
            return MISS
        return None

    def draw(self, screen: pygame.Surface) -> None:
        cx, cy = int(self.x), int(self.y)
        for r in range(8, 0, -2):
            alpha = max(0, 80 - r * 10)
            s = pygame.Surface((r * 4, r * 4), pygame.SRCALPHA)
            pygame.draw.circle(s, (0, 255, 100, alpha), (r * 2, r * 2), r * 2)
            screen.blit(s, (cx - r * 2, cy - r * 2))
        pygame.draw.circle(screen, UFO_GREEN, (cx, cy), 4)
        pygame.draw.circle(screen, WHITE, (cx, cy), 2)


class UFO:
    def __init__(self) -> None:
        self.x = float(random.randint(150, WIDTH - 150))
        self.y = -60.0
        self.target_y = float(random.randint(80, HEIGHT // 3))
        self.vx = random.uniform(-0.8, 0.8)
        self.vy = 1.5
        self.state = "entering"
        self.shots_remaining = random.randint(3, 7)
        self.shot_cooldown = 60
        self.beams: List[UFOBeam] = []
        self.health = 5
        self.rect = pygame.Rect(0, 0, 60, 30)
        self.rect.center = (int(self.x), int(self.y))
        self.done = False

    def update(self, players: List[Player]) -> List[Particle] | None:
        if self.done:
            return None

        particles: List[Particle] = []

        if self.state == "entering":
            self.y += self.vy
            self.x += self.vx
            if self.y >= self.target_y:
                self.state = "attacking"
                self.shot_cooldown = 45
        elif self.state == "attacking":
            self.x += math.sin(pygame.time.get_ticks() * 0.003) * 0.3
            self.shot_cooldown -= 1
            if self.shot_cooldown <= 0 and self.shots_remaining > 0:
                alive = [p for p in players if p.alive]
                if alive:
                    target = random.choice(alive)
                    beam = UFOBeam(
                        self.x,
                        self.y,
                        target.rect.centerx,
                        target.rect.centery,
                    )
                    self.beams.append(beam)
                self.shots_remaining -= 1
                self.shot_cooldown = 50
            if self.shots_remaining <= 0 and not self.beams:
                self.state = "leaving"
        elif self.state == "leaving":
            self.y -= 3
            self.x += self.vx * 0.5
            if self.y < -150:
                self.done = True

        self.rect.center = (int(self.x), int(self.y))

        for i in range(len(self.beams) - 1, -1, -1):
            res = self.beams[i].update(players)
            if res is MISS or res is None:
                if self.beams[i].done:
                    self.beams.pop(i)
            elif isinstance(res, Player):
                p = res.die()
                if p:
                    particles.extend(p)
                self.beams.pop(i)

        return particles if particles else None

    def hit(self) -> List[Particle] | None:
        self.health -= 1
        if self.health <= 0:
            parts = [Particle(self.x, self.y, UFO_GREEN) for _ in range(25)]
            self.done = True
            self.beams.clear()
            return parts
        return None

    def draw(self, screen: pygame.Surface) -> None:
        for beam in self.beams:
            beam.draw(screen)

        if self.done:
            return

        cx, cy = int(self.x), int(self.y)

        glow = pygame.Surface((80, 30), pygame.SRCALPHA)
        pygame.draw.ellipse(glow, (0, 255, 100, 30), (0, 0, 80, 30))
        screen.blit(glow, (cx - 40, cy + 5))

        pygame.draw.ellipse(screen, (50, 120, 60), (cx - 30, cy - 8, 60, 18))
        pygame.draw.ellipse(screen, (80, 180, 100), (cx - 22, cy - 18, 44, 22))
        pygame.draw.ellipse(screen, (130, 230, 150), (cx - 18, cy - 20, 36, 16))
        pygame.draw.circle(screen, (200, 255, 220), (cx, cy - 10), 6)
        pygame.draw.circle(screen, WHITE, (cx, cy - 10), 3)

        for i in range(5):
            lx = cx - 20 + i * 10
            ly = cy + 2
            blink = int(abs(math.sin(pygame.time.get_ticks() * 0.005 + i)) * 200 + 55)
            pygame.draw.circle(screen, (255, 255, blink), (lx, ly), 2)

        pygame.draw.rect(screen, (100, 200, 120), (cx - 25, cy - 3, 6, 6))
        pygame.draw.rect(screen, (100, 200, 120), (cx + 19, cy - 3, 6, 6))
