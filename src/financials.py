"""
financials.py
=============
Indicatieve financiële berekeningen per isolatiemaatregel:
investeringskosten, jaarlijkse besparing en terugverdientijd.

Retourneert altijd bandbreedtes — geen precieze getallen.
Gebruik uitvoer altijd met een indicatie-disclaimer.

Bronnen:
  Kostenbandbreedtes : gemiddelde marktprijzen installateurs 2025-2026
                       (Milieu Centraal, VHR, ISSO-publicaties)
  Warmteverliesaandelen : NEN 1068, RVO verliesanalyse Nederlandse woningen
  Energieprijs          : DDNB consumentenprijs aardgas 2026 (gemiddeld)
"""
from __future__ import annotations
from typing import Optional


# ── Energieprijzen ─────────────────────────────────────────────────────────────
GAS_PRIJS_EUR_M3: float = 1.10   # EUR/m³ incl. belastingen en netwerktarieven
KWH_PER_M3_GAS:   float = 8.79   # calorische waarde aardgas (kWh/Nm³)


# ── Indicatieve investeringskosten per maatregel (EUR/m², incl. arbeid, excl. BTW) ──
# Aanpassen als marktprijzen significant veranderen.
KOSTEN_PER_M2: dict[str, dict] = {
    "dakisolatie": {"min": 100,  "max": 150,   "eenheid": "m²"},
    "zoldervloer": {"min": 65,   "max": 85,   "eenheid": "m²"},
    "spouwmuur":   {"min": 15,   "max": 25,   "eenheid": "m²"},
    "gevel":       {"min": 175,   "max": 230,  "eenheid": "m²"},
    "vloer":       {"min": 22,   "max": 30,   "eenheid": "m²"},
    "bodem":       {"min": 15,   "max": 25,   "eenheid": "m²"},
    "hrpp":        {"min": 80,   "max": 150,  "eenheid": "m²"},
    "vacuum":      {"min": 150,  "max": 200,  "eenheid": "m²"},
    "triple":      {"min": 180,  "max": 200,  "eenheid": "m²"},
    "deuren":      {"min": 1250,  "max": 2000, "eenheid": "stuk"},
}


# ── Warmteverliesaandeel per bouwdeel en bouwperiode ──────────────────────────
# Fractie van de totale warmtebehoefte die via dit bouwdeel verloren gaat.
# Referentie: standaard Nederlandse tussenwoning.
# Vrijstaande woning heeft ~20-30% hogere gevels; appartement heeft geen dak.
VERLIES_AANDEEL: dict[str, dict[str, float]] = {
    "voor_1975":  {"dak": 0.25, "gevel": 0.35, "vloer": 0.15, "glas": 0.20},
    "1975_1991":  {"dak": 0.22, "gevel": 0.30, "vloer": 0.15, "glas": 0.22},
    "1992_2005":  {"dak": 0.18, "gevel": 0.25, "vloer": 0.12, "glas": 0.20},
    "2006_2014":  {"dak": 0.15, "gevel": 0.20, "vloer": 0.10, "glas": 0.15},
    "2015plus":   {"dak": 0.10, "gevel": 0.10, "vloer": 0.08, "glas": 0.10},
}


# ── Besparingsefficientie per scoreniveau ─────────────────────────────────────
# Fractie van het verliesaandeel dat de maatregel realiseert.
# Score 5 (ongeïsoleerd) → maatregel pakt ~80% van het verlies aan.
# Score 3 (matige isolatie) → nog ~40% extra besparing mogelijk.
VERBETER_EFFICIENTIE: dict[int, float] = {
    5: 0.80,
    4: 0.65,
    3: 0.40,
    2: 0.15,
    1: 0.05,
}


# ── ISDE minimale subsidiabele oppervlaktes ───────────────────────────────────
# Bron: ISDE-regelgeving 2026 (RVO Uitvoeringsregeling ISDE).
# Maatregelen onder dit minimum komen niet in aanmerking voor ISDE-subsidie.
ISDE_MIN_OPP_ISOLATIE: dict[str, float] = {
    "gevel": 10.0,   # gevelisolatie heeft een apart lager minimum van 10 m²
    # dakisolatie, zoldervloer, spouwmuur, vloer, bodem: allen 20 m²
}
ISDE_MIN_OPP_DEFAULT: float = 20.0  # standaard minimum voor alle overige isolatiemaatregelen
# Glas heeft geen minimum-m² eis in de ISDE; subsidie geldt per m² vervangen glas.


# ── Default warmtebehoefte als EP-Online ontbreekt (kWh/m²/jr) ────────────────
# Gebaseerd op BZK/RVO woningenergiemonitor, gemiddelden per bouwperiode.
WARMTE_DEFAULT_KWH_M2: dict[str, float] = {
    "voor_1975":  185.0,
    "1975_1991":  145.0,
    "1992_2005":   95.0,
    "2006_2014":   70.0,
    "2015plus":    45.0,
}


