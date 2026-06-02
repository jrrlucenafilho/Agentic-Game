from __future__ import annotations

import math
import random
from typing import TYPE_CHECKING

import pygame

from ..config import (
    ASTEROID_BODY,
    ASTEROID_CRATER,
    ASTEROID_EDGE,
    HEIGHT,
    WIDTH,
)
from .particle import Particle

if TYPE_CHECKING:
    from .player import Player
    from .platform import Platform


class Planetoid:
    def __init__(self, mode: str = "falling") -> None:
        self.mode = mode
        self.health = 1 if mode == "falling" else 3

        if mode == "moving":
            if random.random() < 0.55:
                self.shape = "ellipse"
                self.rx = random.randint(30, 60)
                self.ry = random.randint(20, 40)
                self.angle = random.uniform(0, math.pi)
            else:
                self.shape = "circle"
                self.rx = self.ry = random.randint(20, 40)
                self.angle = 0.0
            self.size = max(self.rx, self.ry)
            self.x = float(random.choice([-self.size - 10, WIDTH + self.size + 10]))
            self.y = float(random.randint(100, HEIGHT - 100))
            self.vx = random.uniform(1.5, 3.5) * (1 if self.x < 0 else -1)
            self.vy = 0.0
            self.gravity_strength = 0.6
            self.gravity_range = self.size * 4
            self._seed = int(self.x * 1009 + self.y * 7) & 0x7FFFFFFF
            self.spiky = random.random() < 0.4
            if self.spiky:
                self.spike_factor = 0.3
                self.num_spikes = max(8, self.size // 3)
                self.spike_half_angle = math.pi / self.num_spikes * 0.8
                step = 2 * math.pi / self.num_spikes
                self.spike_angles = [
                    i * step + random.uniform(-0.12, 0.12) for i in range(self.num_spikes)
                ]
        else:
            self.shape = "circle"
            self.rx = self.ry = random.randint(6, 16)
            self.angle = 0.0
            self.size = self.rx
            self.x = float(random.randint(0, WIDTH))
            self.y = float(random.randint(-100, -30))
            self.vx = random.uniform(-2, 2)
            self.vy = random.uniform(3, 8)
            self._seed = 0
            self.spiky = False

        self.rect = pygame.Rect(0, 0, self.size * 2, self.size * 2)
        self.rect.center = (int(self.x), int(self.y))
        self.done = False

    def get_boundary_radius(self, world_angle: float) -> float:
        if self.shape == "circle":
            return float(self.size)
        local_angle = world_angle - self.angle
        c = math.cos(local_angle)
        s = math.sin(local_angle)
        return self.rx * self.ry / math.sqrt((self.ry * c) ** 2 + (self.rx * s) ** 2)

    def point_inside(self, px: float, py: float) -> bool:
        dx = px - self.x
        dy = py - self.y
        if self.shape == "circle":
            return dx * dx + dy * dy <= self.size * self.size
        c = math.cos(self.angle)
        s = math.sin(self.angle)
        lx = dx * c + dy * s
        ly = -dx * s + dy * c
        return (lx / self.rx) ** 2 + (ly / self.ry) ** 2 <= 1

    def _noise(self, *args: int) -> int:
        h = self._seed
        for a in args:
            h = (h * 1000003 + a) & 0x7FFFFFFF
        return h % 10000

    def update(
        self, platforms: list[Platform], players: list[Player]
    ) -> list[Particle] | None:
        if self.done:
            return None

        if self.mode == "moving":
            self.x += self.vx

            for plat in platforms:
                dx = self.x - plat.x
                dy = self.y - plat.y
                dist = math.hypot(dx, dy)
                angle_to = math.atan2(dy, dx)
                br_a = self.get_boundary_radius(angle_to + math.pi)
                br_b = plat.get_boundary_radius(angle_to)
                if dist < br_a + br_b and dist > 0:
                    overlap = br_a + br_b - dist
                    nx = dx / dist
                    ny = dy / dist
                    plat.x -= nx * overlap * 0.5
                    plat.y -= ny * overlap * 0.5
                    self.x += nx * overlap * 0.5
                    self.y += ny * overlap * 0.5
                    dvn = self.vx * nx + self.vy * ny
                    if dvn < 0:
                        impulse = -dvn * 1.2
                        plat.vx -= nx * impulse
                        plat.vy -= ny * impulse
                        self.vx += nx * impulse
                        self.vy += ny * impulse

            if self.x < -self.size:
                self.x = -self.size
                self.vx = abs(self.vx)
            elif self.x > WIDTH + self.size:
                self.x = WIDTH + self.size
                self.vx = -abs(self.vx)
        else:
            self.x += self.vx
            self.y += self.vy
            self.vy += 0.12

            for plat in platforms:
                if plat.point_inside(self.x, self.y):
                    parts = [Particle(self.x, self.y, (255, 140, 40)) for _ in range(15)]
                    self.done = True
                    return parts

        self.rect.center = (int(self.x), int(self.y))

        if self.mode != "moving":
            for player in players:
                if player.alive and self.rect.colliderect(player.rect):
                    result = player.die()
                    parts = [Particle(self.x, self.y, (255, 140, 40)) for _ in range(15)]
                    if result:
                        parts.extend(result)
                    self.done = True
                    return parts

        if self.mode == "falling" and self.y > HEIGHT + 100:
            self.done = True
            return None

        return None

    def collide_player(self, player: Player) -> None:
        if self.mode != "moving" or self.done:
            return

        if self.spiky:
            dx = player.rect.centerx - self.x
            dy = player.rect.centery - self.y
            dist = math.hypot(dx, dy)
            if dist > 0:
                angle_to = math.atan2(dy, dx)
                br = self.get_boundary_radius(angle_to)
                if br < dist < br * (1 + self.spike_factor):
                    for sa in self.spike_angles:
                        diff = abs(angle_to - sa)
                        diff = min(diff, 2 * math.pi - diff)
                        if diff < self.spike_half_angle:
                            player.die()
                            return

        if not self.point_inside(player.rect.centerx, player.rect.centery):
            return
        dx = player.rect.centerx - self.x
        dy = player.rect.centery - self.y
        if dx == 0 and dy == 0:
            dy = -1
        dist = math.hypot(dx, dy)
        nx = dx / dist
        ny = dy / dist
        angle_to = math.atan2(dy, dx)
        push = self.get_boundary_radius(angle_to) + 12 - dist
        if push > 0:
            player.rect.x += nx * push
            player.rect.y += ny * push
            player.on_ground = True
            player.ground_nx = nx
            player.ground_ny = ny
            if player.vx * nx + player.vy * ny < 0:
                player.vy = 0
            if abs(nx) > 0.7:
                player.on_wall = 1 if nx > 0 else -1

    def hit(self, damage: int = 1) -> list[Particle] | None:
        self.health -= damage
        if self.health <= 0:
            self.done = True
            color = (100, 105, 110) if self.mode == "moving" else (255, 140, 40)
            return [Particle(self.x, self.y, color) for _ in range(20)]
        return None

    def draw(self, screen: pygame.Surface) -> None:
        if self.done:
            return

        cx, cy = int(self.x), int(self.y)

        if self.mode == "moving":
            n = self._noise

            gs = pygame.Surface(
                (int(self.gravity_range) * 2, int(self.gravity_range) * 2), pygame.SRCALPHA
            )
            pygame.draw.circle(
                gs,
                (200, 205, 215, 60),
                (int(self.gravity_range), int(self.gravity_range)),
                int(self.gravity_range),
                1,
            )
            screen.blit(gs, (int(self.x - self.gravity_range), int(self.y - self.gravity_range)))

            if self.shape == "circle":
                r = self.size

                pygame.draw.circle(screen, ASTEROID_BODY, (cx, cy), r)

                for a in range(0, 360, 12):
                    angle = math.radians(a + n(a) % 8 - 4)
                    vr = r * (0.88 + (n(a, 1) % 200) / 2000)
                    bx = cx + math.cos(angle) * vr
                    by = cy + math.sin(angle) * vr
                    sz = max(2, r // 10)
                    dv = n(a, 3) % 18
                    c = (
                        ASTEROID_BODY[0] - dv,
                        ASTEROID_BODY[1] - dv // 2,
                        ASTEROID_BODY[2] - dv // 2,
                    )
                    pygame.draw.circle(screen, c, (int(bx), int(by)), sz)

                pixel = 4
                for i in range(2 + n(0) % 3):
                    a = math.radians(n(i, 0) % 360)
                    d = r * (0.2 + (n(i, 1) % 100) / 250)
                    cr = max(3, int(r * (0.12 + (n(i, 2) % 100) / 600)))
                    crx = cx + math.cos(a) * d
                    cry = cy + math.sin(a) * d
                    cpx = (int(crx) // pixel) * pixel + pixel // 2
                    cpy = (int(cry) // pixel) * pixel + pixel // 2
                    rim_in = cr - 3
                    rim_out = cr + 1
                    for by in range(cpy - cr - pixel, cpy + cr + pixel, pixel):
                        for bx in range(cpx - cr - pixel, cpx + cr + pixel, pixel):
                            dx = bx + pixel // 2 - cpx
                            dy = by + pixel // 2 - cpy
                            dist_sq = dx * dx + dy * dy
                            if dist_sq < rim_in * rim_in:
                                screen.fill(ASTEROID_CRATER, (bx, by, pixel, pixel))
                            elif dist_sq < rim_out * rim_out:
                                screen.fill(ASTEROID_EDGE, (bx, by, pixel, pixel))

                if self.spiky:
                    for sa in self.spike_angles:
                        br = self.get_boundary_radius(sa)
                        tip = br * (1 + self.spike_factor)
                        tx = self.x + math.cos(sa) * tip
                        ty = self.y + math.sin(sa) * tip
                        base = br * 0.85
                        bx = self.x + math.cos(sa) * base
                        by = self.y + math.sin(sa) * base
                        pa = sa + math.pi / 2
                        hw = 3
                        bl = (bx + math.cos(pa) * hw, by + math.sin(pa) * hw)
                        br2 = (bx - math.cos(pa) * hw, by - math.sin(pa) * hw)
                        pygame.draw.polygon(
                            screen,
                            (180, 60, 60),
                            [(int(tx), int(ty)), (int(bl[0]), int(bl[1])), (int(br2[0]), int(br2[1]))],
                        )
                        pygame.draw.polygon(
                            screen,
                            (220, 100, 100),
                            [(int(tx), int(ty)), (int(bl[0]), int(bl[1])), (int(br2[0]), int(br2[1]))],
                            1,
                        )
            else:
                max_r = int(self.size) + 20

                surf = pygame.Surface((max_r * 2, max_r * 2))
                surf.fill((0, 0, 0))
                surf.set_colorkey((0, 0, 0))
                lcx = lcy = max_r
                rect = pygame.Rect(lcx - self.rx, lcy - self.ry, self.rx * 2, self.ry * 2)

                pygame.draw.ellipse(surf, ASTEROID_BODY, rect)

                for a in range(0, 360, 15):
                    local_a = math.radians(a)
                    world_a = local_a + self.angle
                    br = self.get_boundary_radius(world_a)
                    vr = br * (0.85 + (n(a, 7) % 250) / 2000)
                    bx = lcx + math.cos(local_a) * vr
                    by = lcy + math.sin(local_a) * vr
                    sz = max(2, int(br // 8))
                    dv = n(a, 9) % 18
                    c = (
                        ASTEROID_BODY[0] - dv,
                        ASTEROID_BODY[1] - dv // 2,
                        ASTEROID_BODY[2] - dv // 2,
                    )
                    pygame.draw.circle(surf, c, (int(bx), int(by)), sz)

                pixel = 4
                for i in range(1 + n(1) % 3):
                    a = math.radians(n(i, 3) % 360)
                    d = n(i, 4) % 100 / 100
                    crx = lcx + math.cos(a) * self.rx * d * 0.7
                    cry = lcy + math.sin(a) * self.ry * d * 0.7
                    cr = max(3, int(min(self.rx, self.ry) * (0.12 + (n(i, 5) % 100) / 600)))
                    cpx = (int(crx) // pixel) * pixel + pixel // 2
                    cpy = (int(cry) // pixel) * pixel + pixel // 2
                    rim_in = cr - 3
                    rim_out = cr + 1
                    for by in range(cpy - cr - pixel, cpy + cr + pixel, pixel):
                        for bx in range(cpx - cr - pixel, cpx + cr + pixel, pixel):
                            dx = bx + pixel // 2 - cpx
                            dy = by + pixel // 2 - cpy
                            dist_sq = dx * dx + dy * dy
                            if dist_sq < rim_in * rim_in:
                                surf.fill(ASTEROID_CRATER, (bx, by, pixel, pixel))
                            elif dist_sq < rim_out * rim_out:
                                surf.fill(ASTEROID_EDGE, (bx, by, pixel, pixel))

                if self.spiky:
                    for sa in self.spike_angles:
                        br = self.get_boundary_radius(sa + self.angle)
                        tip = br * (1 + self.spike_factor)
                        tx = lcx + math.cos(sa) * tip
                        ty = lcy + math.sin(sa) * tip
                        base = br * 0.85
                        bx = lcx + math.cos(sa) * base
                        by = lcy + math.sin(sa) * base
                        pa = sa + math.pi / 2
                        hw = 3
                        bl = (bx + math.cos(pa) * hw, by + math.sin(pa) * hw)
                        br2 = (bx - math.cos(pa) * hw, by - math.sin(pa) * hw)
                        pygame.draw.polygon(
                            surf,
                            (180, 60, 60),
                            [(int(tx), int(ty)), (int(bl[0]), int(bl[1])), (int(br2[0]), int(br2[1]))],
                        )
                        pygame.draw.polygon(
                            surf,
                            (220, 100, 100),
                            [(int(tx), int(ty)), (int(bl[0]), int(bl[1])), (int(br2[0]), int(br2[1]))],
                            1,
                        )

                rotated = pygame.transform.rotate(surf, -math.degrees(self.angle))
                r_rect = rotated.get_rect(center=(self.x, self.y))
                screen.blit(rotated, r_rect)
        else:
            g = self.size + 6
            glow = pygame.Surface((g * 2, g * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow, (255, 180, 50, 60), (g, g), g)
            screen.blit(glow, (cx - g, cy - g))

            pygame.draw.circle(screen, (180, 100, 50), (cx, cy), self.size)
            pygame.draw.circle(screen, (240, 180, 80), (cx, cy), self.size - 3)

            tail = min(self.size * 3, int(self.vy * 4))
            for i in range(tail):
                a = int(120 * (1 - i / tail))
                tx = self.x - self.vx / max(abs(self.vy), 0.5) * i * 1.2
                ty = self.y - self.vy / max(abs(self.vy), 0.5) * i * 1.2
                s = pygame.Surface((4, 4), pygame.SRCALPHA)
                s.fill((255, max(0, 200 - i * 6), 40, a))
                screen.blit(s, (int(tx - 2), int(ty - 2)))
