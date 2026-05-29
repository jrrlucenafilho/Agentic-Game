import math
import random
import sys

import pygame

pygame.init()

WIDTH, HEIGHT = 1400, 900
TILE_SIZE = 32
FPS = 60

GRAVITY = 0.15
JUMP_FORCE = 30
MOVE_SPEED = 5
ARROW_SPEED = 10
ARROW_COOLDOWN = 500
METEOR_START = 600

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Agentic Battle - Slime Arena")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 36)
big_font = pygame.font.Font(None, 72)
small_font = pygame.font.Font(None, 28)

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BG_COLOR = (8, 10, 30)
BG_DARK = (22, 33, 62)
PLATFORM_COLOR = (74, 78, 105)
PLATFORM_TOP = (154, 140, 152)
PLATFORM_LINE = (34, 34, 59)
ARROW_SHAFT = (139, 69, 19)
ARROW_HEAD = (160, 82, 45)


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

    def draw(self):
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


class Player:
    def __init__(self, x, y, color, controls, name):
        self.rect = pygame.Rect(x, y, 28, 28)
        self.vx = 0
        self.vy = 0
        self.color = color
        self.controls = controls
        self.name = name
        self.alive = True
        self.on_ground = False
        self.on_wall = 0
        self.last_shot = 0
        self.facing = 1
        self.spawn_pos = (x, y)
        self.ground_nx = 0
        self.ground_ny = -1
        self.gravity_nx = 0
        self.gravity_ny = 0

    def update(self, keys, platforms):
        if not self.alive:
            return

        ctrl = self.controls

        if self.on_ground:
            tx = -self.ground_ny
            ty = self.ground_nx

            if keys[ctrl["left"]]:
                self.vx = -tx * MOVE_SPEED
                self.vy = -ty * MOVE_SPEED
                self.facing = -1
            elif keys[ctrl["right"]]:
                self.vx = tx * MOVE_SPEED
                self.vy = ty * MOVE_SPEED
                self.facing = 1
            else:
                self.vx *= 0.8
                self.vy *= 0.8

            if keys[ctrl["up"]]:
                self.vx = self.ground_nx * JUMP_FORCE
                self.vy = self.ground_ny * JUMP_FORCE
                self.on_ground = False
        else:
            in_field = self.gravity_nx != 0 or self.gravity_ny != 0
            if in_field:
                tx = self.gravity_ny
                ty = -self.gravity_nx
                if keys[ctrl["left"]]:
                    self.vx = -tx * MOVE_SPEED
                    self.vy = -ty * MOVE_SPEED
                    self.facing = -1
                elif keys[ctrl["right"]]:
                    self.vx = tx * MOVE_SPEED
                    self.vy = ty * MOVE_SPEED
                    self.facing = 1
                else:
                    self.vx *= 0.8
                    self.vy *= 0.8
            else:
                if keys[ctrl["left"]]:
                    self.vx = -MOVE_SPEED
                    self.facing = -1
                elif keys[ctrl["right"]]:
                    self.vx = MOVE_SPEED
                    self.facing = 1
            self.vy += GRAVITY

        in_gravity_field = False
        self.gravity_nx = 0
        self.gravity_ny = 0
        max_gravity_force = 0
        for plat in platforms:
            dx = self.rect.centerx - plat.x
            dy = self.rect.centery - plat.y
            dist = math.sqrt(dx * dx + dy * dy)
            if 0 < dist < plat.gravity_range:
                in_gravity_field = True
                t = dist / plat.gravity_range
                force = plat.gravity_strength * (1 - t * t)
                if force > max_gravity_force and force >= 0.05:
                    max_gravity_force = force
                    self.gravity_nx = -dx / dist
                    self.gravity_ny = -dy / dist
                if not self.on_ground:
                    self.vx -= force * dx / dist
                    self.vy -= force * dy / dist

        self.on_ground = False
        self.on_wall = 0

        self.rect.x += self.vx
        self.rect.y += self.vy
        for plat in platforms:
            plat.collide_player(self)

        if self.rect.y > HEIGHT + 100:
            self.die()

    def shoot(self):
        now = pygame.time.get_ticks()
        if now - self.last_shot < ARROW_COOLDOWN:
            return None
        self.last_shot = now
        if self.on_ground:
            tx = -self.ground_ny * self.facing
            ty = self.ground_nx * self.facing
        else:
            tx = self.facing
            ty = 0
        arrow_x = self.rect.centerx + tx * 12
        arrow_y = self.rect.centery + ty * 12
        return Arrow(arrow_x, arrow_y, ARROW_SPEED * tx, ARROW_SPEED * ty, self)

    def die(self):
        if not self.alive:
            return
        self.alive = False
        particles = []
        for _ in range(20):
            particles.append(
                Particle(
                    self.rect.x + self.rect.w // 2,
                    self.rect.y + self.rect.h // 2,
                    self.color,
                )
            )
        return particles

    def respawn(self):
        self.rect.x, self.rect.y = self.spawn_pos
        self.vx = 0
        self.vy = 0
        self.alive = True
        self.on_ground = False

    def draw(self):
        if not self.alive:
            return

        if self.on_ground:
            tx = -self.ground_nx
            ty = -self.ground_ny
        elif self.gravity_nx != 0 or self.gravity_ny != 0:
            tx = self.gravity_nx
            ty = self.gravity_ny
        else:
            tx = 0
            ty = 0

        if tx != 0 or ty != 0:
            surf_size = 40
            surf = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
            center = surf_size // 2
            pygame.draw.circle(surf, self.color, (center, center), 14)
            eye_x = center + (5 if self.facing > 0 else -5)
            pygame.draw.circle(surf, BLACK, (eye_x, center - 2), 4)
            pygame.draw.circle(
                surf, WHITE, (eye_x + (1 if self.facing > 0 else -1), center - 1), 2
            )
            s = pygame.Surface((8, 4), pygame.SRCALPHA)
            s.fill((*self.color, 220))
            surf.blit(s, (center - 10, center - 18))
            s2 = pygame.Surface((6, 6), pygame.SRCALPHA)
            s2.fill((*self.color, 220))
            surf.blit(s2, (center - 2, center - 20))
            angle = math.degrees(math.atan2(ty, tx) - math.pi / 2)
            surf = pygame.transform.rotate(surf, angle)
            rect = surf.get_rect(center=self.rect.center)
            screen.blit(surf, rect)
        else:
            cx, cy = self.rect.centerx, self.rect.centery
            pygame.draw.circle(screen, self.color, (cx, cy), 14)
            eye_x = cx + (5 if self.facing > 0 else -5)
            pygame.draw.circle(screen, BLACK, (eye_x, cy - 2), 4)
            pygame.draw.circle(
                screen, WHITE, (eye_x + (1 if self.facing > 0 else -1), cy - 1), 2
            )
            s = pygame.Surface((8, 4), pygame.SRCALPHA)
            s.fill((*self.color, 220))
            screen.blit(s, (cx - 10, cy - 18))
            s2 = pygame.Surface((6, 6), pygame.SRCALPHA)
            s2.fill((*self.color, 220))
            screen.blit(s2, (cx - 2, cy - 20))


