"""
narratives.py
=============
Genereert alle tekstblokken voor het PandIQ isolatie quickscan rapport.
Niveau: inzicht (1) + duiding (2) + actie (3).
"""
from __future__ import annotations
from datetime import datetime
from typing import Any, Optional
from teksten_bouwperiodes import (
    bouw_bouwperiode_tekst, get_risicos_tekst, get_focus, get_actie,
    get_subsidies_periode_tekst, get_maatregelen_tekst
)

MAANDEN = [
    "", "januari", "februari", "maart", "april", "mei", "juni",
    "juli", "augustus", "september", "oktober", "november", "december"
]


# ── Hulpfuncties ─────────────────────────────────────────────────────────────

def _fmt_date(s: Optional[str]) -> Optional[str]:
    if not s:
        return None
    try:
        dt = datetime.fromisoformat(str(s).split("T")[0])
        return f"{dt.day} {MAANDEN[dt.month]} {dt.year}"
    except Exception:
        return str(s).split("T")[0]


# ── Score mapping ─────────────────────────────────────────────────────────────

_SCORE_TEKST: dict[int, dict] = {
    1: {
        "label": "Goed",
        "blok": (
            "Uw woning heeft een sterke basis: de weg naar gasloos wonen ligt open.\n\n"
            "Gefeliciteerd, uit de scan blijkt dat uw woning beschikt over een goede isolatieschil. "
            "Uw woning verliest relatief weinig warmte, wat zorgt voor een stabiel binnenklimaat "
            "en lagere energielasten.\n\n"
            "Waarom nu optimaliseren naar de Standaard?\n"
            "- Klaar voor gasloos: wanneer uw woning aan de Standaard voldoet, is deze officieel "
            "geschikt voor een volledige elektrische warmtepomp zonder ingrijpende aanpassingen.\n"
            "- Maximaal rendement: kleine upgrades zoals WTW-ventilatie of kierdichting halen "
            "het maximale rendement uit uw duurzame installaties.\n"
            "- Toekomstbestendige waarde: woningen die de stap van goed naar uitmuntend maken "
            "zijn het best voorbereid op veranderende wetgeving en stijgen in vastgoedwaarde.\n\n"
            "Overstappen naar gasloos met PandIQ: omdat uw woning al voldoende geïsoleerd is, "
            "kunt u nu serieus kijken naar gasloos wonen. Via de ISDE ontvangt u in 2026 een "
            "startbedrag van EUR 1.025 plus EUR 225 per kW vermogen. Voor toestellen met A+++ "
            "energielabel geldt een extra bonus van EUR 200.\n\n"
            "PandIQ helpt u bij de definitieve sprong naar een duurzame installatie: volledige "
            "subsidiecheck, aanvraagafhandeling en overzicht in uw persoonlijk dashboard."
        ),
    },
    2: {
        "label": "Redelijk",
        "blok": (
            "Een goede basis, maar bent u klaar voor de toekomst?\n\n"
            "Uw woning beschikt over een redelijke mate van isolatie. Hoewel u waarschijnlijk al "
            "dubbel glas in de hoofdruimtes heeft en een basislaag isolatie, voldoet uw woning "
            "nog niet aan de huidige Standaard voor woningisolatie.\n\n"
            "Waarom nu een upgrade overwegen?\n"
            "- Warmtepomp-klaar: door uw isolatieniveau te verhogen naar Rc 3,5-4,5 verlaagt u "
            "de warmtevraag zodanig dat een gasvrije toekomst haalbaar wordt.\n"
            "- Comfort: glas ouder dan 10-15 jaar verliest zijn isolerende werking. "
            "Vervanging door HR++ elimineert koudeval en verhoogt het binnencomfort.\n"
            "- Efficientie: hoe beter de schil, hoe lager de aanvoertemperatuur van uw "
            "verwarmingssysteem -- dit bespaart direct op uw energierekening.\n\n"
            "PandIQ voert een nauwkeurige scan uit om te bepalen waar bij-isoleren het meest "
            "rendabel is. Via uw persoonlijk dashboard vraagt u eenvoudig offertes aan die "
            "voldoen aan de ISDE-subsidie-eisen."
        ),
    },
    3: {
        "label": "Matig",
        "blok": (
            "Er is duidelijk verbeterpotentieel. Een investering verdient zich naar verwachting "
            "terug en verhoogt direct het wooncomfort.\n\n"
            "- Volgens de Trias Energetica is de eerste stap: beperk de energievraag door betere "
            "isolatie. Dit is de meest kosteneffectieve aanpak.\n"
            "- De eerste centimeters isolatie leveren financieel het meeste op: spouwmuur "
            "na-isoleren heeft een gemiddelde terugverdientijd van slechts 4 jaar.\n"
            "- Betere isolatie verhoogt uw energielabel en daarmee de verkoopwaarde van uw woning.\n\n"
            "Plan een inspectie en vraag een offerte aan via PandIQ. Wij voeren de subsidiecheck "
            "uit en verzorgen de volledige aanvraag."
        ),
    },
    4: {
        "label": "Slecht",
        "blok": (
            "Uw woning is op dit onderdeel slecht geïsoleerd. "
            "Warmte ontsnapt ongehinderd naar buiten -- u stookt letterlijk voor de mussen.\n\n"
            "Waarom nu investeren?\n"
            "- Direct comfort: koude binnenwanden verdwijnen. De thermostaat kan lager, "
            "het binnenklimaat wordt stabieler en aangenamer.\n"
            "- Forse kostenbesparing: een spouwmuur na-isoleren heeft een terugverdientijd "
            "van gemiddeld slechts 4 jaar.\n"
            "- Waardevermeerdering: betere isolatie verlaagt de warmtevraag, verbetert "
            "uw energielabel en verhoogt de verkoopwaarde.\n\n"
            "PandIQ ondersteunt u volledig: van technische inspectie tot subsidieaanvraag (ISDE). "
            "Alle stappen komen samen in uw persoonlijk dashboard."
        ),
    },
    5: {
        "label": "Zeer slecht",
        "blok": (
            "Uw woning als energielek: de noodzaak voor een warme jas.\n\n"
            "Dit onderdeel is zeer slecht of geheel niet geïsoleerd. Uw woning verliest "
            "momenteel massaal warmte, met grote gevolgen:\n"
            "- Extreem energieverlies: een ongeïsoleerde muur verbruikt circa 13,4 m3 gas per "
            "m2 per jaar, een goed geïsoleerde muur slechts 1,5 m3.\n"
            "- Onbehaaglijk leefklimaat: koude binnenwanden zijn niet op te lossen door "
            "de thermostaat hoger te zetten.\n"
            "- Risico op vocht en schimmel: condensatie op koude muren leidt tot ongezonde "
            "schimmelvorming die de constructie aantast.\n\n"
            "PandIQ ontzorgt u volledig: van inspectie tot uitvoering en subsidieaanvraag (ISDE). "
            "Wij zorgen dat u geen subsidie misloopt. Met PandIQ wordt uw woning weer "
            "comfortabel en betaalbaar."
        ),
    },
}


