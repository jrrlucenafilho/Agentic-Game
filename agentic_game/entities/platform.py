import math

import pygame

from ..config import TILE_SIZE, PLATFORM_COLOR, PLATFORM_TOP, PLATFORM_LINE


class Platform:
    def __init__(self, x, y, shape, rx, ry=None, angle=0):
        self.x = x
        self.y = y
        self.shape = shape
        self.angle = angle
        self.rx = rx
        self.ry = ry if ry is not None else rx
        if shape == "circle":
            self.radius = rx
        else:
            self.radius = max(rx, ry)
        self.gravity_strength = 0.6
        self.gravity_range = self.radius * 3

    def get_boundary_radius(self, world_angle):
        if self.shape == "circle":
            return self.radius
        local_angle = world_angle - self.angle
        c = math.cos(local_angle)
        s = math.sin(local_angle)
        return self.rx * self.ry / math.sqrt((self.ry * c) ** 2 + (self.rx * s) ** 2)

    def point_inside(self, px, py):
        dx = px - self.x
        dy = py - self.y
        if self.shape == "circle":
            return dx * dx + dy * dy <= self.radius * self.radius
        c = math.cos(self.angle)
        s = math.sin(self.angle)
        lx = dx * c + dy * s
        ly = -dx * s + dy * c
        return (lx / self.rx) ** 2 + (ly / self.ry) ** 2 <= 1

    def apply_gravity(self, player):
        dx = player.rect.centerx - self.x
        dy = player.rect.centery - self.y
        dist = math.sqrt(dx * dx + dy * dy)
        if 0 < dist < self.gravity_range:
            t = dist / self.gravity_range
            force = self.gravity_strength * (1 - t * t)
            player.vx -= force * dx / dist
            player.vy -= force * dy / dist
            return True
        return False

    def collide_player(self, player):
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

    def draw(self, screen):
        pygame.draw.circle(
            screen, (50, 55, 90), (int(self.x), int(self.y)), int(self.gravity_range), 2
        )
        if self.shape == "circle":
            for ring in range(1, 4):
                r = int(self.radius * (1 + ring * 0.5))
                if r <= self.gravity_range:
                    alpha = max(0, 60 - ring * 15)
                    s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                    pygame.draw.circle(s, (*PLATFORM_TOP[:3], alpha), (r, r), r, 1)
                    screen.blit(s, (self.x - r, self.y - r))
            pygame.draw.circle(
                screen, PLATFORM_COLOR, (int(self.x), int(self.y)), self.radius
            )
            pygame.draw.circle(
                screen, PLATFORM_TOP, (int(self.x), int(self.y)), self.radius, 3
            )
            for i in range(-self.radius + TILE_SIZE // 2, self.radius, TILE_SIZE):
                if abs(i) < self.radius:
                    h = int(math.sqrt(max(0, self.radius * self.radius - i * i)))
                    pygame.draw.line(
                        screen,
                        PLATFORM_LINE,
                        (self.x + i, self.y - h),
                        (self.x + i, self.y + h),
                        2,
                    )
        else:
            max_r = int(max(self.rx, self.ry)) + 10
            surf = pygame.Surface((max_r * 2, max_r * 2), pygame.SRCALPHA)
            cx = cy = max_r
            rect = pygame.Rect(cx - self.rx, cy - self.ry, self.rx * 2, self.ry * 2)
            pygame.draw.ellipse(surf, PLATFORM_COLOR, rect)
            pygame.draw.ellipse(surf, PLATFORM_TOP, rect, 3)
            for i in range(-self.rx + TILE_SIZE // 2, self.rx, TILE_SIZE):
                if abs(i) < self.rx:
                    h = int(self.ry * math.sqrt(max(0, 1 - (i / self.rx) ** 2)))
                    pygame.draw.line(
                        surf, PLATFORM_LINE, (cx + i, cy - h), (cx + i, cy + h), 2
                    )
            rotated = pygame.transform.rotate(surf, -math.degrees(self.angle))
            rect = rotated.get_rect(center=(self.x, self.y))
            screen.blit(rotated, rect)
