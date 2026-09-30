from __future__ import annotations

import pygame

from settings import (
    DASH_DECELERATION, DASH_SPEED, FALL_GRAVITY, GRAVITY, GROUND_TOP, JUMP_SPEED, PLAYER_COLOR, PLAYER_HEIGHT,
    PLAYER_PIXEL_SIZE, PLAYER_SPEED, PLAYER_SPRITE_HEIGHT,
    PLAYER_SPRITE_WIDTH, PLAYER_WIDTH, WIDTH,
)


class Player:
    """Herói pixelado com espera, caminhada, pulo e pulo duplo."""

    WIDTH, HEIGHT = PLAYER_WIDTH, PLAYER_HEIGHT

    def __init__(self) -> None:
        self.rect = pygame.Rect(0, 0, self.WIDTH, self.HEIGHT)
        self.rect.midbottom = (WIDTH // 2, GROUND_TOP)
        self.position = pygame.Vector2(self.rect.topleft)
        self.velocity_y = 0.0
        self.on_ground = True
        self.jumps_remaining = 2
        self.facing_right = True
        self.walk_time = 0.0
        self.walk_frame = 0
        self.state = "idle"
        self.jetpack_time = 0.0
        self.jetpack_frame = 0
        self.jetpack_mode = ""
        self.dash_velocity = 0.0

    def jump(self) -> bool:
        if self.jumps_remaining > 0:
            self.velocity_y = -JUMP_SPEED
            self.jumps_remaining -= 1
            self.on_ground = False
            # Apenas o segundo salto aciona a breve animação do jetpack.
            if self.jumps_remaining == 0:
                self.jetpack_time = 0.34
                self.jetpack_mode = "jump"
            return self.jumps_remaining == 0
        return False

    def dash(self, direction: int) -> None:
        """Impulso horizontal de jetpack, disponível no chão e no ar."""
        self.facing_right = direction > 0
        self.dash_velocity = direction * DASH_SPEED
        self.jetpack_time = 0.28
        self.jetpack_mode = "dash"

    def update(self, dt: float) -> bool:
        was_on_ground = self.on_ground
        keys = pygame.key.get_pressed()
        direction = int(keys[pygame.K_d] or keys[pygame.K_RIGHT]) - int(keys[pygame.K_a] or keys[pygame.K_LEFT])
        if direction:
            self.facing_right = direction > 0
            self.walk_time += dt
            if self.walk_time >= 0.12:
                self.walk_frame = 1 - self.walk_frame
                self.walk_time = 0.0
        else:
            self.walk_time, self.walk_frame = 0.0, 0

        self.position.x = max(0, min(self.position.x + (direction * PLAYER_SPEED + self.dash_velocity) * dt, WIDTH - self.rect.width))
        if self.dash_velocity > 0:
            self.dash_velocity = max(0, self.dash_velocity - DASH_DECELERATION * dt)
        elif self.dash_velocity < 0:
            self.dash_velocity = min(0, self.dash_velocity + DASH_DECELERATION * dt)
        self.velocity_y += (FALL_GRAVITY if self.velocity_y > 0 else GRAVITY) * dt
        self.position.y += self.velocity_y * dt
        if self.jetpack_time > 0:
            self.jetpack_time = max(0, self.jetpack_time - dt)
            self.jetpack_frame = 1 - self.jetpack_frame
            if self.jetpack_time == 0:
                self.jetpack_mode = ""
        if self.position.y + self.rect.height >= GROUND_TOP:
            self.position.y, self.velocity_y, self.on_ground, self.jumps_remaining = GROUND_TOP - self.rect.height, 0, True, 2
        else:
            self.on_ground = False
        if not self.on_ground:
            self.state = "jump_up" if self.velocity_y < 0 else "jump_down"
        elif direction:
            self.state = "walk"
        else:
            self.state = "idle"
        self.rect.topleft = (round(self.position.x), round(self.position.y))
        return self.on_ground and not was_on_ground

    def _sprite(self) -> pygame.Surface:
        """Monta um sprite pixelado 14×16, ampliado sem suavização."""
        s = PLAYER_PIXEL_SIZE
        image = pygame.Surface((PLAYER_SPRITE_WIDTH * s, PLAYER_SPRITE_HEIGHT * s), pygame.SRCALPHA)
        dark, suit, light, visor, boot = (17, 31, 47), PLAYER_COLOR, (224, 255, 219), (255, 207, 76), (28, 42, 57)
        blocks = [(4, 1, 6, 1, dark), (3, 2, 8, 4, dark), (4, 2, 6, 3, light), (7, 3, 3, 1, visor),
                  (3, 6, 8, 6, dark), (4, 6, 6, 6, suit), (2, 7, 2, 4, suit), (10, 7, 2, 4, suit)]
        if self.state == "walk":
            legs = [(4, 12, 2, 3), (8, 13, 2, 2)] if self.walk_frame == 0 else [(4, 13, 2, 2), (8, 12, 2, 3)]
        elif self.state == "jump_up":
            legs = [(4, 12, 2, 2), (8, 12, 2, 2), (2, 10, 2, 2), (10, 10, 2, 2)]
        elif self.state == "jump_down":
            legs = [(3, 12, 3, 2), (8, 12, 3, 2), (2, 8, 2, 3), (10, 8, 2, 3)]
        else:
            legs = [(4, 12, 2, 3), (8, 12, 2, 3)]
        blocks.extend((x, y, w, h, boot) for x, y, w, h in legs)
        for x, y, w, h, color in blocks:
            pygame.draw.rect(image, color, (x * s, y * s, w * s, h * s))
        return pygame.transform.flip(image, True, False) if not self.facing_right else image

    def draw(self, surface: pygame.Surface) -> None:
        # A chama é desenhada atrás da mochila apenas durante o pulo duplo.
        if self.jetpack_time > 0:
            flame_size = 28 if self.jetpack_frame else 20
            if self.jetpack_mode == "dash":
                flame_x = self.rect.x - flame_size if self.facing_right else self.rect.right
                pygame.draw.rect(surface, (255, 92, 54), (flame_x, self.rect.centery - 9, flame_size, 18))
                inner_x = flame_x + 3 if self.facing_right else flame_x + flame_size - 11
                pygame.draw.rect(surface, (255, 218, 75), (inner_x, self.rect.centery - 4, 8, 8))
            else:
                backpack_x = self.rect.x + (0 if self.facing_right else self.rect.width - 18)
                pygame.draw.rect(surface, (255, 92, 54), (backpack_x, self.rect.y + 49, 18, flame_size))
                pygame.draw.rect(surface, (255, 218, 75), (backpack_x + 5, self.rect.y + 52, 8, flame_size - 7))
        surface.blit(self._sprite(), self.rect.topleft)