# ── Oppervlaktefactoren per woningtype ────────────────────────────────────────
# Vermenigvuldigen met BAG gebruiksoppervlakte → indicatieve isolatieoppervlakte.
# Nauwkeurigheid: ±25-30%. Gebruik uitsluitend voor subsidie/kostenscenario's.
_OPP_FACTOREN: dict[str, dict[str, float]] = {
    "vrijstaand":   {"dak": 0.60, "gevel": 0.90, "vloer": 0.50, "glas": 0.14},
    "hoekwoning":   {"dak": 0.58, "gevel": 0.70, "vloer": 0.50, "glas": 0.11},
    "tussenwoning": {"dak": 0.55, "gevel": 0.50, "vloer": 0.50, "glas": 0.08},
    "appartement":  {"dak": 0.00, "gevel": 0.28, "vloer": 0.42, "glas": 0.06},
}
_OPP_FACTOREN_DEFAULT = _OPP_FACTOREN["tussenwoning"]


# ── Hulpfunctie: bouwjaar → interne periode-sleutel ───────────────────────────

def periode_sleutel(bouwjaar: int) -> str:
    """Mapt bouwjaar naar de interne sleutel voor VERLIES_AANDEEL en WARMTE_DEFAULT."""
    if bouwjaar < 1975:
        return "voor_1975"
    if bouwjaar < 1992:
        return "1975_1991"
    if bouwjaar < 2006:
        return "1992_2005"
    if bouwjaar < 2015:
        return "2006_2014"
    return "2015plus"


# ── Publieke functies ──────────────────────────────────────────────────────────

def schat_oppervlaktes(opp_m2: float, gebouwtype: Optional[str]) -> dict[str, float]:
    """
    Schat indicatieve isolatieoppervlaktes per element.

    Args:
        opp_m2: BAG gebruiksoppervlakte in m²
        gebouwtype: woningtype uit EP-Online (of None)

    Returns:
        {"dak": m², "gevel": m², "vloer": m², "glas": m²}
        Waarden zijn indicatief (±25%). Gebruik niet voor offertes.
    """
    type_lower = (gebouwtype or "").lower()

    if "vrijstaand" in type_lower:
        factoren = _OPP_FACTOREN["vrijstaand"]
    elif "hoek" in type_lower:
        factoren = _OPP_FACTOREN["hoekwoning"]
    elif any(w in type_lower for w in ("appartement", "flat", "galerij", "portiek")):
        factoren = _OPP_FACTOREN["appartement"]
    else:
        # tussenwoning als standaard voor onbekend type
        factoren = _OPP_FACTOREN_DEFAULT

    return {k: round(opp_m2 * f, 1) for k, f in factoren.items()}


def schat_warmtebehoefte_totaal(
    warmtebehoefte_m2: Optional[float],
    opp_thermische_zone: Optional[float],
    opp_bag: Optional[float],
    bouwjaar: int,
) -> float:
    """
    Geeft totale jaarlijkse warmtebehoefte in kWh.
    Gebruikt EP-Online data als beschikbaar; valt anders terug op bouwperiode-defaults.

    Voorkeursvolgorde:
    1. EP-Online kWh/m² × thermische zone
    2. EP-Online kWh/m² × BAG oppervlakte
    3. Default kWh/m² voor bouwperiode × BAG oppervlakte
    4. Default × 90 m² (absolute fallback)
    """
    if warmtebehoefte_m2 and opp_thermische_zone:
        return warmtebehoefte_m2 * opp_thermische_zone

    if warmtebehoefte_m2 and opp_bag:
        return warmtebehoefte_m2 * opp_bag

    periode = periode_sleutel(bouwjaar)
    kwh_m2 = WARMTE_DEFAULT_KWH_M2[periode]
    return kwh_m2 * (opp_bag or 90.0)


def bereken_besparing(
    element: str,
    score: int,
    warmte_totaal_kwh: float,
    bouwjaar: int,
) -> tuple[float, float]:
    """
    Geeft (min, max) jaarlijkse besparing in EUR na uitvoering van een maatregel.

    Methode: warmteverlies via element × verbeteringsefficientie bij dit scoreniveau
             → kWh bespaard per jaar → EUR bespaard per jaar (bandbreedte gasprijs ±15%).

    Returns:
        (eur_min, eur_max) — beide afgerond op hele euro's
    """
    periode = periode_sleutel(bouwjaar)
    verlies_f    = VERLIES_AANDEEL.get(periode, {}).get(element, 0.0)
    efficientie  = VERBETER_EFFICIENTIE.get(score, 0.0)

    kwh_bespaard = warmte_totaal_kwh * verlies_f * efficientie

    eur_min = round((kwh_bespaard / KWH_PER_M3_GAS) * (GAS_PRIJS_EUR_M3 * 0.85))
    eur_max = round((kwh_bespaard / KWH_PER_M3_GAS) * (GAS_PRIJS_EUR_M3 * 1.15))

    return eur_min, eur_max


