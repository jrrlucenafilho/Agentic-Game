import math

import pygame

from ..config import MELEE_RANGE, WIDTH, HEIGHT, WHITE


class LaserBeam:
    def __init__(self, x, y, vx, vy, color, owner):
        self.x = float(x)
        self.y = float(y)
        self.vx = vx
        self.vy = vy
        self.color = color
        self.owner = owner
        self.rect = pygame.Rect(0, 0, 12, 12)
        self.rect.center = (int(x), int(y))
        self.trail = []

    def update(self, platforms, players):
        self.trail.append((self.x, self.y))
        if len(self.trail) > 6:
            self.trail.pop(0)

        self.x += self.vx
        self.y += self.vy
        self.rect.center = (int(self.x), int(self.y))

        hit = False
        for plat in platforms:
            cx = max(self.rect.left, min(plat.x, self.rect.right))
            cy = max(self.rect.top, min(plat.y, self.rect.bottom))
            if plat.point_inside(cx, cy):
                hit = True
                break
        if not hit:
            for player in players:
                if player.alive and player != self.owner:
                    if self.rect.colliderect(player.rect):
                        return player
        if (
            hit
            or self.x < -50
            or self.x > WIDTH + 50
            or self.y < -50
            or self.y > HEIGHT + 50
        ):
            return "miss"
        return None

    def draw(self, screen):
        for i, (tx, ty) in enumerate(self.trail):
            alpha = int(60 * (i / len(self.trail))) + 10
            r = 2 + i
            s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*self.color, alpha), (r, r), r)
            screen.blit(s, (int(tx - r), int(ty - r)))

        cx, cy = int(self.x), int(self.y)
        s = pygame.Surface((16, 16), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, 200), (8, 8), 6)
        pygame.draw.circle(s, WHITE, (8, 8), 3)
        screen.blit(s, (cx - 8, cy - 8))


class LightsaberSwipe:
    def __init__(self, x, y, aim_x, aim_y, color, owner):
        self.x = float(x)
        self.y = float(y)
        self.owner = owner
        self.color = color
        self.range = MELEE_RANGE
        self.lifetime = 10
        self.base_angle = math.atan2(aim_y, aim_x)
        self.hit_players = set()
        self.done = False

    def update(self, players):
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.done = True
            return None

        for player in players:
            if player.alive and player != self.owner and player not in self.hit_players:
                dx = player.rect.centerx - self.x
                dy = player.rect.centery - self.y
                dist = math.hypot(dx, dy)
                if dist <= self.range:
                    angle_to = math.atan2(dy, dx)
                    diff = (angle_to - self.base_angle + math.pi) % (
                        2 * math.pi
                    ) - math.pi
                    if abs(diff) <= math.pi / 3:
                        self.hit_players.add(player)
                        return player
        return None

    def draw(self, screen):
        if self.done:
            return

        cx, cy = int(self.x), int(self.y)
        progress = 1 - self.lifetime / 10
        total_sweep = math.pi * 0.8
        sweep = progress * total_sweep
        start_angle = self.base_angle - total_sweep / 2
        current_angle = start_angle + sweep
        r = self.range

        trail_steps = 5
        for i in range(trail_steps):
            t = (i + 1) / (trail_steps + 1)
            if t > progress:
                break
            trail_angle = start_angle + t * total_sweep
            trail_alpha = int(40 * (t / progress))
            trail_width = max(1, int(4 * (t / progress)))
            ex = cx + math.cos(trail_angle) * r
            ey = cy + math.sin(trail_angle) * r
            s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.line(
                s,
                (*self.color, trail_alpha),
                (r, r),
                (
                    int(r + math.cos(trail_angle) * r),
                    int(r + math.sin(trail_angle) * r),
                ),
                trail_width,
            )
            screen.blit(s, (cx - r, cy - r))

        ex = cx + math.cos(current_angle) * r
        ey = cy + math.sin(current_angle) * r
        for thickness, alpha in [(10, 30), (6, 80), (3, 200)]:
            s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.line(
                s,
                (*self.color, alpha),
                (r, r),
                (
                    int(r + math.cos(current_angle) * r),
                    int(r + math.sin(current_angle) * r),
                ),
                thickness,
            )
            screen.blit(s, (cx - r, cy - r))
