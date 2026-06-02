from __future__ import annotations

import math

import pygame

from ..config import ASTEROID_BODY, ASTEROID_CRATER, ASTEROID_EDGE


def make_noise_func(seed: int):
    def noise(*args: int) -> int:
        h = seed
        for a in args:
            h = (h * 1000003 + a) & 0x7FFFFFFF
        return h % 10000
    return noise


def draw_gravity_ring(screen, cx, cy, gravity_range):
    s = pygame.Surface(
        (int(gravity_range) * 2, int(gravity_range) * 2), pygame.SRCALPHA
    )
    pygame.draw.circle(
        s,
        (200, 205, 215, 60),
        (int(gravity_range), int(gravity_range)),
        int(gravity_range),
        1,
    )
    screen.blit(s, (int(cx - gravity_range), int(cy - gravity_range)))


def _circle_noise_dots(screen, cx, cy, r, noise):
    for a in range(0, 360, 12):
        angle = math.radians(a + noise(a) % 8 - 4)
        vr = r * (0.88 + (noise(a, 1) % 200) / 2000)
        bx = cx + math.cos(angle) * vr
        by = cy + math.sin(angle) * vr
        sz = max(2, r // 10)
        dv = noise(a, 3) % 18
        c = (
            ASTEROID_BODY[0] - dv,
            ASTEROID_BODY[1] - dv // 2,
            ASTEROID_BODY[2] - dv // 2,
        )
        pygame.draw.circle(screen, c, (int(bx), int(by)), sz)


def _craters_to_screen(screen, cx, cy, r, noise):
    pixel = 4
    for i in range(2 + noise(0) % 3):
        a = math.radians(noise(i, 0) % 360)
        d = r * (0.2 + (noise(i, 1) % 100) / 250)
        cr = max(3, int(r * (0.12 + (noise(i, 2) % 100) / 600)))
        crx = cx + math.cos(a) * d
        cry = cy + math.sin(a) * d
        cpx = (int(crx) // pixel) * pixel + pixel // 2
        cpy = (int(cry) // pixel) * pixel + pixel // 2
        rim_in = cr - 3
        rim_out = cr + 1
        for by in range(cpy - cr - pixel, cpy + cr + pixel, pixel):
            for bx in range(cpx - cr - pixel, cpx + cr + pixel, pixel):
                dist_sq = (bx + pixel // 2 - cpx) ** 2 + (by + pixel // 2 - cpy) ** 2
                if dist_sq < rim_in * rim_in:
                    screen.fill(ASTEROID_CRATER, (bx, by, pixel, pixel))
                elif dist_sq < rim_out * rim_out:
                    screen.fill(ASTEROID_EDGE, (bx, by, pixel, pixel))


def draw_circle_asteroid(screen, cx, cy, r, noise):
    pygame.draw.circle(screen, ASTEROID_BODY, (cx, cy), r)
    _circle_noise_dots(screen, cx, cy, r, noise)
    _craters_to_screen(screen, cx, cy, r, noise)


def _ellipse_boundary_radius(rx, ry, angle, world_angle):
    local_angle = world_angle - angle
    c = math.cos(local_angle)
    s = math.sin(local_angle)
    return rx * ry / math.sqrt((ry * c) ** 2 + (rx * s) ** 2)


def _ellipse_noise_dots(surf, lcx, lcy, rx, ry, angle, noise):
    for a in range(0, 360, 15):
        local_a = math.radians(a)
        world_a = local_a + angle
        br = _ellipse_boundary_radius(rx, ry, angle, world_a)
        vr = br * (0.85 + (noise(a, 7) % 250) / 2000)
        bx = lcx + math.cos(local_a) * vr
        by = lcy + math.sin(local_a) * vr
        sz = max(2, int(br // 8))
        dv = noise(a, 9) % 18
        c = (
            ASTEROID_BODY[0] - dv,
            ASTEROID_BODY[1] - dv // 2,
            ASTEROID_BODY[2] - dv // 2,
        )
        pygame.draw.circle(surf, c, (int(bx), int(by)), sz)


def _craters_to_surface(surf, lcx, lcy, rx, ry, noise):
    pixel = 4
    for i in range(1 + noise(1) % 3):
        a = math.radians(noise(i, 3) % 360)
        d = noise(i, 4) % 100 / 100
        crx = lcx + math.cos(a) * rx * d * 0.7
        cry = lcy + math.sin(a) * ry * d * 0.7
        cr = max(3, int(min(rx, ry) * (0.12 + (noise(i, 5) % 100) / 600)))
        cpx = (int(crx) // pixel) * pixel + pixel // 2
        cpy = (int(cry) // pixel) * pixel + pixel // 2
        rim_in = cr - 3
        rim_out = cr + 1
        for by in range(cpy - cr - pixel, cpy + cr + pixel, pixel):
            for bx in range(cpx - cr - pixel, cpx + cr + pixel, pixel):
                dist_sq = (bx + pixel // 2 - cpx) ** 2 + (by + pixel // 2 - cpy) ** 2
                if dist_sq < rim_in * rim_in:
                    surf.fill(ASTEROID_CRATER, (bx, by, pixel, pixel))
                elif dist_sq < rim_out * rim_out:
                    surf.fill(ASTEROID_EDGE, (bx, by, pixel, pixel))


def draw_ellipse_asteroid_body(surf, lcx, lcy, rx, ry, angle, noise):
    rect = pygame.Rect(lcx - rx, lcy - ry, rx * 2, ry * 2)
    pygame.draw.ellipse(surf, ASTEROID_BODY, rect)
    _ellipse_noise_dots(surf, lcx, lcy, rx, ry, angle, noise)
    _craters_to_surface(surf, lcx, lcy, rx, ry, noise)


def draw_ellipse_asteroid(screen, cx, cy, rx, ry, angle, noise):
    max_r = int(max(rx, ry)) + 20
    surf = pygame.Surface((max_r * 2, max_r * 2))
    surf.fill((0, 0, 0))
    surf.set_colorkey((0, 0, 0))
    lcx = lcy = max_r

    draw_ellipse_asteroid_body(surf, lcx, lcy, rx, ry, angle, noise)

    rotated = pygame.transform.rotate(surf, -math.degrees(angle))
    r_rect = rotated.get_rect(center=(cx, cy))
    screen.blit(rotated, r_rect)


def add_spikes_to_asteroid(
    draw_target, cx, cy, spike_angles, bound_radius, angle_offset=0, spike_factor=0.3
):
    for sa in spike_angles:
        br = bound_radius(sa + angle_offset)
        tip = br * (1 + spike_factor)
        tx = cx + math.cos(sa) * tip
        ty = cy + math.sin(sa) * tip
        base = br * 0.85
        bx = cx + math.cos(sa) * base
        by = cy + math.sin(sa) * base
        pa = sa + math.pi / 2
        hw = 3
        bl = (bx + math.cos(pa) * hw, by + math.sin(pa) * hw)
        br2 = (bx - math.cos(pa) * hw, by - math.sin(pa) * hw)
        pygame.draw.polygon(
            draw_target,
            (180, 60, 60),
            [(int(tx), int(ty)), (int(bl[0]), int(bl[1])), (int(br2[0]), int(br2[1]))],
        )
        pygame.draw.polygon(
            draw_target,
            (220, 100, 100),
            [(int(tx), int(ty)), (int(bl[0]), int(bl[1])), (int(br2[0]), int(br2[1]))],
            1,
        )
