"""
aannames.py
===========
Centrale configuratie voor alle rekenparameters in de PandIQ Isolatie Quickscan.

Alle hardcoded getallen in berekeningen horen hier thuis.
Bronvermeldingen staan per parameter vermeld zodat aannames transparant en
navolgbaar zijn.
"""
from __future__ import annotations
from typing import Any


# ── Centrale aannames-dictionary ──────────────────────────────────────────────
# Structuur per item: waarde, eenheid, bron, aanpasbaar (bool)

AANNAMES: dict[str, dict[str, Any]] = {

    # ── Energieprijzen ─────────────────────────────────────────────────────────
    "gasprijs": {
        "waarde":     1.45,
        "eenheid":    "€/m³",
        "bron":       "ACM consumentenprijs aardgas 2026 (incl. belastingen en netwerktarieven)",
        "aanpasbaar": True,
    },
    "energieinhoud_gas": {
        "waarde":     9.77,
        "eenheid":    "kWh/m³",
        "bron":       "NEN-EN 437 / calorische waarde aardgas (bovenwaarde)",
        "aanpasbaar": False,
    },
    "cv_rendement_oud": {
        "waarde":     0.78,
        "eenheid":    "factor",
        "bron":       "ISSO 82.1 tabel A1, oud atmosferisch toestel",
        "aanpasbaar": True,
    },
    "cv_rendement_hr": {
        "waarde":     0.92,
        "eenheid":    "factor",
        "bron":       "ISSO 82.1 tabel A1, HR-107 ketel",
        "aanpasbaar": True,
    },

    # ── Klimaat (NEN 5060 referentieklimaatjaar NL) ────────────────────────────
    "temperatuurverschil_dt": {
        "waarde":     10,
        "eenheid":    "K",
        "bron":       "NEN 5060 referentieklimaatjaar NL, ontwerpwaarde ΔT binnen/buiten",
        "aanpasbaar": False,
    },
    "verwarmingsuren_jr": {
        "waarde":     5500,
        "eenheid":    "uur/jr",
        "bron":       "NEN 5060 referentieklimaatjaar NL, stookseizoen Nederlandse woning",
        "aanpasbaar": False,
    },

    # ── Financieel ────────────────────────────────────────────────────────────
    "energieprijsstijging_pct": {
        "waarde":     0.03,
        "eenheid":    "fractie/jr",
        "bron":       "PBL Klimaat- en Energieverkenning 2024, mediaan energieprijsscenario",
        "aanpasbaar": True,
    },
    "discontovoet": {
        "waarde":     0.04,
        "eenheid":    "fractie/jr",
        "bron":       "Standaard maatschappelijke discontovoet (Rijkswaterstaat MKBA-leidraad)",
        "aanpasbaar": True,
    },

    # ── Woningafmetingen (CBS Woononderzoek 2021 + SBR referentiewoningen) ─────
    "breedte_rijwoning": {
        "waarde":     6.0,
        "eenheid":    "m",
        "bron":       "CBS Woononderzoek 2021, mediane breedte rijwoning",
        "aanpasbaar": True,
    },
    "breedte_hoekwoning": {
        "waarde":     7.0,
        "eenheid":    "m",
        "bron":       "CBS Woononderzoek 2021 + SBR referentiewoningen 2022",
        "aanpasbaar": True,
    },
    "breedte_twee_onder_een_kap": {
        "waarde":     8.0,
        "eenheid":    "m",
        "bron":       "SBR referentiewoningen 2022, type twee-onder-één-kap",
        "aanpasbaar": True,
    },
    "verhouding_vrijstaand": {
        "waarde":     1.3,
        "eenheid":    "factor (diepte/breedte)",
        "bron":       "SBR referentiewoningen 2022, gemiddelde verhouding vrijstaande woning",
        "aanpasbaar": True,
    },
    "verdiepingshoogte_oud": {
        "waarde":     2.85,
        "eenheid":    "m",
        "bron":       "SBR referentiewoningen 2022, voor 1945",
        "aanpasbaar": True,
    },
    "verdiepingshoogte_midden": {
        "waarde":     2.60,
        "eenheid":    "m",
        "bron":       "SBR referentiewoningen 2022, 1945–1992",
        "aanpasbaar": True,
    },
    "verdiepingshoogte_nieuw": {
        "waarde":     2.70,
        "eenheid":    "m",
        "bron":       "SBR referentiewoningen 2022, na 1992",
        "aanpasbaar": True,
    },

    # ── Glasandeel van geveloppervlak (SBR referentiewoningen 2022) ───────────
    "glasandeel_voorgevel": {
        "waarde":     0.25,
        "eenheid":    "fractie",
        "bron":       "SBR referentiewoningen 2022, gemiddeld glasandeel voorgevel",
        "aanpasbaar": True,
    },
    "glasandeel_achtergevel": {
        "waarde":     0.20,
        "eenheid":    "fractie",
        "bron":       "SBR referentiewoningen 2022, gemiddeld glasandeel achtergevel",
        "aanpasbaar": True,
    },
    "glasandeel_zijgevel": {
        "waarde":     0.10,
        "eenheid":    "fractie",
        "bron":       "SBR referentiewoningen 2022, gemiddeld glasandeel zijgevel",
        "aanpasbaar": True,
    },

    # ── Dakfactor ─────────────────────────────────────────────────────────────
    "dakfactor_hellend": {
        "waarde":     1.25,
        "eenheid":    "factor",
        "bron":       "30° helling → 1/cos30° ≈ 1.15, +10% voor overstekken (praktijkcorrectie)",
        "aanpasbaar": True,
    },
    "dakfactor_plat": {
        "waarde":     1.00,
        "eenheid":    "factor",
        "bron":       "Plat dak = footprint-oppervlak, geen hellingscodering nodig",
        "aanpasbaar": False,
    },

    # ── Rc-eisen voor ISDE subsidie (bron: RVO ISDE 2026) ─────────────────────
    "rc_eis_dak": {
        "waarde":     3.5,
        "eenheid":    "m²K/W",
        "bron":       "RVO ISDE 2026, minimale Rc-waarde voor dakisolatie",
        "aanpasbaar": False,
    },
    "rc_eis_vloer": {
        "waarde":     3.5,
        "eenheid":    "m²K/W",
        "bron":       "RVO ISDE 2026, minimale Rc-waarde voor vloerisolatie",
        "aanpasbaar": False,
    },
    "rc_eis_gevel": {
        "waarde":     3.5,
        "eenheid":    "m²K/W",
        "bron":       "RVO ISDE 2026, minimale Rc-waarde voor gevelisolatie",
        "aanpasbaar": False,
    },
    "rc_eis_spouw": {
        "waarde":     1.1,
        "eenheid":    "m²K/W",
        "bron":       "RVO ISDE 2026, minimale Rc-waarde voor spouwmuurisolatie",
        "aanpasbaar": False,
    },

    # ── U-eisen glas ──────────────────────────────────────────────────────────
    "u_eis_hrpp": {
        "waarde":     1.2,
        "eenheid":    "W/m²K",
        "bron":       "RVO ISDE 2026, maximale U-waarde voor HR++ glas",
        "aanpasbaar": False,
    },
    "u_eis_triple": {
        "waarde":     0.7,
        "eenheid":    "W/m²K",
        "bron":       "RVO ISDE 2026, maximale U-waarde voor triple glas",
        "aanpasbaar": False,
    },
}


