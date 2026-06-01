import random

import pygame

from ..config import WHITE


class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.vx = random.uniform(-4, 4)
        self.vy = random.uniform(-4, 4)
        self.life = 30
        self.color = color

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.2
        self.life -= 1
        return self.life > 0

    def draw(self, screen):
        alpha = int(255 * (self.life / 30))
        s = pygame.Surface((4, 4), pygame.SRCALPHA)
        s.fill((*self.color, alpha))
        screen.blit(s, (self.x - 2, self.y - 2))
