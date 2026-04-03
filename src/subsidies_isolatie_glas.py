"""
subsidies_isolatie_glas.py
==========================
Subsidiedata isolatie en glas (ISDE 2026) per bouwperiode.

HOE AANPASSEN?
  Zoek de gewenste bouwperiode (zoek op '── PERIODE').
  - Maatregel toevoegen:  voeg de sleutel toe aan 'isolatie' of 'glas' lijst
  - Maatregel verwijderen: verwijder de sleutel uit de lijst
  - Volgorde aanpassen:   verander de volgorde in de lijst
  - Bedrag wijzigen:      pas het aan in ISOLATIE_BEDRAGEN of GLAS_BEDRAGEN bovenaan
  - Periode-opmerking:    wijzig 'notitie' in het periodeblok
"""
from __future__ import annotations

# ── Bedragen (ISDE 2026) ──────────────────────────────────────────────────────
# Aanpassen? Wijzig hier — alle periodes worden automatisch bijgewerkt.

ISOLATIE_BEDRAGEN: dict[str, dict] = {
    "dakisolatie": {
        "naam":  "Dakisolatie",
        "enkel": 8.13,
        "meer":  16.25,
        "bio":   5.00,
        "rd":    "Rc ≥ 3,5 m²K/W",
    },
    "zoldervloer": {
        "naam":  "Zoldervloerisolatie",
        "enkel": 2.00,
        "meer":  4.00,
        "bio":   1.50,
        "rd":    "Rc ≥ 3,5 m²K/W",
    },
    "spouwmuur": {
        "naam":  "Spouwmuurisolatie",
        "enkel": 2.63,
        "meer":  5.25,
        "bio":   1.50,
        "rd":    "Rc ≥ 1,1 m²K/W",
    },
    "gevel": {
        "naam":  "Gevelisolatie (binnen/buiten)",
        "enkel": 10.13,
        "meer":  20.25,
        "bio":   6.00,
        "rd":    "Rc ≥ 3,5 / Rd ≥ 2,5 m²K/W",
    },
    "vloer": {
        "naam":  "Vloerisolatie",
        "enkel": 2.75,
        "meer":  5.50,
        "bio":   2.00,
        "rd":    "Rc ≥ 3,5 m²K/W",
    },
    "bodem": {
        "naam":  "Bodemisolatie (kruipruimte)",
        "enkel": 1.50,
        "meer":  3.00,
        "bio":   1.00,
        "rd":    "Rc ≥ 1,3 m²K/W",
    },
}

GLAS_BEDRAGEN: dict[str, dict] = {
    "hrpp": {
        "naam":  "HR++ glas",
        "enkel": 12.50,
        "meer":  25.00,
        "ug":    "U ≤ 1,2 W/m²K",
        "noot":  "",
    },
    "vacuum": {
        "naam":  "Vacuümglas",
        "enkel": 12.50,
        "meer":  25.00,
        "ug":    "U ≤ 0,7 W/m²K",
        "noot":  "Past in bestaande kozijnen, telt als HR++ tarief.",
    },
    "triple": {
        "naam":  "Triple glas",
        "enkel": 55.50,
        "meer":  111.00,
        "ug":    "U ≤ 0,7 W/m²K",
        "noot":  "Vereist vervanging van kozijnen (Uf ≤ 1,5 W/m²K).",
    },
    "deuren": {
        "naam":  "Isolerende deuren",
        "enkel": 55.50,
        "meer":  111.00,
        "ug":    "U ≤ 1,0 W/m²K",
        "noot":  "",
    },
}

MONUMENT_GLAS = {
    "enkel": 20.00,
    "meer":  40.00,
    "noot":  "Monumentaal tarief geldt voor alle glastypes bij erkend rijks- of gemeentelijk monument.",
}

WARMTEPOMP = {
    "startbedrag": 1025,
    "per_kw":      225,
    "aplus_bonus": 200,
    "toelichting": (
        "Combinatie van isolatie met een warmtepomp telt automatisch als meervoudig — "
        "daardoor verdubbelt het subsidie per m² én ontvangt u extra warmtepomp-subsidie."
    ),
}

