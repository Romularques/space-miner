from __future__ import annotations

import random

import pygame

from settings import GROUND_TOP, WIDTH


class Powerup:
    """Item de chão temporário: kit médico, relógio, bomba ou escudo."""

    SIZE = 32
    DURATION_MS = 4_000

    def __init__(self, kind: str) -> None:
        self.kind = kind
        self.rect = pygame.Rect(random.randint(8, WIDTH - self.SIZE - 8), GROUND_TOP - self.SIZE, self.SIZE, self.SIZE)
        self.elapsed_ms = 0.0

    def update(self, dt: float) -> bool:
        self.elapsed_ms += dt * 1000
        return self.elapsed_ms >= self.DURATION_MS

    def visible(self) -> bool:
        if self.elapsed_ms <= 2_000:
            return True
        progress = min(1.0, (self.elapsed_ms - 2_000) / 2_000)
        interval = 240 - round(180 * progress)
        return int((self.elapsed_ms - 2_000) / interval) % 2 == 0

    def draw(self, surface: pygame.Surface) -> None:
        if not self.visible():
            return
        pygame.draw.rect(surface, (35, 42, 54), self.rect.inflate(4, 4))
        if self.kind == "medkit":
            pygame.draw.rect(surface, (236, 238, 222), self.rect)
            pygame.draw.rect(surface, (212, 55, 63), (self.rect.x + 12, self.rect.y + 5, 8, 22))
            pygame.draw.rect(surface, (212, 55, 63), (self.rect.x + 5, self.rect.y + 12, 22, 8))
        elif self.kind == "clock":
            pygame.draw.rect(surface, (99, 190, 237), self.rect)
            pygame.draw.rect(surface, (231, 244, 245), (self.rect.x + 5, self.rect.y + 5, 22, 22))
            pygame.draw.rect(surface, (45, 72, 107), (self.rect.centerx - 2, self.rect.y + 9, 4, 10))
            pygame.draw.rect(surface, (45, 72, 107), (self.rect.centerx, self.rect.centery - 2, 8, 4))
        elif self.kind == "shield":
            pygame.draw.rect(surface, (39, 74, 66), self.rect)
            # Ícone de escudo em degraus para manter a leitura pixel art.
            green, light = (61, 211, 129), (162, 255, 191)
            pygame.draw.rect(surface, green, (self.rect.x + 7, self.rect.y + 5, 18, 5))
            pygame.draw.rect(surface, green, (self.rect.x + 5, self.rect.y + 10, 22, 10))
            pygame.draw.rect(surface, green, (self.rect.x + 8, self.rect.y + 20, 16, 5))
            pygame.draw.rect(surface, green, (self.rect.x + 12, self.rect.y + 25, 8, 3))
            pygame.draw.rect(surface, light, (self.rect.x + 12, self.rect.y + 8, 4, 13))
        else:
            pygame.draw.rect(surface, (76, 61, 66), self.rect)
            pygame.draw.rect(surface, (36, 34, 43), (self.rect.x + 5, self.rect.y + 8, 22, 20))
            pygame.draw.rect(surface, (240, 83, 65), (self.rect.x + 14, self.rect.y + 2, 5, 8))
            pygame.draw.rect(surface, (255, 220, 75), (self.rect.x + 19, self.rect.y, 6, 3))
