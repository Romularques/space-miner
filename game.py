from __future__ import annotations

import random
import sys

import pygame

from falling_number import FallingNumber
from audio import Audio
if sys.platform == "emscripten":
    from global_scores import GlobalScores
else:
    from high_scores import HighScores
from monster import Monster
from powerup import Powerup
from pixel_font import PixelFont
from player import Player
from settings import (
    BACKGROUND_COLOR, FPS, GROUND_COLOR, GROUND_TOP, HEIGHT,
    MIN_SPAWN_INTERVAL_MS, SKY_COLOR, SPAWN_INTERVAL_MS, TITLE, WIDTH, WINDOW_HEIGHT, WINDOW_WIDTH,
)


class Game:
    """Controla a partida, as fases e os estados de conclusão/fim de jogo."""

    BASE_GOAL_PER_PHASE = 10
    EXTRA_GOAL_PER_PHASE = 2
    ENERGY_BONUS = 5

    def __init__(self) -> None:
        pygame.init()
        self.audio = Audio()
        # Toda a lógica desenha na resolução-base; a janela só apresenta uma versão ampliada.
        self.window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE)
        self.screen = pygame.Surface((WIDTH, HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.hud_font = PixelFont(3)
        self.number_font = PixelFont(3)
        self.info_font = PixelFont(2)
        self.title_font = PixelFont(6)
        self.high_scores = GlobalScores() if sys.platform == "emscripten" else HighScores()
        self.running = True
        self.last_direction_tap = {-1: -1_000, 1: -1_000}
        self.story_screen = True
        self.instructions_screen = False
        self.title_screen = False
        self.reset()

    def reset(self) -> None:
        self.player = Player()
        self.score = 0
        self.phase = 1
        self.feedbacks: list[list[object]] = []
        self.explosions: list[list[object]] = []
        self.game_over = False
        self.name_entry = False
        self.initials = ""
        self.phase_complete = False
        self.start_phase()

    def start_phase(self) -> None:
        """Inicia uma fase com energia cheia, sem mexer na pontuação total."""
        self.energy = 10
        self.collected = 0
        self.numbers: list[FallingNumber] = []
        self.spawn_elapsed_ms = 700.0
        self.phase_bonus = 0
        self.phase_bonus_awarded = False
        self.phase_complete = False
        self.damage_flash_ms = 0.0
        self.monster: Monster | None = None
        self.audio.stop_monster()
        self.monster_roll_ms = 0.0
        self.powerups: dict[str, Powerup | None] = {"medkit": None, "clock": None, "bomb": None}
        self.powerup_roll_ms = {"medkit": 0.0, "clock": 0.0, "bomb": 0.0}
        self.slow_motion_ms = 0.0
        self.audio.set_slow(False)
        self.bomb_flash_ms = 0.0
        self.background = self.generate_background()

    def generate_background(self) -> pygame.Surface:
        """Cria um céu espacial escuro exclusivo para a fase atual."""
        themes = [
            ((8, 13, 37), (42, 29, 50), (17, 34, 48), (111, 80, 185)),
            ((28, 8, 33), (50, 22, 43), (43, 18, 45), (228, 85, 143)),
            ((5, 25, 37), (18, 46, 50), (10, 42, 50), (82, 199, 182)),
            ((34, 19, 11), (50, 38, 25), (48, 30, 25), (245, 165, 72)),
            ((13, 25, 34), (37, 48, 50), (19, 40, 50), (164, 213, 255)),
        ]
        sky, nebula, mountain, accent = random.choice(themes)
        background = pygame.Surface((WIDTH, GROUND_TOP))
        background.fill(sky)
        for _ in range(random.randint(16, 30)):
            x, y = random.randrange(WIDTH), random.randrange(GROUND_TOP)
            color = random.choice([(136, 183, 255), (255, 220, 143), (225, 184, 255), (181, 252, 238), accent])
            size = random.choice((2, 3, 4))
            pygame.draw.rect(background, color, (x, y, size, size))
        # Nebulosas translúcidas, planetas em discos simples e montanhas distantes em blocos.
        mist = pygame.Surface((WIDTH, GROUND_TOP), pygame.SRCALPHA)
        for _ in range(4):
            color = (*nebula, random.randrange(28, 58))
            pygame.draw.circle(mist, color, (random.randrange(WIDTH), random.randrange(50, 300)), random.randrange(70, 150))
        background.blit(mist, (0, 0))
        for _ in range(random.randint(1, 3)):
            radius = random.randrange(24, 52)
            x, y = random.randrange(radius, WIDTH - radius), random.randrange(radius, 210)
            # Planetas recebem a maior parte da cor do próprio céu, evitando contraste excessivo.
            planet_color = tuple(round(sky[index] * 0.72 + accent[index] * 0.28) for index in range(3))
            highlight = tuple(min(105, value + 24) for value in planet_color)
            pygame.draw.circle(background, planet_color, (x, y), radius)
            pygame.draw.circle(background, highlight, (x - radius // 3, y - radius // 3), max(4, radius // 6))
            if random.random() < 0.6:
                pygame.draw.line(background, highlight, (x - radius, y), (x + radius, y), 2)
        mountain_color = mountain
        points = [(0, GROUND_TOP)]
        for x in range(0, WIDTH + 120, 120):
            points.extend([(x + 55, random.randrange(GROUND_TOP - 130, GROUND_TOP - 55)), (x + 120, GROUND_TOP)])
        pygame.draw.polygon(background, mountain_color, points)
        return background

    def lose_energy(self, amount: int) -> None:
        self.energy = max(0, self.energy - amount)
        self.damage_flash_ms = 140
        self.audio.play("ouch")
        if self.energy <= 0:
            self.game_over = True
            self.audio.stop_monster()
            self.name_entry = self.high_scores.qualifies(self.score, self.phase)

    def save_score(self) -> None:
        """Salva um resultado elegível após receber exatamente três iniciais."""
        if sys.platform == "emscripten":
            self.high_scores.submit_in_background(self.initials, self.score, self.phase)
        else:
            self.high_scores.add(self.initials, self.score, self.phase)
        self.name_entry = False

    def max_numbers(self) -> int:
        # Curva agressiva: 3, 6, 9... até o limite de 20 números em tela.
        return min(20, self.phase * 3)

    def numbers_needed(self) -> int:
        """Meta de coleta: 10, 12, 14... conforme a fase avança."""
        return self.BASE_GOAL_PER_PHASE + (self.phase - 1) * self.EXTRA_GOAL_PER_PHASE

    def spawn_interval_ms(self) -> int:
        return max(MIN_SPAWN_INTERVAL_MS, SPAWN_INTERVAL_MS - (self.phase - 1) * 100)

    def monster_chance(self) -> float:
        """5% na Fase 1, crescendo linearmente até 30% na Fase 10."""
        return min(0.30, 0.05 + (self.phase - 1) * (0.25 / 9))

    def monster_speed(self) -> float:
        """Progressão linear: 400 px/s na Fase 1 até 600 px/s na Fase 15."""
        return min(600.0, 400.0 + (self.phase - 1) * (200.0 / 14))

    def add_feedback(self, value: int, position: tuple[int, int]) -> None:
        self.feedbacks.append([str(value), pygame.Vector2(position), 0.0])

    def add_explosion(self, position: tuple[int, int]) -> None:
        self.explosions.append([pygame.Vector2(position), 0.0])

    def finish_phase(self) -> None:
        self.phase_bonus = self.energy * self.ENERGY_BONUS
        self.numbers.clear()  # Números da fase anterior não continuam na próxima.
        self.monster = None
        self.audio.stop_monster()
        self.phase_complete = True
        self.audio.play("celebrate")

    def handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.VIDEORESIZE:
                self.window = pygame.display.set_mode(event.size, pygame.RESIZABLE)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif self.story_screen:
                    self.story_screen = False
                    self.instructions_screen = True
                    self.audio.play("poc")
                elif self.instructions_screen:
                    self.instructions_screen = False
                    self.title_screen = True
                    self.audio.play("poc")
                elif self.title_screen:
                    self.title_screen = False
                    self.audio.play("poc")
                elif not self.game_over and not self.phase_complete and event.key in (pygame.K_a, pygame.K_LEFT, pygame.K_d, pygame.K_RIGHT):
                    direction = -1 if event.key in (pygame.K_a, pygame.K_LEFT) else 1
                    now = pygame.time.get_ticks()
                    if now - self.last_direction_tap[direction] <= 250:
                        self.player.dash(direction)
                        self.audio.play("vuush")
                    self.last_direction_tap[direction] = now
                elif self.game_over and event.key in (pygame.K_r, pygame.K_RETURN, pygame.K_SPACE):
                    if not self.name_entry:
                        self.reset()
                        self.audio.play("poc")
                elif self.phase_complete and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    if not self.phase_bonus_awarded:
                        self.score += self.phase_bonus
                        self.phase_bonus_awarded = True
                    else:
                        self.phase += 1
                        self.start_phase()
                    self.audio.play("poc")
                elif not self.game_over and event.key in (pygame.K_w, pygame.K_UP, pygame.K_SPACE):
                    if self.player.jump():
                        self.audio.play("vuush")
                elif self.name_entry:
                    if event.key == pygame.K_BACKSPACE:
                        self.initials = self.initials[:-1]
                    elif event.unicode.isalpha() and len(self.initials) < 3:
                        self.initials += event.unicode.upper()
                        self.audio.play("poc")
                        if len(self.initials) == 3:
                            self.save_score()

    def update_feedbacks(self, dt: float) -> None:
        for feedback in self.feedbacks[:]:
            feedback[2] += dt * 1000
            # O número fica no ponto de coleta por meio segundo e só então sobe.
            if feedback[2] > 500:
                feedback[1].y -= 28 * dt
            if feedback[2] > 1_300:
                self.feedbacks.remove(feedback)

    def update_explosions(self, dt: float) -> None:
        for explosion in self.explosions[:]:
            explosion[1] += dt * 1000
            if explosion[1] > 360:
                self.explosions.remove(explosion)

    def detonate_bomb(self) -> None:
        """Destrói tudo em cena; minerais comuns contam como coleta pontuada."""
        for number in self.numbers:
            if number.radioactive:
                self.score += 10
                self.add_feedback(10, number.rect.midtop)
            else:
                self.score += number.current_value
                self.collected += 1
                self.add_feedback(number.current_value, number.rect.midtop)
        self.numbers.clear()
        if self.monster:
            self.score += 10
            self.add_feedback(10, self.monster.rect.midtop)
        self.monster = None
        self.audio.stop_monster()
        for kind in self.powerups:
            self.powerups[kind] = None
        self.bomb_flash_ms = 150
        if self.collected >= self.numbers_needed():
            self.finish_phase()

    def update_powerups(self, dt: float, slowed_dt: float) -> None:
        """Atualiza duração desacelerada dos itens e sorteia cada tipo a cada segundo real."""
        for kind in tuple(self.powerups):
            item = self.powerups[kind]
            if item:
                if item.update(slowed_dt):
                    self.powerups[kind] = None
                elif self.player.rect.colliderect(item.rect):
                    self.powerups[kind] = None
                    if kind == "medkit":
                        self.energy = 10
                        self.audio.play("medkit")
                    elif kind == "clock":
                        self.slow_motion_ms = 5_000
                        self.audio.set_slow(True)
                    else:
                        self.audio.play("bomb")
                        self.detonate_bomb()
                        return
            else:
                self.powerup_roll_ms[kind] += dt * 1000
                if self.powerup_roll_ms[kind] >= 1_000:
                    self.powerup_roll_ms[kind] -= 1_000
                    if random.random() < 0.02:
                        self.powerups[kind] = Powerup(kind)

    def update(self, dt: float) -> None:
        self.damage_flash_ms = max(0, self.damage_flash_ms - dt * 1000)
        self.bomb_flash_ms = max(0, self.bomb_flash_ms - dt * 1000)
        self.update_explosions(dt)
        if self.story_screen or self.instructions_screen or self.title_screen or self.game_over or self.phase_complete:
            return
        was_slow = self.slow_motion_ms > 0
        self.slow_motion_ms = max(0, self.slow_motion_ms - dt * 1000)
        if was_slow and self.slow_motion_ms == 0:
            self.audio.set_slow(False)
        slowed_dt = dt * (0.10 if self.slow_motion_ms > 0 else 1.0)
        if self.player.update(dt):
            self.audio.play("tuf")
        self.spawn_elapsed_ms += slowed_dt * 1000
        if self.spawn_elapsed_ms >= self.spawn_interval_ms() and len(self.numbers) < self.max_numbers():
            self.numbers.append(FallingNumber())
            self.spawn_elapsed_ms = 0
        if self.monster:
            if self.monster.update(slowed_dt):
                self.monster = None
                self.audio.stop_monster()
            elif self.player.rect.colliderect(self.monster.rect):
                self.audio.play("impact")
                self.lose_energy(3)
                self.monster = None
                self.audio.stop_monster()
        else:
            self.monster_roll_ms += dt * 1000
            if self.monster_roll_ms >= 1_000:
                self.monster_roll_ms -= 1_000
                if random.random() < self.monster_chance():
                    self.monster = Monster(random.choice((True, False)), self.monster_speed())
                    self.audio.start_monster()

        for number in self.numbers[:]:
            reached_ground = number.update(slowed_dt)
            if self.player.rect.colliderect(number.rect):
                self.numbers.remove(number)
                if number.radioactive:
                    self.audio.play("impact")
                    self.lose_energy(2)
                    if self.game_over:
                        break
                else:
                    self.score += number.current_value
                    self.collected += 1
                    self.add_feedback(number.current_value, number.rect.midtop)
                    self.audio.play("mineral")
                    if self.collected >= self.numbers_needed():
                        self.finish_phase()
                        break
            elif reached_ground:
                self.score += number.current_value
                if not number.radioactive:
                    self.lose_energy(1)
                self.audio.play("impact")
                self.add_explosion(number.rect.midbottom)
                self.numbers.remove(number)
                if self.game_over:
                    break
        self.update_powerups(dt, slowed_dt)
        self.update_feedbacks(dt)

    def draw_hud(self) -> None:
        phase = self.hud_font.render(f"Fase: {self.phase}", False, (255, 255, 255))
        score = self.hud_font.render(f"Pontos: {self.score}", False, (255, 255, 255))
        energy = self.hud_font.render("Energia", False, (255, 255, 255))
        collected = self.hud_font.render(f"Minerais coletados: {self.collected}/{self.numbers_needed()}", False, (255, 255, 255))
        # Informações de progresso ficam no rodapé, sobre a faixa verde do chão.
        self.screen.blit(phase, (20, GROUND_TOP + 12))
        self.screen.blit(score, (WIDTH - score.get_width() - 20, GROUND_TOP + 33))
        segment_width, segment_gap = 10, 2
        bar_width = 10 * segment_width + 9 * segment_gap
        label_x = WIDTH - energy.get_width() - 8 - bar_width - 20
        bar_x, bar_y = label_x + energy.get_width() + 8, 19
        self.screen.blit(energy, (label_x, 14))
        bar_color = (100, 225, 145) if self.energy > 6 else (245, 201, 67) if self.energy > 3 else (238, 77, 73)
        for index in range(10):
            segment = pygame.Rect(bar_x + index * (segment_width + segment_gap), bar_y, segment_width, 13)
            pygame.draw.rect(self.screen, (33, 39, 52), segment.inflate(3, 3))
            if index < self.energy:
                pygame.draw.rect(self.screen, bar_color, segment)
        self.screen.blit(collected, (20, GROUND_TOP + 39))

    def draw_overlay(self) -> None:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((8, 11, 19, 205))
        self.screen.blit(overlay, (0, 0))
        if self.game_over:
            title = self.title_font.render("GAME OVER", False, (255, 110, 110))
            lines = [f"Pontuação final: {self.score}", f"Fase alcançada: {self.phase}"]
            if self.name_entry:
                lines.extend([
                    "ENTROU NO TOP 10! DIGITE 3 LETRAS:",
                    f"[ {self.initials.ljust(3, '_')} ]",
                ])
            else:
                lines.append("Pressione R, Enter ou Espaço para reiniciar")
        else:
            title = self.title_font.render(f"FASE {self.phase} CONCLUÍDA!", False, (110, 235, 152))
            if self.phase_bonus_awarded:
                lines = [
                    f"Bônus de energia adicionado: {self.energy} × {self.ENERGY_BONUS} = +{self.phase_bonus}",
                    f"Pontuação total: {self.score}",
                    "Pressione Enter ou Espaço para a próxima fase",
                ]
            else:
                lines = [
                    f"Você coletou {self.collected}/{self.numbers_needed()} minerais!",
                    f"Bônus de energia disponível: {self.energy} × {self.ENERGY_BONUS} = {self.phase_bonus}",
                    "Pressione Enter ou Espaço para receber o bônus",
                ]
        title_y = 74 if self.game_over else HEIGHT // 2 - 65
        line_y = 132 if self.game_over else HEIGHT // 2
        line_spacing = 28 if self.game_over else 36
        self.screen.blit(title, title.get_rect(center=(WIDTH // 2, title_y)))
        for index, line in enumerate(lines):
            text = self.hud_font.render(line, False, (255, 255, 255))
            self.screen.blit(text, text.get_rect(center=(WIDTH // 2, line_y + index * line_spacing)))
        if self.game_over and not self.name_entry:
            self.draw_high_scores(line_y + len(lines) * line_spacing + 24)

    def draw_high_scores(self, top: int) -> None:
        """Exibe as dez posições no formato clássico de fliperama."""
        heading = self.info_font.render("TOP 10  -  PONTOS / FASE / NOME", False, (255, 218, 112))
        self.screen.blit(heading, heading.get_rect(center=(WIDTH // 2, top)))
        for index, entry in enumerate(self.high_scores.scores):
            line = f"{index + 1:02d}  {int(entry['score']):06d}  F{int(entry['phase']):02d}  {entry['initials']}"
            text = self.info_font.render(line, False, (255, 255, 255))
            self.screen.blit(text, text.get_rect(center=(WIDTH // 2, top + 23 + index * 20)))

    def draw_explosions(self) -> None:
        for position, elapsed in self.explosions:
            frame = min(2, int(elapsed / 120))
            size = (10, 20, 30)[frame]
            colors = ((255, 226, 92), (255, 139, 53), (213, 63, 50))
            for index, color in enumerate(colors):
                offset = (index - 1) * (size // 2)
                pygame.draw.rect(self.screen, color, (position.x + offset - 4, position.y - size // 2, 8, size))
                pygame.draw.rect(self.screen, color, (position.x - size // 2, position.y + offset - 4, size, 8))

    def draw(self) -> None:
        self.screen.fill(BACKGROUND_COLOR)
        self.screen.blit(self.background, (0, 0))
        pygame.draw.rect(self.screen, GROUND_COLOR, (0, GROUND_TOP, WIDTH, HEIGHT - GROUND_TOP))
        pygame.draw.line(self.screen, (141, 202, 111), (0, GROUND_TOP), (WIDTH, GROUND_TOP), 4)
        # Minerais e blocos de solo reforçam a leitura arcade com paleta limitada.
        for x, y in ((80, 90), (195, 145), (330, 65), (520, 125), (690, 75), (850, 155)):
            pygame.draw.rect(self.screen, (220, 236, 255), (x, y, 4, 4))
        for x in range(0, WIDTH, 32):
            pygame.draw.rect(self.screen, (86, 126, 70), (x, GROUND_TOP + 15, 22, 7))
        for number in self.numbers:
            number.draw(self.screen, self.number_font)
        for item in self.powerups.values():
            if item:
                item.draw(self.screen)
        self.draw_explosions()
        if self.monster:
            self.monster.draw(self.screen)
        self.player.draw(self.screen)
        self.draw_hud()
        for text, position, elapsed in self.feedbacks:
            opacity = 255 if elapsed <= 500 else round(255 * max(0, 1 - (elapsed - 500) / 800))
            rendered = self.hud_font.render(text, False, (255, 255, 255))
            outlined = self.hud_font.render(text, False, (54, 60, 73))
            feedback_surface = pygame.Surface((rendered.get_width() + 8, rendered.get_height() + 8), pygame.SRCALPHA)
            for offset_x, offset_y in ((0, 2), (2, 0), (4, 2), (2, 4)):
                feedback_surface.blit(outlined, (offset_x, offset_y))
            feedback_surface.blit(rendered, (2, 2))
            feedback_surface.set_alpha(opacity)
            self.screen.blit(feedback_surface, feedback_surface.get_rect(center=position))
        if self.game_over or self.phase_complete:
            self.draw_overlay()
        if self.story_screen:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((3, 7, 18, 225))
            self.screen.blit(overlay, (0, 0))
            heading = self.title_font.render("HISTORIA", False, (255, 183, 75))
            lines = [
                "NA ESTACAO MINERADORA DO CINTURAO DE CERES,",
                "AS MAQUINAS SE REBELARAM.",
                "ELAS ABANDONARAM A MINERACAO E AGORA ATACAM.",
                "USE SEU JET PACK PARA COLETAR MINERAIS",
                "E DESVIE DOS ROBOS REBELDES.",
                "APERTE QUALQUER TECLA PARA CONTINUAR",
            ]
            self.screen.blit(heading, heading.get_rect(center=(WIDTH // 2, 82)))
            for index, line in enumerate(lines):
                text = self.hud_font.render(line, False, (255, 255, 255))
                self.screen.blit(text, text.get_rect(center=(WIDTH // 2, 155 + index * 48)))
        elif self.instructions_screen:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((3, 7, 18, 225))
            self.screen.blit(overlay, (0, 0))
            heading = self.title_font.render("COMO JOGAR", False, (112, 232, 157))
            lines = [
                "A/D OU SETAS: MOVER", "W, CIMA OU ESPACO: PULAR", "VOCE TEM PULO DUPLO.",
                "TOQUE DUAS VEZES ESQUERDA OU DIREITA: DASH.", "QUANTO MAIS CEDO PEGAR UM MINERAL, MAIS PONTOS VALE.",
                "MINERAIS BAIXOS PODEM VALER NEGATIVO,", "MAS E MELHOR QUE PERDER UMA VIDA.",
                "A CADA FASE, SUA ENERGIA VOLTA A 10.", "ENERGIA PRESERVADA GERA BONUS DE PONTOS.",
                "APERTE QUALQUER TECLA PARA CONTINUAR",
            ]
            self.screen.blit(heading, heading.get_rect(center=(WIDTH // 2, 65)))
            for index, line in enumerate(lines):
                text = self.info_font.render(line, False, (255, 255, 255))
                self.screen.blit(text, text.get_rect(center=(WIDTH // 2, 125 + index * 36)))
        elif self.title_screen:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((3, 7, 18, 215))
            self.screen.blit(overlay, (0, 0))
            title = self.title_font.render("SPACE MINER", False, (112, 232, 157))
            prompt = self.hud_font.render("APERTE QUALQUER TECLA PARA COMEÇAR", False, (255, 255, 255))
            self.screen.blit(title, title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 35)))
            self.screen.blit(prompt, prompt.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 35)))
        if self.damage_flash_ms > 0:
            flash = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            flash.fill((255, 35, 45, round(150 * self.damage_flash_ms / 140)))
            self.screen.blit(flash, (0, 0))
        if self.bomb_flash_ms > 0:
            flash = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            flash.fill((255, 255, 255, round(220 * self.bomb_flash_ms / 150)))
            self.screen.blit(flash, (0, 0))
        window_width, window_height = self.window.get_size()
        scale = min(window_width / WIDTH, window_height / HEIGHT)
        target_size = (round(WIDTH * scale), round(HEIGHT * scale))
        scaled_screen = pygame.transform.scale(self.screen, target_size)
        self.window.fill((0, 0, 0))
        self.window.blit(scaled_screen, ((window_width - target_size[0]) // 2, (window_height - target_size[1]) // 2))
        pygame.display.flip()

    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(FPS) / 1000
            self.handle_events()
            self.update(dt)
            self.draw()
        pygame.quit()

    async def run_web(self) -> None:
        """Loop cooperativo necessário para Pygbag manter o navegador responsivo."""
        await self.high_scores.refresh()
        while self.running:
            dt = self.clock.tick(FPS) / 1000
            self.handle_events()
            self.update(dt)
            self.draw()
            # No navegador, cede o controle ao JavaScript a cada quadro.
            import asyncio
            await asyncio.sleep(0)
