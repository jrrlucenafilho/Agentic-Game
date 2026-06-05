"""Run the dedicated game server (headless).

    python server.py                # listen on 0.0.0.0:5555
    AGENTIC_PORT=6000 python server.py

Then expose it to the internet with ngrok:

    ngrok tcp 5555

ngrok prints something like  tcp://0.tcp.ngrok.io:12345  -- give that whole
string to the other player. They paste it into server.txt (or set the
AGENTIC_SERVER env var) and pick "Jogar Online" in the menu.
"""

import os

from agentic_game.network.server import GameServer

if __name__ == "__main__":
    port = int(os.environ.get("AGENTIC_PORT", "5555"))
    GameServer(port=port).run_forever()
