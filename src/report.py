# src/report.py
from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional

MAANDEN = [
    "", "januari", "februari", "maart", "april", "mei", "juni",
    "juli", "augustus", "september", "oktober", "november", "december"
]

def _fmt_datum(s: Any) -> str:
    """Zet ISO-datumstring om naar leesbare Nederlandse notatie."""
    if not s:
        return "—"
    try:
        dt = datetime.fromisoformat(str(s).split("T")[0])
        return f"{dt.day} {MAANDEN[dt.month]} {dt.year}"
    except Exception:
        return str(s).split("T")[0]


# ---------- Helpers ----------
def bouwjaar_band(bouwjaar: int) -> str:
    if bouwjaar < 1975:
        return "voor 1975"
    if bouwjaar < 1992:
        return "1975–1991"
    if bouwjaar < 2006:
        return "1992–2005"
    if bouwjaar < 2015:
        return "2006–2014"
    return "2015+"


def _dash(v: Any) -> str:
    return "—" if v is None or v == "" else str(v)


def _fmt_num(v: Any, suffix: str = "", decimals: int = 2) -> str:
    if isinstance(v, (int, float)):
        return f"{v:.{decimals}f}{suffix}"
    return "—"


def _label_strength(labelklasse: Optional[str]) -> Optional[str]:
    """Ruwe duiding label voor tekst (niet voor berekening)."""
    if not labelklasse:
        return None
    lk = str(labelklasse).upper().strip()
    if lk.startswith("A"):
        return "hoog"
    if lk in {"B", "C"}:
        return "gemiddeld"
    if lk in {"D", "E", "F", "G"}:
        return "laag"
    return None


# ---------- Quickscan scoring ----------
def quickscan_scores(bouwjaar: int, label: Optional[dict[str, Any]]) -> dict[str, Any]:
    band = bouwjaar_band(bouwjaar)

    # Basisschatting op bouwperiode
    base = {"dak": 3, "gevel": 3, "vloer": 3, "glas": 3}
    if band == "2015+":
        base = {"dak": 1, "gevel": 1, "vloer": 1, "glas": 1}
    elif band == "2006–2014":
        base = {"dak": 2, "gevel": 2, "vloer": 2, "glas": 2}
    elif band == "voor 1975":
        base = {"dak": 4, "gevel": 4, "vloer": 4, "glas": 4}

    # Correctie op label (indicatief)
    if label and label.get("labelklasse"):
        lk = str(label["labelklasse"]).upper()
        if lk in ["A", "A+", "A++", "A+++", "A++++"]:
            for k in base:
                base[k] = max(1, base[k] - 1)
        if lk in ["E", "F", "G"]:
            for k in base:
                base[k] = min(5, base[k] + 1)

    return {"band": band, "scores": base}



