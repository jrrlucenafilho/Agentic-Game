from __future__ import annotations

import math
import random
from typing import TYPE_CHECKING

import pygame

from ..config import HEIGHT, WIDTH
from ..rendering.asteroid import (
    add_spikes_to_asteroid,
    draw_circle_asteroid,
    draw_ellipse_asteroid_body,
    draw_gravity_ring,
    make_noise_func,
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
            self._noise = make_noise_func(int(self.x * 1009 + self.y * 7) & 0x7FFFFFFF)
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
            self._noise = make_noise_func(0)
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
            draw_gravity_ring(screen, self.x, self.y, self.gravity_range)

            if self.shape == "circle":
                draw_circle_asteroid(screen, cx, cy, self.size, self._noise)
                if self.spiky:
                    add_spikes_to_asteroid(
                        screen, self.x, self.y, self.spike_angles,
                        self.get_boundary_radius, spike_factor=self.spike_factor,
                    )
            else:
                max_r = int(self.size) + 20
                surf = pygame.Surface((max_r * 2, max_r * 2))
                surf.fill((0, 0, 0))
                surf.set_colorkey((0, 0, 0))
                lcx = lcy = max_r

                draw_ellipse_asteroid_body(surf, lcx, lcy, self.rx, self.ry, self.angle, self._noise)

                if self.spiky:
                    add_spikes_to_asteroid(
                        surf, lcx, lcy, self.spike_angles,
                        self.get_boundary_radius, angle_offset=self.angle,
                        spike_factor=self.spike_factor,
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
