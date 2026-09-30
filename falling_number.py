from __future__ import annotations

import math
import random

import pygame

from settings import FALL_TIME_MAX_MS, FALL_TIME_MIN_MS, GROUND_TOP, STAR_FALL_GRAVITY, WIDTH


class FallingNumber:
    """Estrela irregular em três estágios; seu valor só é exibido ao coletá-la."""

    SMALL_SIZE = 38
    MISSILE_WIDTH = 62
    MISSILE_HEIGHT = 96

    def __init__(self) -> None:
        self.initial_value = random.randint(10, 20)
        self.final_ground_value = random.randint(-5, 0)
        self.required_losses = self.initial_value - self.final_ground_value
        # Quanto maior a diferença de pontos, menor a duração e maior a velocidade inicial da queda.
        # Com valores 10–20 e finais −5–0, a diferença possível é 10–25.
        min_losses, max_losses = 10, 25
        ratio = (self.required_losses - min_losses) / (max_losses - min_losses)
        self.fall_time_ms = round(FALL_TIME_MAX_MS - ratio * (FALL_TIME_MAX_MS - FALL_TIME_MIN_MS))
        self.current_value = self.initial_value
        self.elapsed_ms = 0.0
        self.radioactive = random.random() < 0.03
        self.start_size = self.MISSILE_WIDTH if self.radioactive else random.randint(94, 120)
        self.base_color = random.choice([(72, 196, 255), (112, 232, 157), (247, 198, 74), (176, 120, 245), (255, 136, 185)])
        if self.radioactive:
            self.base_color = (220, 66, 53)
        self.vertices = self._make_vertices()
        self.center_x = random.randint(self._dimensions()[0] // 2, WIDTH - self._dimensions()[0] // 2)
        # A base fica alinhada ao topo: o primeiro movimento já coloca a estrela dentro da tela.
        self.center_y = -self._dimensions()[1] / 2
        total_time = self.fall_time_ms / 1000
        distance = GROUND_TOP - self._dimensions()[1] / 2 - self.center_y
        self.velocity_y = (distance - 0.5 * STAR_FALL_GRAVITY * total_time**2) / total_time
        self.rect = pygame.Rect(0, 0, *self._dimensions())
        self._resize_rect()

    def _make_vertices(self) -> list[tuple[float, float]]:
        """Gera uma silhueta assimétrica única, com pontas e reentrâncias irregulares."""
        vertices = []
        count = random.randint(9, 13)
        for index in range(count):
            angle = -math.pi / 2 + index * 2 * math.pi / count
            radius = random.uniform(0.48, 1.0) if index % 2 == 0 else random.uniform(0.34, 0.67)
            vertices.append((math.cos(angle) * radius, math.sin(angle) * radius))
        return vertices

    def stage(self) -> int:
        return min(2, int(self.elapsed_ms / (self.fall_time_ms / 3)))

    def _dimensions(self) -> tuple[int, int]:
        if self.radioactive:
            return self.MISSILE_WIDTH, self.MISSILE_HEIGHT
        # Mudanças discretas: grande, médio e pequeno, sem interpolação visual.
        size = (self.start_size, round(self.start_size * 0.67), self.SMALL_SIZE)[self.stage()]
        return size, size

    def _color(self) -> tuple[int, int, int]:
        if self.radioactive:
            pulse = (math.sin(self.elapsed_ms * 0.014) + 1) / 2
            red = round(220 + 35 * pulse)
            green = round(66 + 76 * pulse)
            return (red, green, 50)
        red, green, blue = self.base_color
        added_red = (0, 65, 125)[self.stage()]
        return (min(255, red + added_red), max(35, green - added_red // 3), max(35, blue - added_red // 3))

    def _resize_rect(self) -> None:
        self.rect = pygame.Rect(0, 0, *self._dimensions())
        self.rect.center = (round(self.center_x), round(self.center_y))

    def update(self, dt: float) -> bool:
        self.elapsed_ms = min(self.elapsed_ms + dt * 1000, self.fall_time_ms)
        # O valor subjacente percorre toda a faixa de maneira linear; a exibição continua inteira.
        progress = self.elapsed_ms / self.fall_time_ms
        losses = min(self.required_losses, int(progress * self.required_losses))
        self.current_value = self.initial_value - losses
        self.velocity_y += STAR_FALL_GRAVITY * dt
        self.center_y += self.velocity_y * dt
        self._resize_rect()
        reached_ground = self.elapsed_ms >= self.fall_time_ms or self.rect.bottom >= GROUND_TOP
        if reached_ground:
            self.current_value = self.final_ground_value
            self.center_y = GROUND_TOP - self._dimensions()[1] / 2
            self._resize_rect()
        return reached_ground

    def _points(self) -> list[tuple[int, int]]:
        radius = self.rect.width / 2
        return [(round(self.rect.centerx + x * radius), round(self.rect.centery + y * radius)) for x, y in self.vertices]

    def draw(self, surface: pygame.Surface, _font: pygame.font.Font) -> None:
        if self.radioactive:
            image = pygame.Surface((16, 24), pygame.SRCALPHA)
            color = self._color()
            frame = int(self.elapsed_ms / 130) % 2
            outline, dark, steel, eye = (35, 22, 34), (117, 31, 43), (107, 111, 119), (255, 237, 60)
            # Layout inspirado na referência: chama no alto, segmentos metálicos, aletas e face na ponta inferior.
            flame = [(7, 0, 2, 2, (255, 224, 57)), (6, 2, 4, 2, (255, 143, 44))] if frame == 0 else [
                (7, 0, 2, 1, (255, 224, 57)), (6, 1, 4, 3, (255, 111, 38))]
            blocks = flame + [
                (5, 3, 6, 2, outline), (6, 3, 4, 2, color),
                (4, 5, 8, 5, outline), (5, 5, 6, 5, color),
                (2, 7, 2, 4, dark), (12, 7, 2, 4, dark),  # aletas superiores
                (4, 10, 8, 3, outline), (5, 10, 6, 3, steel), (6, 11, 4, 2, dark),
                (3, 13, 10, 5, outline), (4, 13, 8, 5, color),
                (1, 14, 3, 4, dark), (12, 14, 3, 4, dark),  # aletas inferiores
                (4, 18, 8, 2, outline), (5, 18, 6, 2, steel),
                (4, 20, 8, 3, outline), (5, 20, 6, 3, dark),
                (5, 21, 2, 1, eye), (9, 21, 2, 1, eye), (7, 22, 2, 1, steel),
                (6, 23, 4, 1, color),
            ]
            for x, y, width, height, block_color in blocks:
                pygame.draw.rect(image, block_color, (x, y, width, height))
            surface.blit(pygame.transform.scale(image, self.rect.size), self.rect.topleft)
            return
        points = self._points()
        pygame.draw.polygon(surface, (25, 28, 48), [(x + 3, y + 4) for x, y in points])
        pygame.draw.polygon(surface, self._color(), points)
        pygame.draw.polygon(surface, (245, 244, 224), points, 2)
