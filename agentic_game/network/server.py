"""Authoritative, headless battle-royale server.

Runs the full simulation and is the single source of truth. Every client that
connects spawns its own player (random color); any number can join. Expose the
TCP port with e.g. ``ngrok tcp 5555`` and share the address.

Performance notes:
- The simulation runs at 60 fps but state is broadcast at 30 fps.
- Each frame is JSON-encoded once and the same bytes are fanned out to all
  clients (no per-client serialisation).
- Each client has its own sender thread that always ships the *latest* frame,
  dropping stale ones, so a slow client never stalls the simulation or the
  other players.
"""

from __future__ import annotations

import socket
import threading
import time

import pygame

from ..config import FPS
from ..core.game import Game
from ..systems.spawner import random_color
from . import protocol
from .serialize import snapshot

EMPTY_INPUT = {
    "left": False, "right": False, "up": False,
    "down": False, "shoot": False, "melee": False,
}
SEND_EVERY = 2  # broadcast every 2nd sim tick -> ~30 fps


class _Client:
    def __init__(self, sock: socket.socket, addr, player) -> None:
        self.sock = sock
        self.addr = addr
        self.player = player
        self.input = dict(EMPTY_INPUT)
        self.anykey = False
        self.prev_anykey = False
        self.connected = True
        self.last_sent_version = 0


class GameServer:
    def __init__(self, host: str = "0.0.0.0", port: int = protocol.DEFAULT_PORT) -> None:
        self.host = host
        self.port = port
        self.game = Game(headless=True, manage_players=True)
        self.clients: list[_Client] = []
        self.lock = threading.Lock()
        self.running = False
        self.latest_payload: bytes | None = None
        self.frame_version = 0
        self._join_count = 0

    # -- networking -------------------------------------------------------- #
    def _accept_loop(self, server_sock: socket.socket) -> None:
        while self.running:
            try:
                sock, addr = server_sock.accept()
            except OSError:
                break
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            with self.lock:
                self._join_count += 1
                name = f"P{self._join_count}"
                color = random_color()
                player = self.game.add_player(name, color)
                client = _Client(sock, addr, player)
                client.last_sent_version = self.frame_version
                self.clients.append(client)
            print(f"[server] {addr} joined as {name} ({len(self.clients)} online)")
            try:
                protocol.send_msg(sock, {
                    "type": "welcome", "pid": player.pid, "name": name, "color": list(color),
                })
            except OSError:
                client.connected = False
                continue
            threading.Thread(target=self._recv_loop, args=(client,), daemon=True).start()
            threading.Thread(target=self._send_loop, args=(client,), daemon=True).start()

    def _recv_loop(self, client: _Client) -> None:
        while self.running and client.connected:
            try:
                msg = protocol.recv_msg(client.sock)
            except OSError:
                msg = None
            if msg is None:
                break
            if msg.get("type") == "input":
                client.input = {k: bool(msg.get(k, False)) for k in EMPTY_INPUT}
                client.anykey = bool(msg.get("anykey", False))
        client.connected = False

    def _send_loop(self, client: _Client) -> None:
        while self.running and client.connected:
            if self.latest_payload is not None and self.frame_version != client.last_sent_version:
                client.last_sent_version = self.frame_version
                try:
                    protocol.send_raw(client.sock, self.latest_payload)
                except OSError:
                    client.connected = False
                    break
            else:
                time.sleep(0.004)

    # -- main loop --------------------------------------------------------- #
    def run_forever(self) -> None:
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_sock.bind((self.host, self.port))
        server_sock.listen(16)
        self.running = True
        print(f"[server] listening on {self.host}:{self.port}")
        print("[server] expose it with:  ngrok tcp", self.port)

        threading.Thread(target=self._accept_loop, args=(server_sock,), daemon=True).start()

        from ..rendering import background as bg
        bg.generate()
        self.game._reset_round(1, reset_scores=True)

        clock = pygame.time.Clock()
        tick = 0
        try:
            while self.running:
                self._tick()
                tick += 1
                if tick % SEND_EVERY == 0:
                    self.latest_payload = protocol.encode_msg(
                        {"type": "state", **snapshot(self.game)}
                    )
                    self.frame_version += 1
                clock.tick(FPS)
        except KeyboardInterrupt:
            print("\n[server] shutting down")
        finally:
            self.running = False
            server_sock.close()

    def _tick(self) -> None:
        game = self.game

        # Drop disconnected clients and their players.
        with self.lock:
            dead = [c for c in self.clients if not c.connected]
            for c in dead:
                game.remove_player(c.player)
                self.clients.remove(c)
                try:
                    c.sock.close()
                except OSError:
                    pass
            clients = list(self.clients)

        # Apply each client's input to its own player.
        any_continue = False
        for client in clients:
            if client.player in game.state.players:
                client.player.input.update(client.input)
            if client.anykey and not client.prev_anykey:
                any_continue = True
            client.prev_anykey = client.anykey

        if game.state.round_ended:
            if game.state.message_timer > 0:
                game.state.message_timer -= 1
            game._update_particles()
            if any_continue:
                game._reset_round(game.state.round_num + 1)
        else:
            game._simulate()
