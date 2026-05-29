import math

import pygame

from ..config import (ARROW_COOLDOWN, ARROW_SPEED, BLACK, GRAVITY, HEIGHT,
                      JUMP_FORCE, MELEE_COOLDOWN, MOVE_SPEED,
                      TRANSITION_DURATION, WHITE, WIDTH)
from .particle import Particle
from .projectile import LaserBeam, LightsaberSwipe


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
        self.charging = False
        self.charge_angle = 0.0
        self.charge_dir = 1
        self.aim_dir = (1, 0)
        self.last_melee = 0
        self.transition_timer = 0

    def update(self, keys, platforms):
        if not self.alive:
            return

        ctrl = self.controls

        ax, ay = 0, 0
        if keys[ctrl["left"]]:
            ax = -1
            self.facing = -1
        elif keys[ctrl["right"]]:
            ax = 1
            self.facing = 1
        if keys[ctrl["up"]]:
            ay = -1
        elif keys[ctrl["down"]]:
            ay = 1
        if ax != 0 or ay != 0:
            if ax != 0 and ay != 0:
                self.aim_dir = (ax * 0.7071, ay * 0.7071)
            else:
                self.aim_dir = (ax, ay)

        gravity_field_count = 0
        for plat in platforms:
            dx = self.rect.centerx - plat.x
            dy = self.rect.centery - plat.y
            dist = math.sqrt(dx * dx + dy * dy)
            if 0 < dist < plat.gravity_range:
                gravity_field_count += 1

        in_hover = gravity_field_count >= 2 and not self.on_ground

        # Track transition from shared-gravity hover to single-gravity field
        if in_hover:
            self.transition_timer = 0
        elif (
            not self.on_ground
            and gravity_field_count == 1
            and self.transition_timer < TRANSITION_DURATION
        ):
            self.transition_timer += 1
        else:
            self.transition_timer = TRANSITION_DURATION

        blend = self.transition_timer / TRANSITION_DURATION

        if self.on_ground:
            if not self.charging:
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

                if keys[ctrl["down"]] and self.ground_ny > 0.5:
                    self.vx = self.ground_nx * JUMP_FORCE
                    self.vy = self.ground_ny * JUMP_FORCE
                    self.on_ground = False
                elif keys[ctrl["up"]] and self.ground_ny < -0.5:
                    self.vx = self.ground_nx * JUMP_FORCE
                    self.vy = self.ground_ny * JUMP_FORCE
                    self.on_ground = False
                elif keys[ctrl["right"]] and self.ground_nx > 0.5:
                    self.vx = self.ground_nx * JUMP_FORCE
                    self.vy = self.ground_ny * JUMP_FORCE
                    self.on_ground = False
                elif keys[ctrl["left"]] and self.ground_nx < -0.5:
                    self.vx = self.ground_nx * JUMP_FORCE
                    self.vy = self.ground_ny * JUMP_FORCE
                    self.on_ground = False
            elif self.charging:
                self.vx *= 0.8
                self.vy *= 0.8
        elif in_hover or (blend < 1.0 and gravity_field_count == 1):
            friction = 0.85 - blend * 0.05
            if not self.charging:
                if keys[ctrl["left"]]:
                    self.vx = -MOVE_SPEED
                    self.facing = -1
                elif keys[ctrl["right"]]:
                    self.vx = MOVE_SPEED
                    self.facing = 1
                else:
                    self.vx *= friction

                if keys[ctrl["up"]]:
                    self.vy = -MOVE_SPEED
                elif keys[ctrl["down"]]:
                    self.vy = MOVE_SPEED
                else:
                    self.vy *= friction
            else:
                self.vx *= friction
                self.vy *= friction

            self.vy += GRAVITY * blend
        else:
            if not self.charging:
                in_field = self.gravity_nx != 0 or self.gravity_ny != 0
                if in_field:
                    if keys[ctrl["left"]]:
                        self.vx = -MOVE_SPEED
                        self.facing = -1
                    elif keys[ctrl["right"]]:
                        self.vx = MOVE_SPEED
                        self.facing = 1
                    else:
                        self.vx *= 0.8

                    if keys[ctrl["up"]]:
                        self.vy = -MOVE_SPEED
                    elif keys[ctrl["down"]]:
                        self.vy = MOVE_SPEED
                    else:
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
                if not self.on_ground and not in_hover:
                    self.vx -= force * dx / dist
                    self.vy -= force * dy / dist

        self.on_ground = False
        self.on_wall = 0

        self.rect.x += self.vx
        self.rect.y += self.vy
        for plat in platforms:
            plat.collide_player(self)

        if self.rect.left < 0:
            self.rect.left = 0
            self.vx = 0
        if self.rect.right > WIDTH:
            self.rect.right = WIDTH
            self.vx = 0
        if self.rect.top < 0:
            self.rect.top = 0
            self.vy = 0

        if self.rect.y > HEIGHT + 100:
            self.die()

    def get_forward_vector(self):
        return self.aim_dir

    def get_aim_vector(self):
        tx, ty = self.get_forward_vector()
        fwd_angle = math.atan2(ty, tx)
        angle = fwd_angle + math.radians(self.charge_angle)
        return math.cos(angle), math.sin(angle)

    def shoot(self):
        now = pygame.time.get_ticks()
        if now - self.last_shot < ARROW_COOLDOWN:
            return None
        self.last_shot = now
        tx, ty = self.get_aim_vector()
        beam_x = self.rect.centerx + tx * 12
        beam_y = self.rect.centery + ty * 12
        return LaserBeam(
            beam_x, beam_y, ARROW_SPEED * tx, ARROW_SPEED * ty, self.color, self
        )

    def melee(self):
        now = pygame.time.get_ticks()
        if now - self.last_melee < MELEE_COOLDOWN:
            return None
        self.last_melee = now
        tx, ty = self.get_forward_vector()
        return LightsaberSwipe(
            self.rect.centerx,
            self.rect.centery,
            tx,
            ty,
            self.color,
            self,
        )

    def start_charge(self):
        now = pygame.time.get_ticks()
        if now - self.last_shot < ARROW_COOLDOWN:
            return
        self.charging = True
        self.charge_angle = 0.0
        self.charge_dir = 1

    def update_charge(self):
        if not self.charging:
            return
        self.charge_angle += self.charge_dir * 2.0
        if self.charge_angle > 22.5:
            self.charge_angle = 22.5
            self.charge_dir = -1
        elif self.charge_angle < -22.5:
            self.charge_angle = -22.5
            self.charge_dir = 1

    def release_charge(self):
        if not self.charging:
            return None
        self.charging = False
        return self.shoot()

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

    def draw(self, screen):
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
            bx = center - 13 * self.facing
            pygame.draw.rect(
                surf,
                (
                    max(0, self.color[0] - 60),
                    max(0, self.color[1] - 60),
                    max(0, self.color[2] - 60),
                ),
                (bx - 3, center - 5, 6, 10),
            )
            pygame.draw.rect(surf, (40, 40, 40), (bx - 3, center - 5, 6, 10), 1)
            if not self.on_ground:
                t = pygame.time.get_ticks()
                for i in range(3):
                    fs = max(2, 5 - i + (t + i * 70) % 6 - 3)
                    fy = center + (i - 1) * 4
                    fx = bx - (3 + i * 2) * self.facing
                    s = pygame.Surface((fs * 2, fs * 2), pygame.SRCALPHA)
                    r, g, b = (
                        (255, 160 - i * 50, 30) if i < 2 else (255, 100 - i * 20, 5)
                    )
                    pygame.draw.circle(s, (r, g, b, 160 - i * 40), (fs, fs), fs)
                    surf.blit(s, (fx - fs, fy - fs))
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
            bx = cx - 13 * self.facing
            pygame.draw.rect(
                screen,
                (
                    max(0, self.color[0] - 60),
                    max(0, self.color[1] - 60),
                    max(0, self.color[2] - 60),
                ),
                (bx - 3, cy - 5, 6, 10),
            )
            pygame.draw.rect(screen, (40, 40, 40), (bx - 3, cy - 5, 6, 10), 1)
            if not self.on_ground:
                t = pygame.time.get_ticks()
                for i in range(3):
                    fs = max(2, 5 - i + (t + i * 70) % 6 - 3)
                    fy = cy + (i - 1) * 4
                    fx = bx - (3 + i * 2) * self.facing
                    s = pygame.Surface((fs * 2, fs * 2), pygame.SRCALPHA)
                    r, g, b = (
                        (255, 160 - i * 50, 30) if i < 2 else (255, 100 - i * 20, 5)
                    )
                    pygame.draw.circle(s, (r, g, b, 160 - i * 40), (fs, fs), fs)
                    screen.blit(s, (fx - fs, fy - fs))

        if self.charging:
            tx, ty = self.get_forward_vector()
            aim_x, aim_y = self.get_aim_vector()
            cx, cy = self.rect.center
            angle_fwd = math.atan2(ty, tx)
            half = math.radians(22.5)
            arc_r = 50
            arc_rect = pygame.Rect(cx - arc_r, cy - arc_r, arc_r * 2, arc_r * 2)
            pygame.draw.arc(
                screen, WHITE, arc_rect, angle_fwd - half, angle_fwd + half, 2
            )
            for offset in (-half, half):
                ex = cx + math.cos(angle_fwd + offset) * arc_r
                ey = cy + math.sin(angle_fwd + offset) * arc_r
                pygame.draw.line(screen, WHITE, (cx, cy), (ex, ey), 1)
            line_len = 80
            end_x = cx + aim_x * line_len
            end_y = cy + aim_y * line_len
            pygame.draw.line(screen, WHITE, (cx, cy), (end_x, end_y), 3)