ALGEMENE_NOTEN = [
    "Meervoudig tarief geldt bij 2+ maatregelen, of bij 1 isolatiemaatregel gecombineerd met een warmtepomp.",
    "U ontvangt slechts subsidie voor één type dakisolatie (dak óf zoldervloer) "
    "en één type vloerisolatie (vloer óf bodem).",
    "Minimale oppervlakten: gevel 10 m², overige maatregelen 20 m².",
    "Alleen vervanging van bestaand enkel glas of oud dubbel glas komt in aanmerking.",
]


# ── Relevantie per bouwperiode ────────────────────────────────────────────────
# Volgorde in de lijst = volgorde in het rapport.
# Sleutels moeten overeenkomen met ISOLATIE_BEDRAGEN / GLAS_BEDRAGEN hierboven.

PERIODES: list[dict] = [

    # ── PERIODE 1 — vóór 1945 ─────────────────────────────────────────────────
    {
        "tot_en_met": 1945,
        "isolatie": [
            "gevel",        # massieve muur of vroege spouw — grootste winst
            "dakisolatie",
            "vloer",
            "bodem",
            "zoldervloer",
            "spouwmuur",    # alleen indien spouw aanwezig en schoon
        ],
        "glas": [
            "hrpp",
            "vacuum",
            "deuren",
            # triple glas niet opgenomen: kozijnen te smal voor nieuw kozijn
        ],
        "notitie": (
            "Massieve muren (vóór ~1930) komen niet in aanmerking voor spouwmuursubsidie. "
            "Gevelisolatie (binnen of buiten) is dan de aangewezen route."
        ),
        "warmtepomp_toelichting": (
            "Door isolatie te combineren met een warmtepomp verdubbelt het isolatiesubsidie "
            "automatisch naar het meervoudige tarief."
        ),
    },

    # ── PERIODE 2 — 1946–1974 ─────────────────────────────────────────────────
    {
        "tot_en_met": 1974,
        "isolatie": [
            "spouwmuur",    # prioriteit 1: rendabele stap, ~4 jaar terugverdientijd
            "dakisolatie",
            "vloer",
            "bodem",
        ],
        "glas": [
            "hrpp",
            "vacuum",
            "triple",
            "deuren",
        ],
        "notitie": (
            "Controleer de spouw vooraf op vervuiling met een endoscoop. "
            "Een vuile spouw (valspecie, puin) vormt een vochtbrug na isolatie."
        ),
        "warmtepomp_toelichting": (
            "Na spouw- en vloerisolatie is een warmtepomp bij deze bouwperiode zeer rendabel."
        ),
    },

    # ── PERIODE 3 — 1975–1991 ─────────────────────────────────────────────────
    {
        "tot_en_met": 1991,
        "isolatie": [
            "spouwmuur",    # bestaande dunne laag uitbreiden
            "dakisolatie",
            "zoldervloer",
        ],
        "glas": [
            "hrpp",
            "vacuum",
            "triple",
            "deuren",
        ],
        "notitie": (
            "Bestaande isolatielagen niet verwijderen — bij-isoleren aan de binnenzijde "
            "vereist dampremmende folie aan de warme kant."
        ),
        "warmtepomp_toelichting": (
            "Na schilverbetering is deze bouwperiode vaak direct geschikt voor een hybride warmtepomp."
        ),
    },

    # ── PERIODE 4 — 1992–2014 ─────────────────────────────────────────────────
    {
        "tot_en_met": 2014,
        "isolatie": [
            "dakisolatie",
            "vloer",
            "gevel",
            "spouwmuur",
        ],
        "glas": [
            "triple",
            "deuren",
            "hrpp",
            "vacuum",
        ],
        "notitie": (
            "Schil is al redelijk op orde (Rc ≥ 2,5). "
            "Prioriteit ligt bij installatietechniek; isolatiesubsidie is hier aanvullend."
        ),
        "warmtepomp_toelichting": (
            "De schil is al op orde. Doe de 50-graden test om te zien of het afgiftesysteem "
            "klaar is voor een warmtepomp."
        ),
    },

    # ── PERIODE 5 — vanaf 2015 ────────────────────────────────────────────────
    {
        "tot_en_met": 9999,
        "isolatie": [
            # Geen isolatiemaatregelen — woning voldoet al aan huidige normen
        ],
        "glas": [
            "triple",       # enige relevante optimalisatie
        ],
        "notitie": (
            "Woning is al goed geïsoleerd (Rc dak 6,0 / gevel 4,5). "
            "Geen isolatiesubsidie van toepassing. Triple glas alleen zinvol bij renovatie."
        ),
        "warmtepomp_toelichting": (
            "Focus verder op zonnepanelen, thuisbatterij en slimme monitoring."
        ),
    },
]


