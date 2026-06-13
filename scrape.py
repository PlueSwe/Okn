#!/usr/bin/env python3
"""
Hämtar och strukturerar alla vägledande beslut från Överklagandenämnden
(Skolväsendets överklagandenämnd) till sökbar JSON.

Körs:  python3 scrape.py
Skapar: beslut.json  och  data.js  (för den fristående webbappen index.html)

Varje beslut på webbplatsen ligger i ett "ReadMoreBlock" (dragspel). Knappens
rubrik är beslutets rättsfråga (vår titel). Datum + diarienummer står, när det
finns, i ett föregående "Beslut: ÅÅÅÅ-MM-DD Dnr: ÅÅÅÅ:NNN"-huvud. Varje block har
ett stabilt id (#ReadMoreBlock-NNNN) som vi djuplänkar till så att en träff alltid
pekar på exakt rätt beslut.
"""
import re, json, time, sys, os, urllib.request
import html as H

BASE = "https://www.overklagandenamnden.se"
ROOT = "/vagledande-beslut/"
HDR  = {"User-Agent": "Mozilla/5.0 (overklagandenamnden-vagledande-beslut indexer)"}

CAT_LABELS = {
    "allmanna-fragor": "Allmänna frågor",
    "anpassad-utbildning-for-rorelsehindrade": "Anpassad utbildning för rörelsehindrade",
    "forskoleklassgrundskola": "Förskoleklass/grundskola",
    "grundsarskola": "Anpassad grundskola",
    "gymnasiesarskola": "Anpassad gymnasieskola",
    "gymnasieskola": "Gymnasieskola",
    "kommunal-vuxenutbildning": "Kommunal vuxenutbildning",
    "sameskola": "Sameskola",
    "specialskola": "Specialskola",
    "utbildning-i-svenska-for-invandrare": "Utbildning i svenska för invandrare",
}
TOPIC_LABELS = {
    "atgardprogram": "Åtgärdsprogram",
    "atgardsprogram": "Åtgärdsprogram",
    "mottagande-av-elev-i-grundskolan": "Mottagande av elev i grundskolan",
    "omplacering-pa-grund-av-andra-elevers-trygghet-och-studiero":
        "Omplacering på grund av andra elevers trygghet och studiero",
    "skolplacering": "Skolplacering",
    "allmanna-beslut": "Allmänna beslut",
    "behorighet": "Behörighet",
    "erbjuds-utbildningen-av-hemkommunen": "Erbjuds utbildningen av hemkommunen",
    "sarskilda-skal-for-mottagande": "Särskilda skäl för mottagande",
    "behorighet-till-studier-vid-kommunal-vuxenutbildning":
        "Behörighet till studier vid kommunal vuxenutbildning",
    "interkommunal-ersattning": "Interkommunal ersättning",
    "mottagande-till-kommunal-vuxenutbildning": "Mottagande till kommunal vuxenutbildning",
    "upphorande-av-studier-vid-kommunal-vuxenutbildning":
        "Upphörande av studier vid kommunal vuxenutbildning",
}
MONTHS = "januari februari mars april maj juni juli augusti september oktober november december".split()


def fetch(path):
    url = BASE + path if path.startswith("/") else path
    req = urllib.request.Request(url, headers=HDR)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def crawl():
    """Följ alla länkar under /vagledande-beslut/ och returnera {path: html}."""
    seen, pages, queue = set(), {}, [ROOT]
    while queue:
        p = queue.pop(0)
        if p in seen:
            continue
        seen.add(p)
        try:
            html = fetch(p)
        except Exception as e:
            print("FEL", p, e, file=sys.stderr)
            continue
        pages[p] = html
        for m in re.finditer(r'href="([^"]+)"', html):
            href = m.group(1)
            if href.startswith(BASE):
                href = href[len(BASE):]
            if not href.startswith(ROOT):
                continue
            href = href.split("#")[0].split("?")[0]
            if not href.endswith("/"):
                href += "/"
            if href not in seen and href not in queue:
                queue.append(href)
        time.sleep(0.3)
    return pages


def title_case(slug):
    if not slug:
        return ""
    return TOPIC_LABELS.get(slug, slug.replace("-", " ").capitalize())


def strip_tags_text(frag):
    frag = re.sub(r"(?i)<br\s*/?>", "\n", frag)
    frag = re.sub(r"(?i)</(p|div|li|h[1-6]|tr|table)>", "\n", frag)
    frag = re.sub(r"(?i)<li[^>]*>", "• ", frag)
    frag = re.sub(r"<[^>]+>", "", frag)
    frag = H.unescape(frag).replace("\xa0", " ")
    frag = re.sub(r"[ \t]+", " ", frag)
    frag = re.sub(r"\n[ \t]+", "\n", frag)
    frag = re.sub(r"\n{3,}", "\n\n", frag)
    return frag.strip()