def score_to_text(score: int | None) -> str:
    """Vertaalt een score (1-5) naar begrijpelijke tekst. 1=goed, 5=slecht."""
    if score is None:
        return "Onvoldoende data beschikbaar voor beoordeling."
    s = _SCORE_TEKST.get(int(score))
    if not s:
        return "Score niet herkend."
    return s["blok"]


def score_label(score: int | None) -> str:
    """Geeft alleen het label terug: Goed / Redelijk / Matig / Slecht / Zeer slecht."""
    if score is None:
        return "-"
    s = _SCORE_TEKST.get(int(score))
    return s["label"] if s else "-"


# ── Gebouwprofiel ─────────────────────────────────────────────────────────────

def _bouw_gebouwprofiel(
    adres: str,
    bouwjaar: int | None,
    label: str | None,
    gebouwtype: str | None,
    geldig_tot: str | None,
) -> str:
    delen = [
        f"Dit rapport is opgesteld op basis van openbare registraties (BAG en EP-Online) voor {adres}."
    ]

    if gebouwtype:
        delen.append(f"Het betreft een {gebouwtype.lower()}.")

    if bouwjaar:
        delen.append(f"De woning is gebouwd in {bouwjaar}.")

    if label:
        lbl = label.upper()
        geldig = f", geldig tot {geldig_tot}" if geldig_tot else ""
        delen.append(f"Het geregistreerde energielabel is {lbl}{geldig}.")

    return " ".join(delen)


