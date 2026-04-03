"""
teksten_bouwperiodes.py
=======================
Dynamische teksten per bouwperiode, gekoppeld aan energielabel en woningtype.
Aanpassen? Wijzig de teksten hieronder — de code kiest automatisch de juiste combinatie.
"""
from __future__ import annotations

PERIODES: list[dict] = [
    {
        "tot_en_met": 1945,
        "label": "vóór 1945",
        "naam": "Traditionele bouw",
        "focus": "schil",
        "inleiding_base": (
            "Uw woning stamt uit een periode waarin energieverbruik nog geen rol speelde bij het ontwerp. "
            "Typisch voor deze bouw zijn massieve muren of vroege spouwmuren zonder isolatie, houten "
            "vloerbalken en oorspronkelijk enkel glas. Energetisch gezien behoren woningen uit deze "
            "periode tot de meest energie-intensieve van Nederland — maar daarmee ook tot de categorie "
            "met de grootste besparingspotentie."
        ),
        "maatregelen": [
            "De Warme Jas: vanwege het ontbreken van een spouw adviseren wij hoogwaardige binnenmuurisolatie "
            "met vochtregulerende materialen zoals houtvezelplaten.",
            "Hoogwaardig glas: vervang enkel glas door HR++ of vacuumglas om koudeval te elimineren.",
            "Dak- en vloercomfort: isoleer het dak aan de binnenzijde en gebruik schuimglas-granulaat "
            "in de kruipruimte om optrekkende kou te stoppen.",
        ],
        "risicos": [
            "Vocht en houtrot: isoleren aan de binnenzijde kan condensatie veroorzaken bij houten "
            "vloerbalken in de muren. Laat dit altijd eerst beoordelen door een specialist.",
            "Koudebruggen zoals stenen dorpels en stalen balken boven ramen blijven na isolatie extra koud "
            "en vormen een verhoogd risico op schimmelvorming.",
            "Binnenklimaat: het dichten van kieren zonder nieuw ventilatiesysteem maakt de lucht snel "
            "vochtig en ongezond. Het is daarom belangrijk dat luchtdichting en gecontroleerde ventilatie "
            "(zoals een decentrale WTW) op orde is om houtrot en schimmel te voorkomen.",
        ],
        "subsidies_periode": [
            "Gevelisolatie (2025): € 20,25 per m² (bonus biobased: + € 6,00 per m²).",
            "Glas-upgrade (2025): € 25,00 per m².",
            "Warmtepomp via ISDE (2026): startbedrag € 1.025 + € 225 per kW vermogen. "
            "Extra bonus van € 200 voor toestellen met A+++ energielabel.",
        ],
        "actie": "Laat een schil-scan uitvoeren om te bepalen welke isolatiemaatregel het meest rendabel is.",
    },
    {
        "tot_en_met": 1974,
        "label": "1946-1974",
        "naam": "Wederopbouw en eerste isolatienormen",
        "focus": "schil",
        "inleiding_base": (
            "Uw woning is gebouwd in de wederopbouw- of vroege isolatieperiode. "
            "De spouwmuur werd in deze jaren de standaard om vochtproblemen te voorkomen, "
            "maar werd zonder isolatiemateriaal opgeleverd. De meeste woningen uit deze periode "
            "hebben een loze spouw, een ongeïsoleerde of dunne vloer en beperkte dakisolatie."
        ),
        "maatregelen": [
            "Spouwmuur-upgrade: het laten inblazen van een schone spouw met minerale wol of EPS-parels "
            "is een zeer rendabele stap met een terugverdientijd van circa 4 jaar.",
            "Vloerisolatie: verbeter de oorspronkelijk lage Rc-waarde van de vloer naar de moderne "
            "standaard van 3,5 m²K/W.",
        ],
        "risicos": [
            "Spouwvervuiling: bouwafval of cementspecie in de spouw vormt een vochtbrug van buiten- naar "
            "binnenmuur. Controleer de spouw vooraf met een endoscoop op vervuiling om vochtbruggen "
            "na isolatie te voorkomen.",
            "Verouderd dubbelglas: veel originele ramen zijn vervangen door glas uit de jaren 80-90 "
            "dat inmiddels zijn isolatiewaarde heeft verloren en nauwelijks beter presteert dan enkel glas.",
            "Thermische lekken bij balkons: betonvloeren liepen in deze periode vaak rechtstreeks "
            "van binnen naar buiten door, wat grote koudebruggen oplevert met condens en schimmel.",
        ],
        "subsidies_periode": [
            "Spouwisolatie (2025): € 5,25 per m².",
            "Vloerisolatie (2025): € 5,50 per m².",
            "Warmtepomp via ISDE (2026): startbedrag € 1.025 + € 225 per kW vermogen. "
            "Extra bonus van € 200 voor toestellen met A+++ energielabel.",
        ],
        "actie": (
            "Prioriteer spouwisolatie en vloerisolatie — dit levert bij deze bouwperiode doorgaans "
            "de hoogste besparing per geïnvesteerde euro, met een korte terugverdientijd."
        ),
    },
    {
        "tot_en_met": 1991,
        "label": "1975-1991",
        "naam": "Reactie op de oliecrisis",
        "focus": "schil",
        "inleiding_base": (
            "Uw woning is gebouwd na de oliecrisis van 1973, toen isolatie voor het eerst serieus "
            "werd aangepakt. Dak, gevel en vloer zijn bij oplevering geïsoleerd, en vanaf 1979 werd "
            "dubbel glas standaard. De woning is daarmee comfortabeler dan oudere woningen, maar voldoet "
            "nog niet aan de huidige eisen voor een goed geïsoleerde schil."
        ),
        "maatregelen": [
            "Na-isolatie: upgrade de bestaande dunne isolatielagen in het dak en de spouw naar "
            "de huidige standaard.",
            "Glasverbetering: vervang verouderd dubbel glas (ouder dan 10-15 jaar) door HR++ glas "
            "voor aanzienlijk minder warmteverlies.",
        ],
        "risicos": [
            "Verzakte isolatie: de isolatiematerialen uit deze periode kunnen zijn ingezakt of deels "
            "hun werking verloren hebben — met name in de spouw en kruipruimte. Koude plekken en "
            "schimmel op muren kunnen hiervan het gevolg zijn.",
            "Ventilatieprobleem: woningen werden dichter gebouwd maar ventilatie bleef simpel. "
            "Bij onvoldoende ventilatie ontstaat vochtstapeling en een verslechterd binnenklimaat.",
        ],
        "subsidies_periode": [
            "Warmtepomp-gereed: deze woningen zijn na schilverbetering vaak direct geschikt voor "
            "een (hybride) warmtepomp.",
            "Warmtepomp via ISDE (2026): startbedrag € 1.025 + € 225 per kW vermogen. "
            "Extra bonus van € 200 voor toestellen met A+++ energielabel.",
        ],
        "actie": (
            "Controleer of de bestaande isolatie nog op dikte en kwaliteit is. "
            "Kierdichting en glasvervanging leveren bij deze bouwperiode vaak nog goede resultaten."
        ),
    },
    {
        "tot_en_met": 2014,
        "label": "1992-2014",
        "naam": "Moderne regelgeving",
        "focus": "installaties",
        "inleiding_base": (
            "Uw woning valt onder het Bouwbesluit van 1992, met latere aanscherpingen via de "
            "Energieprestatiecoëfficiënt (EPC). De schil is standaard voorzien van dakisolatie, "
            "spouwvulling en mechanische ventilatie — een kwalitatief goede basis met Rc 2,5. "
            "Het verbeterpotentieel zit bij deze woningen primair in installatie-optimalisatie: "
            "denk aan zonnepanelen, batterijopslag en een warmtepomp."
        ),
        "maatregelen": [
            "Zonnepanelen (PV): de meeste daken kunnen goed gebruikt worden voor plaatsing van "
            "PV-panelen, één paneel kan wel 300-400 kWh per jaar opleveren.",
            "Batterij-opslag: terugleveren van stroom aan het net wordt steeds duurder, waardoor "
            "opslag van energie steeds belangrijker wordt.",
        ],
        "risicos": [
            "Vervuilde of verkeerd ingestelde ventilatie: de mechanische afzuiging is vaak niet "
            "onderhouden. Dit kost energie en verslechtert de luchtkwaliteit merkbaar.",
            "Sluipverbruik: sluipverbruik van apparatuur en inefficiënte instellingen van "
            "ventilatiesystemen zijn de grootste verliesposten — onzichtbaar maar structureel "
            "aanwezig op de energierekening.",
        ],
        "subsidies_periode": [
            "LTV-check: doe de 50-graden test om te zien of uw afgiftesysteem klaar is voor "
            "een warmtepomp.",
            "Warmtepomp via ISDE (2026): startbedrag € 1.025 + € 225 per kW vermogen. "
            "Extra bonus van € 200 voor toestellen met A+++ energielabel.",
        ],
        "actie": (
            "Laat de ventilatie controleren en overweeg een warmtepomp of hybride systeem — "
            "de schil is al op orde, de installatie is de volgende logische stap."
        ),
    },
    {
        "tot_en_met": 9999,
        "label": "vanaf 2015",
        "naam": "Hoogwaardige bouw",
        "focus": "optimalisatie",
        "inleiding_base": (
            "Uw woning behoort tot de nieuwste generatie en voldoet aan strenge energienormen. "
            "De schil is zeer goed geïsoleerd met Rc-waarden van 4,5 tot 6,0, de woning is "
            "luchtdicht en voorzien van balansventilatie met warmteterugwinning (WTW). "
            "Veel woningen uit deze periode zijn al gasloos opgeleverd."
        ),
        "maatregelen": [
            "Monitoring: gebruik slimme meters en apps om het energiegebruik per uur te volgen "
            "en verbruikspieken te identificeren.",
            "Passieve koeling: voorkom oververhitting in de zomer door de inzet van buitenzonwering.",
        ],
        "risicos": [
            "Oververhitting in de zomer: de uitstekende isolatie houdt warmte ook binnen — "
            "zonder zonwering of nachtventilatie kan dit leiden tot oncomfortabele temperaturen.",
            "Gebruikersfouten: de complexiteit van de installaties vraagt om deskundig onderhoud "
            "om het rendement te behouden. Het uitzetten van ventilatie of verkeerd instellen van "
            "de warmtepomp heeft direct effect op comfort en energierekening.",
        ],
        "subsidies_periode": [
            "Warmtepomp via ISDE (2026): startbedrag € 1.025 + € 225 per kW vermogen. "
            "Extra bonus van € 200 voor toestellen met A+++ energielabel.",
            "Zelfs bij nieuwbouw kan PandIQ u helpen bij het optimaliseren van uw energieprestaties "
            "en het checken van resterende subsidies.",
        ],
        "actie": (
            "Focus op gebruiksoptimalisatie en overweeg zonnepanelen of een thuisbatterij "
            "als logische en rendabele vervolgstap."
        ),
    },
]

