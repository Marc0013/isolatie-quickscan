"""
teksten_bouwperiodes.py
=======================
Dynamische teksten per bouwperiode, gekoppeld aan energielabel en woningtype.

HOE TEKSTEN AANPASSEN?
  Zoek de gewenste bouwperiode hieronder op (zoek op 'label').
  Elke periode heeft vier tekstvelden:
    - inleiding_base   : intro-alinea bovenaan het rapport
    - maatregelen      : lijst met concrete aanpak-onderdelen
    - risicos          : lijst met aandachtspunten en risico's
    - subsidies_periode: subsidie-informatie specifiek voor deze periode
  Pas de tekst aan en sla op. De code gebruikt automatisch de juiste periode.
"""
from __future__ import annotations

PERIODES: list[dict] = [

    # ──────────────────────────────────────────────────────────────────────────
    # PERIODE 1 — vóór 1945 (Traditionele bouw)
    # ──────────────────────────────────────────────────────────────────────────
    {
        "tot_en_met": 1945,
        "label": "vóór 1945",
        "naam": "Traditionele bouw",
        "focus": "schil",
        "inleiding_base": (
            "Uw woning stamt uit een periode waarin energieverbruik nog geen rol speelde bij het "
            "ontwerp. Kenmerkend zijn de houten begane grondvloeren en gevels die tot circa 1930 "
            "massief (steens) werden uitgevoerd of daarna voorzien zijn van een zeer beperkte, "
            "ongeïsoleerde luchtspouw. Isolatie ontbrak oorspronkelijk volledig, waardoor woningen "
            "uit deze periode tot de meest energie-intensieve van Nederland behoren — maar ook tot "
            "de categorie met de grootste besparingspotentie."
        ),
        "maatregelen": [
            "Gevel: isoleer de binnenzijde of buitenzijde bij massieve muren, "
            "of na-isoleer de spouw indien deze aanwezig en schoon is.",
            "Dak: breng volledige isolatie aan, aangezien de oorspronkelijke waarde nagenoeg nul is.",
            "Vloer: isoleer de houten vloer of de bodem van de kruipruimte "
            "om optrekkend vocht en kou tegen te gaan.",
            "Ramen: vervang enkel glas door HR++ of vacuümglas.",
            "Ventilatie: breng gecontroleerde ventilatie aan (zoals decentrale WTW) "
            "om de verhoogde luchtvochtigheid na kierdichting te beheersen.",
        ],
        "risicos": [
            "Vocht en houtrot: deze woningen zijn vaak 'dampopen' gebouwd zonder spouw of met een "
            "zeer smalle spouw. Bij binnenisolatie daalt de temperatuur van de oorspronkelijke muur "
            "sterk, met condensatierisico als gevolg. Gebruik vochtregulerende folies (zoals Intello) "
            "en dampopen materialen zoals houtvezel of vlas — vermijd volledig dampdichte plastics.",
            "Balkkoppen: houten vloerbalken in de buitenmuur worden door binnenisolatie kouder en "
            "vochtiger. Dit leidt tot houtrot. Laat dit altijd vooraf beoordelen door een specialist.",
            "Dampdichte buitengevel: controleer of de gevel aan de buitenzijde niet dampdicht is "
            "(geglazuurde steen of latexverf), want dan kan vocht niet naar buiten uitdampen.",
            "Binnenklimaat: kieren dichten zonder nieuw ventilatiesysteem maakt de lucht snel vochtig "
            "en ongezond. Luchtdichting en gecontroleerde ventilatie moeten samen worden aangepakt.",
        ],
        "subsidies_periode": [
            "Woningen uit deze periode hebben vaak massieve muren of zeer vroege spouwen en houten "
            "vloeren. De focus ligt op het aanbrengen van een volledige isolatieschil.",
            "Gevelisolatie (2025): € 20,25 per m² (bonus biobased materiaal: + € 6,00 per m²).",
            "Glas-upgrade (2025): € 25,00 per m².",
            "Warmtepomp via ISDE (2026): startbedrag € 1.025 + € 225 per kW vermogen. "
            "Extra bonus van € 200 voor toestellen met A+++ energielabel.",
        ],
        "actie": (
            "Laat een schil-scan uitvoeren om te bepalen welke isolatiemaatregel "
            "het meest rendabel is voor uw specifieke situatie."
        ),
    },

    # ──────────────────────────────────────────────────────────────────────────
    # PERIODE 2 — 1946–1974 (Wederopbouw en vroege systeembouw)
    # ──────────────────────────────────────────────────────────────────────────
    {
        "tot_en_met": 1974,
        "label": "1946-1974",
        "naam": "Wederopbouw en vroege systeembouw",
        "focus": "schil",
        "inleiding_base": (
            "Uw woning is gebouwd in de wederopbouw- of vroege systeembouwperiode. Na de oorlog "
            "verschoof de focus naar industriële bouw om de woningnood snel op te lossen, waarbij "
            "betonvloeren steeds vaker houten vloeren vervingen. De spouwmuur werd de standaard om "
            "vochtproblemen te voorkomen, maar werd zonder isolatiemateriaal opgeleverd. De "
            "isolatiewaarden van gevels en daken bleven in deze periode zeer laag "
            "(Rc-waarden tussen 0,15 en 0,86)."
        ),
        "maatregelen": [
            "Spouwmuur: na-isoleer de lege spouw met inblaasmateriaal (minerale wol of EPS-parels). "
            "Dit is een zeer rendabele stap met een terugverdientijd van circa 4 jaar.",
            "Vloer: isoleer de ongeïsoleerde betonvloer (oorspronkelijk vaak slechts Rc 0,17) "
            "naar de huidige standaard van Rc 3,5 m²K/W.",
            "Dak: schaal de minimale dakisolatie op naar een hoogwaardig niveau.",
            "Glas: vervang enkel glas of oud dubbel glas door HR-beglazing.",
            "Verwarming: onderzoek of de woning na schilverbetering geschikt is "
            "voor een (hybride) warmtepomp.",
        ],
        "risicos": [
            # 1946–1964: spouwvervuiling
            "Spouwvervuiling (1946–1964): in de spouw bevindt zich vaak valspecie of puin. "
            "Bij na-isolatie fungeren deze resten als vochtbruggen naar de binnenmuur. "
            "Een endoscopisch onderzoek is essentieel: controleer of de spouw schoon is en "
            "minimaal 50 mm breed, en beoordeel de kwaliteit van de spouwankers.",
            "Kitwerk spouw: zorg dat naden tussen kozijnen en metselwerk aan de binnenzijde goed "
            "zijn afgekit met acrylaatkit (geen siliconen of PUR) om te voorkomen dat "
            "isolatiemateriaal de woning binnendringt.",
            # 1965–1974: koudebruggen
            "Koudebruggen (1965–1974): doorlopende betonvloeren of balkons fungeren als grote "
            "koudebruggen. Na spouwisolatie stijgt de muurtemperatuur, maar de koudebrug blijft "
            "koud. Als bewoners minder ventileren, concentreert schimmel zich op deze betonpunten. "
            "Spoor koudebruggen op met een thermische scan in de winter; let op roeststrepen boven "
            "ramen (stalen balken als koudebrug). Isoleer ernstige koudebruggen afzonderlijk "
            "met Aerogel-strips.",
            "Verouderd dubbelglas: veel originele ramen zijn vervangen door glas uit de jaren 80–90 "
            "dat inmiddels zijn isolatiewaarde heeft verloren en nauwelijks beter presteert "
            "dan enkel glas.",
        ],
        "subsidies_periode": [
            "In deze periode werd de spouwmuur de standaard, maar deze is vaak nog ongeïsoleerd. "
            "Ook de vloerisolatie is oorspronkelijk zeer beperkt (Rc ~0,17).",
            "Spouwisolatie (2025): € 5,25 per m².",
            "Vloerisolatie (2025): € 5,50 per m².",
            "Warmtepomp via ISDE (2026): startbedrag € 1.025 + € 225 per kW vermogen. "
            "Extra bonus van € 200 voor toestellen met A+++ energielabel.",
        ],
        "actie": (
            "Prioriteer spouwisolatie en vloerisolatie — dit levert bij deze bouwperiode "
            "doorgaans de hoogste besparing per geïnvesteerde euro, met een korte terugverdientijd."
        ),
    },

    # ──────────────────────────────────────────────────────────────────────────
    # PERIODE 3 — 1975–1991 (Eerste isolatienormen)
    # ──────────────────────────────────────────────────────────────────────────
    {
        "tot_en_met": 1991,
        "label": "1975-1991",
        "naam": "Eerste isolatienormen",
        "focus": "schil",
        "inleiding_base": (
            "Uw woning is gebouwd na de oliecrisis van 1973, toen isolatie voor het eerst serieus "
            "werd aangepakt. Vanaf 1975 golden landelijke eisen voor de isolatie van de gehele "
            "schil; in 1979 werd dubbel glas de norm voor woonvertrekken. De woning beschikt "
            "daarmee over een basisisolatie (Rc circa 1,3 tot 2,0), maar voldoet nog niet aan "
            "de huidige 'Standaard' voor aardgasvrij wonen."
        ),
        "maatregelen": [
            "Schil-upgrade: bij-isoleer dak, gevel en vloer om de thermische weerstand te verhogen "
            "naar Rc 3,5 of hoger.",
            "Beglazing: vervang verouderd dubbel glas (ouder dan 10–15 jaar) door "
            "hoogrendementsglas om koudeval te elimineren.",
            "Koudebruggen: pak specifieke thermische lekken aan, zoals doorlopende betonvloeren "
            "bij balkons, met materialen zoals Aerogel.",
            "Installaties: installeer een hybride warmtepomp als tussenstap naar gasloos wonen.",
        ],
        "risicos": [
            "Dubbele isolatie en dampremming: deze woningen hebben al een dunne laag isolatie. "
            "Het risico bij bij-isoleren aan de binnenzijde is dat vocht opgesloten raakt tussen "
            "de twee lagen. Breng dampremmende lagen altijd aan de warme binnenzijde aan.",
            "Verzakte isolatie: minerale wol uit deze periode kan zijn ingezakt of deels zijn "
            "werking verloren hebben — met name in de spouw en kruipruimte. Controleer op koude "
            "plekken en schimmel op muren.",
            "Verouderd dubbelglas: controleer het jaartal in de strip van het glas. Glas ouder dan "
            "15 jaar fungeert soms nog maar als enkel glas.",
            "Ventilatieprobleem: woningen werden dichter gebouwd maar de ventilatie bleef eenvoudig. "
            "Bij onvoldoende ventilatie ontstaat vochtstapeling en een verslechterd binnenklimaat.",
        ],
        "subsidies_periode": [
            "Deze woningen beschikken over matige basisisolatie (Rc 1,3 tot 2,0). "
            "De winst zit in het 'bij-isoleren' naar de moderne Standaard.",
            "Warmtepomp-gereed: na schilverbetering zijn deze woningen vaak direct geschikt "
            "voor een (hybride) warmtepomp.",
            "Warmtepomp via ISDE (2026): startbedrag € 1.025 + € 225 per kW vermogen. "
            "Extra bonus van € 200 voor toestellen met A+++ energielabel.",
        ],
        "actie": (
            "Controleer of de bestaande isolatie nog op dikte en kwaliteit is. "
            "Kierdichting en glasvervanging leveren bij deze bouwperiode vaak nog goede resultaten."
        ),
    },

    # ──────────────────────────────────────────────────────────────────────────
    # PERIODE 4 — 1992–2014 (Moderne regelgeving en EPC)
    # ──────────────────────────────────────────────────────────────────────────
    {
        "tot_en_met": 2014,
        "label": "1992-2014",
        "naam": "Moderne regelgeving en EPC",
        "focus": "installaties",
        "inleiding_base": (
            "Uw woning valt onder het Bouwbesluit van 1992, met latere aanscherpingen via de "
            "Energieprestatiecoëfficiënt (EPC). De schil is standaard voorzien van dakisolatie, "
            "spouwvulling en mechanische ventilatie — een kwalitatief goede basis met Rc 2,5. "
            "De focus verschuift hier van basisisolatie naar het optimaliseren van systemen "
            "en het dichten van de laatste energielekken."
        ),
        "maatregelen": [
            "Luchtdichtheid: verbeter de naad- en kierdichting om onnodig warmteverlies "
            "te voorkomen.",
            "Ventilatie: upgrade de mechanische afvoer (Type C) naar balansventilatie "
            "met WTW (Type D).",
            "Zonne-energie: benut het dakvlak maximaal voor PV-panelen of een zonneboiler.",
            "Warmte-afgifte: regel de installatie waterzijdig in om de woning klaar te maken "
            "voor een volledige warmtepomp.",
        ],
        "risicos": [
            "Slechte luchtkwaliteit: deze woningen zijn bij oplevering al redelijk luchtdicht. "
            "Het verder dichten van kieren zonder het ventilatiesysteem te upgraden leidt direct "
            "tot een ongezond binnenklimaat en verhoogde kans op schimmelgroei.",
            "Vervuilde ventilatie: de mechanische afzuiging is vaak niet onderhouden. "
            "Dit kost energie en verslechtert de luchtkwaliteit merkbaar.",
            "Oververhitting in de zomer: de goede isolatieschil houdt warmte ook binnen. "
            "Bij het vervangen van glas voor zonwerende beglazing houdt dit in de winter "
            "ook 'gratis' zonnewarmte tegen. Overweeg een CO2-indicator om de luchtkwaliteit "
            "na verduurzaming te monitoren.",
            "Sluipverbruik: inefficiënte instellingen van ventilatiesystemen zijn de grootste "
            "verliesposten — onzichtbaar maar structureel aanwezig op de energierekening.",
        ],
        "subsidies_periode": [
            "Woningen uit deze periode zijn al redelijk goed geïsoleerd (Rc ≥ 2,5). "
            "De focus verschuift naar installatietechniek en het dichten van de laatste kieren.",
            "LTV-check: doe de 50-graden test om te zien of uw afgiftesysteem klaar is "
            "voor een warmtepomp.",
            "Warmtepomp via ISDE (2026): startbedrag € 1.025 + € 225 per kW vermogen. "
            "Extra bonus van € 200 voor toestellen met A+++ energielabel.",
        ],
        "actie": (
            "Laat de ventilatie controleren en overweeg een warmtepomp of hybride systeem — "
            "de schil is al op orde, de installatie is de volgende logische stap."
        ),
    },

    # ──────────────────────────────────────────────────────────────────────────
    # PERIODE 5 — vanaf 2015 (Hoogwaardige bouw)
    # ──────────────────────────────────────────────────────────────────────────
    {
        "tot_en_met": 9999,
        "label": "vanaf 2015",
        "naam": "Hoogwaardige bouw",
        "focus": "optimalisatie",
        "inleiding_base": (
            "Uw woning behoort tot de nieuwste generatie en voldoet aan strenge energienormen "
            "(Rc dak 6,0 / gevel 4,5). De woning is luchtdicht en voorzien van balansventilatie "
            "met warmteterugwinning (WTW). Veel woningen uit deze periode zijn al gasloos "
            "opgeleverd. De uitdaging ligt nu in het beheer van de complexe installaties "
            "en het voorkomen van oververhitting in de zomer."
        ),
        "maatregelen": [
            "Monitoring: gebruik slimme systemen om het energiegebruik en de "
            "ventilatiebehoefte fijn te regelen.",
            "Koeling: pas passieve koelingsmaatregelen toe (buitenzonwering, groen dak) "
            "om zomerse hitte buiten te houden.",
            "Onderhoud: reinig ventilatiekanalen en zonnepanelen regelmatig "
            "om het rendement te waarborgen.",
            "Opslag: verken de mogelijkheden voor energieopslag (batterijen) "
            "in combinatie met eigen opwek.",
        ],
        "risicos": [
            "Oververhitting in de zomer: de uitstekende isolatie houdt warmte ook binnen. "
            "Zonder zonwering of nachtventilatie kan dit leiden tot oncomfortabele temperaturen.",
            "Slechte luchtkwaliteit door te weinig ventilatie: verder dichten zonder "
            "ventilatieupgrade leidt direct tot een ongezond binnenklimaat.",
            "Gebruikersfouten: de complexiteit van de installaties vraagt om deskundig onderhoud. "
            "Het uitzetten van ventilatie of verkeerd instellen van de warmtepomp heeft "
            "direct effect op comfort en energierekening.",
        ],
        "subsidies_periode": [
            "Deze woningen voldoen aan zeer strenge eisen (Rc dak 6,0 / gevel 4,5) "
            "en zijn vaak al gasloos. De winst zit in monitoring en hernieuwbare opwek.",
            "Warmtepomp via ISDE (2026): mocht de woning nog een gasaansluiting hebben, "
            "dan is de stap naar een warmtepomp financieel aantrekkelijk: startbedrag € 1.025 "
            "+ € 225 per kW vermogen, met een mogelijke label-bonus van € 200 (A+++).",
        ],
        "actie": (
            "Focus op gebruiksoptimalisatie en overweeg zonnepanelen of een thuisbatterij "
            "als logische en rendabele vervolgstap."
        ),
    },
]

# ── Subsidienuances (van toepassing op alle periodes) ─────────────────────────
SUBSIDIE_NUANCES = [
    "Verdubbeling: de genoemde m²-bedragen gelden bij twee of meer maatregelen (of één "
    "isolatiemaatregel gecombineerd met een warmtepomp). Bij slechts één maatregel wordt "
    "het bedrag gehalveerd.",
    "Beperkingen: u ontvangt slechts subsidie voor één type vloerisolatie (bodem óf vloer) "
    "en één type dakisolatie (dak óf zoldervloer).",
    "Oppervlaktes: let op de minimale oppervlakte-eisen "
    "(bijv. minimaal 10 m² voor gevel en 20 m² voor dak/vloer).",
]

# ── Label-duiding ─────────────────────────────────────────────────────────────
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


# ── Opzoekfuncties (niet aanpassen) ──────────────────────────────────────────

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

    return "\n\n".join(delen)
