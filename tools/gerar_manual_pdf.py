# Gera MANUAL.pdf a partir de MANUAL.md.
# Uso: python tools/gerar_manual_pdf.py
# Requer: python -m pip install markdown  (Chrome/Edge usado para imprimir o PDF).

import os
import subprocess
import sys

import markdown

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MD = os.path.join(RAIZ, "MANUAL.md")
HTML = os.path.join(RAIZ, "MANUAL.html")
PDF = os.path.join(RAIZ, "MANUAL.pdf")

CSS = """
@page { size: A4; margin: 20mm 18mm; }
body { font-family: -apple-system, "Segoe UI", Helvetica, Arial, sans-serif;
       color: #1a1a1a; font-size: 11pt; line-height: 1.5; }
h1 { font-size: 22pt; font-weight: 700; margin: 0 0 4px; padding-bottom: 10px;
     border-bottom: 3px solid #333; }
h2 { font-size: 15pt; font-weight: 700; margin: 26px 0 10px;
     padding-bottom: 6px; border-bottom: 1px solid #ddd; }
h3 { font-size: 12.5pt; font-weight: 700; margin: 18px 0 8px; }
p, li { color: #222; }
a { color: #2a6dd8; text-decoration: none; }
code { font-family: "Consolas", "SFMono-Regular", monospace; font-size: 9.5pt;
       color: #c7254e; }
pre { background: #f5f6f7; border-radius: 4px; padding: 12px 14px;
      overflow-x: auto; }
pre code { color: #333; font-size: 9.5pt; line-height: 1.35; }
blockquote { background: #eef4fb; border-left: 4px solid #4a90d9;
             margin: 14px 0; padding: 10px 14px; color: #22415f; }
blockquote code { color: #b3355c; }
table { border-collapse: collapse; width: 100%; margin: 12px 0; font-size: 10pt; }
th { background: #2d3a4f; color: #fff; text-align: left; padding: 8px 10px;
     font-weight: 600; }
td { border: 1px solid #dcdcdc; padding: 7px 10px; vertical-align: top; }
tr:nth-child(even) td { background: #fafafa; }
"""

TEMPLATE = """<!doctype html><html lang="pt-br"><head>
<meta charset="utf-8"><style>{css}</style></head>
<body>{corpo}</body></html>"""


def achar_navegador():
    candidatos = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]
    for c in candidatos:
        if os.path.isfile(c):
            return c
    return None


def main():
    with open(MD, "r", encoding="utf-8") as f:
        texto = f.read()
    corpo = markdown.markdown(
        texto, extensions=["tables", "fenced_code", "sane_lists"])
    html = TEMPLATE.format(css=CSS, corpo=corpo)
    with open(HTML, "w", encoding="utf-8") as f:
        f.write(html)

    navegador = achar_navegador()
    if not navegador:
        sys.exit("Chrome/Edge nao encontrado. HTML gerado em MANUAL.html; "
                 "imprima-o para PDF manualmente.")

    url = "file:///" + HTML.replace("\\", "/")
    cmd = [navegador, "--headless", "--disable-gpu", "--no-pdf-header-footer",
           f"--print-to-pdf={PDF}", url]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if not os.path.isfile(PDF):
        sys.exit(f"Falha ao gerar PDF.\n{r.stderr}")
    print(f"OK: {PDF} ({os.path.getsize(PDF)} bytes)")


if __name__ == "__main__":
    main()