class Arrow:
    def __init__(self, x, y, vx, vy, owner):
        self.rect = pygame.Rect(x, y, 16, 4)
        self.vx = vx
        self.vy = vy
        self.owner = owner

    def update(self, platforms, players):
        self.rect.x += self.vx
        self.rect.y += self.vy
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
            or self.rect.x < 0
            or self.rect.x > WIDTH
            or self.rect.y < 0
            or self.rect.y > HEIGHT
        ):
            return "miss"
        return None

    def draw(self):
        surf = pygame.Surface((20, 12), pygame.SRCALPHA)
        pygame.draw.rect(surf, ARROW_SHAFT, (2, 4, 16, 4))
        pygame.draw.rect(surf, ARROW_HEAD, (16, 2, 4, 8))
        angle = math.degrees(math.atan2(self.vy, self.vx))
        surf = pygame.transform.rotate(surf, -angle)
        rect = surf.get_rect(center=self.rect.center)
        screen.blit(surf, rect)


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

    def draw(self):
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


class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.vx = random.uniform(-4, 4)
        self.vy = random.uniform(-4, 4)
        self.life = 30
        self.color = color

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.2
        self.life -= 1
        return self.life > 0

    def draw(self):
        alpha = int(255 * (self.life / 30))
        s = pygame.Surface((4, 4), pygame.SRCALPHA)
        s.fill((*self.color, alpha))
        screen.blit(s, (self.x - 2, self.y - 2))


