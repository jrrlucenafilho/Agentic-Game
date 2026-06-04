from __future__ import annotations

import math
import random
import sys
from dataclasses import dataclass, field
from typing import List

import pygame

from ..config import (
    BEAM_COLLISION_PARTICLES,
    FPS,
    HEIGHT,
    INITIAL_PLANETOID_MAX,
    INITIAL_PLANETOID_MIN,
    LASER_CLASH_PARTICLES,
    METEOR_FALL_INTERVAL_BASE,
    METEOR_FALL_INTERVAL_DECAY,
    METEOR_FALL_INTERVAL_MAX,
    METEOR_START,
    MOVING_PLANETOID_BASE_CHANCE,
    MOVING_PLANETOID_CHANCE_PER_ROUND,
    MOVING_PLANETOID_INTERVAL,
    MOVING_PLANETOID_MAX_CHANCE,
    MOVING_PLANETOID_START_TIME,
    PLANETOID_COLLISION_COLOR,
    PLANETOID_COLLISION_PARTICLES,
    ROUND_END_MSG_DURATION,
    ROUND_START_MSG_DURATION,
    SWIPE_CLASH_FORCE,
    SWIPE_CLASH_PARTICLES,
    UFO_GREEN,
    UFO_RESPAWN_DELAY,
    UFO_SPAWN_CHANCE,
    UFO_SPAWN_INTERVAL_BASE,
    UFO_SPAWN_INTERVAL_DECAY,
    UFO_SPAWN_INTERVAL_MAX,
    WHITE,
    WIDTH,
)
from ..entities.enemy import UFO
from ..entities.particle import Particle
from ..entities.planetoid import Planetoid
from ..rendering import background as bg
from ..rendering.hud import draw_hud, draw_message
from ..systems.spawner import create_platforms, init_players


@dataclass
class GameState:
    round_num: int = 1
    round_timer: int = 0
    round_ended: bool = False
    message_timer: int = 0
    message_surf: pygame.Surface | None = None
    prompt_surf: pygame.Surface | None = None
    p1_score: int = 0
    p2_score: int = 0
    platforms: List = field(default_factory=list)
    players: List = field(default_factory=list)
    lasers: List = field(default_factory=list)
    swipes: List = field(default_factory=list)
    particles: List = field(default_factory=list)
    planetoids: List = field(default_factory=list)
    ufos: List = field(default_factory=list)
    ufo_respawn_timer: int = 0


