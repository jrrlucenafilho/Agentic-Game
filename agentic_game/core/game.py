import math
import random
import sys

import pygame

from ..config import FPS, HEIGHT, METEOR_START, UFO_GREEN, WHITE, WIDTH
from ..entities.enemy import UFO
from ..entities.planetoid import Planetoid
from ..entities.particle import Particle
from ..rendering import background as bg
from ..rendering.hud import draw_hud, draw_message
from ..systems.spawner import create_platforms, init_players


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Agentic Battle - Slime Arena")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.big_font = pygame.font.Font(None, 72)
        self.small_font = pygame.font.Font(None, 28)

    def run(self):
        round_num = 1
        round_timer = 0
        round_ended = False
        message_timer = 0
        message_surf = None
        prompt_surf = self.small_font.render("Press any key to continue", True, WHITE)

        p1_score = 0
        p2_score = 0

        bg.generate()
        platforms = create_platforms()
        players = init_players(platforms)
        lasers = []
        swipes = []
        particles = []
        planetoids = [Planetoid(mode="moving") for _ in range(random.randint(1, 2))]
        ufos = []
        ufo_respawn_timer = 0

        def show_message(text, duration):
            nonlocal message_timer, message_surf
            message_timer = duration
            message_surf = self.big_font.render(text, True, WHITE)

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
                    lasers.clear()
                    swipes.clear()
                    particles.clear()
                    planetoids.clear()
                    ufos.clear()
                    ufo_respawn_timer = 0
                    round_timer = 0
                    round_ended = False
                    planetoids.extend([Planetoid(mode="moving") for _ in range(random.randint(1, 2))])
                    show_message(f"ROUND {round_num}", 90)
                if event.type == pygame.KEYDOWN and round_ended:
                    round_num += 1
                    platforms = create_platforms()
                    players = init_players(platforms)
                    lasers.clear()
                    swipes.clear()
                    particles.clear()
                    planetoids.clear()
                    ufos.clear()
                    ufo_respawn_timer = 0
                    round_timer = 0
                    round_ended = False
                    planetoids.extend([Planetoid(mode="moving") for _ in range(random.randint(1, 2))])
                    show_message(f"ROUND {round_num}", 90)

            if message_timer > 0:
                message_timer -= 1

            if round_ended:
                particles = [p for p in particles if p.update()]
                bg.draw(self.screen)
                for plat in platforms:
                    plat.draw(self.screen)
                for p in planetoids:
                    p.draw(self.screen)
                for u in ufos:
                    u.draw(self.screen)
                for s in swipes:
                    s.draw(self.screen)
                for laser in lasers:
                    laser.draw(self.screen)
                for player in players:
                    player.draw(self.screen)
                for p in particles:
                    p.draw(self.screen)
                draw_message(
                    self.screen, self.big_font, message_surf, message_timer, prompt_surf
                )
                pygame.display.flip()
                self.clock.tick(FPS)
                continue

            for player in players:
                player.update(keys_pressed, platforms, planetoids)
            check_round_end()

            for player in players:
                shoot_held = keys_pressed[player.controls["shoot"]]
                if shoot_held and not player.charging:
                    player.start_charge()
                elif not shoot_held and player.charging:
                    beam = player.release_charge()
                    if beam:
                        lasers.append(beam)
                elif shoot_held and player.charging:
                    player.update_charge()

                if keys_pressed[player.controls["melee"]]:
                    swipe = player.melee()
                    if swipe:
                        swipes.append(swipe)

            for i in range(len(ufos) - 1, -1, -1):
                result = ufos[i].update(players)
                if result == "miss":
                    ufos.pop(i)
                elif isinstance(result, list):
                    particles.extend(result)
                    check_round_end()
                elif ufos[i].done:
                    ufos.pop(i)

            for i in range(len(lasers) - 1, -1, -1):
                result = lasers[i].update(platforms, players)
                if result == "miss":
                    lasers.pop(i)
                elif isinstance(result, type(players[0])):
                    particles.extend(result.die())
                    if lasers[i].owner == players[0]:
                        p1_score += 1
                    else:
                        p2_score += 1
                    lasers.pop(i)
                    check_round_end()

            for i in range(len(lasers) - 1, -1, -1):
                hit_ufo = False
                for u in ufos:
                    if not u.done and lasers[i].rect.colliderect(u.rect):
                        hit_result = u.hit()
                        if hit_result:
                            particles.extend(hit_result)
                            ufo_respawn_timer = 600
                        lasers.pop(i)
                        hit_ufo = True
                        break
                if hit_ufo:
                    continue

            for i in range(len(lasers) - 1, -1, -1):
                for p in planetoids:
                    if not p.done and lasers[i].rect.colliderect(p.rect):
                        hit_result = p.hit()
                        if hit_result:
                            particles.extend(hit_result)
                        lasers.pop(i)
                        break

            removed_lasers = set()
            for i in range(len(lasers)):
                if i in removed_lasers:
                    continue
                for j in range(i + 1, len(lasers)):
                    if j in removed_lasers:
                        continue
                    if lasers[i].rect.colliderect(lasers[j].rect):
                        mx = (lasers[i].x + lasers[j].x) / 2
                        my = (lasers[i].y + lasers[j].y) / 2
                        for _ in range(15):
                            particles.append(Particle(mx, my, WHITE))
                        removed_lasers.add(i)
                        removed_lasers.add(j)
                        break
            for idx in sorted(removed_lasers, reverse=True):
                lasers.pop(idx)

            for i in range(len(swipes) - 1, -1, -1):
                result = swipes[i].update(players)
                if result == "miss":
                    swipes.pop(i)
                elif isinstance(result, type(players[0])):
                    particles.extend(result.die())
                    swipes.pop(i)
                    check_round_end()
                elif swipes[i].done:
                    swipes.pop(i)

            for i in range(len(swipes) - 1, -1, -1):
                if swipes[i].done:
                    continue
                sx, sy = swipes[i].x, swipes[i].y
                r = swipes[i].range
                for u in ufos:
                    if u.done:
                        continue
                    dx = u.rect.centerx - sx
                    dy = u.rect.centery - sy
                    if dx * dx + dy * dy <= r * r:
                        hit_result = u.hit()
                        if hit_result:
                            particles.extend(hit_result)
                            ufo_respawn_timer = 600
                        swipes.pop(i)
                        break

            for i in range(len(swipes) - 1, -1, -1):
                if swipes[i].done:
                    continue
                sx, sy = swipes[i].x, swipes[i].y
                r = swipes[i].range
                for p in planetoids:
                    if not p.done:
                        dx = p.rect.centerx - sx
                        dy = p.rect.centery - sy
                        if dx * dx + dy * dy <= r * r:
                            hit_result = p.hit()
                            if hit_result:
                                particles.extend(hit_result)
                            swipes.pop(i)
                            break

            for i in range(len(swipes) - 1, -1, -1):
                s1 = swipes[i]
                if s1.done:
                    continue
                for j in range(i - 1, -1, -1):
                    s2 = swipes[j]
                    if s2.done:
                        continue
                    dx = s2.x - s1.x
                    dy = s2.y - s1.y
                    dist_sq = dx * dx + dy * dy
                    range_sum = s1.range + s2.range
                    if dist_sq <= range_sum * range_sum:
                        mx = (s1.x + s2.x) / 2
                        my = (s1.y + s2.y) / 2
                        for _ in range(25):
                            particles.append(Particle(mx, my, WHITE))
                        push_force = 8
                        s1.owner.vx += -s1.owner.aim_dir[0] * push_force
                        s1.owner.vy += -s1.owner.aim_dir[1] * push_force
                        s2.owner.vx += -s2.owner.aim_dir[0] * push_force
                        s2.owner.vy += -s2.owner.aim_dir[1] * push_force
                        s1.done = True
                        s2.done = True
                        break

            for u in ufos:
                if u.done:
                    continue
                for bi in range(len(u.beams) - 1, -1, -1):
                    beam = u.beams[bi]
                    for li in range(len(lasers) - 1, -1, -1):
                        if beam.rect.colliderect(lasers[li].rect):
                            for _ in range(5):
                                particles.append(Particle(beam.x, beam.y, UFO_GREEN))
                            u.beams.pop(bi)
                            lasers.pop(li)
                            break
                    else:
                        for si in range(len(swipes) - 1, -1, -1):
                            if swipes[si].done:
                                continue
                            sx, sy = swipes[si].x, swipes[si].y
                            r = swipes[si].range
                            dx = beam.x - sx
                            dy = beam.y - sy
                            if dx * dx + dy * dy <= r * r:
                                for _ in range(5):
                                    particles.append(
                                        Particle(beam.x, beam.y, UFO_GREEN)
                                    )
                                u.beams.pop(bi)
                                break

            particles = [p for p in particles if p.update()]

            if ufo_respawn_timer > 0:
                ufo_respawn_timer -= 1
            round_timer += 1

            if (
                round_timer > METEOR_START
                and round_timer % max(60, 120 - (round_timer - METEOR_START) // 30) == 0
            ):
                planetoids.append(Planetoid(mode="falling"))

            moving_chance = min(0.6, 0.15 + round_num * 0.08)
            if (
                random.random() < moving_chance
                and round_timer > 240
                and round_timer % 150 == 0
            ):
                planetoids.append(Planetoid(mode="moving"))

            if (
                round_timer > METEOR_START
                and round_timer % max(120, 240 - (round_timer - METEOR_START) // 20)
                == 0
                and random.random() < 0.5
                and ufo_respawn_timer <= 0
                and not any(not u.done for u in ufos)
            ):
                ufos.append(UFO())

            for i in range(len(planetoids) - 1, -1, -1):
                result = planetoids[i].update(platforms, players)
                if result == "miss":
                    planetoids.pop(i)
                elif isinstance(result, list):
                    particles.extend(result)
                    planetoids.pop(i)
                    check_round_end()

            for i in range(len(planetoids) - 1, -1, -1):
                a = planetoids[i]
                if a.done:
                    continue
                for j in range(i - 1, -1, -1):
                    b = planetoids[j]
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
                            for _ in range(5):
                                mx = (a.x + b.x) / 2
                                my = (a.y + b.y) / 2
                                particles.append(Particle(mx, my, (200, 200, 255)))

            for plat in platforms:
                plat.update()
            bg.draw(self.screen)
            for plat in platforms:
                plat.draw(self.screen)
            for p in planetoids:
                p.draw(self.screen)
            for u in ufos:
                u.draw(self.screen)
            for s in swipes:
                s.draw(self.screen)
            for laser in lasers:
                laser.draw(self.screen)
            for player in players:
                player.draw(self.screen)
            for p in particles:
                p.draw(self.screen)

            draw_message(self.screen, self.big_font, message_surf, message_timer)
            draw_hud(self.screen, self.font, players, (p1_score, p2_score), round_num)

            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()
