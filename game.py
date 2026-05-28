import math
import random
import sys

import pygame

pygame.init()

WIDTH, HEIGHT = 800, 600
TILE_SIZE = 32
FPS = 60

GRAVITY = 0.6
JUMP_FORCE = 12
MOVE_SPEED = 5
ARROW_SPEED = 10
ARROW_COOLDOWN = 500
WATER_RISE_SPEED = 0.2

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Agentic Battle - Slime Arena")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 36)
big_font = pygame.font.Font(None, 72)
small_font = pygame.font.Font(None, 28)

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BG_COLOR = (15, 52, 96)
BG_DARK = (22, 33, 62)
PLATFORM_COLOR = (74, 78, 105)
PLATFORM_TOP = (154, 140, 152)
PLATFORM_LINE = (34, 34, 59)
WATER_COLOR = (30, 144, 255, 153)
WATER_TOP = (65, 105, 225, 204)
ARROW_SHAFT = (139, 69, 19)
ARROW_HEAD = (160, 82, 45)


class Platform:
    def __init__(self, x, y, radius):
        self.x = x
        self.y = y
        self.radius = radius
        self.gravity_strength = radius * radius * 0.00015
        self.gravity_range = radius * 3

    def apply_gravity(self, player):
        dx = player.rect.centerx - self.x
        dy = player.rect.centery - self.y
        dist = math.sqrt(dx * dx + dy * dy)
        if 0 < dist < self.gravity_range:
            force = self.gravity_strength * (1 - dist / self.gravity_range)
            player.vx -= force * dx / dist
            player.vy -= force * dy / dist
            return True
        return False

    def collide_player(self, player):
        if player.rect.collidepoint(self.x, self.y):
            dx = player.rect.centerx - self.x
            dy = player.rect.centery - self.y
            if dx == 0 and dy == 0:
                dy = -1
            dist = math.sqrt(dx * dx + dy * dy)
            nx = dx / dist
            ny = dy / dist
            push = self.radius + 12 - dist
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
        dx = cx - self.x
        dy = cy - self.y
        dist = math.sqrt(dx * dx + dy * dy)
        if dist >= self.radius or dist == 0:
            return
        overlap = self.radius - dist
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
        for ring in range(1, 4):
            r = int(self.radius * (1 + ring * 0.5))
            if r <= self.gravity_range:
                alpha = max(0, 60 - ring * 15)
                s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                pygame.draw.circle(s, (*PLATFORM_TOP[:3], alpha), (r, r), r, 1)
                screen.blit(s, (self.x - r, self.y - r))
        pygame.draw.circle(screen, PLATFORM_COLOR, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(
            screen, PLATFORM_TOP, (int(self.x), int(self.y)), self.radius, 3
        )
        for i in range(-self.radius + TILE_SIZE // 2, self.radius, TILE_SIZE):
            if abs(i) < self.radius:
                h = int(math.sqrt(max(0, self.radius * self.radius - i * i)))
                pygame.draw.line(
                    screen, PLATFORM_LINE, (self.x + i, self.y - h), (self.x + i, self.y + h), 2
                )


class Player:
    def __init__(self, x, y, color, controls, name):
        self.rect = pygame.Rect(x, y, 24, 24)
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

    def update(self, keys, platforms):
        if not self.alive:
            return

        ctrl = self.controls
        if keys[ctrl["left"]]:
            self.vx = -MOVE_SPEED
            self.facing = -1
        elif keys[ctrl["right"]]:
            self.vx = MOVE_SPEED
            self.facing = 1
        else:
            self.vx *= 0.8

        if keys[ctrl["up"]] and self.on_ground:
            self.vx = self.ground_nx * JUMP_FORCE
            self.vy = self.ground_ny * JUMP_FORCE
            self.on_ground = False

        in_gravity_field = False
        for plat in platforms:
            if plat.apply_gravity(self):
                in_gravity_field = True

        if not in_gravity_field:
            self.vy += GRAVITY

        self.on_ground = False
        self.on_wall = 0

        self.rect.x += self.vx
        self.rect.y += self.vy
        for plat in platforms:
            plat.collide_player(self)

        if (
            self.rect.y > water_level
            or self.rect.x < 0
            or self.rect.x + self.rect.w > WIDTH
        ):
            self.die()

    def shoot(self):
        now = pygame.time.get_ticks()
        if now - self.last_shot < ARROW_COOLDOWN:
            return None
        self.last_shot = now
        arrow_x = self.rect.x + self.rect.w // 2 + self.facing * 12
        arrow_y = self.rect.y + self.rect.h // 2 - 2
        return Arrow(arrow_x, arrow_y, ARROW_SPEED * self.facing, self)

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
        pygame.draw.rect(screen, self.color, self.rect)
        eye_x = self.rect.x + 14 if self.facing > 0 else self.rect.x + 4
        pygame.draw.rect(screen, BLACK, (eye_x, self.rect.y + 6, 6, 6))
        pygame.draw.rect(screen, WHITE, (eye_x + 2, self.rect.y + 8, 2, 2))
        s = pygame.Surface((8, 4), pygame.SRCALPHA)
        s.fill((*self.color, 178))
        screen.blit(s, (self.rect.x + 4, self.rect.y - 4))
        s2 = pygame.Surface((6, 6), pygame.SRCALPHA)
        s2.fill((*self.color, 178))
        screen.blit(s2, (self.rect.x + 12, self.rect.y - 6))


class Arrow:
    def __init__(self, x, y, vx, owner):
        self.rect = pygame.Rect(x, y, 16, 4)
        self.vx = vx
        self.owner = owner

    def update(self, platforms, players):
        self.rect.x += self.vx
        hit = False
        for plat in platforms:
            cx = max(self.rect.left, min(plat.x, self.rect.right))
            cy = max(self.rect.top, min(plat.y, self.rect.bottom))
            dx = cx - plat.x
            dy = cy - plat.y
            if dx * dx + dy * dy < plat.radius * plat.radius:
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
        pygame.draw.rect(screen, ARROW_SHAFT, self.rect)
        head_x = self.rect.x + self.rect.w - 4 if self.vx > 0 else self.rect.x
        pygame.draw.rect(screen, ARROW_HEAD, (head_x, self.rect.y - 2, 4, 8))


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
    return [
        Platform(400, 450, 140),
        Platform(180, 280, 60),
        Platform(620, 280, 60),
        Platform(400, 140, 60),
        Platform(80, 490, 40),
        Platform(720, 490, 40),
    ]


def init_players():
    return [
        Player(
            250,
            300,
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
            500,
            300,
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


def draw_background():
    screen.fill(BG_COLOR)
    for x in range(0, WIDTH, TILE_SIZE * 2):
        for y in range(0, HEIGHT, TILE_SIZE * 2):
            if (x + y) % (TILE_SIZE * 4) == 0:
                pygame.draw.rect(screen, BG_DARK, (x, y, TILE_SIZE, TILE_SIZE))


def draw_water():
    water_height = HEIGHT - water_level
    if water_height <= 0:
        return
    water_surface = pygame.Surface((WIDTH, water_height), pygame.SRCALPHA)
    water_surface.fill(WATER_COLOR)
    screen.blit(water_surface, (0, water_level))
    pygame.draw.rect(screen, WATER_TOP, (0, water_level, WIDTH, 4))


def main():
    global water_level, water_rising, round_timer, round_num
    round_num = 1
    water_level = HEIGHT + 50
    water_rising = False
    round_timer = 0
    round_ended = False
    message = ""
    message_timer = 0
    message_surf = None
    prompt_surf = small_font.render("Press any key to continue", True, WHITE)

    platforms = create_platforms()
    players = init_players()
    arrows = []
    particles = []

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
                platforms = create_platforms()
                players = init_players()
                arrows.clear()
                particles.clear()
                water_level = HEIGHT + 50
                water_rising = False
                round_timer = 0
                round_ended = False
                show_message(f"ROUND {round_num}", 90)
            if event.type == pygame.KEYDOWN and round_ended:
                round_num += 1
                platforms = create_platforms()
                players = init_players()
                arrows.clear()
                particles.clear()
                water_level = HEIGHT + 50
                water_rising = False
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
            draw_water()
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
                arrows.pop(i)
                check_round_end()

        particles = [p for p in particles if p.update()]

        round_timer += 1
        if round_timer > 600 and not water_rising:
            water_rising = True
            show_message("WATER RISING!", 60)

        if water_rising:
            water_level -= WATER_RISE_SPEED

        draw_background()
        for plat in platforms:
            plat.draw()
        draw_water()
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
            f"P1: {'ALIVE' if players[0].alive else 'DEAD'}", True, WHITE
        )
        p2_status = font.render(
            f"P2: {'ALIVE' if players[1].alive else 'DEAD'}", True, WHITE
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
