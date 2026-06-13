# Vägledande beslut – Överklagandenämnden (sökbart)

Samlar **alla** vägledande beslut från Skolväsendets överklagandenämnd
(<https://www.overklagandenamnden.se/vagledande-beslut/>) i ett sökbart och
filtrerbart gränssnitt. På den ursprungliga sidan ligger besluten utspridda i
dragspel under tio skolformer; här ligger de samlade på ett ställe.

## Funktioner

- **Autocomplete** – skriv minst tre bokstäver så börjar förslag dyka upp.
  Klicka på ett förslag för att öppna exakt det beslutet.
- **Sökning** – på rättsfråga (rubrik), diarienummer (t.ex. `2018:575`),
  skolform, ämne och hela beslutstexten. Skip- och accent­okänslig.
- **Filter** – skolform, utfall (avslag/bifall/…), och år.
- **Pekar rätt** – varje träff visar diarienummer, nämndens beslutsdatum och
  datum för det överklagade beslutet, samt en **djuplänk** direkt till rätt
  beslut på overklagandenamnden.se (`#ReadMoreBlock-…`). Inget kan misstolkas.

För nyare, avidentifierade beslut publicerar nämnden inget diarienummer – då
visas "Diarienummer ej publicerat" istället för en gissning.

## Filer

| Fil | Innehåll |
|-----|----------|
| `index.html` | **Färdig, helt självständig app.** Data, typsnitt (Muli) och logotyp är inbäddade – fungerar genom att bara dubbelklickas, även offline. |
| `template.html` | Läsbar källa (HTML/CSS/JS) som `build.py` fyller i. |
| `build.py`   | Bäddar in typsnitt + logotyp + data i `index.html`. |
| `beslut.json`| Datat som ren JSON, för vidare bruk. |
| `data.js`    | Datat som `window.OUN_BESLUT` (för utveckling mot `template.html`). |
| `scrape.py`  | Hämtar och strukturerar om datat från källan. |
| `fonts/`, `okn-logo.png` | Muli-typsnitt och logotyp från overklagandenamnden.se. |
| `serve.py`   | Liten lokal server (valfri – behövs ej för den färdiga `index.html`). |

## Använda

Öppna bara **`index.html`** i webbläsaren (dubbelklick). Inget mer behövs.

## Bygga om

```bash
cd overklagandenamnden
python3 scrape.py    # 1. hämtar färska beslut -> beslut.json + data.js
python3 build.py     # 2. bäddar in allt -> färdig index.html
```

Profil hämtad direkt från overklagandenamnden.se: typsnitt **Muli**, primärfärg
vinröd **#8b212a**, action-blå #006399, grön bifall #137870.

Antal beslut vid senaste körning: **69** (varav 29 med publicerat diarienummer).
Alla beslut är avidentifierade av nämnden. Vid avvikelse gäller originalbeslutet.
