# PandIQ – Isolatie Quickscan (BAG + EP-Online) + Narratief Rapport

Dit pakket is bedoeld om **1-op-1** in jouw map `isolatie-quickscan/` te zetten.

## Installatie
1) Maak/activeer venv:
- `python -m venv .venv`
- `.venv\Scripts\activate`

2) Installeer dependencies:
- `pip install -r requirements.txt`

## Sleutels
Kopieer `.env.example` naar `.env` en vul minimaal:
- `EPONLINE_API_KEY=...`

## Run
- `python .\src\main.py 9746CR 107`

## PDF maken (Pandoc + wkhtmltopdf)
Voorbeeld:
- `pandoc "output\quickscan_9746CR_107.md" -o "output\quickscan_9746CR_107.pdf" --pdf-engine="C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe" --template=templates\report.html`

## Logo
Ja: zet je logo als PNG in `assets\pandiq_logo.png`.
- Bestandsnaam moet exact zo zijn (of pas `templates/report.html` aan).
- Transparante achtergrond is het mooist.
