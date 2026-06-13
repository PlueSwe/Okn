#!/usr/bin/env python3
"""
Bygger en HELT självständig index.html från template.html.

Bäddar in typsnitt (Muli, base64), logotyp (base64) och beslutsdatat direkt i
filen så att den fungerar genom att bara dubbelklickas – även offline och utan
webbserver. Kör efter scrape.py (som genererar beslut.json).

  python3 scrape.py   # hämtar data
  python3 build.py     # bygger index.html
"""
import base64, json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))

# Muli (= Mulish) i de vikter appen använder. Filerna hämtas från
# overklagandenamnden.se/assets/fonts/Muli/ och ligger i ./fonts/.
FONTS = [
    ("Muli-Regular.ttf",  400),
    ("Muli-SemiBold.ttf", 600),
    ("Muli-Bold.ttf",     700),
    ("Muli-ExtraBold.ttf", 800),
]


def b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("ascii")


def fontface_css():
    css = []
    for fn, weight in FONTS:
        data = b64(os.path.join(HERE, "fonts", fn))
        css.append(
            "@font-face{font-family:'Mulish';font-style:normal;font-weight:%d;"
            "font-display:swap;src:url(data:font/ttf;base64,%s) format('truetype')}"
            % (weight, data)
        )
    return "\n".join(css)


def main():
    template = open(os.path.join(HERE, "template.html"), encoding="utf-8").read()
    data = json.load(open(os.path.join(HERE, "beslut.json"), encoding="utf-8"))
    logo = "data:image/png;base64," + b64(os.path.join(HERE, "okn-logo.png"))
    favicon = "data:image/png;base64," + b64(os.path.join(HERE, "okn-favicon.png"))

    html = template
    html = html.replace("/*@FONTFACE@*/", fontface_css())
    html = html.replace("@LOGO@", logo)
    html = html.replace("@FAVICON@", favicon)
    # data sist (kan innehålla tecken som krockar med replace-mönster -> använd lambda)
    html = html.replace("@DATA@", json.dumps(data, ensure_ascii=False))

    out = os.path.join(HERE, "index.html")
    open(out, "w", encoding="utf-8").write(html)
    print(f"Byggde index.html ({os.path.getsize(out)//1024} kB, {len(data)} beslut, "
          f"{len(FONTS)} typsnitt + logotyp inbäddade).")


if __name__ == "__main__":
    main()
