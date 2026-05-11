"""
oppervlaktes.py
===============
Berekent indicatieve isolatieoppervlaktes per bouwdeel op basis van
BAG-gebruiksoppervlakte, woningtype, bouwjaar en daktype.

Methode:
  De berekening werkt in 9 expliciete stappen die elk worden bijgehouden in
  "_stappen". Alle maataannames komen uitsluitend uit aannames.py.

Nauwkeurigheid:
  ±20-30%. Gebruik uitsluitend voor subsidie-/kostenscenario's, niet voor offertes.
"""
from __future__ import annotations

import math
from typing import Optional

from aannames import AANNAMES, get as aanname


def bereken_oppervlaktes(
    bvo_m2: float,
    woningtype: Optional[str],
    bouwjaar: int,
    dak_type: str = "hellend",
) -> dict:
    """
    Berekent indicatieve oppervlaktes per bouwdeel.

    Args:
        bvo_m2:     BAG gebruiksoppervlakte in m²
        woningtype: "rijwoning" | "tussenwoning" | "hoekwoning" |
                    "twee_onder_een_kap" | "vrijstaand" | "appartement"
        bouwjaar:   bouwjaar van de woning
        dak_type:   "hellend" | "plat"

    Returns:
        Dict met per element {"opp_m2", "toelichting", "aanname_gebruikt"},
        plus "_stappen" (berekenlog) en "_meta" (inputparameters).
    """
    stappen: list[str] = []
    wtype = (woningtype or "tussenwoning").lower().replace("-", "_").replace(" ", "_")

    # ── Stap 1: Footprint en verdiepingen ─────────────────────────────────────
    # Standaard footprints in m² per woningtype (CBS/SBR referentiewoningen).
    FOOTPRINT_DEFAULTS: dict[str, float] = {
        "rijwoning":          50.0,
        "tussenwoning":       50.0,
        "hoekwoning":         50.0,
        "twee_onder_een_kap": 80.0,
    }

    if wtype == "vrijstaand":
        # Schat verdiepingen en leidt footprint af uit BVO
        verd_schat = max(1, round(bvo_m2 / 65.0))
        footprint  = bvo_m2 / max(1, verd_schat)
        stappen.append(
            f"Stap 1 (vrijstaand): geschatte verdiepingen={verd_schat} "
            f"(BVO/{65} m²/verdieping), footprint={bvo_m2}/{verd_schat}={footprint:.1f} m²"
        )
    elif wtype == "appartement":
        # Appartement: ~80% van BVO is thermische schil (gang/trappenhuis buiten schil)
        footprint  = bvo_m2 * 0.80
        verd_schat = 1
        stappen.append(
            f"Stap 1 (appartement): footprint={bvo_m2}×0.80={footprint:.1f} m² "
            f"(80% BVO is thermische schil)"
        )
    else:
        footprint  = FOOTPRINT_DEFAULTS.get(wtype, 50.0)
        verd_schat = max(1, round(bvo_m2 / footprint))
        stappen.append(
            f"Stap 1: woningtype={wtype}, standaard footprint={footprint:.0f} m², "
            f"verdiepingen=round({bvo_m2}/{footprint:.0f})={verd_schat}"
        )

    verdiepingen = verd_schat

    # ── Stap 2: Verdiepingshoogte uit AANNAMES op basis van bouwjaar ──────────
    if bouwjaar < 1945:
        vh       = aanname("verdiepingshoogte_oud")
        bron_vh  = AANNAMES["verdiepingshoogte_oud"]["bron"]
        periode_vh = "voor 1945"
    elif bouwjaar < 1992:
        vh       = aanname("verdiepingshoogte_midden")
        bron_vh  = AANNAMES["verdiepingshoogte_midden"]["bron"]
        periode_vh = "1945-1992"
    else:
        vh       = aanname("verdiepingshoogte_nieuw")
        bron_vh  = AANNAMES["verdiepingshoogte_nieuw"]["bron"]
        periode_vh = "na 1992"

    totaal_hoogte = vh * verdiepingen
    stappen.append(
        f"Stap 2: bouwjaar={bouwjaar} → periode '{periode_vh}', "
        f"verdiepingshoogte={vh} m (bron: {bron_vh}), "
        f"totale hoogte={vh}×{verdiepingen}={totaal_hoogte:.2f} m"
    )

    # ── Stap 3: Breedte en diepte per woningtype ──────────────────────────────
    if wtype == "vrijstaand":
        verhouding = aanname("verhouding_vrijstaand")
        breedte    = math.sqrt(footprint / verhouding)
        diepte     = breedte * verhouding
        stappen.append(
            f"Stap 3 (vrijstaand): verhouding={verhouding}, "
            f"breedte=√({footprint:.1f}/{verhouding})={breedte:.2f} m, "
            f"diepte={breedte:.2f}×{verhouding}={diepte:.2f} m"
        )
    elif wtype == "appartement":
        breedte = math.sqrt(footprint * 0.8)
        diepte  = (footprint / breedte) if breedte > 0 else breedte
        stappen.append(
            f"Stap 3 (appartement): breedte=√({footprint:.1f}×0.8)={breedte:.2f} m, "
            f"diepte={footprint:.1f}/{breedte:.2f}={diepte:.2f} m"
        )
    elif wtype == "hoekwoning":
        breedte = aanname("breedte_hoekwoning")
        diepte  = footprint / breedte
        stappen.append(
            f"Stap 3 (hoekwoning): standaard breedte={breedte} m "
            f"(bron: {AANNAMES['breedte_hoekwoning']['bron']}), "
            f"diepte={footprint:.0f}/{breedte}={diepte:.2f} m"
        )
    elif wtype == "twee_onder_een_kap":
        breedte = aanname("breedte_twee_onder_een_kap")
        diepte  = footprint / breedte
        stappen.append(
            f"Stap 3 (twee-onder-een-kap): standaard breedte={breedte} m "
            f"(bron: {AANNAMES['breedte_twee_onder_een_kap']['bron']}), "
            f"diepte={footprint:.0f}/{breedte}={diepte:.2f} m"
        )
    else:
        # rijwoning / tussenwoning
        breedte = aanname("breedte_rijwoning")
        diepte  = footprint / breedte
        stappen.append(
            f"Stap 3 (rijwoning/tussenwoning): standaard breedte={breedte} m "
            f"(bron: {AANNAMES['breedte_rijwoning']['bron']}), "
            f"diepte={footprint:.0f}/{breedte}={diepte:.2f} m"
        )

    # ── Stap 4: Geveloppervlak per woningtype ─────────────────────────────────
    opp_voor   = breedte * totaal_hoogte
    opp_achter = breedte * totaal_hoogte
    opp_zij    = diepte  * totaal_hoogte

    if wtype in ("rijwoning", "tussenwoning"):
        totaal_gevel = opp_voor + opp_achter
        stappen.append(
            f"Stap 4 (rijwoning): voor+achter = "
            f"{opp_voor:.1f}+{opp_achter:.1f} = {totaal_gevel:.1f} m²"
        )
    elif wtype == "hoekwoning":
        totaal_gevel = opp_voor + opp_achter + opp_zij
        stappen.append(
            f"Stap 4 (hoekwoning): voor+achter+1 zij = "
            f"{opp_voor:.1f}+{opp_achter:.1f}+{opp_zij:.1f} = {totaal_gevel:.1f} m²"
        )
    elif wtype == "twee_onder_een_kap":
        totaal_gevel = opp_voor + opp_achter + 2 * opp_zij
        stappen.append(
            f"Stap 4 (twee-onder-een-kap): voor+achter+2×zij = "
            f"{opp_voor:.1f}+{opp_achter:.1f}+2×{opp_zij:.1f} = {totaal_gevel:.1f} m²"
        )
    elif wtype == "vrijstaand":
        totaal_gevel = 2 * opp_voor + 2 * opp_zij
        stappen.append(
            f"Stap 4 (vrijstaand): 2×voor+2×zij = "
            f"2×{opp_voor:.1f}+2×{opp_zij:.1f} = {totaal_gevel:.1f} m²"
        )
    elif wtype == "appartement":
        totaal_gevel = opp_voor  # standaard 1 buitengevel
        stappen.append(
            f"Stap 4 (appartement): 1 buitengevel = {opp_voor:.1f} m² "
            f"(voor 2 buitengevels bij hoek-appartement: pas woningtype aan)"
        )
    else:
        totaal_gevel = opp_voor + opp_achter
        stappen.append(
            f"Stap 4 (onbekend type, fallback rijwoning): {totaal_gevel:.1f} m²"
        )

    # ── Stap 5: Glasoppervlak per gevelzijde ──────────────────────────────────
    ga_voor   = aanname("glasandeel_voorgevel")
    ga_achter = aanname("glasandeel_achtergevel")
    ga_zij    = aanname("glasandeel_zijgevel")

    glas_voor   = opp_voor   * ga_voor
    glas_achter = opp_achter * ga_achter
    glas_zij    = opp_zij    * ga_zij

    if wtype in ("rijwoning", "tussenwoning"):
        totaal_glas = glas_voor + glas_achter
        glas_log = f"voor×{ga_voor}+achter×{ga_achter}"
    elif wtype == "hoekwoning":
        totaal_glas = glas_voor + glas_achter + glas_zij
        glas_log = f"voor×{ga_voor}+achter×{ga_achter}+zij×{ga_zij}"
    elif wtype == "twee_onder_een_kap":
        totaal_glas = glas_voor + glas_achter + 2 * glas_zij
        glas_log = f"voor×{ga_voor}+achter×{ga_achter}+2×zij×{ga_zij}"
    elif wtype == "vrijstaand":
        totaal_glas = 2 * glas_voor + 2 * glas_zij
        glas_log = f"2×voor×{ga_voor}+2×zij×{ga_zij}"
    elif wtype == "appartement":
        totaal_glas = glas_voor
        glas_log = f"voor×{ga_voor}"
    else:
        totaal_glas = glas_voor + glas_achter
        glas_log = f"voor×{ga_voor}+achter×{ga_achter}"

    stappen.append(
        f"Stap 5: glas = {glas_log} = {totaal_glas:.1f} m² "
        f"(bron: {AANNAMES['glasandeel_voorgevel']['bron']})"
    )

    # ── Stap 6: Netto gevel (zonder glas) ─────────────────────────────────────
    netto_gevel = max(0.0, totaal_gevel - totaal_glas)
    stappen.append(
        f"Stap 6: netto gevel = {totaal_gevel:.1f} − {totaal_glas:.1f} = {netto_gevel:.1f} m²"
    )

    # ── Stap 7: Dakoppervlak ──────────────────────────────────────────────────
    if wtype == "appartement":
        dak_opp = 0.0
        stappen.append("Stap 7: appartement → dak = 0 m² (geen eigen dak)")
    else:
        dakfactor_sleutel = "dakfactor_plat" if dak_type == "plat" else "dakfactor_hellend"
        dakfactor = aanname(dakfactor_sleutel)
        dak_opp   = round(footprint * dakfactor, 1)
        stappen.append(
            f"Stap 7: dak = footprint×dakfactor = {footprint:.1f}×{dakfactor} = {dak_opp:.1f} m² "
            f"(dak_type={dak_type}, bron: {AANNAMES[dakfactor_sleutel]['bron']})"
        )
        dakfactor  # bewaar voor toelichting hieronder

    # ── Stap 8: Vloeroppervlak = footprint ────────────────────────────────────
    vloer_opp = round(footprint, 1)
    stappen.append(f"Stap 8: vloer = footprint = {vloer_opp:.1f} m²")

    # ── Stap 9: Spouwmuuroppervlak ────────────────────────────────────────────
    if bouwjaar <= 1920:
        spouw_opp = 0.0
        stappen.append(
            f"Stap 9: spouw = 0 m² "
            f"(bouwjaar {bouwjaar} <= 1920, massief metselwerk aannemelijk, geen spouw)"
        )
    elif wtype == "appartement":
        spouw_opp = 0.0
        stappen.append(
            "Stap 9: spouw = 0 m² "
            "(appartement, buitengevel volgt gevel-maatregel, spouw niet separaat)"
        )
    else:
        spouw_opp = round(netto_gevel, 1)
        stappen.append(
            f"Stap 9: spouw = netto_gevel = {spouw_opp:.1f} m² "
            f"(zelfde vlak als gevel, andere ISDE-maatregel)"
        )

    # ── Resultaat samenvoegen ─────────────────────────────────────────────────
    dak_factor_val = aanname("dakfactor_plat") if dak_type == "plat" else (
        aanname("dakfactor_hellend") if wtype != "appartement" else 1.0
    )

    return {
        "dak": {
            "opp_m2":           dak_opp,
            "toelichting":      (
                f"{'Hellend' if dak_type == 'hellend' else 'Plat'} dak, "
                f"footprint {footprint:.0f} m² × factor {dak_factor_val}"
                if wtype != "appartement" else "Geen eigen dak (appartement)"
            ),
            "aanname_gebruikt": True,
        },
        "vloer": {
            "opp_m2":           vloer_opp,
            "toelichting":      f"Vloer = footprint {footprint:.0f} m²",
            "aanname_gebruikt": True,
        },
        "gevel": {
            "opp_m2":           round(netto_gevel, 1),
            "toelichting":      (
                f"Netto gevel (excl. glas), {wtype}; "
                f"bruto {totaal_gevel:.0f} m² − glas {totaal_glas:.0f} m²"
            ),
            "aanname_gebruikt": True,
        },
        "spouw": {
            "opp_m2":           spouw_opp,
            "toelichting":      (
                "Geen spouw aanwezig (voor 1920 of appartement)"
                if spouw_opp == 0.0
                else f"Spouwmuuroppervlak = netto gevel {spouw_opp:.0f} m²"
            ),
            "aanname_gebruikt": True,
        },
        "glas": {
            "opp_m2":           round(totaal_glas, 1),
            "toelichting":      (
                f"Glasoppervlak o.b.v. hoeveelheden glas per gevelzijde, {wtype}"
            ),
            "aanname_gebruikt": True,
        },
        "_stappen": stappen,
        "_meta": {
            "bvo_m2":        bvo_m2,
            "woningtype":    wtype,
            "bouwjaar":      bouwjaar,
            "dak_type":      dak_type,
            "footprint_m2":  round(footprint, 1),
            "verdiepingen":  verdiepingen,
            "hoogte_totaal": round(totaal_hoogte, 2),
        },
    }