# ── Energieprestatie ──────────────────────────────────────────────────────────

def _bouw_energieprestatie(
    energie: float | None,
    warmte: float | None,
    label: str | None,
) -> str:
    if energie is None and warmte is None:
        return (
            "Er zijn geen EP-Online kengetallen beschikbaar voor deze woning. "
            "De energieprestatie kan daardoor niet automatisch worden geduid. "
            "Een maatwerkadvies geeft hier meer inzicht."
        )

    delen = []

    if energie is not None:
        delen.append(f"De geregistreerde energiebehoefte bedraagt {energie:.0f} kWh per m² per jaar.")
    if warmte is not None:
        delen.append(f"De warmtebehoefte is {warmte:.0f} kWh per m² per jaar.")

    # Duiding op basis van warmtebehoefte
    if warmte is not None:
        if warmte < 50:
            delen.append(
                "Dit is een zeer lage warmtevraag. De gebouwschil presteert uitstekend. "
                "Verdere winst zit vooral in installaties en gebruiksgedrag."
            )
        elif warmte < 80:
            delen.append(
                "Dit wijst op een efficiënte gebouwschil. Grote isolatiemaatregelen zijn "
                "waarschijnlijk niet de eerste prioriteit; optimalisatie van installaties is effectiever."
            )
        elif warmte < 120:
            delen.append(
                "De warmtevraag ligt in de middenrange. Gerichte verbeteringen aan glas, "
                "kierdichting of dakisolatie zijn vaak kosteneffectief."
            )
        elif warmte < 160:
            delen.append(
                "De warmtevraag is relatief hoog. Isolatie van de schil, met name dak, "
                "gevel en vloer, levert hier de grootste besparing."
            )
        else:
            delen.append(
                "De warmtevraag is hoog. Dit wijst op een slecht geïsoleerde schil. "
                "Aanpak van de isolatie is urgent voor zowel comfort als kostenbesparing."
            )

    # Labelduiding als extra context
    if label:
        lbl = label.upper()
        if lbl in ("F", "G"):
            delen.append(
                f"Energielabel {lbl} bevestigt dat er sprake is van een lage energieprestatie. "
                "Bij verkoop of verhuur gelden hiervoor aanvullende verplichtingen."
            )
        elif lbl in ("A+", "A++", "A+++", "A++++"):
            delen.append(
                f"Energielabel {lbl} bevestigt de goede prestatie van deze woning."
            )

    return " ".join(delen)


# ── Aanpak ────────────────────────────────────────────────────────────────────

def _bouw_aanpak(
    bouwjaar: int | None,
    scores: dict[str, int],
    warmte: float | None,
) -> str:
    from teksten_bouwperiodes import get_maatregelen, get_actie, get_focus
    focus = get_focus(bouwjaar) if bouwjaar else "schil"
    actie = get_actie(bouwjaar) if bouwjaar else ""
    maatregelen = get_maatregelen(bouwjaar) if bouwjaar else []

    delen = []

    if focus == "optimalisatie":
        delen.append(
            "Voor deze woning is de gebouwschil al op orde. De aanpak richt zich op "
            "optimalisatie van installaties, gebruiksgedrag en eventuele duurzame opwek."
        )
    elif focus == "installaties":
        delen.append(
            "De schil van deze woning is redelijk goed. De meeste winst zit in "
            "installaties: ventilatie, verwarming en warm tapwater."
        )
    else:
        delen.append(
            "Voor deze woning liggen de meeste verbeterkansen in de gebouwschil: "
            "dak, gevel, vloer en ramen. De geprioriteerde maatregelen met financiële "
            "indicaties vindt u in het overzicht van aanbevolen maatregelen."
        )

    if actie:
        delen.append(actie)

    delen.append(
        "De bovenstaande aanbevelingen zijn indicatief op basis van registratiedata. "
        "Maatwerkadvies door erkende bedrijven is altijd aan te raden."
    )

    return "\n\n".join(delen)