# ---------- Main renderer ----------
def render_markdown(
    adres: str,
    bouwjaar: int,
    opp_m2: float | None,
    label: dict | None,
    scan: dict,
    subsidies: list[dict] | None = None,
    narrative: dict | None = None,
) -> str:
    today = date.today()
    today_nl = f"{today.day} {MAANDEN[today.month]} {today.year}"
    lines: list[str] = []

    # ─────────────────────────────────────────────
    # YAML front matter voor Pandoc-template
    # ─────────────────────────────────────────────
    lines.append("---")
    lines.append(f"pagetitle: \"{adres}\"")
    lines.append(f"date: \"{today_nl}\"")
    lines.append("lang: nl")
    lines.append("---")
    lines.append("")

    # ─────────────────────────────────────────────
    # Introductie (onder de cover in het template)
    # ─────────────────────────────────────────────
    lines.append(
        "Dit rapport geeft u een eerste, onafhankelijk inzicht in de energetische kwaliteit "
        "van uw woning en de meest logische stappen richting verduurzaming. "
        "De analyse is gebaseerd op openbare registraties en erkende databronnen, aangevuld "
        "met aannames die gebruikelijk zijn voor vergelijkbare woningen."
    )
    lines.append("")

    # ─────────────────────────────────────────────
    # Interpretatie & context  (hoofdstuk 1 — inleiding op de data)
    # ─────────────────────────────────────────────
    lines.append("## 1. Interpretatie en context")
    lines.append("")
    if narrative:
        lines.append(narrative.get("gebouw", ""))
        lines.append("")
        lines.append(narrative.get("energie", ""))
        lines.append("")
        lines.append(narrative.get("aanpak", ""))
    else:
        band = scan["band"]
        _band_tekst = {
            "voor 1975": "gebouwd vóór 1975 met beperkte isolatie-eisen; dak, gevel, vloer en glas bieden doorgaans de grootste verbeterkansen.",
            "1975–1991": "gebouwd in een periode met geleidelijk oplopende isolatie-eisen; er is vaak nog substantiële winst te behalen.",
            "1992–2005": "gebouwd in een periode met oplopende energieprestatie-eisen; er is vaak nog winst via schil- en detailverbetering.",
            "2006–2014": "gebouwd in een periode met duidelijke energieprestatie-eisen; de basis is vaak redelijk, gerichte optimalisaties leveren het meest op.",
            "2015+": "relatief recent gebouwd met goede isolatie als basis; grootschalige maatregelen leveren beperkt extra rendement, maar detailverbetering kan comfort verhogen.",
        }
        lines.append(f"De woning is {_band_tekst.get(band, 'gebouwd in een periode met variabele isolatienormen.')}")
        lines.append("")
        if label and label.get("labelklasse"):
            lines.append(
                f"Het geregistreerde energielabel (**{label.get('labelklasse')}**) ondersteunt dit beeld. "
                "Dit rapport richt zich op **realistische verbeterkansen** en **logische vervolgstappen**."
            )
        else:
            lines.append(
                "Omdat geen actueel energielabel beschikbaar is, is de energieprestatie ingeschat "
                "op basis van bouwjaar en vergelijkbare woningen."
            )

    # ─────────────────────────────────────────────
    # Woninggegevens  (hoofdstuk 2 — feiten uit registraties)
    # ─────────────────────────────────────────────
    lines.append("")
    lines.append("## 2. Woninggegevens")
    lines.append("")
    lines.append(f"**Adres:** {adres}  ")
    lines.append(f"**Datum rapport:** {today_nl}  ")
    lines.append(f"**Bouwjaar (BAG):** {bouwjaar} — bouwperiode: {scan['band']}  ")

    if opp_m2 is not None:
        lines.append(f"**Gebruiksoppervlakte (BAG):** {opp_m2} m²  ")

    if label:
        lk = label.get("labelklasse") or "—"
        reg_datum = _fmt_datum(label.get("registratiedatum"))
        geldig_tot = _fmt_datum(label.get("geldig_tot"))
        eb = label.get("energiebehoefte")
        wb = label.get("warmtebehoefte")
        tz = label.get("opp_thermische_zone")

        lines.append(f"**Energielabel:** {lk}  ")
        lines.append(f"**Registratiedatum:** {reg_datum}  ")
        lines.append(f"**Geldig tot:** {geldig_tot}  ")
        lines.append(
            f"**Energiebehoefte:** "
            f"{f'{eb:.1f} kWh/m².jr' if isinstance(eb, (int, float)) else '—'}  "
        )
        lines.append(
            f"**Warmtebehoefte:** "
            f"{f'{wb:.1f} kWh/m².jr' if isinstance(wb, (int, float)) else '—'}  "
        )
        lines.append(
            f"**Gebruiksoppervlakte thermische zone:** "
            f"{f'{tz:.0f} m²' if isinstance(tz, (int, float)) else '—'}"
        )
    else:
        lines.append("**Energielabel:** niet gevonden of niet gekoppeld")

    lines.append("")
    lines.append(
        "_Bron: Basisregistratie Adressen en Gebouwen (BAG/PDOK) en "
        "landelijke energielabelregistratie EP-Online._"
    )


    # ─────────────────────────────────────────────
    # Kansen
    # ─────────────────────────────────────────────
    lines.append("")
    lines.append("## 3. Kansen en verbeterpotentieel")
    lines.append("")
    lines.append(
        "De onderstaande scores geven een indicatie van het verwachte verbeterpotentieel "
        "per onderdeel. Een lage score betekent niet dat geen actie mogelijk is, "
        "maar dat het rendement ten opzichte van de investering doorgaans beperkter is."
    )
    lines.append("")

    from teksten_elementen import get_slottekst_kansen
    element_namen = {"dak": "Dak", "gevel": "Gevel", "vloer": "Vloer", "glas": "Glas"}
    for k, v in scan["scores"].items():
        naam       = element_namen.get(k, k.capitalize())
        score_label = narrative.get(f"score_{k}_tekst", str(v)) if narrative else str(v)
        lines.append(f"### {naam} — score {v}/5 ({score_label})")
        lines.append("")
        if narrative:
            tekst = narrative.get(f"element_tekst_{k}", "")
            if tekst:
                lines.append(tekst)
                lines.append("")

    slottekst = get_slottekst_kansen(scan["scores"])
    lines.append(slottekst)
    lines.append("")

    # ─────────────────────────────────────────────
    # Inhoudelijk advies / optimalisaties
    # ─────────────────────────────────────────────
    lines.append("")
    lines.append("## 4. Waarschijnlijke optimalisaties")
    lines.append("")
    lines.append(
        "Op basis van bouwjaar, woningtype en geregistreerde prestaties zijn de volgende "
        "maatregelen het meest logisch om nader te onderzoeken:"
    )
    lines.append("")
    lines.append(
        "### 1. Controle en optimalisatie van bestaande isolatie\n"
        "In woningen uit deze periode is isolatie aanwezig, maar de uitvoering en detaillering "
        "verschillen sterk. Verbetering van aansluitingen, kierdichting en isolatiekwaliteit "
        "kan het comfort verhogen en ongewenst warmteverlies beperken."
    )
    lines.append("")
    lines.append(
        "### 2. Glas en kozijnen\n"
        "Indien nog niet volledig uitgevoerd, kan verbetering van glas (HR++ of triple) "
        "zorgen voor merkbaar meer comfort, minder koudeval en betere geluidsisolatie."
    )
    lines.append("")
    lines.append(
        "### 3. Installaties en regeling\n"
        "Bij een relatief goede schil ligt aanvullende winst vaak in de optimalisatie van "
        "verwarming, regeling en eventueel duurzame opwek. Denk aan waterzijdig inregelen, "
        "slimme thermostaten of voorbereiding op lage-temperatuurverwarming."
    )

    # ─────────────────────────────────────────────
    # Subsidies
    # ─────────────────────────────────────────────
    lines.append("")
    lines.append("## 5. Mogelijk relevante subsidies")
    lines.append("")
    lines.append("| Subsidie | Bedrag | Voor wie |")
    lines.append("|---|---|---|")
    lines.append("| ISDE warmtepomp | € 1.025 + € 225/kW | Woningeigenaren warmtepomp |")
    lines.append("| Gemeentelijke subsidie | Verschilt per gemeente | Isolatie en energieadvies |")
    lines.append("| Nationaal Warmtefonds | Lening lage rente | Investering spreiden |")
    lines.append("")
    lines.append(
        "Exacte bedragen en voorwaarden wijzigen regelmatig. "
        "Controleer de actuele regelingen via www.pandiq.nl/subsidie."
    )

    # ─────────────────────────────────────────────
    # Vervolg & CTA
    # ─────────────────────────────────────────────
    lines.append("")
    lines.append("## 6. Vervolgstappen")
    lines.append("")
    lines.append(
        "Dit rapport is bedoeld als startpunt. Door aanvullende informatie of foto’s toe te voegen "
        "kan de analyse worden aangescherpt en kan worden bepaald welke maatregelen "
        "daadwerkelijk technisch en financieel passend zijn voor uw woning."
    )
    lines.append("")
    lines.append(
        "- Upload foto’s van dak, gevel, glas, installaties en kruipruimte\n"
        "- Bevestig woningtype en eventuele renovatiejaren\n"
        "- Gebruik dit rapport als basis voor offerte- of adviesgesprekken"
    )

    # ─────────────────────────────────────────────
    # Disclaimer
    # ─────────────────────────────────────────────
    lines.append("")
    lines.append(
        "> Disclaimer: dit rapport is indicatief en gebaseerd op registraties en aannames. "
        "Aan dit document kunnen geen rechten worden ontleend. "
        "Uitvoering vereist altijd verificatie op locatie en controle van actuele regelgeving."
    )

    return "\n".join(lines)

