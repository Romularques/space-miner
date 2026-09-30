"""Sintetizador pequeno de áudio arcade, sem arquivos externos."""

from array import array
import math
import random

import pygame


class Audio:
    RATE = 22_050

    def __init__(self) -> None:
        self.enabled = True
        self.monster_channel: pygame.mixer.Channel | None = None
        self.music_channel: pygame.mixer.Channel | None = None
        self.slow = False
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(self.RATE, -16, 1, 512)
            self.sounds = {
                "mineral": self._sound(0.22, 420, 640, 0.34),
                "vuush": self._sound(0.38, 560, 120, 0.30, noise=0.22),
                "tuf": self._sound(0.07, 100, 58, 0.238, noise=0.55),
                "ouch": self._sound(0.24, 185, 120, 0.40, noise=0.10),
                "impact": self._sound(0.20, 125, 55, 0.40, noise=0.32),
                "medkit": self._sound(0.62, 180, 390, 0.28),
                "bomb": self._sound(0.42, 130, 38, 0.50, noise=0.52),
                "celebrate": self._sound(0.70, 300, 720, 0.38),
                "poc": self._sound(0.06, 520, 360, 0.25),
                "monster": self._monster_sound(),
                "music": self._music(),
            }
            self.slow_sounds = {
                name: self._sound(duration, start, end, volume, noise, 0.62)
                for name, duration, start, end, volume, noise in (
                    ("mineral", 0.22, 420, 640, 0.34, 0), ("vuush", 0.38, 560, 120, 0.30, 0.22),
                    ("tuf", 0.07, 100, 58, 0.238, 0.55), ("ouch", 0.24, 185, 120, 0.40, 0.10),
                    ("impact", 0.20, 125, 55, 0.40, 0.32), ("medkit", 0.62, 180, 390, 0.28, 0),
                    ("bomb", 0.42, 130, 38, 0.50, 0.52), ("celebrate", 0.70, 300, 720, 0.38, 0),
                    ("poc", 0.06, 520, 360, 0.25, 0),
                )
            }
            self.slow_sounds["monster"] = self._monster_sound(0.62)
            self.slow_sounds["music"] = self._music(0.62)
            self.sounds["music"].set_volume(0.16)
            self.sounds["monster"].set_volume(0.18)
            self.slow_sounds["music"].set_volume(0.16)
            self.slow_sounds["monster"].set_volume(0.18)
            self._start_music()
        except pygame.error:
            self.enabled = False
            self.sounds = {}

    def _sound(self, duration: float, start: float, end: float, volume: float, noise: float = 0.0, pitch: float = 1.0) -> pygame.mixer.Sound:
        count = int(self.RATE * duration / pitch)
        samples = array("h")
        for index in range(count):
            progress = index / max(1, count - 1)
            frequency = (start + (end - start) * progress) * pitch
            envelope = min(1, index / (self.RATE * 0.012)) * (1 - progress) ** 1.7
            tone = math.sin(2 * math.pi * frequency * index / self.RATE)
            tone += noise * random.uniform(-1, 1)
            samples.append(max(-32767, min(32767, int(tone * envelope * volume * 32767))))
        return pygame.mixer.Sound(buffer=samples.tobytes())

    def _monster_sound(self, pitch: float = 1.0) -> pygame.mixer.Sound:
        samples = array("h")
        duration = 0.72 / pitch
        for index in range(int(self.RATE * duration)):
            time = index / self.RATE
            wobble = (95 + 35 * math.sin(time * math.pi * 6 * pitch)) * pitch
            value = math.sin(2 * math.pi * wobble * time) + 0.35 * math.sin(2 * math.pi * wobble * 2 * time)
            samples.append(int(value * 0.15 * 32767))
        return pygame.mixer.Sound(buffer=samples.tobytes())

    def _music(self, pitch: float = 1.0) -> pygame.mixer.Sound:
        samples = array("h")
        duration = int(8 / pitch)
        for index in range(self.RATE * duration):
            time = index / self.RATE
            beat = (time * pitch) % 2
            bass_frequency = (55, 65, 49, 58)[int(time * pitch // 2) % 4] * pitch
            bass = math.sin(2 * math.pi * bass_frequency * time) * math.exp(-beat * 1.7)
            pad = 0.30 * math.sin(2 * math.pi * (bass_frequency * 2) * time)
            pad += 0.16 * math.sin(2 * math.pi * (bass_frequency * 3 / 2) * time)
            samples.append(int((bass * 0.45 + pad * 0.18) * 0.22 * 32767))
        return pygame.mixer.Sound(buffer=samples.tobytes())

    def play(self, name: str) -> None:
        if self.enabled and name in self.sounds:
            (self.slow_sounds if self.slow else self.sounds)[name].play()

    def _start_music(self) -> None:
        if self.music_channel:
            self.music_channel.stop()
        self.music_channel = (self.slow_sounds if self.slow else self.sounds)["music"].play(-1)

    def set_slow(self, active: bool) -> None:
        if not self.enabled or self.slow == active:
            return
        monster_active = self.monster_channel is not None
        self.stop_monster()
        self.slow = active
        self._start_music()
        if monster_active:
            self.start_monster()

    def start_monster(self) -> None:
        if self.enabled and not self.monster_channel:
            self.monster_channel = (self.slow_sounds if self.slow else self.sounds)["monster"].play(-1)

    def stop_monster(self) -> None:
        if self.monster_channel:
            self.monster_channel.stop()
            self.monster_channel = None