def get(sleutel: str) -> Any:
    """Geeft de waarde van een aanname. Gooit KeyError bij onbekende sleutel."""
    return AANNAMES[sleutel]["waarde"]


# ── Rc-tabel per element en bouwperiode ──────────────────────────────────────
# Bron: ISSO 82.1, tabel 3 — indicatieve Rc-waarden voor bestaande bouw.
# Structuur: per element → lijst van perioden met van/tot/rc/toelichting/bron.

RC_TABEL: dict[str, list[dict]] = {
    "dak": [
        {"van": 0,    "tot": 1920, "rc": 0.3,  "toelichting": "Houten gordingenkap zonder isolatielaag",                  "bron": "ISSO 82.1 tabel 3"},
        {"van": 1920, "tot": 1945, "rc": 0.4,  "toelichting": "Dakbeschot aanwezig, geen aparte isolatielaag",            "bron": "ISSO 82.1 tabel 3"},
        {"van": 1945, "tot": 1975, "rc": 0.5,  "toelichting": "Lichte dakconstructie, soms minerale wol aanwezig",        "bron": "ISSO 82.1 tabel 3"},
        {"van": 1975, "tot": 1992, "rc": 1.3,  "toelichting": "Eerste isolatielaag (~40 mm) na oliecrisis",               "bron": "ISSO 82.1 tabel 3"},
        {"van": 1992, "tot": 2012, "rc": 2.5,  "toelichting": "Bouwbesluit 1992+, Rc ≥ 2.5 m²K/W",                       "bron": "ISSO 82.1 tabel 3"},
        {"van": 2012, "tot": 9999, "rc": 3.5,  "toelichting": "Bouwbesluit 2012+, Rc ≥ 3.5 m²K/W",                       "bron": "ISSO 82.1 tabel 3"},
    ],
    "vloer": [
        {"van": 0,    "tot": 1920, "rc": 0.2,  "toelichting": "Houten balkenvloer op kruipruimte, geen isolatie",         "bron": "ISSO 82.1 tabel 3"},
        {"van": 1920, "tot": 1945, "rc": 0.3,  "toelichting": "Houten vloer, soms betegeld, geen isolatielaag",           "bron": "ISSO 82.1 tabel 3"},
        {"van": 1945, "tot": 1975, "rc": 0.4,  "toelichting": "Lichte vloerconstructie, kruipruimte aanwezig",            "bron": "ISSO 82.1 tabel 3"},
        {"van": 1975, "tot": 1992, "rc": 1.3,  "toelichting": "Betonnen begane grondvloer, beperkte isolatie",            "bron": "ISSO 82.1 tabel 3"},
        {"van": 1992, "tot": 2012, "rc": 2.5,  "toelichting": "Bouwbesluit 1992+, Rc ≥ 2.5 m²K/W",                       "bron": "ISSO 82.1 tabel 3"},
        {"van": 2012, "tot": 9999, "rc": 3.5,  "toelichting": "Bouwbesluit 2012+, Rc ≥ 3.5 m²K/W",                       "bron": "ISSO 82.1 tabel 3"},
    ],
    "gevel": [
        {"van": 0,    "tot": 1920, "rc": 0.3,  "toelichting": "Massief metselwerk 30–45 cm, geen spouw",                  "bron": "ISSO 82.1 tabel 3"},
        {"van": 1920, "tot": 1945, "rc": 0.4,  "toelichting": "Spouwmuur met lege spouw (~50 mm)",                        "bron": "ISSO 82.1 tabel 3"},
        {"van": 1945, "tot": 1975, "rc": 0.5,  "toelichting": "Spouwmuur 60–80 mm, ongeïsoleerd",                         "bron": "ISSO 82.1 tabel 3"},
        {"van": 1975, "tot": 1992, "rc": 0.9,  "toelichting": "Spouwmuur, deels gevuld of dunne isolatiestrook",          "bron": "ISSO 82.1 tabel 3"},
        {"van": 1992, "tot": 2012, "rc": 2.5,  "toelichting": "Bouwbesluit 1992+, spouw gevuld, Rc ≥ 2.5 m²K/W",         "bron": "ISSO 82.1 tabel 3"},
        {"van": 2012, "tot": 9999, "rc": 3.5,  "toelichting": "Bouwbesluit 2012+, Rc ≥ 3.5 m²K/W",                       "bron": "ISSO 82.1 tabel 3"},
    ],
    "spouw": [
        {"van": 0,    "tot": 1920, "rc": 0.0,  "toelichting": "Geen spouw aanwezig (massief metselwerk)",                 "bron": "ISSO 82.1 tabel 3"},
        {"van": 1920, "tot": 1945, "rc": 0.15, "toelichting": "Lege spouw ~50 mm, alleen luchtspouw-Rc",                  "bron": "ISSO 82.1 tabel 3"},
        {"van": 1945, "tot": 1975, "rc": 0.20, "toelichting": "Lege spouw 60–80 mm",                                      "bron": "ISSO 82.1 tabel 3"},
        {"van": 1975, "tot": 1992, "rc": 0.60, "toelichting": "Deels gevulde spouw of dunne PUR-injectie",                "bron": "ISSO 82.1 tabel 3"},
        {"van": 1992, "tot": 2012, "rc": 1.3,  "toelichting": "Spouw volledig gevuld met minerale wol of EPS",            "bron": "ISSO 82.1 tabel 3"},
        {"van": 2012, "tot": 9999, "rc": 2.0,  "toelichting": "Ruime spouw met isolatie conform Bouwbesluit 2012",        "bron": "ISSO 82.1 tabel 3"},
    ],
}


