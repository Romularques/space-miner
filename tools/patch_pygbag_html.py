"""Remove referência obsoleta ao BrowserFS no template do Pygbag 0.9.3."""

from pathlib import Path
import re
import sys


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Uso: python tools/patch_pygbag_html.py CAMINHO/DO/index.html")
    page = Path(sys.argv[1])
    content = page.read_text(encoding="utf-8")
    fixed, replacements = re.subn(
        r'\s*<script src="[^"]*browserfs\.min\.js"></script>', "", content
    )
    if replacements != 1:
        raise RuntimeError(f"Esperava remover 1 referência ao BrowserFS; encontrei {replacements}.")
    page.write_text(fixed, encoding="utf-8")


if __name__ == "__main__":
    main()
