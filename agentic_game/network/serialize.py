"""Convert the live game state into a JSON-friendly snapshot, and rebuild
lightweight "view" entities on the client so the existing .draw() code can
render the remote game unchanged.

View objects are created with ``cls.__new__(cls)`` to skip the randomised
constructors; we just set the attributes each entity's ``draw`` actually
reads.
"""

from __future__ import annotations

from typing import Any, Dict, List

import pygame

from ..entities.black_hole import BlackHole
from ..entities.enemy import UFO, UFOBeam
from ..entities.particle import Particle
from ..entities.planetoid import Planetoid
from ..entities.platform import Platform
from ..entities.player import Player
from ..entities.projectile import LaserBeam, LightsaberSwipe
from ..rendering.asteroid import make_noise_func

MAX_PARTICLES = 110


# --------------------------------------------------------------------------- #
#  Server side: state  ->  dict
# --------------------------------------------------------------------------- #
def snapshot(game: Any) -> Dict[str, Any]:
    s = game.state
    return {
        "players": [_player_state(p) for p in s.players],
        "lasers": [_laser_state(l) for l in s.lasers],
        "swipes": [_swipe_state(w) for w in s.swipes if not w.done],
        "planetoids": [_planetoid_state(p) for p in s.planetoids if not p.done],
        "platforms": [_platform_state(p) for p in s.platforms],
        "black_holes": [_blackhole_state(b) for b in s.black_holes if not b.done],
        "ufos": [_ufo_state(u) for u in s.ufos if not u.done],
        "particles": [_particle_state(p) for p in s.particles[:MAX_PARTICLES]],
        "scores": [s.p1_score, s.p2_score],
        "round_num": s.round_num,
        "round_ended": s.round_ended,
        "msg": s.message_text if s.message_timer > 0 else None,
    }


def _player_state(p: Player) -> Dict[str, Any]:
    return {
        "x": p.rect.centerx, "y": p.rect.centery,
        "c": list(p.color), "f": p.facing, "a": p.alive,
        "og": p.on_ground, "gnx": round(p.ground_nx, 3), "gny": round(p.ground_ny, 3),
        "fnx": round(p.gravity_nx, 3), "fny": round(p.gravity_ny, 3),
        "ch": p.charging, "ca": round(p.charge_angle, 2), "aim": [round(v, 3) for v in p.aim_dir],
        "n": p.name, "pid": getattr(p, "pid", -1),
    }


def _laser_state(l: LaserBeam) -> Dict[str, Any]:
    return {
        "x": round(l.x, 1), "y": round(l.y, 1), "c": list(l.color),
        "t": [[round(tx, 1), round(ty, 1)] for tx, ty in l.trail],
    }


def _swipe_state(w: LightsaberSwipe) -> Dict[str, Any]:
    return {
        "x": round(w.x, 1), "y": round(w.y, 1), "ba": round(w.base_angle, 3),
        "lt": w.lifetime, "c": list(w.color), "r": w.range,
    }


def _planetoid_state(p: Planetoid) -> Dict[str, Any]:
    d = {
        "m": p.mode, "x": round(p.x, 1), "y": round(p.y, 1), "sh": p.shape,
        "sz": p.size, "rx": p.rx, "ry": p.ry, "an": round(p.angle, 3),
        "gr": getattr(p, "gravity_range", 0), "sd": p.seed,
        "vx": round(p.vx, 2), "vy": round(p.vy, 2), "sp": p.spiky,
    }
    if p.spiky:
        d["sa"] = [round(a, 3) for a in p.spike_angles]
        d["sf"] = p.spike_factor
    return d


def _platform_state(p: Platform) -> Dict[str, Any]:
    return {
        "x": round(p.x, 1), "y": round(p.y, 1), "sh": p.shape, "rad": p.radius,
        "rx": p.rx, "ry": p.ry, "an": round(p.angle, 3), "gr": p.gravity_range, "sd": p.seed,
    }


def _blackhole_state(b: BlackHole) -> Dict[str, Any]:
    return {
        "k": b.kind, "x": round(b.x, 1), "y": round(b.y, 1),
        "r": b.radius, "pr": b.pull_range, "sp": round(b.spin, 3),
    }


def _ufo_state(u: UFO) -> Dict[str, Any]:
    return {
        "x": round(u.x, 1), "y": round(u.y, 1),
        "b": [[round(bm.x, 1), round(bm.y, 1)] for bm in u.beams],
    }