# ── U-tabel glas per bouwperiode ──────────────────────────────────────────────
# Bron: SBR referentiewoningen 2022, tabel glaswaarden.

U_TABEL: list[dict] = [
    {"van": 0,    "tot": 1980, "u": 5.8, "toelichting": "Enkel glas",                                        "bron": "SBR referentiewoningen 2022"},
    {"van": 1980, "tot": 2000, "u": 3.1, "toelichting": "Dubbel glas, eerste generatie HR",                  "bron": "SBR referentiewoningen 2022"},
    {"van": 2000, "tot": 2012, "u": 2.0, "toelichting": "HR glas (HR+/HR++)",                                "bron": "SBR referentiewoningen 2022"},
    {"van": 2012, "tot": 9999, "u": 1.4, "toelichting": "HR++ of triple glas (Bouwbesluit 2012+)",           "bron": "SBR referentiewoningen 2022"},
]


# ── Lookup-functies ───────────────────────────────────────────────────────────

def rc_oud(element: str, bouwjaar: int) -> dict:
    """
    Geeft de indicatieve Rc-waarde voor een bouwdeel op basis van bouwjaar.

    Args:
        element:  "dak" | "vloer" | "gevel" | "spouw"
        bouwjaar: bouwjaar van de woning

    Returns:
        {"rc": float, "bron": str, "periode_label": str, "toelichting": str}
    """
    tabel = RC_TABEL.get(element)
    if tabel is None:
        raise ValueError(f"Onbekend element: '{element}'. Kies uit: {list(RC_TABEL)}")

    for rij in tabel:
        if rij["van"] <= bouwjaar < rij["tot"]:
            van_str = str(rij["van"]) if rij["van"] > 0 else "voor 1920"
            tot_str = str(rij["tot"]) if rij["tot"] < 9999 else "heden"
            return {
                "rc":            rij["rc"],
                "bron":          rij["bron"],
                "toelichting":   rij["toelichting"],
                "periode_label": f"{van_str}–{tot_str}",
            }

    # Fallback: laatste rij (bouwjaar >= 9999 of buiten bereik)
    rij = tabel[-1]
    return {
        "rc":            rij["rc"],
        "bron":          rij["bron"],
        "toelichting":   rij["toelichting"],
        "periode_label": f"{rij['van']}–heden",
    }


def u_oud_glas(bouwjaar: int) -> dict:
    """
    Geeft de indicatieve U-waarde van glas op basis van bouwjaar.

    Returns:
        {"u": float, "bron": str, "toelichting": str}
    """
    for rij in U_TABEL:
        if rij["van"] <= bouwjaar < rij["tot"]:
            return {
                "u":           rij["u"],
                "bron":        rij["bron"],
                "toelichting": rij["toelichting"],
            }

    # Fallback: laatste rij
    rij = U_TABEL[-1]
    return {
        "u":           rij["u"],
        "bron":        rij["bron"],
        "toelichting": rij["toelichting"],
    }
