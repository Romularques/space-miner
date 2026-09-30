"""Ajusta o template do Pygbag para o Space Miner."""

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
    fixed, replacements = re.subn(r"<title>.*?</title>", "<title>Space Miner</title>", fixed, count=1)
    if replacements != 1:
        raise RuntimeError(f"Esperava substituir 1 título; encontrei {replacements}.")
    fixed, replacements = re.subn(
        r'<link rel="icon" type="image/png" href="favicon\.png" sizes="16x16">',
        f'<link rel="icon" type="image/svg+xml" href="favicon.svg?v={revision}">',
        fixed,
        count=1,
    )
    if replacements != 1:
        raise RuntimeError(f"Esperava substituir 1 favicon; encontrei {replacements}.")
    fixed = fixed.replace('platform.document.body.style.background = "#7f7f7f"', 'platform.document.body.style.background = "#000000"')
    loader_theme = """
    <style id="space-miner-loader-theme">
        html, body { background: #000 !important; }
        #transfer { position: fixed; inset: 0; display: flex !important; flex-direction: column;
                    align-items: center; justify-content: center; gap: 14px; background: #000; }
        #status { margin: 0; color: #fff; font: 600 18px/1.4 Arial, sans-serif; }
        #progress { accent-color: #fff; }
        #infobox { background: transparent; color: #fff; padding: 0; font: 600 18px/1.4 Arial, sans-serif;
                   text-align: center; box-shadow: none; }
    </style>
    """
    fixed = fixed.replace("</head>", loader_theme + "</head>", 1)
    page.write_text(fixed, encoding="utf-8")


if __name__ == "__main__":
    main()
