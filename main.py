import asyncio
import sys

import pygame

from game import Game


if __name__ == "__main__":
    game = Game()
    if sys.platform == "emscripten":
        asyncio.run(game.run_web())
    else:
        game.run()