def bereken_kosten(maatregel_key: str, opp_element: float) -> tuple[float, float]:
    """
    Geeft (min, max) indicatieve investeringskosten in EUR.

    Voor maatregelen per stuk (deuren): aanname 2 stuks per woning.
    """
    k = KOSTEN_PER_M2.get(maatregel_key)
    if not k:
        return 0, 0

    if k["eenheid"] == "stuk":
        # Deuren: 2 buitendeuren als standaard aanname
        return k["min"] * 2, k["max"] * 2

    return round(opp_element * k["min"]), round(opp_element * k["max"])


def bereken_subsidie_indicatie(
    maatregel_key: str,
    opp_element: float,
) -> float:
    """
    Geeft indicatief ISDE-subsidiebedrag in EUR voor een maatregel.

    Returns:
        Afgerond bedrag in EUR. Nul als maatregel geen ISDE heeft.
    """
    from subsidies_isolatie_glas import ISOLATIE_BEDRAGEN, GLAS_BEDRAGEN

    if maatregel_key in ISOLATIE_BEDRAGEN:
        # Controleer ISDE minimale oppervlakte; onder minimum = geen subsidie.
        min_opp = ISDE_MIN_OPP_ISOLATIE.get(maatregel_key, ISDE_MIN_OPP_DEFAULT)
        if opp_element < min_opp:
            return 0
        per_m2 = ISOLATIE_BEDRAGEN[maatregel_key]["bedrag"]
        return round(opp_element * per_m2)

    if maatregel_key in GLAS_BEDRAGEN:
        per_m2 = GLAS_BEDRAGEN[maatregel_key]["bedrag"]
        return round(opp_element * per_m2)

    return 0


def bereken_terugverdientijd(
    kosten_min: float,
    kosten_max: float,
    subsidie: float,
    besparing_min: float,
    besparing_max: float,
) -> Optional[tuple[float, float]]:
    """
    Geeft (min, max) terugverdientijd in jaren na aftrek van subsidie.

    Returns:
        (jaren_min, jaren_max) of None als besparing nul/negatief.
        Netto kosten kunnen nooit negatief zijn (subsidie overstijgt investering niet).
    """
    if besparing_min <= 0 or besparing_max <= 0:
        return None

    netto_min = max(0.0, kosten_min - subsidie)
    netto_max = max(0.0, kosten_max - subsidie)

    tvt_min = round(netto_min / besparing_max, 1)
    tvt_max = round(netto_max / besparing_min, 1)

    return tvt_min, tvt_max


# ── Glasbesparing: vaste norm per m² ──────────────────────────────────────────
GAS_BESPARING_GLAS_M3_M2: float = 12.0  # m³ gas/m²/jr — enkel → HR++ glas
# Bron: Milieu Centraal / EnergieNederland referentiewaarden 2024


def bereken_besparing_glas(opp_m2: float) -> dict:
    """
    Berekent energiebesparing bij glasvervanging (enkel → HR++) via vaste m³/m²-norm.

    Vaste waarde: 12 m³ gas per m² glas per jaar.
    Bron: Milieu Centraal / EnergieNederland 2024.

    Returns:
        {"m3_gas_jr": float, "kwh_jr": float, "euro_jr": float}
    """
    m3_gas_jr = round(opp_m2 * GAS_BESPARING_GLAS_M3_M2, 1)
    kwh_jr    = round(m3_gas_jr * KWH_PER_M3_GAS, 1)
    euro_jr   = round(m3_gas_jr * GAS_PRIJS_EUR_M3, 2)
    return {
        "m3_gas_jr": m3_gas_jr,
        "kwh_jr":    kwh_jr,
        "euro_jr":   euro_jr,
    }


# ── Nieuwe fysische berekeningen (importeren uitsluitend uit aannames.py) ─────