_LABEL_DUIDING: dict[str, str] = {
    "A++++": "een uitzonderlijk efficiënte woning",
    "A+++":  "een zeer energiezuinige woning",
    "A++":   "een energiezuinige woning",
    "A+":    "een energiezuinige woning",
    "A":     "een goed presterende woning",
    "B":     "een redelijk efficiënte woning met verbeterpotentieel",
    "C":     "een gemiddeld presterende woning met duidelijk verbeterpotentieel",
    "D":     "een woning met een matige energieprestatie",
    "E":     "een woning met een slechte energieprestatie",
    "F":     "een woning met een zeer slechte energieprestatie",
    "G":     "een woning met de laagst mogelijke energieprestatie",
}

_LABEL_FOCUS: dict[str, str] = {
    "A++++": "Het verbeterpotentieel is minimaal; focus op beheer en comfort.",
    "A+++":  "Het verbeterpotentieel is minimaal; focus op beheer en comfort.",
    "A++":   "Het verbeterpotentieel is minimaal; focus op beheer en comfort.",
    "A+":    "",
    "A":     "",
    "B":     "Kierdichting en glasverbetering zijn kosteneffectieve vervolgstappen.",
    "C":     "Er zijn concrete kansen op het gebied van isolatie en installaties.",
    "D":     "Isolatie van de schil (dak, gevel, vloer) levert hier de grootste besparing.",
    "E":     "Een grondige aanpak van de gebouwschil is dringend aan te raden.",
    "F":     "Urgente verbetering van de isolatieschil is noodzakelijk voor comfort en besparing.",
    "G":     "Volledige schilrenovatie is het vertrekpunt — dit is een prioritaire aanpak.",
}

