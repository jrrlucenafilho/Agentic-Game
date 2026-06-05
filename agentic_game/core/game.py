from __future__ import annotations

import math
import os
import random
from dataclasses import dataclass, field
from typing import List

import pygame

from ..config import (
    BEAM_COLLISION_PARTICLES,
    BLACKHOLE_LAUNCH_FORCE,
    BLACKHOLE_MAX,
    BLACKHOLE_SPAWN_CHANCE,
    BLACKHOLE_SPAWN_INTERVAL,
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
    WARP_COOLDOWN,
    WHITE,
    WIDTH,
)
from ..entities.black_hole import BlackHole
from ..entities.enemy import UFO
from ..entities.particle import Particle, burst, directional
from ..entities.planetoid import Planetoid
from ..entities.player import Player
from ..rendering import background as bg
from ..rendering.hud import draw_hud, draw_message
from ..systems import audio
from ..systems.spawner import (
    NETWORK_CONTROLS,
    create_platforms,
    init_players,
    random_spawn,
    spawn_points,
)


@dataclass
class GameState:
    round_num: int = 1
    round_timer: int = 0
    round_ended: bool = False
    message_timer: int = 0
    message_text: str | None = None
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
    black_holes: List = field(default_factory=list)
    ufo_respawn_timer: int = 0


