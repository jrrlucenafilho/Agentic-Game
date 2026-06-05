from __future__ import annotations

import math
from typing import TYPE_CHECKING, Dict, List, Tuple

import pygame

from ..config import (
    ARROW_COOLDOWN,
    ARROW_SPEED,
    BLACK,
    GRAVITY,
    HEIGHT,
    JUMP_FORCE,
    MELEE_COOLDOWN,
    MOVE_SPEED,
    TRANSITION_DURATION,
    WHITE,
    WIDTH,
)
from .particle import Particle
from .projectile import LaserBeam, LightsaberSwipe

if TYPE_CHECKING:
    from .planetoid import Planetoid
    from .platform import Platform


class Player:
    def __init__(
        self,
        x: float,
        y: float,
        color: Tuple[int, int, int],
        controls: Dict[str, int],
        name: str,
    ) -> None:
        self.rect = pygame.Rect(x, y, 28, 28)
        self.vx = 0.0
        self.vy = 0.0
        self.color = color
        self.controls = controls
        self.name = name
        self.alive = True
        self.on_ground = False
        self.on_wall = 0
        self.last_shot = 0
        self.facing = 1
        self.spawn_pos = (x, y)
        self.ground_nx = 0.0
        self.ground_ny = -1.0
        self.gravity_nx = 0.0
        self.gravity_ny = 0.0
        self.charging = False
        self.charge_angle = 0.0
        self.charge_dir = 1
        self.aim_dir = (1.0, 0.0)
        self.last_melee = 0
        self.transition_timer = 0
        self.movement_locked = False
        self.jumped = False
        self.warp_cooldown = 0

    def update(
        self,
        keys: List[bool],
        platforms: List[Platform],
        planetoids: List[Planetoid] = (),
    ) -> None:
        if not self.alive:
            return
        if self.warp_cooldown > 0:
            self.warp_cooldown -= 1
        self._update_aim_dir(keys)
        gravity_field_count, in_hover, blend = self._compute_gravity_state(platforms, planetoids)
        self._handle_movement(keys, in_hover, blend, gravity_field_count)
        self._apply_gravity_forces(platforms, planetoids, in_hover)
        self._apply_collisions_and_bounds(platforms, planetoids)

    def _update_aim_dir(self, keys: List[bool]) -> None:
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

    def _compute_gravity_state(
        self, platforms: List[Platform], planetoids: List[Planetoid]
    ) -> Tuple[int, bool, float]:
        count = 0
        for plat in platforms:
            dx = self.rect.centerx - plat.x
            dy = self.rect.centery - plat.y
            dist = math.sqrt(dx * dx + dy * dy)
            if 0 < dist < plat.gravity_range:
                count += 1
        for p in planetoids:
            if p.mode == "moving":
                dx = self.rect.centerx - p.x
                dy = self.rect.centery - p.y
                dist = math.sqrt(dx * dx + dy * dy)
                if 0 < dist < p.gravity_range:
                    count += 1

        in_hover = count >= 2 and not self.on_ground
        if in_hover:
            self.transition_timer = 0
        elif not self.on_ground and count == 1 and self.transition_timer < TRANSITION_DURATION:
            self.transition_timer += 1
        else:
            self.transition_timer = TRANSITION_DURATION
        return count, in_hover, self.transition_timer / TRANSITION_DURATION

    def _handle_movement(
        self, keys: List[bool], in_hover: bool, blend: float, gravity_field_count: int
    ) -> None:
        ctrl = self.controls
        if self.movement_locked and not (
            keys[ctrl["left"]] or keys[ctrl["right"]] or keys[ctrl["up"]] or keys[ctrl["down"]]
        ):
            self.movement_locked = False
        if self.on_ground:
            self._move_on_ground(keys, ctrl)
        elif in_hover or (blend < 1.0 and gravity_field_count == 1):
            self._move_hovering(keys, ctrl, blend)
        else:
            self._move_free(keys, ctrl)

    def _move_on_ground(self, keys: List[bool], ctrl: dict) -> None:
        if self.charging or self.movement_locked:
            self.vx *= 0.8
            self.vy *= 0.8
            return
        tx = -self.ground_ny
        ty = self.ground_nx
        if keys[ctrl["left"]]:
            self.vx = -tx * MOVE_SPEED
            self.vy = -ty * MOVE_SPEED
            self.facing = -1
            # Aim follows the surface tangent the player is actually walking
            # along, so attacks fire where the player is heading.
            self.aim_dir = (-tx, -ty)
        elif keys[ctrl["right"]]:
            self.vx = tx * MOVE_SPEED
            self.vy = ty * MOVE_SPEED
            self.facing = 1
            self.aim_dir = (tx, ty)
        else:
            self.vx *= 0.8
            self.vy *= 0.8

        if keys[ctrl["down"]] and self.ground_ny > 0.5:
            self.vx = self.ground_nx * JUMP_FORCE
            self.vy = self.ground_ny * JUMP_FORCE
            self.on_ground = False
            self.jumped = True
        elif keys[ctrl["up"]] and self.ground_ny < -0.5:
            self.vx = self.ground_nx * JUMP_FORCE
            self.vy = self.ground_ny * JUMP_FORCE
            self.on_ground = False
            self.jumped = True
        elif keys[ctrl["right"]] and self.ground_nx > 0.5:
            self.vx = self.ground_nx * JUMP_FORCE
            self.vy = self.ground_ny * JUMP_FORCE
            self.on_ground = False
            self.jumped = True
        elif keys[ctrl["left"]] and self.ground_nx < -0.5:
            self.vx = self.ground_nx * JUMP_FORCE
            self.vy = self.ground_ny * JUMP_FORCE
            self.on_ground = False
            self.jumped = True

    def _move_hovering(self, keys: List[bool], ctrl: dict, blend: float) -> None:
        friction = 0.85 - blend * 0.05
        if not self.charging and not self.movement_locked:
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

    def _move_free(self, keys: List[bool], ctrl: dict) -> None:
        if not self.charging and not self.movement_locked:
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

    def _apply_gravity_forces(
        self, platforms: List[Platform], planetoids: List[Planetoid], in_hover: bool
    ) -> None:
        self.gravity_nx = 0.0
        self.gravity_ny = 0.0
        max_gravity_force = 0.0
        for plat in platforms:
            dx = self.rect.centerx - plat.x
            dy = self.rect.centery - plat.y
            dist = math.sqrt(dx * dx + dy * dy)
            if 0 < dist < plat.gravity_range:
                t = dist / plat.gravity_range
                force = plat.gravity_strength * (1 - t * t)
                if force > max_gravity_force and force >= 0.05:
                    max_gravity_force = force
                    self.gravity_nx = -dx / dist
                    self.gravity_ny = -dy / dist
                if not self.on_ground and not in_hover:
                    self.vx -= force * dx / dist
                    self.vy -= force * dy / dist
        for p in planetoids:
            if p.mode == "moving":
                dx = self.rect.centerx - p.x
                dy = self.rect.centery - p.y
                dist = math.sqrt(dx * dx + dy * dy)
                if 0 < dist < p.gravity_range:
                    t = dist / p.gravity_range
                    force = p.gravity_strength * (1 - t * t)
                    if force > max_gravity_force and force >= 0.05:
                        max_gravity_force = force
                        self.gravity_nx = -dx / dist
                        self.gravity_ny = -dy / dist
                    self.vx -= force * dx / dist
                    self.vy -= force * dy / dist

    def _apply_collisions_and_bounds(
        self, platforms: List[Platform], planetoids: List[Planetoid]
    ) -> None:
        self.on_ground = False
        self.on_wall = 0
        self.rect.x += self.vx
        self.rect.y += self.vy
        for plat in platforms:
            plat.collide_player(self)
        for p in planetoids:
            if p.mode == "moving":
                p.collide_player(self)
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

    def get_forward_vector(self) -> Tuple[float, float]:
        return self.aim_dir

    def get_aim_vector(self) -> Tuple[float, float]:
        tx, ty = self.get_forward_vector()
        fwd_angle = math.atan2(ty, tx)
        angle = fwd_angle + math.radians(self.charge_angle)
        return math.cos(angle), math.sin(angle)

    def shoot(self) -> LaserBeam | None:
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

    def melee(self) -> LightsaberSwipe | None:
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

    def start_charge(self) -> None:
        now = pygame.time.get_ticks()
        if now - self.last_shot < ARROW_COOLDOWN:
            return
        self.charging = True
        self.charge_angle = 0.0
        self.charge_dir = 1

    def update_charge(self) -> None:
        if not self.charging:
            return
        self.charge_angle += self.charge_dir * 2.0
        if self.charge_angle > 22.5:
            self.charge_angle = 22.5
            self.charge_dir = -1
        elif self.charge_angle < -22.5:
            self.charge_angle = -22.5
            self.charge_dir = 1

    def release_charge(self) -> LaserBeam | None:
        if not self.charging:
            return None
        self.charging = False
        self.vx = 0
        self.vy = 0
        self.movement_locked = True
        return self.shoot()

    def die(self) -> List[Particle] | None:
        if not self.alive:
            return None
        self.alive = False
        particles = [
            Particle(
                self.rect.x + self.rect.w // 2,
                self.rect.y + self.rect.h // 2,
                self.color,
            )
            for _ in range(20)
        ]
        return particles

    def respawn(self) -> None:
        self.rect.x, self.rect.y = self.spawn_pos
        self.vx = 0
        self.vy = 0
        self.alive = True
        self.on_ground = False

    def _draw_character_body(self, target: pygame.Surface, cx: float, cy: float) -> None:
        pygame.draw.circle(target, self.color, (int(cx), int(cy)), 14)
        eye_x = int(cx) + (5 if self.facing > 0 else -5)
        pygame.draw.circle(target, BLACK, (eye_x, int(cy) - 2), 4)
        pygame.draw.circle(
            target, WHITE, (eye_x + (1 if self.facing > 0 else -1), int(cy) - 1), 2
        )
        s = pygame.Surface((8, 4), pygame.SRCALPHA)
        s.fill((*self.color, 220))
        target.blit(s, (int(cx) - 10, int(cy) - 18))
        s2 = pygame.Surface((6, 6), pygame.SRCALPHA)
        s2.fill((*self.color, 220))
        target.blit(s2, (int(cx) - 2, int(cy) - 20))
        bx = int(cx) - 13 * self.facing
        pygame.draw.rect(
            target,
            (
                max(0, self.color[0] - 60),
                max(0, self.color[1] - 60),
                max(0, self.color[2] - 60),
            ),
            (bx - 3, int(cy) - 5, 6, 10),
        )
        pygame.draw.rect(target, (40, 40, 40), (bx - 3, int(cy) - 5, 6, 10), 1)
        if not self.on_ground:
            t = pygame.time.get_ticks()
            for i in range(3):
                fs = max(2, 5 - i + (t + i * 70) % 6 - 3)
                fy = int(cy) + (i - 1) * 4
                fx = bx - (3 + i * 2) * self.facing
                s = pygame.Surface((fs * 2, fs * 2), pygame.SRCALPHA)
                r, g, b = (
                    (255, 160 - i * 50, 30) if i < 2 else (255, 100 - i * 20, 5)
                )
                pygame.draw.circle(s, (r, g, b, 160 - i * 40), (fs, fs), fs)
                target.blit(s, (fx - fs, fy - fs))

    def _draw_charge_ui(self, screen: pygame.Surface) -> None:
        tx, ty = self.get_forward_vector()
        aim_x, aim_y = self.get_aim_vector()
        cx, cy = self.rect.center
        angle_fwd = math.atan2(ty, tx)
        half = math.radians(22.5)
        arc_r = 50

        for offset in (-half, half):
            ex = cx + math.cos(angle_fwd + offset) * arc_r
            ey = cy + math.sin(angle_fwd + offset) * arc_r
            pygame.draw.line(screen, WHITE, (cx, cy), (ex, ey), 1)

        lx, ly = None, None
        for i in range(11):
            t = i / 10
            a = angle_fwd - half + t * 2 * half
            px = cx + math.cos(a) * arc_r
            py = cy + math.sin(a) * arc_r
            if i > 0:
                pygame.draw.line(screen, WHITE, (int(lx), int(ly)), (int(px), int(py)), 1)
            lx, ly = px, py

        end_x = cx + aim_x * arc_r
        end_y = cy + aim_y * arc_r
        pygame.draw.line(screen, WHITE, (cx, cy), (int(end_x), int(end_y)), 3)

    def draw(self, screen: pygame.Surface) -> None:
        if not self.alive:
            return

        if self.on_ground:
            tx = -self.ground_nx
            ty = -self.ground_ny
        elif self.gravity_nx != 0 or self.gravity_ny != 0:
            tx = self.gravity_nx
            ty = self.gravity_ny
        else:
            tx = 0.0
            ty = 0.0

        surf_size = 40
        surf = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
        center = surf_size // 2
        self._draw_character_body(surf, float(center), float(center))

        if tx != 0 or ty != 0:
            angle = math.degrees(math.atan2(ty, tx) - math.pi / 2)
            surf = pygame.transform.rotate(surf, angle)
        rect = surf.get_rect(center=self.rect.center)
        screen.blit(surf, rect)

        if self.charging:
            self._draw_charge_ui(screen)
