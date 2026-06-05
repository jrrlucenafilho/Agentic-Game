# Agentic-Game

Game made using agentic coding

Made while in an `Agentic Coding` class @ UFPB

## How to Run

```bash
pip install pygame
python main.py
```

You'll get a menu: **Jogar Local** (two players, one keyboard) or **Jogar Online**.

## Controls

- **P1:** WASD to move, F to shoot, G for sword
- **P2:** Arrow keys to move, L to shoot, K for sword
- **R:** Restart  -  **ESC:** back to menu
- Online, you always use **WASD / arrows**, **F or Space** to shoot, **G** for sword.

## Playing Online

The online mode is client–server: one machine runs a dedicated server, both
players connect to it as clients.

1. **Host the server** (any machine, no window needed):

   ```bash
   python server.py
   ```

2. **Expose it to the internet with ngrok:**

   ```bash
   ngrok tcp 5555
   ```

   ngrok prints an address like `tcp://0.tcp.ngrok.io:12345`.

3. **Each player connects.** Tell the game where the server is, either by:
   - creating a `server.txt` file next to `main.py` with the address
     (`0.tcp.ngrok.io:12345` or the full `tcp://...` line), **or**
   - setting an env var: `AGENTIC_SERVER=0.tcp.ngrok.io:12345`

   Then run `python main.py` and pick **Jogar Online**.

The first two clients to connect control player 1 and player 2; anyone else
joins as a spectator. The server is authoritative (runs the simulation); the
port can be changed with `AGENTIC_PORT`.
