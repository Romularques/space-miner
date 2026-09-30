from __future__ import annotations

import math

import pygame

from settings import GROUND_TOP, WIDTH


class Monster:
    """Robô maligno pixelado com caminhada em dois frames."""

    WIDTH, HEIGHT, BASE_SPEED = 78, 96, 510

    def __init__(self, moving_right: bool, speed: float = BASE_SPEED) -> None:
        self.moving_right = moving_right
        self.speed = speed
        self.rect = pygame.Rect(0, 0, self.WIDTH, self.HEIGHT)
        self.rect.bottom = GROUND_TOP
        self.rect.x = -self.WIDTH if moving_right else WIDTH
        self.position_x = float(self.rect.x)
        self.animation_time = 0.0

    def update(self, dt: float) -> bool:
        self.position_x += (1 if self.moving_right else -1) * self.speed * dt
        self.rect.x = round(self.position_x)
        self.animation_time += dt
        return self.rect.left > WIDTH or self.rect.right < 0

    def draw(self, surface: pygame.Surface) -> None:
        scale = 6
        sprite = pygame.Surface((13 * scale, 16 * scale), pygame.SRCALPHA)
        outline, body, light, shadow = (29, 20, 37), (207, 57, 68), (255, 130, 102), (103, 28, 47)
        frame = int(self.animation_time * 9) % 2
        blocks = [(6, 0, 1, 2, outline), (5, 1, 3, 1, body), (2, 2, 9, 5, outline),
                  (3, 3, 7, 3, body), (4, 4, 2, 1, light), (8, 4, 2, 1, light),
                  (3, 7, 7, 5, outline), (4, 7, 5, 5, body), (1, 8, 2, 3, shadow),
                  (10, 8, 2, 3, shadow), (2, 10, 1, 2, body), (11, 10, 1, 2, body)]
        legs = [(4, 12, 2, 3, shadow), (8, 13, 2, 2, shadow)] if frame == 0 else [(4, 13, 2, 2, shadow), (8, 12, 2, 3, shadow)]
        blocks.extend(legs)
        for x, y, width, height, color in blocks:
            pygame.draw.rect(sprite, color, (x * scale, y * scale, width * scale, height * scale))
        if not self.moving_right:
            sprite = pygame.transform.flip(sprite, True, False)
        bob = round(math.sin(self.animation_time * math.pi * 9) * 3)
        surface.blit(sprite, (self.rect.x, self.rect.y + bob))