def match_div(html, start):
    """start = index på <div> som öppnar collapse-blocket. Returnerar inre HTML."""
    depth = 0
    first_open_end = html.index(">", start) + 1
    for m in re.finditer(r"<(/?)div\b", html[start:], re.I):
        if m.group(1) == "":
            depth += 1
        else:
            depth -= 1
            if depth == 0:
                return html[first_open_end:start + m.start()]
    return html[first_open_end:]


def parse_sv_date(s):
    m = re.search(r"(\d{1,2})\s+(" + "|".join(MONTHS) + r")\s+(\d{4})", s)
    if not m:
        return ""
    d = int(m.group(1)); mo = MONTHS.index(m.group(2)) + 1; y = int(m.group(3))
    return f"{y:04d}-{mo:02d}-{d:02d}"


def extract(pages):
    decisions = []
    wrap = re.compile(r'<div class="ReadMoreBlock-wrapper title">', re.I)
    for path, html in sorted(pages.items()):
        parts = path.strip("/").split("/")[1:]  # släpp 'vagledande-beslut'
        cat = parts[0] if parts else ""
        sub = parts[1] if len(parts) > 1 else ""
        for w in wrap.finditer(html):
            ws = w.start()
            bn = re.search(r'<span class="h2">(.*?)</span>\s*</button>', html[ws:ws + 1500], re.S)
            headnote = strip_tags_text(bn.group(1)) if bn else ""
            aid = re.search(r'href="#(ReadMoreBlock-\d+)"', html[ws:ws + 400])
            anchor = aid.group(1) if aid else ""
            # Diarienummer + nämndens beslutsdatum står i en rubrik strax före blocket.
            # Två format förekommer på sajten, t.ex.:
            #   "Beslut: 2018-10-18 Dnr: 2018:1034"   (äldre)
            #   "Beslut: 2025-09-25, dnr 2025:532"     (nyare – komma, gemener, ofta utan kolon)
            # Kravet på nyckelordet "dnr" gör att lagreferenser som "skollagen (2010:800)"
            # aldrig misstas för ett diarienummer.
            pre = html[max(0, ws - 400):ws]
            md = re.search(r"Beslut:?\s*(\d{4}-\d{2}-\d{2})\D{0,8}dnr:?\s*(\d{4}:\d+)", pre, re.I)
            okn_date = md.group(1) if md else ""
            dnr = md.group(2) if md else ""
            cs = html.find('<div class="ReadMoreBlock collapse', ws)
            text = strip_tags_text(match_div(html, cs))
            # Reserv: diarienummer i brödtexten (kräver "dnr"-nyckelord).
            if not dnr:
                mb = re.search(r"\bdnr\.?:?\s*(\d{4}:\d+)", text, re.I)
                if mb:
                    dnr = mb.group(1)
            ap = re.search(r"eslut den (\d{1,2} (?:" + "|".join(MONTHS) + r") \d{4})", text)
            appealed_date = parse_sv_date(ap.group(1)) if ap else ""
            mo = re.search(r"Överklagandenämnden (avslår|avvisar|bifaller|undanröjer|återförvisar|upphäver)", text)
            outcome = mo.group(1) if mo else ""
            decisions.append({
                "id": anchor or (dnr.replace(":", "-") if dnr else f"{cat}-{len(decisions)}"),
                "headnote": headnote,
                "dnr": dnr,
                "oknDate": okn_date,
                "appealedDate": appealed_date,
                "outcome": outcome,
                "category": cat,
                "categoryLabel": CAT_LABELS.get(cat, cat),
                "topic": sub,
                "topicLabel": title_case(sub),
                "sourceUrl": BASE + path + ("#" + anchor if anchor else ""),
                "text": text,
            })
    return decisions


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    print("Hämtar sidor …")
    pages = crawl()
    print(f"  {len(pages)} sidor")
    decisions = extract(pages)
    print(f"  {len(decisions)} beslut extraherade "
          f"({sum(1 for d in decisions if d['dnr'])} med Dnr)")
    json.dump(decisions, open(os.path.join(here, "beslut.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    with open(os.path.join(here, "data.js"), "w", encoding="utf-8") as f:
        f.write("window.OUN_BESLUT = " + json.dumps(decisions, ensure_ascii=False) + ";\n")
    print("Skrev beslut.json och data.js")


if __name__ == "__main__":
    main()
