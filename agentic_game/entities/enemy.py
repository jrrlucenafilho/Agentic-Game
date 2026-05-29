import math
import random

import pygame

from ..config import WIDTH, HEIGHT, UFO_GREEN, WHITE
from .particle import Particle
from .player import Player


class Meteor:
    def __init__(self):
        self.x = random.randint(0, WIDTH)
        self.y = random.randint(-100, -30)
        self.vx = random.uniform(-2, 2)
        self.vy = random.uniform(3, 8)
        self.size = random.randint(6, 16)

    def update(self, platforms, players):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.12

        for plat in platforms:
            if plat.point_inside(self.x, self.y):
                parts = []
                for _ in range(15):
                    parts.append(Particle(self.x, self.y, (255, 140, 40)))
                return parts

        for player in players:
            if player.alive and player.rect.collidepoint(self.x, self.y):
                result = player.die()
                parts = []
                for _ in range(15):
                    parts.append(Particle(self.x, self.y, (255, 140, 40)))
                if result:
                    parts.extend(result)
                return parts

        if self.y > HEIGHT + 100:
            return "miss"
        return None

    def draw(self, screen):
        g = self.size + 6
        glow = pygame.Surface((g * 2, g * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow, (255, 180, 50, 60), (g, g), g)
        screen.blit(glow, (self.x - g, self.y - g))

        pygame.draw.circle(
            screen, (180, 100, 50), (int(self.x), int(self.y)), self.size
        )
        pygame.draw.circle(
            screen, (240, 180, 80), (int(self.x), int(self.y)), self.size - 3
        )

        tail = min(self.size * 3, int(self.vy * 4))
        for i in range(tail):
            a = int(120 * (1 - i / tail))
            tx = self.x - self.vx / max(abs(self.vy), 0.5) * i * 1.2
            ty = self.y - self.vy / max(abs(self.vy), 0.5) * i * 1.2
            s = pygame.Surface((4, 4), pygame.SRCALPHA)
            s.fill((255, max(0, 200 - i * 6), 40, a))
            screen.blit(s, (tx - 2, ty - 2))


class UFOBeam:
    def __init__(self, x, y, target_x, target_y):
        dx = target_x - x
        dy = target_y - y
        dist = math.hypot(dx, dy)
        self.x = float(x)
        self.y = float(y)
        speed = 12
        self.vx = (dx / dist) * speed if dist > 0 else 0
        self.vy = (dy / dist) * speed if dist > 0 else 0
        self.rect = pygame.Rect(0, 0, 10, 10)

    def update(self, players):
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
            return "miss"
        return None

    def draw(self, screen):
        cx, cy = int(self.x), int(self.y)
        for r in range(8, 0, -2):
            alpha = max(0, 80 - r * 10)
            s = pygame.Surface((r * 4, r * 4), pygame.SRCALPHA)
            pygame.draw.circle(s, (0, 255, 100, alpha), (r * 2, r * 2), r * 2)
            screen.blit(s, (cx - r * 2, cy - r * 2))
        pygame.draw.circle(screen, UFO_GREEN, (cx, cy), 4)
        pygame.draw.circle(screen, WHITE, (cx, cy), 2)


class UFO:
    def __init__(self):
        self.x = float(random.randint(150, WIDTH - 150))
        self.y = -60.0
        self.target_y = float(random.randint(80, HEIGHT // 3))
        self.vx = random.uniform(-0.8, 0.8)
        self.vy = 1.5
        self.state = "entering"
        self.shots_remaining = random.randint(3, 7)
        self.shot_cooldown = 60
        self.beams = []
        self.health = 5
        self.rect = pygame.Rect(0, 0, 60, 30)
        self.rect.center = (int(self.x), int(self.y))
        self.done = False

    def update(self, players):
        if self.done:
            return None

        particles = []

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
            if res == "miss":
                self.beams.pop(i)
            elif isinstance(res, Player):
                p = res.die()
                if p:
                    particles.extend(p)
                self.beams.pop(i)

        if particles:
            return particles
        return None

    def hit(self):
        self.health -= 1
        if self.health <= 0:
            parts = []
            for _ in range(25):
                parts.append(Particle(self.x, self.y, UFO_GREEN))
            self.done = True
            self.beams.clear()
            return parts
        return None

    def draw(self, screen):
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
