"""
waarschuwingen.py
=================
Genereert contextuele waarschuwingen en aandachtspunten op basis van
woningfacts, berekende oppervlaktes en Rc-waarden.

Elke waarschuwing heeft: niveau, element, bericht, aanbeveling.
Niveau: "info" | "let_op" | "risico"
"""
from __future__ import annotations

from typing import Any

from aannames import get as aanname


def genereer_waarschuwingen(
    facts:        dict[str, Any],
    oppervlaktes: dict[str, Any],
    rc_waarden:   dict[str, Any],
) -> list[dict]:
    """
    Genereert een lijst van waarschuwingen en aandachtspunten.

    Args:
        facts:        woningfacts-dict (bouwjaar, woningtype, geldig_tot, etc.)
        oppervlaktes: uitvoer van bereken_oppervlaktes()
        rc_waarden:   dict {element: {"rc": float, ...}} per bouwdeel

    Returns:
        list van dicts met sleutels "niveau", "element", "bericht", "aanbeveling"
    """
    waarschuwingen: list[dict] = []

    bouwjaar   = int(facts.get("bouwjaar") or 1995)
    woningtype = (facts.get("woningtype") or "").lower().replace("-", "_").replace(" ", "_")
    label_datum = facts.get("geldig_tot") or facts.get("registratiedatum") or ""

    # ── Check 2: Bouwjaar < 1930, massief metselwerk, geen spouw ────────────
    if bouwjaar < 1930:
        waarschuwingen.append({
            "niveau":      "risico",
            "element":     "spouw",
            "bericht":     (
                f"Bouwjaar {bouwjaar} < 1930: massief metselwerk is aannemelijk, "
                f"er is waarschijnlijk geen spouwmuur aanwezig."
            ),
            "aanbeveling": (
                "Spouwmuurisolatie is technisch niet mogelijk bij massief metselwerk. "
                "Overweeg binnenisolatie of buitengevelisolatie; laat dit bouwkundig controleren."
            ),
        })

    # ── Check 3: Appartement + warmtepomp → VvE-toestemming ──────────────────
    if "appartement" in woningtype:
        waarschuwingen.append({
            "niveau":      "let_op",
            "element":     "installatie",
            "bericht":     (
                "Appartement: voor plaatsing van een warmtepomp of buitenunit is "
                "doorgaans toestemming van de VvE (Vereniging van Eigenaren) vereist."
            ),
            "aanbeveling": (
                "Controleer de VvE-statuten en vraag schriftelijke toestemming aan "
                "voor het indienen van de subsidieaanvraag."
            ),
        })

    # ── Check 4: Bouwjaar < 1975 + binnenisolatie → condensatierisico ────────
    if bouwjaar < 1975:
        waarschuwingen.append({
            "niveau":      "risico",
            "element":     "gevel",
            "bericht":     (
                f"Bouwjaar {bouwjaar} < 1975: bij binnenisolatie van gevels bestaat "
                f"risico op condensatie en schimmelvorming ter plaatse van balkkoppen."
            ),
            "aanbeveling": (
                "Laat een bouwfysisch advies uitvoeren voor toepassing van binnenisolatie. "
                "Let op dampopen uitvoering en detaillering van balkkoppen en aansluitingen."
            ),
        })

    # ── Check 5: Recent label maar lage Rc → inconsistentie ──────────────────
    try:
        if label_datum:
            label_jaar = int(str(label_datum)[:4])
            if label_jaar >= 2015:
                slechte_rc = [
                    el for el, info in rc_waarden.items()
                    if isinstance(info, dict)
                    and info.get("rc", 99.0) < 1.0
                    and el in ("dak", "vloer", "gevel")
                ]
                if slechte_rc:
                    waarschuwingen.append({
                        "niveau":      "let_op",
                        "element":     ", ".join(slechte_rc),
                        "bericht":     (
                            f"Energielabel is recent (geregistreerd {label_jaar}) maar de "
                            f"indicatieve Rc-waarde voor {', '.join(slechte_rc)} is laag "
                            f"op basis van het bouwjaar."
                        ),
                        "aanbeveling": (
                            "Controleer of er al isolatie is aangebracht die niet in het "
                            "bouwjaar is verwerkt. Vraag de EPA-maatwerkrapportage op via RVO."
                        ),
                    })
    except (ValueError, TypeError):
        pass

    # ── Check 6: Netto gevelopp < ISDE-minimum → geen subsidie ───────────────
    isde_min_gevel = 10.0  # bron: financials.ISDE_MIN_OPP_ISOLATIE["gevel"]
    gevel_info = oppervlaktes.get("gevel")
    gevel_opp  = gevel_info.get("opp_m2", 99.0) if isinstance(gevel_info, dict) else 99.0
    if 0 < gevel_opp < isde_min_gevel:
        waarschuwingen.append({
            "niveau":      "info",
            "element":     "gevel",
            "bericht":     (
                f"Netto geveloppervlak ({gevel_opp:.1f} m²) is kleiner dan het "
                f"ISDE-minimum van {isde_min_gevel:.0f} m²."
            ),
            "aanbeveling": (
                "Voor dit geveloppervlak is geen ISDE-subsidie beschikbaar. "
                "De investering kan desondanks rendabel zijn via andere subsidievormen."
            ),
        })

    return waarschuwingen
