from __future__ import annotations
from typing import Any

def likely_isde_subsidies(facts: dict[str, Any]) -> list[dict[str, Any]]:
    """Eenvoudige, veilige start: geeft relevante ISDE-categorieën terug.
    Exacte bedragen wijzigen regelmatig → voeg later een actuele tarieftabel toe.
    """
    label = (facts.get("labelklasse") or "").upper() if facts.get("labelklasse") else None
    bouwjaar = facts.get("bouwjaar")

    subs: list[dict[str, Any]] = []

    if bouwjaar and bouwjaar < 2015:
        subs.append({
            "regeling": "ISDE",
            "maatregel": "Isolatie (dak/gevel/vloer) en/of glas",
            "van_toepassing": True,
            "toelichting": "Bij uitvoering door een bedrijf en voldoen aan minimale oppervlaktes/waarden kan ISDE van toepassing zijn. Met twee maatregelen binnen 24 maanden is de vergoeding doorgaans hoger.",
            "indicatie": "Bedragen zijn afhankelijk van m² en type maatregel."
        })
    else:
        subs.append({
            "regeling": "ISDE",
            "maatregel": "Isolatie/glas, afhankelijk van situatie",
            "van_toepassing": False,
            "toelichting": "Bij nieuwere of al zeer energiezuinige woningen is subsidie vooral relevant bij aantoonbare extra isolatie of glasmaatregelen.",
            "indicatie": "Bedragen zijn afhankelijk van m² en type maatregel."
        })

    if label in (None, "C", "D", "E", "F", "G"):
        subs.append({
            "regeling": "ISDE",
            "maatregel": "Warmtepomp",
            "van_toepassing": True,
            "toelichting": "Subsidie mogelijk bij installatie door een bedrijf en bij een apparaat dat voldoet aan de voorwaarden (o.a. meldcode).",
            "indicatie": "Vaste bedragen per type warmtepomp (afhankelijk van vermogen/variant)."
        })

    return subs