class Game:
    def __init__(self) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Agentic Battle - Slime Arena")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.big_font = pygame.font.Font(None, 72)
        self.small_font = pygame.font.Font(None, 28)
        self.state = GameState(
            prompt_surf=self.small_font.render("Press any key to continue", True, WHITE)
        )

    def _show_message(self, text: str, duration: int) -> None:
        self.state.message_timer = duration
        self.state.message_surf = self.big_font.render(text, True, WHITE)

    def _check_round_end(self) -> None:
        state = self.state
        if state.round_ended:
            return
        alive = [p for p in state.players if p.alive]
        if len(alive) <= 1:
            winner = alive[0].name if alive else "DRAW"
            self._show_message(
                f"{winner} WINS!" if alive else "DRAW!", ROUND_END_MSG_DURATION
            )
            state.round_ended = True

    def _reset_round(self, new_round_num: int, reset_scores: bool = False) -> None:
        state = self.state
        state.round_num = new_round_num
        if reset_scores:
            state.p1_score = 0
            state.p2_score = 0
        state.platforms = create_platforms()
        state.players = init_players(state.platforms)
        state.lasers.clear()
        state.swipes.clear()
        state.particles.clear()
        state.planetoids.clear()
        state.ufos.clear()
        state.ufo_respawn_timer = 0
        state.round_timer = 0
        state.round_ended = False
        state.planetoids.extend(
            [
                Planetoid(mode="moving")
                for _ in range(
                    random.randint(INITIAL_PLANETOID_MIN, INITIAL_PLANETOID_MAX)
                )
            ]
        )
        self._show_message(f"ROUND {state.round_num}", ROUND_START_MSG_DURATION)

    def _draw_scene(self) -> None:
        state = self.state
        bg.draw(self.screen)
        for plat in state.platforms:
            plat.draw(self.screen)
        for p in state.planetoids:
            p.draw(self.screen)
        for u in state.ufos:
            u.draw(self.screen)
        for s in state.swipes:
            s.draw(self.screen)
        for laser in state.lasers:
            laser.draw(self.screen)
        for player in state.players:
            player.draw(self.screen)
        for p in state.particles:
            p.draw(self.screen)

    def _update_players_and_input(self, keys_pressed) -> None:
        state = self.state
        for player in state.players:
            player.update(keys_pressed, state.platforms, state.planetoids)
        self._check_round_end()

        for player in state.players:
            shoot_held = keys_pressed[player.controls["shoot"]]
            if shoot_held and not player.charging:
                player.start_charge()
            elif not shoot_held and player.charging:
                beam = player.release_charge()
                if beam:
                    state.lasers.append(beam)
            elif shoot_held and player.charging:
                player.update_charge()

            if keys_pressed[player.controls["melee"]]:
                swipe = player.melee()
                if swipe:
                    state.swipes.append(swipe)

    def _update_ufos(self) -> None:
        state = self.state
        for i in range(len(state.ufos) - 1, -1, -1):
            ufo = state.ufos[i]
            new_particles = ufo.update(state.players)
            if new_particles:
                state.particles.extend(new_particles)
                self._check_round_end()
            if ufo.done:
                state.ufos.pop(i)

    def _hit_entity(self, entity, hit_check_fn) -> bool:
        if entity.done:
            return False
        if not hit_check_fn(entity):
            return False
        result = entity.hit()
        if result:
            self.state.particles.extend(result)
        return True

    def _hit_ufos(self, hit_check_fn) -> bool:
        for u in self.state.ufos:
            if self._hit_entity(u, hit_check_fn):
                self.state.ufo_respawn_timer = UFO_RESPAWN_DELAY
                return True
        return False

    def _hit_planetoids(self, hit_check_fn) -> bool:
        for p in self.state.planetoids:
            if self._hit_entity(p, hit_check_fn):
                return True
        return False

    def _update_lasers(self) -> None:
        state = self.state
        alive = []

        for laser in state.lasers:
            new_particles = laser.update(state.platforms, state.players)
            if new_particles:
                state.particles.extend(new_particles)
            if laser.done:
                if laser.hit_player:
                    if laser.owner == state.players[0]:
                        state.p1_score += 1
                    else:
                        state.p2_score += 1
                    self._check_round_end()
                continue
            if self._hit_ufos(lambda u: laser.rect.colliderect(u.rect)):
                continue
            if self._hit_planetoids(lambda p: laser.rect.colliderect(p.rect)):
                continue
            alive.append(laser)

        removed: set[int] = set()
        for i in range(len(alive)):
            if i in removed:
                continue
            for j in range(i + 1, len(alive)):
                if j in removed:
                    continue
                if alive[i].rect.colliderect(alive[j].rect):
                    mx = (alive[i].x + alive[j].x) / 2
                    my = (alive[i].y + alive[j].y) / 2
                    for _ in range(LASER_CLASH_PARTICLES):
                        state.particles.append(Particle(mx, my, WHITE))
                    removed.add(i)
                    removed.add(j)
                    break
        state.lasers = [alive[i] for i in range(len(alive)) if i not in removed]

    def _update_swipes(self) -> None:
        state = self.state
        alive = []

        for swipe in state.swipes:
            new_particles = swipe.update(state.players)
            if new_particles:
                state.particles.extend(new_particles)
            if swipe.done:
                if swipe.hit_player:
                    self._check_round_end()
                continue
            if self._hit_ufos(
                lambda u: (
                    (u.rect.centerx - swipe.x) ** 2 + (u.rect.centery - swipe.y) ** 2
                    <= swipe.range * swipe.range
                )
            ):
                continue
            if self._hit_planetoids(
                lambda p: (
                    (p.rect.centerx - swipe.x) ** 2 + (p.rect.centery - swipe.y) ** 2
                    <= swipe.range * swipe.range
                )
            ):
                continue
            alive.append(swipe)

        removed: set[int] = set()
        for i in range(len(alive) - 1, -1, -1):
            if i in removed:
                continue
            s1 = alive[i]
            for j in range(i - 1, -1, -1):
                if j in removed:
                    continue
                s2 = alive[j]
                dx = s2.x - s1.x
                dy = s2.y - s1.y
                dist_sq = dx * dx + dy * dy
                range_sum = s1.range + s2.range
                if dist_sq <= range_sum * range_sum:
                    mx = (s1.x + s2.x) / 2
                    my = (s1.y + s2.y) / 2
                    for _ in range(SWIPE_CLASH_PARTICLES):
                        state.particles.append(Particle(mx, my, WHITE))
                    s1.owner.vx += -s1.owner.aim_dir[0] * SWIPE_CLASH_FORCE
                    s1.owner.vy += -s1.owner.aim_dir[1] * SWIPE_CLASH_FORCE
                    s2.owner.vx += -s2.owner.aim_dir[0] * SWIPE_CLASH_FORCE
                    s2.owner.vy += -s2.owner.aim_dir[1] * SWIPE_CLASH_FORCE
                    removed.add(i)
                    removed.add(j)
                    break
        state.swipes = [s for idx, s in enumerate(alive) if idx not in removed]

    def _update_ufo_beam_collisions(self) -> None:
        state = self.state
        for u in state.ufos:
            if u.done:
                continue
            for bi in range(len(u.beams) - 1, -1, -1):
                beam = u.beams[bi]
                for li in range(len(state.lasers) - 1, -1, -1):
                    if beam.rect.colliderect(state.lasers[li].rect):
                        for _ in range(BEAM_COLLISION_PARTICLES):
                            state.particles.append(Particle(beam.x, beam.y, UFO_GREEN))
                        u.beams.pop(bi)
                        state.lasers.pop(li)
                        break
                else:
                    for si in range(len(state.swipes) - 1, -1, -1):
                        if state.swipes[si].done:
                            continue
                        sx, sy = state.swipes[si].x, state.swipes[si].y
                        r = state.swipes[si].range
                        dx = beam.x - sx
                        dy = beam.y - sy
                        if dx * dx + dy * dy <= r * r:
                            for _ in range(BEAM_COLLISION_PARTICLES):
                                state.particles.append(
                                    Particle(beam.x, beam.y, UFO_GREEN)
                                )
                            u.beams.pop(bi)
                            break

    def _update_particles(self) -> None:
        self.state.particles = [p for p in self.state.particles if p.update()]

    def _advance_timers(self) -> None:
        state = self.state
        if state.ufo_respawn_timer > 0:
            state.ufo_respawn_timer -= 1
        state.round_timer += 1

    def _spawn_entities(self) -> None:
        state = self.state

        if (
            state.round_timer > METEOR_START
            and state.round_timer
            % max(
                METEOR_FALL_INTERVAL_BASE,
                METEOR_FALL_INTERVAL_MAX
                - (state.round_timer - METEOR_START) // METEOR_FALL_INTERVAL_DECAY,
            )
            == 0
        ):
            state.planetoids.append(Planetoid(mode="falling"))

        moving_chance = min(
            MOVING_PLANETOID_MAX_CHANCE,
            MOVING_PLANETOID_BASE_CHANCE
            + state.round_num * MOVING_PLANETOID_CHANCE_PER_ROUND,
        )
        if (
            random.random() < moving_chance
            and state.round_timer > MOVING_PLANETOID_START_TIME
            and state.round_timer % MOVING_PLANETOID_INTERVAL == 0
        ):
            state.planetoids.append(Planetoid(mode="moving"))

        if (
            state.round_timer > METEOR_START
            and state.round_timer
            % max(
                UFO_SPAWN_INTERVAL_BASE,
                UFO_SPAWN_INTERVAL_MAX
                - (state.round_timer - METEOR_START) // UFO_SPAWN_INTERVAL_DECAY,
            )
            == 0
            and random.random() < UFO_SPAWN_CHANCE
            and state.ufo_respawn_timer <= 0
            and not any(not u.done for u in state.ufos)
        ):
            state.ufos.append(UFO())

    def _update_planetoids(self) -> None:
        state = self.state
        alive = []

        for planetoid in state.planetoids:
            new_particles = planetoid.update(state.platforms, state.players)
            if planetoid.done:
                if new_particles:
                    state.particles.extend(new_particles)
                    self._check_round_end()
                continue
            alive.append(planetoid)

        for i in range(len(alive) - 1, -1, -1):
            a = alive[i]
            if a.done:
                continue
            for j in range(i - 1, -1, -1):
                b = alive[j]
                if b.done:
                    continue
                if a.rect.colliderect(b.rect):
                    dx = a.x - b.x
                    dy = a.y - b.y
                    dist = math.hypot(dx, dy)
                    if dist == 0:
                        dist = 0.01
                    overlap = (a.size + b.size) - dist
                    if overlap > 0:
                        nx = dx / dist
                        ny = dy / dist
                        a.x += nx * overlap * 0.5
                        a.y += ny * overlap * 0.5
                        b.x -= nx * overlap * 0.5
                        b.y -= ny * overlap * 0.5
                        a.rect.center = (int(a.x), int(a.y))
                        b.rect.center = (int(b.x), int(b.y))
                        dvx = a.vx - b.vx
                        dvy = a.vy - b.vy
                        dvn = dvx * nx + dvy * ny
                        if dvn < 0:
                            a.vx -= dvn * nx
                            a.vy -= dvn * ny
                            b.vx += dvn * nx
                            b.vy += dvn * ny
                        for _ in range(PLANETOID_COLLISION_PARTICLES):
                            mx = (a.x + b.x) / 2
                            my = (a.y + b.y) / 2
                            state.particles.append(
                                Particle(mx, my, PLANETOID_COLLISION_COLOR)
                            )
        state.planetoids = alive

    def _update_platforms(self) -> None:
        for plat in self.state.platforms:
            plat.update()

    def run(self) -> None:
        bg.generate()
        self._reset_round(1, reset_scores=True)

        running = True
        while running:
            keys_pressed = pygame.key.get_pressed()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                    self._reset_round(1, reset_scores=True)
                if event.type == pygame.KEYDOWN and self.state.round_ended:
                    self._reset_round(self.state.round_num + 1)

            if self.state.message_timer > 0:
                self.state.message_timer -= 1

            if self.state.round_ended:
                self._update_particles()
                self._draw_scene()
                draw_message(
                    self.screen,
                    self.big_font,
                    self.state.message_surf,
                    self.state.message_timer,
                    self.state.prompt_surf,
                )
                pygame.display.flip()
                self.clock.tick(FPS)
                continue

            self._update_players_and_input(keys_pressed)
            self._update_ufos()
            self._update_lasers()
            self._update_swipes()
            self._update_ufo_beam_collisions()
            self._update_particles()
            self._advance_timers()
            self._spawn_entities()
            self._update_planetoids()
            self._update_platforms()
            self._draw_scene()
            draw_message(
                self.screen,
                self.big_font,
                self.state.message_surf,
                self.state.message_timer,
            )
            draw_hud(
                self.screen,
                self.font,
                self.state.players,
                (self.state.p1_score, self.state.p2_score),
                self.state.round_num,
            )

            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()
