"""Monta uma cópia mínima do jogo para o empacotador Pygbag.

Evita publicar o ambiente virtual, arquivos locais de ranking e infraestrutura
do Supabase dentro do download do navegador.
"""

from pathlib import Path
from shutil import copy2, rmtree


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / ".web-source"
FILES = (
    "main.py", "game.py", "settings.py", "player.py", "monster.py", "medkit.py", "powerup.py", "audio.py",
    "falling_number.py", "pixel_font.py", "global_scores.py", "web_config.py", "favicon.svg",
)


def main() -> None:
    if OUTPUT.exists():
        rmtree(OUTPUT)
    OUTPUT.mkdir()
    for filename in FILES:
        copy2(ROOT / filename, OUTPUT / filename)


if __name__ == "__main__":
    main()