# ── Actiegerichte aandachtspunten ─────────────────────────────────────────────

def generate_actionable_advice(
    bouwjaar: int | None,
    gebouwtype: str | None,
    scores: dict[str, int],
    warmte: float | None,
) -> str:
    """
    Genereert concrete aandachtspunten.
    Onderdelen met dezelfde score worden gegroepeerd - geen herhaling.
    """
    delen: list[str] = []

    # Periodegerelateerde risico's
    if bouwjaar:
        risicos = get_risicos_tekst(bouwjaar)
        if risicos:
            delen.append(risicos)

    # Bouwfysisch risico bij na-isoleren: van toepassing zodra er al isolatie aanwezig is
    # (score ≤ 3 wijst op bestaande isolatie die aangevuld zou worden)
    heeft_bestaande_isolatie = any(
        v is not None and v <= 3 for v in scores.values()
    )
    if heeft_bestaande_isolatie:
        delen.append(
            "Bouwfysisch risico bij na-isoleren: als uw woning al (gedeeltelijk) geïsoleerd is, "
            "brengt aanvullende isolatie bouwfysische risico's met zich mee. "
            "Een verstoorde dampdiffusie of onvoldoende ventilatie kan leiden tot vocht, "
            "condensatie en schimmelvorming in de constructie, schade die niet altijd direct "
            "zichtbaar is maar de constructie ernstig kan aantasten. "
            "Laat een erkend bedrijf of bouwfysisch adviseur daarom altijd eerst een technisch "
            "onderzoek uitvoeren voordat u overgaat tot na-isoleren."
        )

    if warmte and warmte > 150:
        delen.append(
            "Hoge warmtevraag: overweeg een warmtescan om de grootste warmtelekken "
            "visueel in beeld te brengen voor u start met investeren."
        )

    delen.append(
        "Laat de bevindingen bevestigen via een foto-inspectie of maatwerkadvies. "
        "Neem contact op met PandIQ voor een concrete vervolgstap: www.pandiq.nl"
    )

    return "\n\n".join(delen) if delen else "Geen specifieke aandachtspunten op basis van beschikbare data."

def generate_subsidy_block(
    bouwjaar: int | None,
    scores: dict[str, int],
    gebouwtype: str | None,
) -> str:
    """Subsidieblok: periode-specifieke tekst + toelichting + CTA."""
    from teksten_bouwperiodes import get_subsidies_periode, SUBSIDIE_NUANCES
    blok: list[str] = []

    # 1. Periode-specifieke subsidieteksten
    if bouwjaar:
        regels = get_subsidies_periode(bouwjaar)
        if regels:
            blok.append("\n".join(f"- {r}" for r in regels))

    # 2. Algemene subsidienuances
    nuances = "\n".join(f"- {n}" for n in SUBSIDIE_NUANCES)
    blok.append("Let op bij subsidieaanvragen:\n" + nuances)

    # 3. CTA
    blok.append("Bereken uw subsidie op maat: www.pandiq.nl/subsidie")

    return "\n\n".join(blok)