def create_platforms():
    platforms = []
    margin = 120
    min_dist = 200
    target = random.randint(10, 16)
    for _ in range(target * 5):
        if len(platforms) >= target:
            break
        x = random.randint(margin, WIDTH - margin)
        y = random.randint(80, HEIGHT - 80)
        too_close = any(
            math.sqrt((x - p.x) ** 2 + (y - p.y) ** 2) < min_dist + max(p.rx, p.ry)
            for p in platforms
        )
        if too_close:
            continue
        if random.random() < 0.45:
            radius = random.randint(28, 55)
            platforms.append(Platform(x, y, "circle", radius))
        else:
            rx = random.randint(50, 100)
            ry = random.randint(28, 55)
            angle = random.uniform(0, math.pi)
            platforms.append(Platform(x, y, "ellipse", rx, ry, angle))
    if len(platforms) < 4:
        for x, y in [
            (WIDTH // 3, HEIGHT // 3),
            (2 * WIDTH // 3, HEIGHT // 3),
            (WIDTH // 2, 2 * HEIGHT // 3),
        ]:
            platforms.append(Platform(x, y, "circle", 45))
    return platforms


def init_players(platforms):
    def spawn_top(plat):
        angle = -math.pi / 2
        r = plat.get_boundary_radius(angle)
        cx = plat.x + math.cos(angle) * (r + 18)
        cy = plat.y + math.sin(angle) * (r + 18)
        return cx - 12, cy - 12

    by_x = sorted(platforms, key=lambda p: p.x)
    idx1 = max(0, len(by_x) // 4 - 1)
    idx2 = min(len(by_x) - 1, 3 * len(by_x) // 4)
    p1_x, p1_y = spawn_top(by_x[idx1])
    p2_x, p2_y = spawn_top(by_x[idx2])

    return [
        Player(
            p1_x,
            p1_y,
            (255, 107, 107),
            {
                "left": pygame.K_a,
                "right": pygame.K_d,
                "up": pygame.K_w,
                "shoot": pygame.K_f,
            },
            "P1",
        ),
        Player(
            p2_x,
            p2_y,
            (78, 205, 196),
            {
                "left": pygame.K_LEFT,
                "right": pygame.K_RIGHT,
                "up": pygame.K_UP,
                "shoot": pygame.K_l,
            },
            "P2",
        ),
    ]


star_positions = []
saturn_surf = None


def generate_background():
    global star_positions, saturn_surf
    star_positions = []
    for _ in range(250):
        x = random.randint(0, WIDTH)
        y = random.randint(0, HEIGHT)
        r = random.random()
        if r < 0.6:
            size = 1
        elif r < 0.85:
            size = 2
        else:
            size = 3
        bright = random.randint(80, 255)
        star_positions.append((x, y, size, bright))

    pw, ph = 32, 24
    surf = pygame.Surface((pw, ph), pygame.SRCALPHA)
    body_c = (220, 190, 140)
    ring_c = (200, 180, 140, 140)
    dark_c = (180, 150, 110)
    cx, cy = pw // 2 - 1, ph // 2

    pygame.draw.circle(surf, body_c, (cx, cy), 7)
    pygame.draw.circle(surf, (200, 170, 120), (cx, cy), 7, 1)
    pygame.draw.rect(surf, dark_c, (cx - 6, cy - 2, 12, 1))
    pygame.draw.rect(surf, dark_c, (cx - 5, cy + 2, 10, 1))
    pygame.draw.ellipse(surf, ring_c, (cx - 12, cy - 4, 24, 8), 1)

    saturn_surf = pygame.transform.scale(surf, (pw * 4, ph * 4))
    saturn_surf.set_alpha(50)


def draw_background():
    screen.fill(BG_COLOR)
    for x, y, size, bright in star_positions:
        shade = (bright, bright, bright)
        if size == 1:
            screen.set_at((x, y), shade)
        elif size == 2:
            pygame.draw.rect(screen, shade, (x, y, 2, 2))
        else:
            pygame.draw.rect(screen, shade, (x, y, 3, 3))

    sx = WIDTH - saturn_surf.get_width() - 60
    sy = 60
    screen.blit(saturn_surf, (sx, sy))


def main():
    global round_timer, round_num
    round_num = 1
    round_timer = 0
    round_ended = False
    message = ""
    message_timer = 0
    message_surf = None
    prompt_surf = small_font.render("Press any key to continue", True, WHITE)

    p1_score = 0
    p2_score = 0

    generate_background()
    platforms = create_platforms()
    players = init_players(platforms)
    arrows = []
    particles = []
    meteors = []

    def show_message(text, duration):
        nonlocal message, message_timer, message_surf
        message = text
        message_timer = duration
        message_surf = big_font.render(text, True, WHITE)

    def check_round_end():
        nonlocal round_ended
        if round_ended:
            return
        alive = [p for p in players if p.alive]
        if len(alive) <= 1:
            winner = alive[0].name if alive else "DRAW"
            show_message(f"{winner} WINS!" if alive else "DRAW!", 999999)
            round_ended = True

    show_message(f"ROUND {round_num}", 90)

    running = True
    while running:
        keys_pressed = pygame.key.get_pressed()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                round_num = 1
                p1_score = 0
                p2_score = 0
                platforms = create_platforms()
                players = init_players(platforms)
                arrows.clear()
                particles.clear()
                meteors.clear()
                round_timer = 0
                round_ended = False
                show_message(f"ROUND {round_num}", 90)
            if event.type == pygame.KEYDOWN and round_ended:
                round_num += 1
                platforms = create_platforms()
                players = init_players(platforms)
                arrows.clear()
                particles.clear()
                meteors.clear()
                round_timer = 0
                round_ended = False
                show_message(f"ROUND {round_num}", 90)

        if message_timer > 0:
            message_timer -= 1

        if round_ended:
            particles = [p for p in particles if p.update()]
            draw_background()
            for plat in platforms:
                plat.draw()
            for m in meteors:
                m.draw()
            for arrow in arrows:
                arrow.draw()
            for player in players:
                player.draw()
            for p in particles:
                p.draw()

            if message_timer > 0 and message_surf:
                text_rect = message_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 20))
                screen.blit(message_surf, text_rect)
                prompt_rect = prompt_surf.get_rect(
                    center=(WIDTH // 2, HEIGHT // 2 + 30)
                )
                screen.blit(prompt_surf, prompt_rect)

            pygame.display.flip()
            clock.tick(FPS)
            continue

        if message_timer > 0:
            message_timer -= 1

        for player in players:
            result = player.update(keys_pressed, platforms)
            if result:
                particles.extend(result)
        check_round_end()

        for player in players:
            if keys_pressed[player.controls["shoot"]]:
                arrow = player.shoot()
                if arrow:
                    arrows.append(arrow)

        for i in range(len(arrows) - 1, -1, -1):
            result = arrows[i].update(platforms, players)
            if result == "miss":
                arrows.pop(i)
            elif isinstance(result, Player):
                particles.extend(result.die())
                if arrows[i].owner == players[0]:
                    p1_score += 1
                else:
                    p2_score += 1
                arrows.pop(i)
                check_round_end()

        particles = [p for p in particles if p.update()]

        round_timer += 1
        if (
            round_timer > METEOR_START
            and round_timer % max(60, 120 - (round_timer - METEOR_START) // 30) == 0
        ):
            meteors.append(Meteor())

        for i in range(len(meteors) - 1, -1, -1):
            result = meteors[i].update(platforms, players)
            if result == "miss":
                meteors.pop(i)
            elif isinstance(result, list):
                particles.extend(result)
                meteors.pop(i)
                check_round_end()

        draw_background()
        for plat in platforms:
            plat.draw()
        for m in meteors:
            m.draw()
        for arrow in arrows:
            arrow.draw()
        for player in players:
            player.draw()
        for p in particles:
            p.draw()

        if message_timer > 0 and message_surf:
            text_rect = message_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 20))
            screen.blit(message_surf, text_rect)

        p1_status = font.render(
            f"P1: {'ALIVE' if players[0].alive else 'DEAD'}  Score: {p1_score}",
            True,
            WHITE,
        )
        p2_status = font.render(
            f"Score: {p2_score}  P2: {'ALIVE' if players[1].alive else 'DEAD'}",
            True,
            WHITE,
        )
        round_text = font.render(f"Round {round_num}", True, WHITE)
        controls_text = font.render(
            "P1: WASD+F | P2: Arrows+L | R: Restart", True, (136, 136, 136)
        )
        screen.blit(p1_status, (10, 10))
        screen.blit(p2_status, (WIDTH - p2_status.get_width() - 10, 10))
        screen.blit(round_text, (WIDTH // 2 - round_text.get_width() // 2, 10))
        screen.blit(
            controls_text, (WIDTH // 2 - controls_text.get_width() // 2, HEIGHT - 40)
        )

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
