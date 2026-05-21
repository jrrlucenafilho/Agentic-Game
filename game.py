import random
import sys

import pygame

pygame.init()

WIDTH, HEIGHT = 800, 600
TILE_SIZE = 32
FPS = 60

GRAVITY = 0.6
JUMP_FORCE = -12
MOVE_SPEED = 5
WALL_JUMP_FORCE_X = 8
WALL_JUMP_FORCE_Y = -10
ARROW_SPEED = 10
ARROW_COOLDOWN = 500
WATER_RISE_SPEED = 0.2

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Agentic Battle - Slime Arena")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 36)
big_font = pygame.font.Font(None, 72)

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
    def __init__(self, x, y, w, h):
        self.rect = pygame.Rect(x, y, w, h)

    def draw(self):
        pygame.draw.rect(screen, PLATFORM_COLOR, self.rect)
        pygame.draw.rect(
            screen, PLATFORM_TOP, (self.rect.x, self.rect.y, self.rect.w, 4)
        )
        for i in range(0, self.rect.w, TILE_SIZE):
            pygame.draw.rect(
                screen, PLATFORM_LINE, (self.rect.x + i, self.rect.y, 2, self.rect.h)
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
            self.vy = JUMP_FORCE
            self.on_ground = False

        if keys[ctrl["up"]] and self.on_wall != 0 and not self.on_ground:
            self.vx = -self.on_wall * WALL_JUMP_FORCE_X
            self.vy = WALL_JUMP_FORCE_Y
            self.on_wall = 0

        self.vy += GRAVITY
        self.rect.x += self.vx
        self.rect.y += self.vy

        self.on_ground = False
        self.on_wall = 0

        for plat in platforms:
            if (
                self.rect.x + self.rect.w > plat.rect.x
                and self.rect.x < plat.rect.x + plat.rect.w
            ):
                if (
                    self.rect.y + self.rect.h > plat.rect.y
                    and self.rect.y + self.rect.h < plat.rect.y + plat.rect.h // 2
                    and self.vy >= 0
                ):
                    self.rect.y = plat.rect.y - self.rect.h
                    self.vy = 0
                    self.on_ground = True

            if (
                self.rect.y + self.rect.h > plat.rect.y + 4
                and self.rect.y < plat.rect.y + plat.rect.h
            ):
                if (
                    self.rect.x + self.rect.w > plat.rect.x
                    and self.rect.x + self.rect.w < plat.rect.x + plat.rect.w // 2
                    and self.vx > 0
                ):
                    self.rect.x = plat.rect.x - self.rect.w
                    self.on_wall = 1
                if (
                    self.rect.x < plat.rect.x + plat.rect.w
                    and self.rect.x > plat.rect.x + plat.rect.w // 2
                    and self.vx < 0
                ):
                    self.rect.x = plat.rect.x + plat.rect.w
                    self.on_wall = -1

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
            if self.rect.colliderect(plat.rect):
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
        Platform(200, 350, 400, 32),
        Platform(100, 250, 150, 24),
        Platform(550, 250, 150, 24),
        Platform(300, 150, 200, 24),
        Platform(50, 450, 100, 24),
        Platform(650, 450, 100, 24),
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
    round_delay = 0
    message = ""
    message_timer = 0
    message_surf = None

    platforms = create_platforms()
    players = init_players()
    arrows = []
    particles = []

    def show_message(text, duration):
        nonlocal message, message_timer, message_surf
        message = text
        message_timer = duration
        message_surf = big_font.render(text, True, WHITE)

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
                show_message(f"ROUND {round_num}", 90)

        if round_delay > 0:
            round_delay -= 1
            if round_delay == 0:
                round_num += 1
                platforms = create_platforms()
                players = init_players()
                arrows.clear()
                particles.clear()
                water_level = HEIGHT + 50
                water_rising = False
                round_timer = 0
                show_message(f"ROUND {round_num}", 90)

        if message_timer > 0:
            message_timer -= 1

        for player in players:
            result = player.update(keys_pressed, platforms)
            if result:
                particles.extend(result)

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
                alive = [p for p in players if p.alive]
                if len(alive) <= 1:
                    winner = alive[0].name if alive else "DRAW"
                    show_message(f"{winner} WINS!" if alive else "DRAW!", 120)
                    round_delay = 120

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
            text_rect = message_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2))
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