def generate_vervolgstappen(
    bouwjaar: int | None,
    scores: dict[str, int],
    label: str | None,
) -> str:
    """
    Conversiegerichte vervolgstappen afgestemd op woningsituatie.
    """
    focus = get_focus(bouwjaar) if bouwjaar else "schil"
    hoge_prio = [k for k, v in scores.items() if v is not None and v >= 4]

    stappen: list[str] = []

    # Stap 1: subsidiecheck altijd eerste
    stappen.append(
        "1. Bereken uw subsidie. Gebruik de PandIQ subsidietool (www.pandiq.nl/subsidie) "
        "om binnen 2 minuten te zien welke subsidies voor u gelden en wat uw netto investering is."
    )

    # Stap 2: foto-upload voor maatwerk
    stappen.append(
        "2. Upload foto's. Stuur foto's van dak, gevel, glas, kruipruimte en installaties "
        "zodat wij uw rapport kunnen omzetten naar een concreet maatwerkadvies."
    )

    # Stap 3: afhankelijk van focus
    if hoge_prio:
        namen = {"dak": "dakisolatie", "gevel": "gevelisolatie", "vloer": "vloerisolatie", "glas": "glasvervanging"}
        maatregelen = " en ".join(namen.get(k, k) for k in hoge_prio)
        stappen.append(
            f"3. Vraag een offerte aan. Op basis van dit rapport is {maatregelen} "
            "de meest kansrijke maatregel. Vraag een vrijblijvende offerte aan via PandIQ."
        )
    elif focus == "installaties":
        stappen.append(
            "3. Plan een installatiecheck. Laat uw ventilatiesysteem en verwarmingsinstallatie "
            "controleren. Dit is voor uw woning de meest effectieve eerste stap."
        )
    else:
        stappen.append(
            "3. Plan een adviesgesprek. Onze adviseurs helpen u de juiste volgorde te bepalen "
            "en de investering te optimaliseren. Gratis en vrijblijvend via www.pandiq.nl."
        )

    return "\n".join(stappen)


# ── Hoofdfunctie ──────────────────────────────────────────────────────────────

def narrative_from_facts(facts: dict[str, Any]) -> dict[str, str]:
    adres      = facts.get("adres") or "het opgegeven adres"
    bouwjaar   = facts.get("bouwjaar")
    label      = (facts.get("labelklasse") or "").upper() or None
    gebouwtype = facts.get("gebouwtype")
    warmte     = facts.get("warmtebehoefte")
    energie    = facts.get("energiebehoefte")
    geldig_tot = _fmt_date(facts.get("geldig_tot"))

    scores = {
        "dak":   facts.get("score_dak"),
        "gevel": facts.get("score_gevel"),
        "vloer": facts.get("score_vloer"),
        "glas":  facts.get("score_glas"),
    }

    from subsidies_isolatie_glas import genereer_subsidietekst
    from teksten_elementen import get_element_tekst

    return {
        # Bestaande placeholders
        "gebouw": _bouw_gebouwprofiel(adres, bouwjaar, label, gebouwtype, geldig_tot),
        "energie": _bouw_energieprestatie(energie, warmte, label),
        "aanpak":  _bouw_aanpak(bouwjaar, scores, warmte),

        # Nieuwe dynamische placeholders
        "bouwperiode_inleiding": bouw_bouwperiode_tekst(bouwjaar, label, gebouwtype) if bouwjaar else "",
        "risicos":               generate_actionable_advice(bouwjaar, gebouwtype, scores, warmte),
        "subsidies_blok":        generate_subsidy_block(bouwjaar, scores, gebouwtype),
        "subsidies_isolatie":    genereer_subsidietekst(bouwjaar) if bouwjaar else "",
        "vervolgstappen_blok":   generate_vervolgstappen(bouwjaar, scores, label),

        # Score labels voor in tabel
        "score_dak_tekst":   score_label(scores.get("dak")),
        "score_gevel_tekst": score_label(scores.get("gevel")),
        "score_vloer_tekst": score_label(scores.get("vloer")),
        "score_glas_tekst":  score_label(scores.get("glas")),

        # Element-specifieke uitleg bij kansen & verbeterpotentieel
        "element_tekst_dak":   get_element_tekst("dak",   scores.get("dak")),
        "element_tekst_gevel": get_element_tekst("gevel", scores.get("gevel")),
        "element_tekst_vloer": get_element_tekst("vloer", scores.get("vloer")),
        "element_tekst_glas":  get_element_tekst("glas",  scores.get("glas")),
    }
