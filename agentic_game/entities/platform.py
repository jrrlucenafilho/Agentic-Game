from __future__ import annotations

import math
from typing import TYPE_CHECKING

import pygame

from ..rendering.asteroid import draw_circle_asteroid, draw_ellipse_asteroid, draw_gravity_ring, make_noise_func

if TYPE_CHECKING:
    from .player import Player


class Platform:
    def __init__(
        self, x: float, y: float, shape: str, rx: int, ry: int | None = None, angle: float = 0
    ) -> None:
        self.x = x
        self.y = y
        self.shape = shape
        self.angle = angle
        self.rx = rx
        self.ry = ry if ry is not None else rx
        self.radius = rx if shape == "circle" else max(rx, self.ry)
        self.gravity_strength = 0.6
        self.gravity_range = self.radius * 3
        self._noise = make_noise_func(int(x * 1009 + y * 7) & 0x7FFFFFFF)
        self.vx = 0.0
        self.vy = 0.0

    def update(self) -> None:
        self.x += self.vx
        self.y += self.vy
        self.vx *= 0.82
        self.vy *= 0.82
        if abs(self.vx) < 0.1:
            self.vx = 0.0
        if abs(self.vy) < 0.1:
            self.vy = 0.0

    def get_boundary_radius(self, world_angle: float) -> float:
        if self.shape == "circle":
            return float(self.radius)
        local_angle = world_angle - self.angle
        c = math.cos(local_angle)
        s = math.sin(local_angle)
        return self.rx * self.ry / math.sqrt((self.ry * c) ** 2 + (self.rx * s) ** 2)

    def point_inside(self, px: float, py: float) -> bool:
        dx = px - self.x
        dy = py - self.y
        if self.shape == "circle":
            return dx * dx + dy * dy <= self.radius * self.radius
        c = math.cos(self.angle)
        s = math.sin(self.angle)
        lx = dx * c + dy * s
        ly = -dx * s + dy * c
        return (lx / self.rx) ** 2 + (ly / self.ry) ** 2 <= 1

    def collide_player(self, player: Player) -> None:
        if self.point_inside(player.rect.centerx, player.rect.centery):
            dx = player.rect.centerx - self.x
            dy = player.rect.centery - self.y
            if dx == 0 and dy == 0:
                dy = -1
            dist = math.sqrt(dx * dx + dy * dy)
            nx = dx / dist
            ny = dy / dist
            angle_to = math.atan2(dy, dx)
            push = self.get_boundary_radius(angle_to) + 12 - dist
            player.rect.x += nx * push
            player.rect.y += ny * push
            player.on_ground = True
            player.ground_nx = nx
            player.ground_ny = ny
            if player.vx * nx + player.vy * ny < 0:
                player.vy = 0
            if abs(nx) > 0.7:
                player.on_wall = 1 if nx > 0 else -1
            return
        cx = max(player.rect.left, min(self.x, player.rect.right))
        cy = max(player.rect.top, min(self.y, player.rect.bottom))
        if self.point_inside(cx, cy):
            dx = cx - self.x
            dy = cy - self.y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist == 0:
                return
            angle_to = math.atan2(dy, dx)
            overlap = self.get_boundary_radius(angle_to) - dist
            nx = dx / dist
            ny = dy / dist
            player.rect.x += nx * overlap
            player.rect.y += ny * overlap
            player.on_ground = True
            player.ground_nx = nx
            player.ground_ny = ny
            if player.vx * nx + player.vy * ny < 0:
                player.vy = 0
            if abs(nx) > 0.7:
                player.on_wall = 1 if nx > 0 else -1

    def draw(self, screen: pygame.Surface) -> None:
        draw_gravity_ring(screen, self.x, self.y, self.gravity_range)
        cx, cy = int(self.x), int(self.y)
        if self.shape == "circle":
            draw_circle_asteroid(screen, cx, cy, self.radius, self._noise)
        else:
            draw_ellipse_asteroid(screen, self.x, self.y, self.rx, self.ry, self.angle, self._noise)