_TYPE_CONTEXT: dict[str, str] = {
    "vrijstaand":         "Als vrijstaande woning heeft u aan alle zijden warmteverlies — dak, gevel en vloer zijn alle vier relevant.",
    "twee-onder-een-kap": "Bij een twee-onder-een-kapwoning heeft u drie buitengevels; de gedeelde muur isoleert al van nature.",
    "tussenwoning":       "Als tussenwoning heeft u twee gedeelde muren — warmteverlies gaat hier vooral via dak, vloer en voor/achtergevel.",
    "rijwoning tussen":   "Als tussenwoning heeft u twee gedeelde muren — warmteverlies gaat hier vooral via dak, vloer en voor/achtergevel.",
    "hoekwoning":         "Als hoekwoning heeft u drie buitengevels en daarmee meer warmteverlies dan een tussenwoning.",
    "rijwoning hoek":     "Als hoekwoning heeft u drie buitengevels en daarmee meer warmteverlies dan een tussenwoning.",
    "appartement":        "Bij een appartement is uw eigen schil beperkt — vloer, plafond en buitengevel(s) zijn het meest relevant.",
}


def get_periode(bouwjaar: int) -> dict:
    for p in PERIODES:
        if bouwjaar <= p["tot_en_met"]:
            return p
    return PERIODES[-1]

