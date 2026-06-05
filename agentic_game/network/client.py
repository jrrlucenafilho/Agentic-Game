"""Online client: connects to the authoritative server, streams local input,
and renders the snapshots it receives by rebuilding view entities."""

from __future__ import annotations

import os
import socket
import threading

import pygame

from ..config import FPS, HEIGHT, WHITE, WIDTH
from ..rendering import background as bg
from ..rendering.hud import draw_message
from . import protocol, serialize


def resolve_server_address() -> str:
    """Where to look for the server, in priority order:
    1. AGENTIC_SERVER env var
    2. a 'server.txt' file in the working directory
    3. localhost fallback
    Accepts ngrok 'tcp://0.tcp.ngrok.io:12345' style strings."""
    env = os.environ.get("AGENTIC_SERVER")
    if env:
        return env
    try:
        with open("server.txt", "r", encoding="utf-8") as fh:
            line = fh.read().strip()
            if line:
                return line
    except OSError:
        pass
    return f"127.0.0.1:{protocol.DEFAULT_PORT}"


def _draw_centered(screen, font, text, y, color=WHITE) -> None:
    surf = font.render(text, True, color)
    screen.blit(surf, surf.get_rect(center=(WIDTH // 2, y)))


def _info_screen(screen, fonts, lines, wait_key=False) -> str | None:
    big, mid, small = fonts
    bg.draw(screen)
    _draw_centered(screen, big, lines[0], HEIGHT // 2 - 60)
    for i, ln in enumerate(lines[1:]):
        _draw_centered(screen, small, ln, HEIGHT // 2 + 10 + i * 34, (190, 190, 210))
    pygame.display.flip()
    if not wait_key:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return "quit"
        return None
    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return "quit"
            if e.type == pygame.KEYDOWN:
                return "menu"
        pygame.time.wait(20)


class _Connection:
    def __init__(self, sock: socket.socket) -> None:
        self.sock = sock
        self.latest: dict | None = None
        self.pid = -1
        self.alive = True
        threading.Thread(target=self._recv_loop, daemon=True).start()

    def _recv_loop(self) -> None:
        while self.alive:
            try:
                msg = protocol.recv_msg(self.sock)
            except OSError:
                msg = None
            if msg is None:
                break
            if msg.get("type") == "welcome":
                self.pid = msg.get("pid", -1)
            elif msg.get("type") == "state":
                self.latest = msg
        self.alive = False

    def send_input(self, payload: dict) -> bool:
        try:
            protocol.send_msg(self.sock, payload)
            return True
        except OSError:
            self.alive = False
            return False

    def close(self) -> None:
        self.alive = False
        try:
            self.sock.close()
        except OSError:
            pass


def _read_input() -> dict:
    keys = pygame.key.get_pressed()
    left = keys[pygame.K_a] or keys[pygame.K_LEFT]
    right = keys[pygame.K_d] or keys[pygame.K_RIGHT]
    up = keys[pygame.K_w] or keys[pygame.K_UP]
    down = keys[pygame.K_s] or keys[pygame.K_DOWN]
    shoot = keys[pygame.K_f] or keys[pygame.K_l] or keys[pygame.K_SPACE]
    melee = keys[pygame.K_g] or keys[pygame.K_k]
    return {
        "type": "input",
        "left": bool(left), "right": bool(right), "up": bool(up), "down": bool(down),
        "shoot": bool(shoot), "melee": bool(melee),
        "anykey": bool(left or right or up or down or shoot or melee or keys[pygame.K_RETURN]),
    }


def _render_state(screen, fonts, state: dict, my_pid: int) -> None:
    big, font, small = fonts
    bg.draw(screen)
    for plat in serialize.build_platforms(state["platforms"]):
        plat.draw(screen)
    for bh in serialize.build_black_holes(state["black_holes"]):
        bh.draw(screen)
    for p in serialize.build_planetoids(state["planetoids"]):
        p.draw(screen)
    for u in serialize.build_ufos(state["ufos"]):
        u.draw(screen)
    for w in serialize.build_swipes(state["swipes"]):
        w.draw(screen)
    for l in serialize.build_lasers(state["lasers"]):
        l.draw(screen)
    players = serialize.build_players(state["players"])
    me = None
    for p in players:
        p.draw(screen)
        if p.pid == my_pid:
            me = p
    for part in serialize.build_particles(state["particles"]):
        part.draw(screen)

    # No scoreboard online -- just a battle-royale alive counter.
    alive = sum(1 for p in players if p.alive)
    counter = small.render(f"Vivos: {alive} / {len(players)}", True, (210, 210, 230))
    screen.blit(counter, (WIDTH // 2 - counter.get_width() // 2, 14))

    msg = state.get("msg")
    if msg:
        surf = big.render(msg, True, WHITE)
        prompt = small.render("Press any key to continue", True, WHITE) if state["round_ended"] else None
        draw_message(screen, big, surf, 1, prompt)

    if me is not None:
        tag = small.render(f"VOCE = {me.name}", True, me.color)
        screen.blit(tag, (WIDTH // 2 - tag.get_width() // 2, HEIGHT - 40))


def run_online_client(screen, clock, fonts, address: str | None = None) -> str:
    """Connect, play, and return 'quit' or 'menu'."""
    address = address or resolve_server_address()
    host, port = protocol.parse_address(address)

    res = _info_screen(screen, fonts, [f"Conectando a {host}:{port}...",
                                       "Procurando o servidor", "ESC para cancelar"])
    if res == "quit":
        return "quit"

    try:
        sock = socket.create_connection((host, port), timeout=8)
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    except OSError as exc:
        return _info_screen(
            screen, fonts,
            ["Falha ao conectar", f"{host}:{port}", str(exc),
             "Defina o endereco em server.txt ou AGENTIC_SERVER",
             "Pressione qualquer tecla para voltar"],
            wait_key=True,
        ) or "menu"

    conn = _Connection(sock)
    bg.generate()

    try:
        while True:
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    conn.close()
                    return "quit"
                if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                    conn.close()
                    return "menu"

            if not conn.alive:
                return _info_screen(
                    screen, fonts,
                    ["Conexao perdida", "Pressione qualquer tecla para voltar"],
                    wait_key=True,
                ) or "menu"

            conn.send_input(_read_input())

            if conn.latest is not None:
                _render_state(screen, fonts, conn.latest, conn.pid)
            else:
                _draw_centered(screen, fonts[0], "Aguardando o jogo...", HEIGHT // 2)
            pygame.display.flip()
            clock.tick(FPS)
    finally:
        conn.close()
