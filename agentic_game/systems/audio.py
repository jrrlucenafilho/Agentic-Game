"""Tiny 8-bit style sound engine.

Sounds are synthesised at startup (square waves / noise) and pushed straight
into pygame.mixer as raw 16-bit stereo buffers, so the game needs no audio
asset files. Every public call is a no-op when no audio device is available
(e.g. headless CI), so importing/using this module is always safe.
"""

from __future__ import annotations

import math
import random
import struct
from typing import Dict

import pygame

SAMPLE_RATE = 44100

_sounds: Dict[str, pygame.mixer.Sound] = {}
_ready = False


def _tone(
    freq: float,
    dur: float,
    wave: str = "square",
    vol: float = 0.35,
    sweep: float = 0.0,
    attack: float = 0.01,
    vibrato: float = 0.0,
    vib_rate: float = 0.0,
) -> pygame.mixer.Sound:
    """Build a single Sound. `sweep` bends the pitch over the duration
    (negative = down, positive = up); `vibrato`/`vib_rate` add a wobble.
    A short attack + linear decay keeps it from clicking."""
    n = max(1, int(SAMPLE_RATE * dur))
    amp = 32767 * vol
    atk = max(1, int(SAMPLE_RATE * attack))
    data = bytearray()
    phase = 0.0
    for i in range(n):
        frac = i / n
        t = i / SAMPLE_RATE
        f = freq * (1.0 + sweep * frac)
        if vibrato:
            f *= 1.0 + vibrato * math.sin(2 * math.pi * vib_rate * t)
        phase += f / SAMPLE_RATE
        ph = phase % 1.0
        if wave == "square":
            s = 1.0 if ph < 0.5 else -1.0
        elif wave == "saw":
            s = 2.0 * ph - 1.0
        elif wave == "triangle":
            s = 4.0 * abs(ph - 0.5) - 1.0
        elif wave == "noise":
            s = random.uniform(-1.0, 1.0)
        else:
            s = math.sin(2 * math.pi * ph)

        if i < atk:
            env = i / atk
        else:
            env = 1.0 - (i - atk) / max(1, n - atk)

        v = int(amp * s * env)
        v = 32767 if v > 32767 else -32768 if v < -32768 else v
        data += struct.pack("<hh", v, v)
    return pygame.mixer.Sound(buffer=bytes(data))


def _build_sounds() -> None:
    _sounds["shoot"] = _tone(720, 0.12, "square", 0.30, sweep=-0.7)
    _sounds["sword"] = _tone(300, 0.14, "square", 0.26, sweep=2.4)
    _sounds["hit"] = _tone(200, 0.16, "square", 0.32, sweep=-0.5)
    _sounds["explode"] = _tone(150, 0.32, "noise", 0.40)
    _sounds["clash"] = _tone(1000, 0.10, "square", 0.30, sweep=0.6)
    _sounds["jump"] = _tone(420, 0.09, "square", 0.24, sweep=1.6)
    # Otherworldly warble for the teleport black hole.
    _sounds["warp"] = _tone(
        480, 0.55, "triangle", 0.30, sweep=1.1, vibrato=0.28, vib_rate=20
    )
    # Deep descending whoosh for the slingshot black hole.
    _sounds["launch"] = _tone(
        700, 0.32, "saw", 0.32, sweep=-0.85, vibrato=0.12, vib_rate=34
    )


def init() -> None:
    """Initialise the mixer and synthesise all sounds. Safe to call twice
    and safe to fail (silently disables audio)."""
    global _ready
    if _ready:
        return
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init(SAMPLE_RATE, -16, 2, 512)
        _build_sounds()
        _ready = True
    except (pygame.error, ValueError):
        _ready = False


def play(name: str) -> None:
    if not _ready:
        return
    snd = _sounds.get(name)
    if snd is not None:
        snd.play()
