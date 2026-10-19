# Kravfångst som tjänst

Webbapp för kravfångst i två tjänster, byggd efter presentationen i
[`docs/Kravfangst_tjanster.pptx`](docs/Kravfangst_tjanster.pptx).

| | Tjänst A – Större initiativ | Tjänst B – Mindre vidareutveckling |
|---|---|---|
| När | Minst ett ja i triagen | Bara nej i triagen |
| Steg | Intag › Triage › Problem & effekter › Lösning & scope › Business case › Prioscore › Beslut & redo | Intag › Triage › User story › Prioritera › Redo & återkoppla |
| Resultat | **Executive summary** med prioscore, ROI och Definition of Ready | **User story** (Som … vill jag … så att …) med behov och acceptanskriterier (Givet/När/Så) |

Flödet visas som brödsmulor överst på varje sida. Avklarade steg är gröna och klickbara, och
steg efter ett ofullständigt steg är låsta. "Spara utkast" sparar utan att kontrollera
obligatoriska fält. "Spara och gå vidare" kontrollerar fälten och går till nästa steg.

## Prioscore (Tjänst A)

```
Prioscore = Affärsvärde × Strategikoefficient ÷ Komplexitet
```

- **Affärsvärde (1–10)**: viktat snitt av ekonomisk effekt 40 %, kund- och användarnytta 30 %,
  regelefterlevnad och riskreducering 20 % samt tidskritikalitet 10 %.
- **Komplexitet (1–10)**: viktat snitt av teknik, beroenden, organisatorisk förändring och
  osäkerhet, 25 % vardera.
- **Strategikoppling (%)**: Σ målets vikt × initiativets bidrag (0–100 %). Koefficienten är
  procentsatsen delad med 100. Målen och vikterna redigeras under *Strategiska mål*, och
  vikterna måste summera till 100 %.
- **Tolkning**: ≥ 1,5 betyder hög prioritet, 1,0–1,5 prioritera vid kapacitet och < 1,0 utmana
  eller omforma.

Vikterna och gränserna finns i `kravfangst/scoring.py`. Startsidan listar alla större
initiativ rangordnade efter prioscore. Om ett strategiskt mål läggs till behöver befintliga
initiativ fylla i sitt bidrag till det nya målet innan prioscore kan räknas igen.

En user story i Tjänst B som visar sig vara större kan eskaleras till Tjänst A. Det som redan
skrivits återanvänds då i problembeskrivningen.

## Webbversion på claude.ai

`web/kravfangst.html` är samma tjänst byggd som en enda webbsida, publicerad på claude.ai som en
Artifact: https://claude.ai/artifact/UajpCbDRNB9M4wJV3jP4Gu. Den kräver ingen installation. Ärenden
och strategiska mål sparas i sidans delade databas, så alla som sidan delas med ser samma data.
Personer med behörigheten Contributor eller högre kan registrera och redigera ärenden. Bara Editor
och ägaren kan ändra de strategiska målen. Reglerna för prioscore är desamma som i
`kravfangst/scoring.py`. Ändrar du dem behöver båda ställena uppdateras.

## Kom igång (Python-versionen)

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt -r requirements-dev.txt
.venv/bin/flask --app kravfangst run --debug   # http://localhost:5000
.venv/bin/pytest
```

Data sparas i SQLite (`instance/kravfangst.sqlite`). Sökvägen kan styras med
`KRAVFANGST_DATABASE`. Sätt `KRAVFANGST_SECRET_KEY` i produktion.

## Struktur

```
kravfangst/
  scoring.py   triage, prioscore och ROI (ren logik, utan Flask)
  flows.py     stegen i båda tjänsterna, validering, Definition of Ready, eskalering
  db.py        SQLite-lagring
  views.py     routes
  templates/   Jinja-mallar (brödsmulor i _crumbs.html)
  static/      CSS och liten JS för live-beräkning av triage och prioscore
tests/         pytest
```