def warmteverlies_reductie(
    opp_m2: float,
    rc_oud_waarde: float,
    rc_nieuw: float,
) -> dict:
    """
    Berekent de warmteverliesreductie bij isolatie van een bouwdeel.

    Formule (NEN 1068, vereenvoudigd indicatief):
        Q = opp × (1/Rc_oud − 1/Rc_nieuw) × ΔT × t / 1000   [kWh/jr]

    Args:
        opp_m2:        oppervlakte van het bouwdeel in m²
        rc_oud_waarde: huidige Rc-waarde in m²K/W
        rc_nieuw:      Rc-waarde na isolatie in m²K/W

    Returns:
        {
            "kwh_jr":           float,
            "m3_gas_jr":        float,
            "euro_jr":          float,
            "formule":          str,
            "aannames_gebruikt": dict
        }
    """
    from aannames import get as aanname, AANNAMES

    dt    = aanname("temperatuurverschil_dt")
    t     = aanname("verwarmingsuren_jr")
    p_gas = aanname("gasprijs")
    e_gas = aanname("energieinhoud_gas")
    eta   = aanname("cv_rendement_oud")

    rc_oud_safe = max(rc_oud_waarde, 0.01)  # voorkom deling door nul
    u_oud       = 1.0 / rc_oud_safe
    u_new       = 1.0 / rc_nieuw if rc_nieuw > 0 else 0.0
    delta_u     = max(0.0, u_oud - u_new)

    kwh_jr    = round(opp_m2 * delta_u * dt * t / 1000, 1)
    m3_gas_jr = round(kwh_jr / (e_gas * eta), 1)
    euro_jr   = round(m3_gas_jr * p_gas, 2)

    formule = (
        f"Q = {opp_m2:.1f} m² × (1/{rc_oud_safe} − 1/{rc_nieuw}) "
        f"× {dt} K × {t} h / 1000 = {kwh_jr} kWh/jr"
    )

    return {
        "kwh_jr":    kwh_jr,
        "m3_gas_jr": m3_gas_jr,
        "euro_jr":   euro_jr,
        "formule":   formule,
        "aannames_gebruikt": {
            "temperatuurverschil_dt": {
                "waarde":  dt,
                "eenheid": AANNAMES["temperatuurverschil_dt"]["eenheid"],
                "bron":    AANNAMES["temperatuurverschil_dt"]["bron"],
            },
            "verwarmingsuren_jr": {
                "waarde":  t,
                "eenheid": AANNAMES["verwarmingsuren_jr"]["eenheid"],
                "bron":    AANNAMES["verwarmingsuren_jr"]["bron"],
            },
            "gasprijs": {
                "waarde":  p_gas,
                "eenheid": AANNAMES["gasprijs"]["eenheid"],
                "bron":    AANNAMES["gasprijs"]["bron"],
            },
            "energieinhoud_gas": {
                "waarde":  e_gas,
                "eenheid": AANNAMES["energieinhoud_gas"]["eenheid"],
                "bron":    AANNAMES["energieinhoud_gas"]["bron"],
            },
            "cv_rendement_oud": {
                "waarde":  eta,
                "eenheid": AANNAMES["cv_rendement_oud"]["eenheid"],
                "bron":    AANNAMES["cv_rendement_oud"]["bron"],
            },
        },
    }


def terugverdientijd_uitgebreid(
    netto_investering: float,
    besparing_jr1: float,
) -> dict:
    """
    Berekent de dynamische terugverdientijd met cumulatieve energieprijsstijging.

    Formule cumulatieve besparing over N jaar:
        C(N) = B1 × ((1+p)^N − 1) / p

    Args:
        netto_investering: investering minus subsidie in EUR
        besparing_jr1:     jaarlijkse besparing in jaar 1 in EUR

    Returns:
        {
            "tvt_jaar":               float | None,
            "prijsstijging_gebruikt": float,
            "doorkijk": {
                1:  {"cum_besparing": float, "saldo": float},
                3:  {...}, 5: {...}, 10: {...}, 15: {...}, 20: {...}
            },
            "formule": str
        }
    """
    from aannames import get as aanname

    p = aanname("energieprijsstijging_pct")

    def cum_besparing(n: int) -> float:
        if p == 0:
            return round(besparing_jr1 * n, 2)
        return round(besparing_jr1 * ((1 + p) ** n - 1) / p, 2)

    # Zoek TVT: kleinste N waarbij C(N) >= netto_investering
    tvt_jaar: Optional[float] = None
    if besparing_jr1 > 0 and netto_investering >= 0:
        for n in range(1, 51):
            c_curr = cum_besparing(n)
            if c_curr >= netto_investering:
                c_prev   = cum_besparing(n - 1)
                fractie  = (
                    (netto_investering - c_prev) / (c_curr - c_prev)
                    if c_curr > c_prev else 0.0
                )
                tvt_jaar = round(n - 1 + fractie, 1)
                break

    doorkijk: dict[int, dict] = {}
    for jaar in (1, 3, 5, 10, 15, 20):
        cb = cum_besparing(jaar)
        doorkijk[jaar] = {
            "cum_besparing": cb,
            "saldo":         round(cb - netto_investering, 2),
        }

    formule = (
        f"C(N) = {besparing_jr1:.2f} × ((1+{p})^N − 1) / {p}  "
        f"[energieprijsstijging {p * 100:.1f}%/jr]"
    )

    return {
        "tvt_jaar":               tvt_jaar,
        "prijsstijging_gebruikt": p,
        "doorkijk":               doorkijk,
        "formule":                formule,
    }
