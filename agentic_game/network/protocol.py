"""Length-prefixed JSON messaging over a TCP socket.

Wire format: a 4-byte big-endian unsigned length, followed by that many
bytes of UTF-8 JSON. Both ends use the same two helpers.
"""

from __future__ import annotations

import json
import socket
import struct
from typing import Any

DEFAULT_PORT = 5555


def encode_msg(obj: Any) -> bytes:
    """Encode a message to a framed byte string once, to fan out to many
    clients without re-serialising per recipient."""
    data = json.dumps(obj, separators=(",", ":")).encode("utf-8")
    return struct.pack("!I", len(data)) + data


def send_raw(sock: socket.socket, framed: bytes) -> None:
    sock.sendall(framed)


def send_msg(sock: socket.socket, obj: Any) -> None:
    sock.sendall(encode_msg(obj))


def _recv_all(sock: socket.socket, n: int) -> bytes | None:
    buf = bytearray()
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            return None
        buf.extend(chunk)
    return bytes(buf)


def recv_msg(sock: socket.socket) -> Any | None:
    header = _recv_all(sock, 4)
    if not header:
        return None
    (length,) = struct.unpack("!I", header)
    payload = _recv_all(sock, length)
    if payload is None:
        return None
    return json.loads(payload.decode("utf-8"))


def parse_address(text: str, default_port: int = DEFAULT_PORT) -> tuple[str, int]:
    """Accept 'host:port', 'tcp://host:port' (ngrok style) or just 'host'."""
    text = text.strip()
    if text.startswith("tcp://"):
        text = text[len("tcp://"):]
    if "/" in text:
        text = text.split("/", 1)[0]
    if ":" in text:
        host, port = text.rsplit(":", 1)
        return host, int(port)
    return text, default_port
