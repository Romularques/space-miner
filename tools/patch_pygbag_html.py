"""Remove referência obsoleta ao BrowserFS no template do Pygbag 0.9.3."""

from pathlib import Path
import re
import sys


def main() -> None:
    if len(sys.argv) not in (2, 3):
        raise SystemExit("Uso: python tools/patch_pygbag_html.py CAMINHO/DO/index.html [REVISAO]")
    page = Path(sys.argv[1])
    revision = sys.argv[2] if len(sys.argv) == 3 else "dev"
    content = page.read_text(encoding="utf-8")
    fixed, replacements = re.subn(
        r'\s*<script src="[^"]*browserfs\.min\.js"></script>', "", content
    )
    if replacements != 1:
        raise RuntimeError(f"Esperava remover 1 referência ao BrowserFS; encontrei {replacements}.")
    # GitHub Pages pode reutilizar o .tar.gz de uma versão anterior. A revisão na
    # query string preserva o arquivo no servidor e invalida o cache do navegador.
    fixed, replacements = re.subn(
        r'platform\.fopen\("\.web-source\.tar\.gz", "rb"\)',
        f'platform.fopen(".web-source.tar.gz?v={revision}", "rb")',
        fixed,
    )
    if replacements != 1:
        raise RuntimeError(f"Esperava versionar 1 arquivo do jogo; encontrei {replacements}.")
    page.write_text(fixed, encoding="utf-8")


if __name__ == "__main__":
    main()