class Game:
    def __init__(
        self,
        screen: pygame.Surface | None = None,
        headless: bool = False,
        manage_players: bool = False,
    ) -> None:
        self.headless = headless
        self.manage_players = manage_players
        self._next_pid = 0
        if headless:
            os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
            os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
        if not pygame.get_init():
            if not headless:
                pygame.mixer.pre_init(audio.SAMPLE_RATE, -16, 2, 512)
            pygame.init()
        if not headless:
            audio.init()
        if screen is not None:
            self.screen = screen
        else:
            self.screen = pygame.display.set_mode((1, 1) if headless else (WIDTH, HEIGHT))
            if not headless:
                pygame.display.set_caption("Agentic Battle - Slime Arena")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.big_font = pygame.font.Font(None, 72)
        self.small_font = pygame.font.Font(None, 28)
        self.should_quit = False
        self._alive_prev: List[bool] = []
        self.state = GameState(
            prompt_surf=self.small_font.render("Press any key to continue", True, WHITE)
        )

    def _show_message(self, text: str, duration: int) -> None:
        self.state.message_timer = duration
        self.state.message_text = text
        self.state.message_surf = self.big_font.render(text, True, WHITE)

    def _respawn_managed_players(self) -> None:
        """Reposition and revive the already-connected players on the fresh
        arena, keeping the same objects so client references stay valid."""
        players = self.state.players
        points = spawn_points(self.state.platforms, len(players))
        for player, (sx, sy) in zip(players, points):
            player.rect.x, player.rect.y = sx, sy
            player.spawn_pos = (sx, sy)
            player.vx = player.vy = 0.0
            player.alive = True
            player.on_ground = False
            player.charging = False
            player.movement_locked = False
            player.warp_cooldown = 0

    def add_player(self, name: str, color) -> Player:
        """Spawn a new network-controlled player and return it."""
        sx, sy = random_spawn(self.state.platforms)
        player = Player(sx, sy, color, dict(NETWORK_CONTROLS), name)
        player.pid = self._next_pid
        self._next_pid += 1
        self.state.players.append(player)
        return player

    def remove_player(self, player: Player) -> None:
        if player in self.state.players:
            self.state.players.remove(player)

    def _check_round_end(self) -> None:
        state = self.state
        if state.round_ended:
            return
        # A match needs at least two contenders (lets a lone player wait in
        # the lobby without instantly "winning").
        if len(state.players) < 2:
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
        if self.manage_players:
            self._respawn_managed_players()
        else:
            state.players = init_players(state.platforms)
        state.lasers.clear()
        state.swipes.clear()
        state.particles.clear()
        state.planetoids.clear()
        state.ufos.clear()
        state.black_holes.clear()
        state.ufo_respawn_timer = 0
        state.round_timer = 0
        state.round_ended = False
        self._alive_prev = [p.alive for p in state.players]
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
        for bh in state.black_holes:
            bh.draw(self.screen)
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

    def _set_local_inputs(self, keys) -> None:
        for player in self.state.players:
            ctrl = player.controls
            inp = player.input
            inp["left"] = bool(keys[ctrl["left"]])
            inp["right"] = bool(keys[ctrl["right"]])
            inp["up"] = bool(keys[ctrl["up"]])
            inp["down"] = bool(keys[ctrl["down"]])
            inp["shoot"] = bool(keys[ctrl["shoot"]])
            inp["melee"] = bool(keys[ctrl["melee"]])

    def _update_players_and_input(self) -> None:
        state = self.state
        for player in state.players:
            player.update(state.platforms, state.planetoids)
            if player.alive:
                self._emit_movement_particles(player)
        self._check_round_end()

        for player in state.players:
            shoot_held = player.input["shoot"]
            if shoot_held and not player.charging:
                player.start_charge()
            elif not shoot_held and player.charging:
                beam = player.release_charge()
                if beam:
                    state.lasers.append(beam)
                    audio.play("shoot")
                    state.particles.extend(
                        directional(beam.x, beam.y, player.color, beam.vx, beam.vy, 8, speed=5)
                    )
            elif shoot_held and player.charging:
                player.update_charge()

            if player.input["melee"]:
                swipe = player.melee()
                if swipe:
                    state.swipes.append(swipe)
                    audio.play("sword")
                    dx = math.cos(swipe.base_angle)
                    dy = math.sin(swipe.base_angle)
                    state.particles.extend(
                        directional(
                            player.rect.centerx, player.rect.centery,
                            player.color, dx, dy, 10, spread=1.0, speed=6, life=14,
                        )
                    )

    def _emit_movement_particles(self, player) -> None:
        state = self.state
        if player.jumped:
            player.jumped = False
            audio.play("jump")
            state.particles.extend(
                burst(player.rect.centerx, player.rect.centery, (255, 180, 60), 6,
                      speed=3, life=14, gravity=0.1, size=3)
            )
            return
        if player.on_ground:
            return
        speed = math.hypot(player.vx, player.vy)
        if speed < 1.5:
            return
        # Thrust trail streaming out behind a flying player.
        state.particles.extend(
            directional(player.rect.centerx, player.rect.centery, (255, 150, 40),
                        -player.vx, -player.vy, 1, spread=0.6, speed=1.5,
                        life=10, gravity=0.04, size=3)
        )

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
            audio.play("hit")
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
                    audio.play("clash")
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
                    audio.play("clash")
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
                        audio.play("clash")
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

        if (
            state.round_timer > 0
            and state.round_timer % BLACKHOLE_SPAWN_INTERVAL == 0
            and len(state.black_holes) < BLACKHOLE_MAX
            and random.random() < BLACKHOLE_SPAWN_CHANCE
        ):
            bh = BlackHole(random.choice(["teleport", "launch"]))
            state.black_holes.append(bh)
            state.particles.extend(
                burst(bh.x, bh.y, bh.color, 20, speed=5, life=28, gravity=0.0, size=3)
            )

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

    def _play_death_sounds(self) -> None:
        cur = [p.alive for p in self.state.players]
        for was, now in zip(self._alive_prev, cur):
            if was and not now:
                audio.play("explode")
        self._alive_prev = cur

    def _update_black_holes(self) -> None:
        state = self.state
        alive = []
        for bh in state.black_holes:
            collapse = bh.update()
            if collapse:
                state.particles.extend(collapse)
            if bh.done:
                continue
            for player in state.players:
                if not player.alive or player.warp_cooldown > 0:
                    continue
                bh.pull(player)
                if bh.contains_center(player):
                    self._trigger_black_hole(bh, player)
            alive.append(bh)
        state.black_holes = alive

    def _trigger_black_hole(self, bh: BlackHole, player) -> None:
        state = self.state
        # Implosion at the spot where the player gets sucked in.
        state.particles.extend(
            burst(player.rect.centerx, player.rect.centery, bh.color, 16,
                  speed=5, life=22, gravity=0.0, size=3)
        )
        if bh.kind == "teleport":
            audio.play("warp")
            dx, dy = self._find_warp_destination(bh)
            player.rect.center = (int(dx), int(dy))
            player.vx *= 0.3
            player.vy *= 0.3
            # Exit burst at the destination.
            state.particles.extend(
                burst(dx, dy, bh.color, 20, speed=6, life=26, gravity=0.0, size=4)
            )
        else:
            audio.play("launch")
            ang = random.uniform(0, math.tau)
            player.vx = math.cos(ang) * BLACKHOLE_LAUNCH_FORCE
            player.vy = math.sin(ang) * BLACKHOLE_LAUNCH_FORCE
            player.on_ground = False
            # Exit streak in the launch direction.
            state.particles.extend(
                directional(player.rect.centerx, player.rect.centery, bh.color,
                            player.vx, player.vy, 20, spread=0.7, speed=8,
                            life=24, gravity=0.0, size=4)
            )
        player.warp_cooldown = WARP_COOLDOWN

    def _find_warp_destination(self, bh: BlackHole) -> tuple[float, float]:
        margin = 120
        for _ in range(20):
            x = random.randint(margin, WIDTH - margin)
            y = random.randint(margin, HEIGHT - margin)
            if any(p.point_inside(x, y) for p in self.state.platforms):
                continue
            if math.hypot(x - bh.x, y - bh.y) < 300:
                continue
            if any(
                math.hypot(x - o.x, y - o.y) < o.radius + 50
                for o in self.state.black_holes
            ):
                continue
            return float(x), float(y)
        return (
            float(random.randint(margin, WIDTH - margin)),
            float(random.randint(margin, HEIGHT - margin)),
        )

    def _simulate(self) -> None:
        """Advance the whole simulation one tick. Shared by local play and
        the authoritative network server (no input reading, no drawing)."""
        if self.state.message_timer > 0:
            self.state.message_timer -= 1
        self._update_players_and_input()
        self._update_black_holes()
        self._update_ufos()
        self._update_lasers()
        self._update_swipes()
        self._update_ufo_beam_collisions()
        self._update_particles()
        self._advance_timers()
        self._spawn_entities()
        self._update_planetoids()
        self._update_platforms()
        self._play_death_sounds()

    def run(self) -> str:
        """Run the local hot-seat game. Returns 'quit' or 'menu'."""
        bg.generate()
        self._reset_round(1, reset_scores=True)

        while True:
            keys_pressed = pygame.key.get_pressed()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.should_quit = True
                    return "quit"
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    return "menu"
                if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                    self._reset_round(1, reset_scores=True)
                if event.type == pygame.KEYDOWN and self.state.round_ended:
                    self._reset_round(self.state.round_num + 1)

            if self.state.round_ended:
                if self.state.message_timer > 0:
                    self.state.message_timer -= 1
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

            self._set_local_inputs(keys_pressed)
            self._simulate()
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
