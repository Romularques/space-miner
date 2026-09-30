from __future__ import annotations

import random

import pygame

from settings import GROUND_TOP, WIDTH


class Medkit:
    """Kit médico pixelado: dura quatro segundos e pisca cada vez mais rápido no fim."""

    SIZE = 32
    DURATION_MS = 4_000

    def __init__(self) -> None:
        self.rect = pygame.Rect(random.randint(8, WIDTH - self.SIZE - 8), GROUND_TOP - self.SIZE, self.SIZE, self.SIZE)
        self.elapsed_ms = 0.0

    def update(self, dt: float) -> bool:
        self.elapsed_ms += dt * 1000
        return self.elapsed_ms >= self.DURATION_MS

    def visible(self) -> bool:
        if self.elapsed_ms <= 2_000:
            return True
        # O intervalo cai de 240 ms para 60 ms durante os últimos dois segundos.
        progress = min(1.0, (self.elapsed_ms - 2_000) / 2_000)
        blink_interval = 240 - round(180 * progress)
        return int((self.elapsed_ms - 2_000) / blink_interval) % 2 == 0

    def draw(self, surface: pygame.Surface) -> None:
        if not self.visible():
            return
        pygame.draw.rect(surface, (35, 42, 54), self.rect.inflate(4, 4))
        pygame.draw.rect(surface, (236, 238, 222), self.rect)
        pygame.draw.rect(surface, (212, 55, 63), (self.rect.x + 12, self.rect.y + 5, 8, 22))
        pygame.draw.rect(surface, (212, 55, 63), (self.rect.x + 5, self.rect.y + 12, 22, 8))