# ── Opzoekfunctie ─────────────────────────────────────────────────────────────

def get_periode(bouwjaar: int) -> dict:
    for p in PERIODES:
        if bouwjaar <= p["tot_en_met"]:
            return p
    return PERIODES[-1]


# ── Generator ─────────────────────────────────────────────────────────────────

def genereer_subsidietekst(bouwjaar: int) -> str:
    """
    Genereert subsidietekst voor {{subsidies_isolatie}}.
    Toont alleen de relevante maatregelen voor de bouwperiode.
    Meervoudig tarief als standaard; enkelvoudig tarief als voetnoot.
    """
    periode = get_periode(bouwjaar)
    regels: list[str] = []

    # ── Isolatie ──────────────────────────────────────────────────────────────
    if periode["isolatie"]:
        regels.append("Isolatie (meervoudig tarief — zie voetnoot voor enkelvoudig):")
        for sleutel in periode["isolatie"]:
            m = ISOLATIE_BEDRAGEN[sleutel]
            bio = f"  |  biobased bonus + € {m['bio']:.2f}" if m.get("bio") else ""
            regels.append(f"- {m['naam']}: € {m['meer']:.2f} per m²  |  {m['rd']}{bio}")
    else:
        regels.append(
            "Isolatie: de woning voldoet al aan de huidige normen. "
            "Geen isolatiesubsidie van toepassing."
        )

    regels.append("")

    # ── Glas ──────────────────────────────────────────────────────────────────
    if periode["glas"]:
        regels.append("Hoogrendementsglas (meervoudig tarief):")
        for sleutel in periode["glas"]:
            g = GLAS_BEDRAGEN[sleutel]
            noot = f"  ({g['noot']})" if g.get("noot") else ""
            regels.append(f"- {g['naam']}: € {g['meer']:.2f} per m²  |  {g['ug']}{noot}")

    regels.append("")

    # ── Warmtepomp combinatie ─────────────────────────────────────────────────
    wp = WARMTEPOMP
    regels.append(
        f"Combinatie met warmtepomp (ISDE 2026): "
        f"startbedrag € {wp['startbedrag']:,} + € {wp['per_kw']} per kW vermogen"
        f" + € {wp['aplus_bonus']} bonus bij A+++ label."
    )
    regels.append(wp["toelichting"])

    regels.append("")

    # ── Periode-specifieke opmerking ──────────────────────────────────────────
    if periode.get("notitie"):
        regels.append(f"Aandachtspunt: {periode['notitie']}")

    regels.append("")

    # ── Enkelvoudig voetnoot ──────────────────────────────────────────────────
    enkel_iso = [
        f"{ISOLATIE_BEDRAGEN[s]['naam']} € {ISOLATIE_BEDRAGEN[s]['enkel']:.2f}"
        for s in periode["isolatie"]
    ]
    enkel_glas = [
        f"{GLAS_BEDRAGEN[s]['naam']} € {GLAS_BEDRAGEN[s]['enkel']:.2f}"
        for s in periode["glas"]
    ]
    alle_enkel = enkel_iso + enkel_glas
    if alle_enkel:
        regels.append(
            "Enkelvoudig tarief (bij slechts 1 maatregel zonder warmtepomp): "
            + " | ".join(alle_enkel)
        )

    regels.append("")

    # ── Algemene noten ────────────────────────────────────────────────────────
    regels.append("Algemene voorwaarden:")
    for n in ALGEMENE_NOTEN:
        regels.append(f"- {n}")

    return "\n".join(regels)
