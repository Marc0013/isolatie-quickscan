"""
advisor.py
==========
Centrale beslislaag voor de PandIQ Isolatie Quickscan.

Transformeert ruwe woningfacts naar een volledig AdviesResult dat door
alle renderers (Markdown, Word, API) gebruikt kan worden.

Gebruik:
    from advisor import build_advice, AdviesResult
    advies = build_advice(facts)

Het facts-dict heeft hetzelfde formaat als dat main.py doorgeeft aan
narrative_from_facts() — zie main.py voor de exacte sleutels.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from report import quickscan_scores, bouwjaar_band
from narratives import narrative_from_facts, score_label
from subsidies_isolatie_glas import get_periode, WARMTEPOMP
from oppervlaktes import bereken_oppervlaktes
from waarschuwingen import genereer_waarschuwingen
from aannames import rc_oud as aannames_rc_oud
from financials import (
    periode_sleutel,
    schat_oppervlaktes,
    schat_warmtebehoefte_totaal,
    bereken_besparing,
    bereken_kosten,
    bereken_subsidie_indicatie,
    bereken_terugverdientijd,
)


# ── Weergavenamen ─────────────────────────────────────────────────────────────

_ELEMENT_NAMEN: dict[str, str] = {
    "dak":   "Dak",
    "gevel": "Gevel",
    "vloer": "Vloer",
    "glas":  "Glas",
}

_MAATREGEL_NAAM: dict[str, str] = {
    "dakisolatie": "Dakisolatie",
    "zoldervloer": "Zoldervloerisolatie",
    "spouwmuur":   "Spouwmuurisolatie",
    "gevel":       "Gevelisolatie",
    "vloer":       "Vloerisolatie",
    "bodem":       "Bodemisolatie (kruipruimte)",
    "hrpp":        "HR++ dubbelglas",
    "vacuum":      "Vacuümglas",
    "triple":      "Triple glas",
    "deuren":      "Isolerende buitendeuren",
}


# ── Dataclasses ───────────────────────────────────────────────────────────────

@dataclass
class PrioriteitItem:
    """Eén geprioriteerde maatregel voor een woning, inclusief financiële indicaties."""
    element:       str            # "dak" | "gevel" | "vloer" | "glas"
    element_naam:  str            # "Dak" | "Gevel" | ...
    score:         int            # 1–5
    urgentie:      str            # "hoog" | "middel" | "laag"
    maatregel_naam: str           # leesbare naam
    maatregel_key:  str           # sleutel in ISDE-tabellen (financials/subsidies)
    opp_indicatief: float         # m² geschat op basis van BAG opp + woningtype
    subsidie_max:   float         # EUR indicatief (meervoudig tarief)
    kosten_min:     float         # EUR totale investering laag
    kosten_max:     float         # EUR totale investering hoog
    besparing_min:  float         # EUR/jaar besparing laag scenario
    besparing_max:  float         # EUR/jaar besparing hoog scenario
    terugverdien_min: Optional[float]  # jaren min (na subsidie)
    terugverdien_max: Optional[float]  # jaren max (na subsidie)


@dataclass
class SubsidieRegel:
    """Eén ISDE-subsidieregel met indicatief bedrag voor deze woning."""
    maatregel:          str    # weergavenaam
    maatregel_key:      str    # sleutel in ISDE-tabellen
    soort:              str    # "isolatie" | "glas" | "warmtepomp"
    bedrag_per_m2:      float  # meervoudig tarief per m²
    opp_indicatief:     float  # m² geschat
    indicatief_totaal:  float  # EUR indicatief totaal voor deze woning
    toelichting:        str


@dataclass
class AdviesResult:
    """
    Volledig adviesresultaat voor één woning.

    Bevat alle data en teksten die renderers (Markdown, Word, API) nodig hebben.
    Maak aan via build_advice(facts) — niet direct instantiëren.

    Velden gemarkeerd met 'indicatief' zijn schattingen; zie de individuele
    docstrings in financials.py voor de methodiek en nauwkeurigheid.
    """
    # ── Identificatie ─────────────────────────────────────────────────────────
    adres:       str
    bouwjaar:    int
    bouwperiode: str            # "voor 1975" | "1975–1991" | "1992–2005" | ...
    opp_m2:      Optional[float]   # BAG gebruiksoppervlakte (m²)
    gebouwtype:  Optional[str]
    data_volledigheid: str      # "volledig" | "geen_label" | "geen_bag" | "minimaal"

    # ── Energielabel ──────────────────────────────────────────────────────────
    labelklasse:     Optional[str]
    energiebehoefte: Optional[float]   # kWh/m²/jr (EP-Online)
    warmtebehoefte:  Optional[float]   # kWh/m²/jr (EP-Online)
    # Totale warmtebehoefte (kWh/jr) — berekend of geschat; zie financials.py
    warmte_totaal_kwh: float
    # Databron gebruikt voor warmtebehoefte-schatting
    # "ep_online_thermisch" | "ep_online_bag" | "default_bouwperiode_bag" | "default_bouwperiode_fallback"
    warmte_bron: str

    # ── Quickscan scores ──────────────────────────────────────────────────────
    scores:         dict[str, int]   # {"dak": 4, "gevel": 4, "vloer": 4, "glas": 4}
    gemiddelde_score: float

    # ── Geprioriteerde maatregelen (gesorteerd: hoogste urgentie eerst) ───────
    # Bevat alleen elementen met score ≥ 2; score 1 wordt apart vermeld.
    prioriteiten: list[PrioriteitItem]

    # ── Subsidies ─────────────────────────────────────────────────────────────
    meervoudig_tarief:          bool    # True als ≥2 maatregelen score ≥3 (combinatiekorting)
    subsidie_regels:            list[SubsidieRegel]
    subsidie_totaal_indicatie:  float   # EUR som indicatieve bedragen (indicatief)

    # ── Narratieve teksten ────────────────────────────────────────────────────
    # Bevat alle bestaande sleutels van narrative_from_facts() voor backward
    # compatibility met fill_docx(), PLUS nieuwe sleutels voor Fase 3.
    #
    # Bestaande sleutels (fill_docx compatibel):
    #   gebouw, energie, aanpak, bouwperiode_inleiding,
    #   score_{element}_tekst, element_tekst_{element},
    #   risicos, subsidies_blok, subsidies_isolatie, vervolgstappen_blok
    #
    # Nieuwe sleutels (Fase 3 renderers):
    #   samenvatting           — executive summary, 4-6 zinnen
    #   prioriteiten_tekst     — geprioriteerde maatregelen met financiële indicaties
    #   subsidie_indicatie_tekst — persoonlijk berekende subsidie-overzicht
    teksten: dict[str, str]

    # ── Call to actions ───────────────────────────────────────────────────────
    cta_primair:   str   # Hoofdactie tekst (bij hoge urgentie: direct offerte)
    cta_secondair: str   # Tweede actie tekst (altijd: subsidiecheck)
    cta_url:       str   # Primaire URL

    # ── Oppervlaktes en waarschuwingen (toegevoegd) ───────────────────────────
    oppervlaktes:   dict = field(default_factory=dict)
    waarschuwingen: list = field(default_factory=list)


# ── Interne helpers ───────────────────────────────────────────────────────────

def _bepaal_data_volledigheid(facts: dict) -> str:
    """
    Beoordeelt welke databronnen beschikbaar zijn.
    opp_bag is de betrouwbare indicator voor succesvolle BAG-respons.
    """
    heeft_bag   = facts.get("opp_bag") is not None
    heeft_label = bool(facts.get("labelklasse"))

    if heeft_bag and heeft_label:
        return "volledig"
    if heeft_bag and not heeft_label:
        return "geen_label"
    if not heeft_bag and heeft_label:
        return "geen_bag"
    return "minimaal"


def _element_naar_maatregel(element: str, bouwjaar: int) -> str:
    """
    Geeft de meest relevante ISDE-maatregelsleutel voor een element en bouwperiode.

    Gevel-mapping: voor 1975 en na 2005 → gevelisolatie (massieve muur of buitengevel);
                   1946–2005 → spouwmuurisolatie (standaard spouwmuur).
    Glas-mapping:  nieuwere woningen (2006+) → triple; oudere → HR++.
    """
    _MAPPING: dict[str, dict[str, str]] = {
        "dak": {
            "voor_1975":  "dakisolatie",
            "1975_1991":  "dakisolatie",
            "1992_2005":  "dakisolatie",
            "2006_2014":  "dakisolatie",
            "2015plus":   "dakisolatie",
        },
        "gevel": {
            "voor_1975":  "gevel",       # massieve muur of vroege spouw → buiten/binnenisolatie
            "1975_1991":  "spouwmuur",   # lege spouw na-isoleren meest rendabel
            "1992_2005":  "spouwmuur",
            "2006_2014":  "gevel",       # al goed gevulde spouw; winst via buitengevel
            "2015plus":   "gevel",
        },
        "vloer": {
            "voor_1975":  "vloer",
            "1975_1991":  "vloer",
            "1992_2005":  "vloer",
            "2006_2014":  "vloer",
            "2015plus":   "vloer",
        },
        "glas": {
            "voor_1975":  "hrpp",
            "1975_1991":  "hrpp",
            "1992_2005":  "hrpp",
            "2006_2014":  "triple",
            "2015plus":   "triple",
        },
    }
    periode = periode_sleutel(bouwjaar)
    return _MAPPING.get(element, {}).get(periode, "dakisolatie")


def _urgentie(score: int) -> str:
    """Score → urgentieniveau voor weergave en sortering."""
    if score >= 4:
        return "hoog"
    if score == 3:
        return "middel"
    return "laag"


def _bouw_prioriteiten(
    scores:         dict[str, int],
    bouwjaar:       int,
    opp_m2:         Optional[float],
    gebouwtype:     Optional[str],
    warmte_totaal:  float,
    meervoudig:     bool = True,
) -> list[PrioriteitItem]:
    """
    Bouwt de lijst van geprioriteerde maatregelen op, gesorteerd op:
    1. Score aflopend (hoogste score = slechtst = eerste prioriteit)
    2. Verwachte besparing (hoog naar laag) bij gelijke score

    Bevat alleen elementen met score ≥ 2. Score 1 is 'goed'; geen actie nodig.
    Elementen met opp_indicatief == 0 (bv. dak bij appartement) worden overgeslagen.
    """
    opp_schatting = schat_oppervlaktes(opp_m2 or 90.0, gebouwtype)

    items: list[PrioriteitItem] = []

    for element, score in scores.items():
        if score is None or score < 2:
            continue  # score 1 = goed, geen actie prioriteit

        maatregel_key  = _element_naar_maatregel(element, bouwjaar)
        opp_elem       = opp_schatting.get(element, 0.0)

        # Sla elementen over zonder oppervlakte (bv. dak bij appartement)
        if opp_elem == 0.0:
            continue

        besparing_min, besparing_max = bereken_besparing(
            element, score, warmte_totaal, bouwjaar
        )
        kosten_min, kosten_max = bereken_kosten(maatregel_key, opp_elem)
        subsidie = bereken_subsidie_indicatie(maatregel_key, opp_elem)
        tvt = bereken_terugverdientijd(
            kosten_min, kosten_max, subsidie, besparing_min, besparing_max
        )

        items.append(PrioriteitItem(
            element        = element,
            element_naam   = _ELEMENT_NAMEN.get(element, element.capitalize()),
            score          = score,
            urgentie       = _urgentie(score),
            maatregel_naam = _MAATREGEL_NAAM.get(maatregel_key, maatregel_key),
            maatregel_key  = maatregel_key,
            opp_indicatief = opp_elem,
            subsidie_max   = subsidie,
            kosten_min     = kosten_min,
            kosten_max     = kosten_max,
            besparing_min  = besparing_min,
            besparing_max  = besparing_max,
            terugverdien_min = tvt[0] if tvt else None,
            terugverdien_max = tvt[1] if tvt else None,
        ))

    # Sorteren: score aflopend, dan besparing_max aflopend
    items.sort(key=lambda x: (-x.score, -x.besparing_max))
    return items


def _bouw_subsidie_regels(
    prioriteiten: list[PrioriteitItem],
    bouwjaar:     int,
) -> list[SubsidieRegel]:
    """
    Bouwt de lijst van relevante ISDE-subsidieregels op basis van de prioriteiten.
    Bevat alleen maatregelen die daadwerkelijk ISDE-subsidie hebben.
    """
    from subsidies_isolatie_glas import ISOLATIE_BEDRAGEN, GLAS_BEDRAGEN

    regels: list[SubsidieRegel] = []

    for item in prioriteiten:
        key = item.maatregel_key

        if key in ISOLATIE_BEDRAGEN:
            data = ISOLATIE_BEDRAGEN[key]
            regels.append(SubsidieRegel(
                maatregel         = item.maatregel_naam,
                maatregel_key     = key,
                soort             = "isolatie",
                bedrag_per_m2     = data["bedrag"],
                opp_indicatief    = item.opp_indicatief,
                indicatief_totaal = item.subsidie_max,
                toelichting       = f"Rc-eis: {data['rd']}",
            ))
        elif key in GLAS_BEDRAGEN:
            data = GLAS_BEDRAGEN[key]
            regels.append(SubsidieRegel(
                maatregel         = item.maatregel_naam,
                maatregel_key     = key,
                soort             = "glas",
                bedrag_per_m2     = data["bedrag"],
                opp_indicatief    = item.opp_indicatief,
                indicatief_totaal = item.subsidie_max,
                toelichting       = f"U-eis: {data['ug']}",
            ))

    return regels


def _bouw_samenvatting(
    adres:              str,
    bouwjaar:           int,
    gebouwtype:         Optional[str],
    labelklasse:        Optional[str],
    gemiddelde_score:   float,
    prioriteiten:       list[PrioriteitItem],
    subsidie_totaal:    float,
    data_volledigheid:  str,
) -> str:
    """
    Genereert de executive summary (4-6 zinnen) bovenaan het rapport.
    Commercieel, persoonlijk en feitelijk onderbouwd.
    """
    delen: list[str] = []
    type_str = f" ({gebouwtype.lower()})" if gebouwtype else ""

    # Databeschikbaarheid-disclaimer als EP-Online ontbreekt
    if data_volledigheid in ("geen_label", "minimaal"):
        delen.append(
            f"Let op: voor uw woning is geen actueel energielabel gevonden in EP-Online. "
            f"De onderstaande scores zijn indicatief op basis van bouwjaar {bouwjaar} "
            f"en vergelijkbare woningen uit dezelfde periode."
        )

    hoge_prio = [p for p in prioriteiten if p.score >= 4]
    middel_prio = [p for p in prioriteiten if p.score == 3]
    goede_elementen = [p for p in prioriteiten if p.score <= 2]

    if gemiddelde_score >= 3.5:
        # Slechte woning: urgente toon, concrete winst centraal
        onderdelen_str = (
            "alle vier onderdelen" if len(hoge_prio) == 4
            else f"{len(hoge_prio)} van de vier onderdelen"
        )
        delen.append(
            f"Uw woning uit {bouwjaar}{type_str} heeft op {onderdelen_str} "
            f"een significant verbeterpotentieel."
        )
        if subsidie_totaal > 0:
            delen.append(
                f"Uw indicatieve ISDE-subsidie voor de relevante maatregelen samen: "
                f"tot €{subsidie_totaal:,.0f}."
            )

    elif gemiddelde_score >= 2.5:
        # Matige woning: verbeterpotentieel, maar geruststellend
        delen.append(
            f"Uw woning uit {bouwjaar}{type_str} heeft een redelijke isolatiebasis, "
            f"maar er zijn gerichte verbeterkansen."
        )
        if middel_prio or hoge_prio:
            top = (hoge_prio + middel_prio)[0]
            delen.append(
                f"De meeste winst zit in {top.element_naam.lower()} ({top.maatregel_naam.lower()}): "
                f"indicatieve besparing €{top.besparing_min:,.0f}–€{top.besparing_max:,.0f} per jaar."
            )
        if subsidie_totaal > 0:
            delen.append(
                f"Indicatieve ISDE-subsidie voor de relevante maatregelen: tot €{subsidie_totaal:,.0f}."
            )

    else:
        # Goede woning: installaties/gasloos als volgende stap
        delen.append(
            f"Uw woning uit {bouwjaar}{type_str} heeft een sterke gebouwschil."
        )
        wp = WARMTEPOMP
        delen.append(
            f"Via de ISDE is mogelijk een startbedrag van €{wp['startbedrag']:,} "
            f"plus €{wp['per_kw']} per kW vermogen beschikbaar voor een warmtepomp."
        )

    # Afsluiten met CTA
    if gemiddelde_score >= 3:
        delen.append(
            "Bereken uw persoonlijke subsidie en vraag een vrijblijvend adviesgesprek "
            "aan via www.pandiq.nl/subsidie."
        )
    else:
        delen.append(
            "Ontdek of uw woning klaar is voor gasloos wonen via www.pandiq.nl."
        )

    return " ".join(delen)


def _bouw_fysische_analyse(
    oppervlaktes:  dict,
    rc_waarden:    dict,
    bouwjaar:      int,
    woningtype:    Optional[str],
) -> str:
    """
    Genereert een sectie met de bouwfysische berekening per bouwdeel:
    oppervlakte, huidige Rc, warmteverliesreductie (kWh/m³/EUR),
    investering, subsidie en dynamische terugverdientijd met doorkijk.
    """
    from aannames import get as aanname
    from financials import (
        warmteverlies_reductie, terugverdientijd_uitgebreid,
        bereken_kosten, bereken_subsidie_indicatie, KOSTEN_PER_M2,
    )

    RC_NIEUW: dict[str, float] = {
        "dak":   aanname("rc_eis_dak"),
        "vloer": aanname("rc_eis_vloer"),
        "gevel": aanname("rc_eis_gevel"),
        "spouw": aanname("rc_eis_spouw"),
    }
    MAATREGEL_KEY: dict[str, str] = {
        "dak":   "dakisolatie",
        "vloer": "vloer",
        "gevel": "gevel",
        "spouw": "spouwmuur",
    }
    ELEMENT_NAAM: dict[str, str] = {
        "dak":   "Dak",
        "vloer": "Vloer",
        "gevel": "Gevelisolatie (buiten/binnen)",
        "spouw": "Spouwmuurisolatie",
    }

    regels: list[str] = []
    wtype = (woningtype or "tussenwoning").lower()

    regels.append(
        f"_Oppervlaktes berekend op basis van woningtype '{wtype}' "
        f"en bouwjaar {bouwjaar}. Alle bedragen zijn indicatief._"
    )
    regels.append("")

    for el in ("dak", "vloer", "spouw", "gevel", "glas"):
        opp_info   = oppervlaktes.get(el, {})
        opp_m2     = opp_info.get("opp_m2", 0.0) if isinstance(opp_info, dict) else 0.0
        toelichting = opp_info.get("toelichting", "") if isinstance(opp_info, dict) else ""

        if el == "glas":
            # Glas apart: toon alleen oppervlak, geen Rc-berekening
            if opp_m2 > 0:
                from aannames import u_oud_glas as _u_oud_glas
                u_info = _u_oud_glas(bouwjaar)
                regels.append(f"**Glas**")
                regels.append(f"Aanname huidige situatie: {u_info.get('toelichting', '')}")
                regels.append(f"_{toelichting}_")
                regels.append("")
                regels.append("")
            continue

        rc_info   = rc_waarden.get(el, {})
        rc_huidig = rc_info.get("rc", 0.0) if isinstance(rc_info, dict) else 0.0
        rc_doel   = RC_NIEUW[el]
        maatr_key = MAATREGEL_KEY[el]

        naam = ELEMENT_NAAM[el]
        regels.append(f"**{naam}**")
        regels.append(f"Aanname huidige situatie: {rc_info.get('toelichting', '')}")

        if opp_m2 == 0.0:
            regels.append("Niet van toepassing voor dit woningtype.")
            regels.append("")
            regels.append("")
            continue

        if rc_huidig >= rc_doel:
            regels.append(
                f"Je Rc-waarde is {rc_huidig} m²K/W en voldoet aan de ISDE-eis "
                f"en komt hierom niet in aanmerking voor subsidie."
            )
            regels.append("")
            regels.append("")
            continue

        regels.append(f"_{toelichting}_")
        regels.append(
            f"Huidige Rc: {rc_huidig} m²K/W "
            f"({rc_info.get('toelichting', '')})"
        )
        regels.append(f"Streefwaarde Rc: {rc_doel} m²K/W (ISDE-minimumeis)")

        verlies = warmteverlies_reductie(opp_m2, rc_huidig, rc_doel)
        kosten_min, kosten_max = bereken_kosten(maatr_key, opp_m2)
        subsidie = bereken_subsidie_indicatie(maatr_key, opp_m2)
        netto    = max(0.0, (kosten_min + kosten_max) / 2 - subsidie)
        tvt      = terugverdientijd_uitgebreid(netto, verlies["euro_jr"])

        regels.append(
            f"Besparing na isolatie naar Rc {rc_doel}: "
            f"**{verlies['kwh_jr']:,.0f} kWh/jr** | "
            f"{verlies['m3_gas_jr']:,.0f} m³ gas/jr | "
            f"**€ {verlies['euro_jr']:,.0f}/jr**"
        )
        regels.append(
            f"Investering: €{kosten_min:,.0f}–€{kosten_max:,.0f} | "
            f"ISDE-subsidie: tot €{subsidie:,.0f} | "
            f"Netto: ~€{netto:,.0f}"
        )
        if tvt["tvt_jaar"] is not None:
            dk = tvt["doorkijk"]
            regels.append(
                f"Terugverdientijd: **{tvt['tvt_jaar']} jaar** "
                f"(bij {tvt['prijsstijging_gebruikt']*100:.0f}% energieprijsstijging/jr)"
            )
            if tvt["tvt_jaar"] > 20:
                regels.append("")
                regels.append(
                    "_Enkel interessant in combinatie met groot onderhoud of verbouw._"
                )
            regels.append(
                f"Doorkijk: "
                f"5 jr → €{dk[5]['cum_besparing']:,.0f} | "
                f"10 jr → €{dk[10]['cum_besparing']:,.0f} | "
                f"20 jr → €{dk[20]['cum_besparing']:,.0f} cumulatief"
            )
        else:
            regels.append("Terugverdientijd: niet berekend (controleer besparing en investering)")

        regels.append("")
        regels.append("")

    # ── Totaalsamenvatting alle maatregelen ───────────────────────────────────
    tot_kosten_min = 0.0
    tot_kosten_max = 0.0
    tot_sub_basis  = 0.0
    tot_besparing  = 0.0
    n_maatregelen  = 0

    for el in ("dak", "vloer", "spouw", "gevel"):
        opp_info  = oppervlaktes.get(el, {})
        opp_m2    = opp_info.get("opp_m2", 0.0) if isinstance(opp_info, dict) else 0.0
        rc_info   = rc_waarden.get(el, {})
        rc_huidig = rc_info.get("rc", 0.0) if isinstance(rc_info, dict) else 0.0
        rc_doel   = RC_NIEUW[el]
        maatr_key = MAATREGEL_KEY[el]

        if opp_m2 == 0.0 or rc_huidig >= rc_doel:
            continue

        verlies         = warmteverlies_reductie(opp_m2, rc_huidig, rc_doel)
        k_min, k_max    = bereken_kosten(maatr_key, opp_m2)
        sub             = bereken_subsidie_indicatie(maatr_key, opp_m2)

        tot_kosten_min += k_min
        tot_kosten_max += k_max
        tot_sub_basis  += sub
        tot_besparing  += verlies["euro_jr"]
        n_maatregelen  += 1

    if n_maatregelen >= 2 and tot_besparing > 0:
        tot_sub_dubbel  = min(tot_sub_basis * 2, (tot_kosten_min + tot_kosten_max) / 2)
        netto_basis     = max(0.0, (tot_kosten_min + tot_kosten_max) / 2 - tot_sub_basis)
        netto_dubbel    = max(0.0, (tot_kosten_min + tot_kosten_max) / 2 - tot_sub_dubbel)
        tvt_basis       = terugverdientijd_uitgebreid(netto_basis,  tot_besparing)
        tvt_dubbel      = terugverdientijd_uitgebreid(netto_dubbel, tot_besparing)

        tvt_b_str = f"{tvt_basis['tvt_jaar']} jaar"  if tvt_basis["tvt_jaar"]  else ">"
        tvt_d_str = f"{tvt_dubbel['tvt_jaar']} jaar" if tvt_dubbel["tvt_jaar"] else ">"

        regels.append("---")
        regels.append("")
        regels.append("**Totaaloverzicht bij uitvoering van alle maatregelen**")
        regels.append("")
        regels.append(
            "Wanneer u meerdere isolatiemaatregelen combineert — of een isolatiemaatregel "
            "koppelt aan een warmtepomp — verdubbelt de ISDE-subsidie automatisch. "
            f"Uw subsidie komt dan niet uit op **€{tot_sub_basis:,.0f}** maar op "
            f"**€{tot_sub_dubbel:,.0f}**."
        )
        regels.append("")
        regels.append(f"| | Bedrag |")
        regels.append(f"|---|---|")
        regels.append(f"| Totale investering | €{tot_kosten_min:,.0f} – €{tot_kosten_max:,.0f} |")
        regels.append(f"| Subsidie (enkelvoudig) | €{tot_sub_basis:,.0f} |")
        regels.append(f"| Subsidie (meervoudig, bij combinatie) | **€{tot_sub_dubbel:,.0f}** |")
        regels.append(f"| Netto investering (enkelvoudig) | €{netto_basis:,.0f} |")
        regels.append(f"| Netto investering (meervoudig) | **€{netto_dubbel:,.0f}** |")
        regels.append(f"| Jaarlijkse energiebesparing | €{tot_besparing:,.0f}/jr |")
        regels.append(f"| Terugverdientijd (enkelvoudig) | {tvt_b_str} |")
        regels.append(f"| Terugverdientijd (meervoudig) | **{tvt_d_str}** |")
        regels.append("")

    return "\n".join(regels)


def _bouw_waarschuwingen_tekst(waarschuwingen: list[dict]) -> str:
    """
    Formatteert de lijst van waarschuwingen als leesbare Markdown-tekst.
    """
    if not waarschuwingen:
        return ""

    NIVEAU_PREFIX = {
        "info":    "**Info**",
        "let_op":  "**Let op**",
        "risico":  "**Aandachtspunt**",
    }

    regels: list[str] = []
    for w in waarschuwingen:
        prefix = NIVEAU_PREFIX.get(w["niveau"], "**Opmerking**")
        regels.append(
            f"- {prefix} ({w['element']}): {w['bericht']}  \n"
            f"  _{w['aanbeveling']}_"
        )

    return "\n".join(regels)


def _bouw_prioriteiten_tekst(
    prioriteiten:      list[PrioriteitItem],
    data_volledigheid: str,
) -> str:
    """
    Genereert de tekst voor de geprioriteerde maatregelen-sectie.
    Vervangt in Fase 3 de hardcoded sectie 3 en 4 in render_markdown().

    Per maatregel met score ≥ 3: naam, score, urgentie, besparing, kosten, terugverdientijd.
    Per maatregel met score 1–2: korte positieve noot.
    """
    if not prioriteiten:
        return (
            "Op basis van de beschikbare gegevens zijn er geen elementen met "
            "een duidelijk verbeterpotentieel geïdentificeerd. "
            "Zie de woninggegevens voor meer context."
        )

    regels: list[str] = []
    rang = 0

    for item in prioriteiten:
        if item.score >= 3:
            rang += 1
            urgentie_label = {
                "hoog":   "Hoge urgentie",
                "middel": "Gemiddelde prioriteit",
                "laag":   "Lage prioriteit",
            }.get(item.urgentie, item.urgentie)

            regels.append(
                f"**{rang}. {item.element_naam} — score {item.score}/5 "
                f"({score_label(item.score)}) — {urgentie_label}**"
            )
            regels.append(f"Aanbevolen maatregel: {item.maatregel_naam}")
            if item.opp_indicatief > 0:
                regels.append(f"Geschatte oppervlakte: ~{item.opp_indicatief:.0f} m²")

            if item.besparing_max > 0:
                regels.append(
                    f"Indicatieve besparing: €{item.besparing_min:,.0f}–"
                    f"€{item.besparing_max:,.0f} per jaar"
                )
            if item.kosten_max > 0:
                regels.append(
                    f"Indicatieve investering: €{item.kosten_min:,.0f}–"
                    f"€{item.kosten_max:,.0f}"
                )
            if item.subsidie_max > 0:
                regels.append(
                    f"ISDE-subsidie indicatie: tot €{item.subsidie_max:,.0f}"
                )
            if item.terugverdien_min is not None and item.terugverdien_max is not None:
                regels.append(
                    f"Terugverdientijd na subsidie: "
                    f"circa {item.terugverdien_min:.0f}–{item.terugverdien_max:.0f} jaar"
                )
            regels.append("")  # witregel

        else:
            # Score 1-2: positieve noot, geen uitgebreide financiële info
            regels.append(
                f"**{item.element_naam} — score {item.score}/5 "
                f"({score_label(item.score)})**  "
                f"Dit onderdeel is op orde. Grote ingrepen zijn hier niet de eerste prioriteit."
            )
            regels.append("")

    if data_volledigheid != "volledig":
        regels.append(
            "_Financiële indicaties zijn schattingen op basis van bouwjaar en "
            "gemiddelde woningkenmerken. Definitieve bedragen hangen af van de "
            "werkelijke situatie ter plaatse._"
        )

    return "\n".join(regels)


def _bouw_subsidie_indicatie_tekst(
    adres:           str,
    opp_m2:          Optional[float],
    bouwjaar:        int,
    subsidie_regels: list[SubsidieRegel],
    subsidie_totaal: float,
) -> str:
    """
    Genereert een persoonlijk subsidie-overzicht op basis van woningkenmerken.
    Vervangt in Fase 3 de generieke 3-rij subsidietabel in render_markdown().
    """
    if not subsidie_regels and subsidie_totaal == 0:
        return (
            "Op basis van het bouwjaar zijn er geen directe ISDE-isolatiesubsidies "
            "van toepassing. Wel is de ISDE warmtepomp-subsidie beschikbaar: "
            f"startbedrag €{WARMTEPOMP['startbedrag']:,} + "
            f"€{WARMTEPOMP['per_kw']} per kW vermogen."
        )

    opp_str = f" ({opp_m2:.0f} m²)" if opp_m2 else ""
    regels: list[str] = [
        f"Op basis van uw woning{opp_str} met bouwjaar {bouwjaar} zijn de "
        f"volgende ISDE-subsidies indicatief van toepassing (tarieven 2026):",
        "",
    ]

    for regel in subsidie_regels:
        regels.append(
            f"- **{regel.maatregel}** (~{regel.opp_indicatief:.0f} m²): "
            f"tot **€{regel.indicatief_totaal:,.0f}**"
            f"  _{regel.toelichting}_"
        )

    regels.append("")
    regels.append(
        f"**Indicatief subsidietotaal: tot €{subsidie_totaal:,.0f}**"
    )

    regels.append("")
    regels.append(
        "**Wanneer wordt het subsidiebedrag verdubbeld?**  \n"
        "Het meervoudig tarief geldt als u een isolatiemaatregel combineert met de installatie "
        "van een warmtepomp, zonneboiler of aansluiting op een warmtenet. "
        "Vraag de subsidie aan binnen 24 maanden na het uitvoeren van de eerste maatregel.  \n"
        "Het subsidiebedrag wordt _niet_ verdubbeld als u de isolatiemaatregel alleen combineert "
        "met ventilatie, of als u isoleert met biobased milieuvriendelijke isolatiematerialen."
    )

    # Warmtepomp toevoegen als aanvulling
    wp = WARMTEPOMP
    regels.append("")
    regels.append(
        f"Daarnaast: ISDE warmtepomp — startbedrag €{wp['startbedrag']:,} "
        f"+ €{wp['per_kw']} per kW + €{wp['aplus_bonus']} bonus bij A+++ label."
    )
    regels.append("")
    regels.append(
        "_Subsidie-indicaties zijn berekend op basis van geschatte oppervlaktes. "
        "Definitieve bedragen worden vastgesteld na technische inspectie. "
        "Bereken uw exacte bedrag op www.pandiq.nl/subsidie._"
    )

    return "\n".join(regels)


def _bepaal_cta(
    gemiddelde_score: float,
    focus:            str,
    data_volledigheid: str,
) -> tuple[str, str, str]:
    """
    Kiest de juiste CTA-variant op basis van woningprofiel.

    Returns:
        (cta_primair, cta_secondair, cta_url)
    """
    if gemiddelde_score >= 4.0:
        # Urgente situatie: direct offerte aanvragen
        return (
            "Vraag nu een vrijblijvende offerte aan — inclusief subsidiecheck en aanvraagafhandeling",
            "Bereken uw subsidie in 2 minuten op www.pandiq.nl/subsidie",
            "https://www.pandiq.nl/offerte",
        )
    elif gemiddelde_score >= 3.0:
        # Verbeteren: plan een adviesgesprek
        return (
            "Plan een gratis adviesgesprek om de juiste volgorde en besparingen te bepalen",
            "Bereken uw subsidie op www.pandiq.nl/subsidie",
            "https://www.pandiq.nl/advies",
        )
    elif gemiddelde_score >= 2.0:
        # Optimaliseren: focus op installaties
        return (
            "Ontdek welke installatie-upgrade het meeste oplevert voor uw woning",
            "Bereken uw warmtepomp-subsidie op www.pandiq.nl/subsidie",
            "https://www.pandiq.nl/warmtepomp",
        )
    else:
        # Goede woning: gasloos wonen
        return (
            "Bekijk of uw woning klaar is voor gasloos wonen met een warmtepomp",
            "Check de ISDE-subsidie voor uw situatie op www.pandiq.nl/subsidie",
            "https://www.pandiq.nl/gasloos",
        )


# ── Publieke interface ────────────────────────────────────────────────────────

def build_advice(facts: dict[str, Any]) -> AdviesResult:
    """
    Bouwt een volledig AdviesResult op basis van de woningfacts.

    Args:
        facts: dict zoals aangemaakt in main.py na de API-calls.
               Verwachte sleutels: adres, bouwjaar, opp_bag,
               labelklasse, gebouwtype, energiebehoefte, warmtebehoefte,
               opp_thermische_zone, score_dak/gevel/vloer/glas (optioneel).

    Returns:
        AdviesResult met alle berekende data en teksten.
    """
    # ── 1. Basisfacts ophalen ─────────────────────────────────────────────────
    adres       = facts.get("adres") or "onbekend adres"
    bouwjaar    = int(facts.get("bouwjaar") or 1995)
    opp_bag     = facts.get("opp_bag")
    opp_m2      = float(opp_bag) if opp_bag is not None else None
    gebouwtype  = facts.get("gebouwtype")
    labelklasse = (facts.get("labelklasse") or "").upper() or None
    energiebeh  = facts.get("energiebehoefte")
    warmbeh     = facts.get("warmtebehoefte")
    opp_therm   = facts.get("opp_thermische_zone")

    bouwperiode        = bouwjaar_band(bouwjaar)
    data_volledigheid  = _bepaal_data_volledigheid(facts)

    # ── 2. Scores ophalen of berekenen ────────────────────────────────────────
    # Facts kan scores al bevatten (gezet door main.py na quickscan_scores()).
    # Als ze ontbreken, berekenen we ze zelf.
    if facts.get("score_dak") is not None:
        scores = {
            "dak":   facts["score_dak"],
            "gevel": facts["score_gevel"],
            "vloer": facts["score_vloer"],
            "glas":  facts["score_glas"],
        }
    else:
        label_dict = {
            "labelklasse":    labelklasse,
            "energiebehoefte": energiebeh,
            "warmtebehoefte":  warmbeh,
        } if labelklasse else None
        scan = quickscan_scores(bouwjaar, label_dict)
        scores = scan["scores"]

    gemiddelde_score = sum(scores.values()) / len(scores) if scores else 3.0

    # ── 3. Totale warmtebehoefte berekenen ────────────────────────────────────
    warmte_totaal = schat_warmtebehoefte_totaal(
        warmbeh, opp_therm, opp_m2, bouwjaar
    )
    # Registreer welke databron voor warmtebehoefte is gebruikt (transparantie)
    if warmbeh and opp_therm:
        warmte_bron = "ep_online_thermisch"
    elif warmbeh and opp_m2:
        warmte_bron = "ep_online_bag"
    elif opp_m2:
        warmte_bron = "default_bouwperiode_bag"
    else:
        warmte_bron = "default_bouwperiode_fallback"

    # ── 4. Geprioriteerde maatregelen ─────────────────────────────────────────
    # Meervoudig tarief: ≥2 elementen met score ≥3 (combinatiekorting ISDE 2026)
    n_relevante    = sum(1 for s in scores.values() if s is not None and s >= 3)
    meervoudig_tarief = n_relevante >= 2

    prioriteiten = _bouw_prioriteiten(
        scores, bouwjaar, opp_m2, gebouwtype, warmte_totaal, meervoudig_tarief
    )

    # ── 5. Subsidieregels ─────────────────────────────────────────────────────
    subsidie_regels = _bouw_subsidie_regels(prioriteiten, bouwjaar)
    subsidie_totaal = sum(r.indicatief_totaal for r in subsidie_regels)

    # ── 6. Narratieve teksten genereren ───────────────────────────────────────
    # Roep bestaande narrative_from_facts() aan voor backward compatibility.
    # Voeg daarna nieuwe sleutels toe.
    teksten: dict[str, str] = narrative_from_facts(facts)

    # Nieuwe sleutels voor Fase 3
    from teksten_bouwperiodes import get_focus
    focus = get_focus(bouwjaar)

    teksten["samenvatting"] = _bouw_samenvatting(
        adres, bouwjaar, gebouwtype, labelklasse,
        gemiddelde_score, prioriteiten, subsidie_totaal, data_volledigheid,
    )
    teksten["prioriteiten_tekst"] = _bouw_prioriteiten_tekst(
        prioriteiten, data_volledigheid
    )
    teksten["subsidie_indicatie_tekst"] = _bouw_subsidie_indicatie_tekst(
        adres, opp_m2, bouwjaar, subsidie_regels, subsidie_totaal
    )

    # ── 7. CTAs ───────────────────────────────────────────────────────────────
    cta_primair, cta_secondair, cta_url = _bepaal_cta(
        gemiddelde_score, focus, data_volledigheid
    )

    # ── 8. Oppervlaktes en waarschuwingen (nieuwe modules) ────────────────────
    woningtype_input = facts.get("woningtype")
    dak_type_input   = facts.get("dak_type", "hellend")
    bvo              = opp_m2 or 90.0

    berekende_oppervlaktes = bereken_oppervlaktes(
        bvo_m2    = bvo,
        woningtype = woningtype_input,
        bouwjaar  = bouwjaar,
        dak_type  = dak_type_input,
    )

    rc_waarden_huidig = {
        el: aannames_rc_oud(el, bouwjaar)
        for el in ("dak", "vloer", "gevel", "spouw")
    }

    berekende_waarschuwingen = genereer_waarschuwingen(
        facts        = facts,
        oppervlaktes = berekende_oppervlaktes,
        rc_waarden   = rc_waarden_huidig,
    )

    teksten["fysische_analyse"] = _bouw_fysische_analyse(
        oppervlaktes = berekende_oppervlaktes,
        rc_waarden   = rc_waarden_huidig,
        bouwjaar     = bouwjaar,
        woningtype   = woningtype_input,
    )
    teksten["waarschuwingen_tekst"] = _bouw_waarschuwingen_tekst(berekende_waarschuwingen)

    return AdviesResult(
        adres                    = adres,
        bouwjaar                 = bouwjaar,
        bouwperiode              = bouwperiode,
        opp_m2                   = opp_m2,
        gebouwtype               = gebouwtype,
        data_volledigheid        = data_volledigheid,
        labelklasse              = labelklasse,
        energiebehoefte          = energiebeh,
        warmtebehoefte           = warmbeh,
        warmte_totaal_kwh        = warmte_totaal,
        warmte_bron              = warmte_bron,
        scores                   = scores,
        gemiddelde_score         = gemiddelde_score,
        prioriteiten             = prioriteiten,
        meervoudig_tarief        = meervoudig_tarief,
        subsidie_regels          = subsidie_regels,
        subsidie_totaal_indicatie = subsidie_totaal,
        teksten                  = teksten,
        cta_primair              = cta_primair,
        cta_secondair            = cta_secondair,
        cta_url                  = cta_url,
        oppervlaktes             = berekende_oppervlaktes,
        waarschuwingen           = berekende_waarschuwingen,
    )