def get_inleiding(bouwjaar: int) -> str:
    return get_periode(bouwjaar)["inleiding_base"]

def get_maatregelen(bouwjaar: int) -> list[str]:
    return get_periode(bouwjaar).get("maatregelen", [])

def get_maatregelen_tekst(bouwjaar: int) -> str:
    return "\n".join(f"- {m}" for m in get_maatregelen(bouwjaar))

def get_risicos(bouwjaar: int) -> list[str]:
    return get_periode(bouwjaar)["risicos"]

def get_risicos_tekst(bouwjaar: int) -> str:
    return "\n".join(f"- {r}" for r in get_risicos(bouwjaar))

def get_subsidies_periode(bouwjaar: int) -> list[str]:
    return get_periode(bouwjaar).get("subsidies_periode", [])

def get_subsidies_periode_tekst(bouwjaar: int) -> str:
    return "\n".join(f"- {s}" for s in get_subsidies_periode(bouwjaar))

def get_label(bouwjaar: int) -> str:
    p = get_periode(bouwjaar)
    return f"{p['label']} - {p['naam']}"

def get_focus(bouwjaar: int) -> str:
    return get_periode(bouwjaar)["focus"]

def get_actie(bouwjaar: int) -> str:
    return get_periode(bouwjaar)["actie"]

def bouw_bouwperiode_tekst(bouwjaar: int, label: str | None, gebouwtype: str | None) -> str:
    """
    Centrale functie: vult {{narrative_bouwperiode}} met gepersonaliseerde tekst.
    Opbouw:
      1. Inleiding bouwperiode
      2. Energielabel duiding
      3. Woningtype context
      4. Verduurzamingsmaatregelen
      5. Actieadvies
    """
    periode = get_periode(bouwjaar)

    # Inleiding + label-duiding: direct aansluitend, geen lege alinea ertussen
    inleiding = periode["inleiding_base"]
    if label:
        lbl = label.upper().strip()
        duiding = _LABEL_DUIDING.get(lbl, "een woning waarvan de energieprestatie is geregistreerd")
        focus   = _LABEL_FOCUS.get(lbl, "")
        label_tekst = f"Met energielabel {lbl} betreft het {duiding}."
        if focus:
            label_tekst += f" {focus}"
        inleiding = inleiding + "\n" + label_tekst

    delen = [inleiding]

    if gebouwtype:
        gt_lower = gebouwtype.lower()
        for sleutel, context in _TYPE_CONTEXT.items():
            if sleutel in gt_lower:
                delen.append(context)
                break

    # Verduurzamingsmaatregelen als eigen alinea
    maatregelen = get_maatregelen(bouwjaar)
    if maatregelen:
        maatregel_tekst = "Aanbevolen verduurzamingsmaatregelen voor deze bouwperiode:\n" + \
                          "\n".join(f"- {m}" for m in maatregelen)
        delen.append(maatregel_tekst)

    return "\n\n".join(delen)
