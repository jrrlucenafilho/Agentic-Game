import pygame

from ..config import WHITE, WIDTH, HEIGHT


def draw_hud(screen, font, players, scores, round_num):
    p1_status = font.render(
        f"P1: {'ALIVE' if players[0].alive else 'DEAD'}  Score: {scores[0]}",
        True, WHITE,
    )
    p2_status = font.render(
        f"Score: {scores[1]}  P2: {'ALIVE' if players[1].alive else 'DEAD'}",
        True, WHITE,
    )
    round_text = font.render(f"Round {round_num}", True, WHITE)
    controls_text = font.render(
        "P1: WASD+F+G | P2: Arrows+L+K | R: Restart", True, (136, 136, 136)
    )
    screen.blit(p1_status, (10, 10))
    screen.blit(p2_status, (WIDTH - p2_status.get_width() - 10, 10))
    screen.blit(round_text, (WIDTH // 2 - round_text.get_width() // 2, 10))
    screen.blit(
        controls_text, (WIDTH // 2 - controls_text.get_width() // 2, HEIGHT - 40)
    )


def draw_message(screen, big_font, message_surf, message_timer, prompt_surf=None):
    if message_timer > 0 and message_surf:
        text_rect = message_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 20))
        screen.blit(message_surf, text_rect)
        if prompt_surf:
            prompt_rect = prompt_surf.get_rect(
                center=(WIDTH // 2, HEIGHT // 2 + 30)
            )
            screen.blit(prompt_surf, prompt_rect)
