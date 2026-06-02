import pygame

from ..config import WHITE, WIDTH, HEIGHT


def draw_panel(screen, x, y, w, h, color, lines, font, pad, line_height):
    panel = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(panel, (*color, 160), (0, 0, w, h), border_radius=10)
    pygame.draw.rect(panel, (*color, 255), (0, 0, w, h), width=2, border_radius=10)
    screen.blit(panel, (x, y))
    for i, line in enumerate(lines):
        surf = font.render(line, True, WHITE)
        screen.blit(surf, (x + pad, y + pad + i * line_height))


def draw_hud(screen, font, players, scores, round_num):
    p1_color = players[0].color
    p2_color = players[1].color

    p1_lines = [
        f"P1: {'ALIVE' if players[0].alive else 'DEAD'}",
        f"Score: {scores[0]}",
        "WASD + F + G",
    ]
    p2_lines = [
        f"P2: {'ALIVE' if players[1].alive else 'DEAD'}",
        f"Score: {scores[1]}",
        "Arrows + L + K",
    ]

    line_height = font.get_height() + 4
    pad = 10
    margin = 10

    p1_max_w = max(font.render(l, True, WHITE).get_width() for l in p1_lines)
    p2_max_w = max(font.render(l, True, WHITE).get_width() for l in p2_lines)
    panel_w = max(p1_max_w, p2_max_w) + pad * 2
    panel_h = len(p1_lines) * line_height + pad * 2

    draw_panel(screen, margin, margin, panel_w, panel_h, p1_color, p1_lines, font, pad, line_height)

    p2_x = WIDTH - margin - panel_w
    draw_panel(screen, p2_x, margin, panel_w, panel_h, p2_color, p2_lines, font, pad, line_height)

    round_text = font.render(f"Round {round_num}", True, WHITE)
    round_x = WIDTH // 2 - round_text.get_width() // 2
    round_y = margin + pad
    screen.blit(round_text, (round_x, round_y))


def draw_message(screen, big_font, message_surf, message_timer, prompt_surf=None):
    if message_timer > 0 and message_surf:
        text_rect = message_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 20))
        screen.blit(message_surf, text_rect)
        if prompt_surf:
            prompt_rect = prompt_surf.get_rect(
                center=(WIDTH // 2, HEIGHT // 2 + 30)
            )
            screen.blit(prompt_surf, prompt_rect)
