import random

import pygame

from settings import GROUND_TOP, WIDTH


class Medkit:
    """Kit médico pixelado: dura dois segundos e pisca no segundo final."""

    SIZE = 32
    DURATION_MS = 2_000

    def __init__(self) -> None:
        self.rect = pygame.Rect(random.randint(8, WIDTH - self.SIZE - 8), GROUND_TOP - self.SIZE, self.SIZE, self.SIZE)
        self.elapsed_ms = 0.0

    def update(self, dt: float) -> bool:
        self.elapsed_ms += dt * 1000
        return self.elapsed_ms >= self.DURATION_MS

    def draw(self, surface: pygame.Surface) -> None:
        if self.elapsed_ms > 1_000 and int(self.elapsed_ms / 120) % 2:
            return
        pygame.draw.rect(surface, (35, 42, 54), self.rect.inflate(4, 4))
        pygame.draw.rect(surface, (236, 238, 222), self.rect)
        pygame.draw.rect(surface, (212, 55, 63), (self.rect.x + 12, self.rect.y + 5, 8, 22))
        pygame.draw.rect(surface, (212, 55, 63), (self.rect.x + 5, self.rect.y + 12, 22, 8))