def _particle_state(p: Particle) -> Dict[str, Any]:
    return {
        "x": round(p.x, 1), "y": round(p.y, 1), "c": list(p.color),
        "l": p.life, "ml": p.max_life, "s": p.size,
    }


# --------------------------------------------------------------------------- #
#  Client side: dict  ->  view objects (for rendering only)
# --------------------------------------------------------------------------- #
def build_players(items: List[dict]) -> List[Player]:
    out = []
    for d in items:
        p = Player.__new__(Player)
        p.rect = pygame.Rect(0, 0, 28, 28)
        p.rect.center = (d["x"], d["y"])
        p.color = tuple(d["c"]); p.facing = d["f"]; p.alive = d["a"]
        p.on_ground = d["og"]; p.ground_nx = d["gnx"]; p.ground_ny = d["gny"]
        p.gravity_nx = d["fnx"]; p.gravity_ny = d["fny"]
        p.charging = d["ch"]; p.charge_angle = d["ca"]; p.aim_dir = tuple(d["aim"])
        p.name = d["n"]; p.pid = d.get("pid", -1)
        out.append(p)
    return out


def build_lasers(items: List[dict]) -> List[LaserBeam]:
    out = []
    for d in items:
        l = LaserBeam.__new__(LaserBeam)
        l.x = d["x"]; l.y = d["y"]; l.color = tuple(d["c"])
        l.trail = [(t[0], t[1]) for t in d["t"]]
        out.append(l)
    return out


def build_swipes(items: List[dict]) -> List[LightsaberSwipe]:
    out = []
    for d in items:
        w = LightsaberSwipe.__new__(LightsaberSwipe)
        w.x = d["x"]; w.y = d["y"]; w.base_angle = d["ba"]
        w.lifetime = d["lt"]; w.color = tuple(d["c"]); w.range = d["r"]
        w.done = False
        out.append(w)
    return out


def build_planetoids(items: List[dict]) -> List[Planetoid]:
    out = []
    for d in items:
        p = Planetoid.__new__(Planetoid)
        p.mode = d["m"]; p.x = d["x"]; p.y = d["y"]; p.shape = d["sh"]
        p.size = d["sz"]; p.rx = d["rx"]; p.ry = d["ry"]; p.angle = d["an"]
        p.gravity_range = d["gr"]; p.seed = d["sd"]; p.vx = d["vx"]; p.vy = d["vy"]
        p.spiky = d["sp"]; p.done = False
        p._noise = make_noise_func(d["sd"])
        if p.spiky:
            p.spike_angles = d["sa"]; p.spike_factor = d["sf"]
        out.append(p)
    return out


def build_platforms(items: List[dict]) -> List[Platform]:
    out = []
    for d in items:
        p = Platform.__new__(Platform)
        p.x = d["x"]; p.y = d["y"]; p.shape = d["sh"]; p.radius = d["rad"]
        p.rx = d["rx"]; p.ry = d["ry"]; p.angle = d["an"]; p.gravity_range = d["gr"]
        p.seed = d["sd"]; p._noise = make_noise_func(d["sd"])
        out.append(p)
    return out


def build_black_holes(items: List[dict]) -> List[BlackHole]:
    from ..config import BLACKHOLE_LAUNCH_COLOR, BLACKHOLE_TELEPORT_COLOR
    out = []
    for d in items:
        b = BlackHole.__new__(BlackHole)
        b.kind = d["k"]; b.x = d["x"]; b.y = d["y"]
        b.radius = d["r"]; b.pull_range = d["pr"]; b.spin = d["sp"]
        b.color = BLACKHOLE_TELEPORT_COLOR if b.kind == "teleport" else BLACKHOLE_LAUNCH_COLOR
        b.done = False
        out.append(b)
    return out


def build_ufos(items: List[dict]) -> List[UFO]:
    out = []
    for d in items:
        u = UFO.__new__(UFO)
        u.x = d["x"]; u.y = d["y"]; u.done = False
        u.beams = []
        for bx, by in d["b"]:
            bm = UFOBeam.__new__(UFOBeam)
            bm.x = bx; bm.y = by
            u.beams.append(bm)
        out.append(u)
    return out


def build_particles(items: List[dict]) -> List[Particle]:
    out = []
    for d in items:
        p = Particle.__new__(Particle)
        p.x = d["x"]; p.y = d["y"]; p.color = tuple(d["c"])
        p.life = d["l"]; p.max_life = d["ml"]; p.size = d["s"]
        out.append(p)
    return out
