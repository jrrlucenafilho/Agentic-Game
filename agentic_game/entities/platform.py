import math

import pygame


ASTEROID_BODY = (70, 75, 80)
ASTEROID_EDGE = (92, 96, 100)
ASTEROID_SHADOW = (24, 26, 28)
ASTEROID_CRATER = (18, 20, 22)
ASTEROID_HIGHLIGHT = (110, 115, 120)


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
        self._seed = int(x * 1009 + y * 7) & 0x7FFFFFFF

    def _noise(self, *args):
        h = self._seed
        for a in args:
            h = (h * 1000003 + a) & 0x7FFFFFFF
        return h % 10000

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
        s = pygame.Surface((int(self.gravity_range) * 2, int(self.gravity_range) * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (200, 205, 215, 60), (int(self.gravity_range), int(self.gravity_range)), int(self.gravity_range), 1)
        screen.blit(s, (int(self.x - self.gravity_range), int(self.y - self.gravity_range)))
        if self.shape == "circle":
            self._draw_circle_asteroid(screen)
        else:
            self._draw_ellipse_asteroid(screen)

    def _draw_circle_asteroid(self, screen):
        r = self.radius
        cx, cy = int(self.x), int(self.y)
        n = self._noise

        pygame.draw.circle(screen, ASTEROID_BODY, (cx, cy), r)

        # Rocky edge bumps
        for a in range(0, 360, 12):
            angle = math.radians(a + n(a) % 8 - 4)
            vr = r * (0.88 + (n(a, 1) % 200) / 2000)
            bx = cx + math.cos(angle) * vr
            by = cy + math.sin(angle) * vr
            sz = max(2, r // 10)
            dv = n(a, 3) % 18
            c = (ASTEROID_BODY[0] - dv, ASTEROID_BODY[1] - dv // 2, ASTEROID_BODY[2] - dv // 2)
            pygame.draw.circle(screen, c, (int(bx), int(by)), sz)

        # Craters (pixel-art holes in the texture)
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

    def _draw_ellipse_asteroid(self, screen):
        max_r = int(max(self.rx, self.ry)) + 20
        surf = pygame.Surface((max_r * 2, max_r * 2))
        surf.fill((0, 0, 0))
        surf.set_colorkey((0, 0, 0))
        lcx = lcy = max_r
        n = self._noise
        rect = pygame.Rect(lcx - self.rx, lcy - self.ry, self.rx * 2, self.ry * 2)

        pygame.draw.ellipse(surf, ASTEROID_BODY, rect)

        # Edge bumps in local space
        for a in range(0, 360, 15):
            local_a = math.radians(a)
            world_a = local_a + self.angle
            br = self.get_boundary_radius(world_a)
            vr = br * (0.85 + (n(a, 7) % 250) / 2000)
            bx = lcx + math.cos(local_a) * vr
            by = lcy + math.sin(local_a) * vr
            sz = max(2, int(br // 8))
            dv = n(a, 9) % 18
            c = (ASTEROID_BODY[0] - dv, ASTEROID_BODY[1] - dv // 2, ASTEROID_BODY[2] - dv // 2)
            pygame.draw.circle(surf, c, (int(bx), int(by)), sz)

        # Craters (pixel-art holes in the texture)
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

        rotated = pygame.transform.rotate(surf, -math.degrees(self.angle))
        rect = rotated.get_rect(center=(self.x, self.y))
        screen.blit(rotated, rect)
