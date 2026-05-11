"""
teksten_elementen.py
====================
Beschrijvende teksten per isolatie-element (gevel, dak, vloer, glas),
opgesplitst in een basis-uitleg en score-specifieke toelichting.

HOE AANPASSEN?
  Zoek het gewenste element op (zoek op 'gevel', 'dak', 'vloer' of 'glas').
  - basis     : altijd getoond, algemene uitleg van het element
  - score_5   : Zeer slecht (score 5)
  - score_4   : Slecht (score 4)
  - score_3   : Matig (score 3)
  - score_2   : Redelijk (score 2)  - optioneel, valt anders terug op basis
  - score_1   : Goed (score 1)      - optioneel, valt anders terug op basis
"""
from __future__ import annotations

# Tekst die getoond wordt bij score 1 of 2 (goed/redelijk), geldt voor alle elementen.
SCORE_VERBETER_TEKST = (
    "Heeft u al verbeteringen uitgevoerd of wilt u dit aanpakken en nog een stap verder "
    "gaan, dan kunt u zich richten op het optimaliseren van installaties en het verder "
    "verlagen van uw energieverbruik.\n\n"
    "Denk aan het toepassen van zonnepanelen, het overstappen naar een (hybride) warmtepomp "
    "en het verbeteren van uw verwarmingssysteem. In combinatie met goede ventilatie zorgt "
    "dit voor een comfortabel en gezond binnenklimaat. Ook batterijopslag kan interessant "
    "zijn om energie tijdelijk op te slaan.\n\n"
    "Door isolatie en installaties slim te combineren, werkt u stap voor stap toe naar een "
    "woning die klaar is voor een toekomst met minder of geen aardgas."
)

SCORE_GOED_TEKST = (
    "Uw woning staat er goed bij. De basis van de gebouwschil is op orde en grote "
    "isolatiemaatregelen zijn waarschijnlijk niet de eerste prioriteit. De meeste winst "
    "is in uw situatie te behalen met het optimaliseren van installaties.\n\n"
    "Denk hierbij aan zonnepanelen voor het opwekken van eigen energie, een warmtepomp "
    "(of hybride oplossing) om het gasverbruik verder te verlagen, en het optimaliseren "
    "van uw verwarmingssysteem. Ook ventilatie speelt een belangrijke rol: een goed "
    "ingeregeld systeem zorgt voor comfort en voorkomt vochtproblemen. Tot slot kan "
    "batterijopslag interessant zijn om opgewekte energie efficiënter te benutten.\n\n"
    "Met deze stappen zet u de volgende stap richting een energiezuinige en "
    "toekomstbestendige woning."
)

ELEMENTEN: dict[str, dict] = {

    "gevel": {
        "basis": (
            "Gevelisolatie brengt een thermische laag aan in de spouw of tegen de muren om "
            "warmteverlies te beperken. Zonder isolatie ontsnapt warmte via het metselwerk "
            "en koelen binnenmuren af."
        ),
        "score_5": (
            "De muren zijn ongeïsoleerd waardoor warmte ongehinderd naar buiten stroomt "
            "en bewoners koude wanden en tocht ervaren. Isoleren levert direct comfort op en "
            "verdient zich bij spouwmuren gemiddeld in vier jaar terug."
        ),
        "score_4": (
            "De huidige gevelisolatie is er niet of onvoldoende waardoor de verwarmingsinstallatie "
            "harder werkt dan nodig is. Bijzetten naar een hogere Rc-waarde zorgt voor minder "
            "energieverlies, een lagere warmtevraag en verbetert het binnenklimaat."
        ),
        "score_3": (
            "De gevel is redelijk geïsoleerd maar optimalisatie naar Rc 3,5 of hoger reduceert "
            "het warmteverlies verder. Bij naisoleren is het extra van belang te kijken naar "
            "bouwfysische risico's om vochtproblemen en schimmel te voorkomen."
        ),
    },

    "dak": {
        "basis": (
            "Dakisolatie houdt opstijgende warme lucht binnen de woning vast en is daarmee een "
            "van de meest effectieve energiemaatregelen. Een slecht geïsoleerd dak is "
            "verantwoordelijk voor een groot deel van het totale warmteverlies."
        ),
        "score_5": (
            "Via het ongeïsoleerde dak lekt de meeste warmte weg, waardoor de bovenverdieping "
            "nauwelijks warm te krijgen is en de energierekening erg hoog is. Isoleren naar "
            "een hogere Rc-waarde zorgt voor minder verspilling en lagere kosten."
        ),
        "score_4": (
            "Uw dak is niet of gering geïsoleerd, maar onvoldoende dik voor de huidige normen. "
            "Er is nog aanzienlijk warmteverlies via de kap. Opschalen naar een hogere Rc-waarde "
            "verbetert het binnenklimaat op de bovenverdieping en verlaagt de stookkosten."
        ),
        "score_3": (
            "Het dak is redelijk geïsoleerd maar bij-isoleren kan zinvol zijn. "
            "Let bij uitvoering op de luchtdichte aansluitingen bij nok en dakvoeten om "
            "warmtelekken te voorkomen."
        ),
    },

    "vloer": {
        "basis": (
            "Vloerisolatie vormt een barrière tussen de warme leefruimte en de koude grond of "
            "kruipruimte. Het stopt warmteverlies via de onderzijde en gaat optrekkend vocht "
            "uit de kruipruimte tegen."
        ),
        "score_5": (
            "De ongeïsoleerde vloer onttrekt voortdurend warmte aan de ruimte waardoor bewoners "
            "koude voeten ervaren en de luchtvochtigheid in huis te hoog is. Isoleren maakt de "
            "vloer direct warmer aanvoelend en verlaagt de luchtvochtigheid merkbaar."
	    "Kijk goed per situatie welke aanpak het beste is om schimmel en vochtprobelemen te "
	    "voorkomen. "
        ),
        "score_4": (
            "De huidige vloerisolatie is onvoldoende, waardoor er nog warmteverlies via de "
            "onderkant optreedt en de kruipruimte invloed heeft op het binnenklimaat. "
            "Vervangen van de isolatie naar een hogere Rc verlaagt het verlies en verhoogt het "
            "wooncomfort."
        ),
        "score_3": (
            "De vloer is redelijk geïsoleerd maar controleer of de isolatie nog volledig op "
            "zijn plaats ligt en droog is. "
        ),
    },

    "glas": {
        "basis": (
            "Isolerend glas vervangt enkel of verouderd dubbel glas door ruiten met een "
            "warmtereflecterende coating die warmte binnenhoudt en koudeval bij de ramen "
            "voorkomt. Ramen zijn de zwakste plekken in de isolatieschil van een woning."
        ),
        "score_5": (
            "Het huidige enkel glas isoleert slecht waardoor bewoners sterke koudeval, "
            "tocht en condens op de ruiten ervaren. Vervangen door HR++ glas vermindert "
            "het warmteverlies via de ruiten met meer dan tachtig procent."
	    "Niet elk raam of kozijn is geschikt voor dubbel glas, omdat er te weinig "
	    "ruimte in het hout is om dubbel glas te plaatsen. Een opdeklat of vervanging "
	    "van de huidige kozijnen kan nodig zijn. "
        ),
        "score_4": (
            "Het aanwezige enkel of oud dubbel glas is verouderd of lek en presteert "
            "niet meer als bij aanleg. Vervangen door nieuwe HR++ ruiten verbetert het "
            "binnenklimaat direct en elimineert koude luchtstromen langs de ramen."
        ),
        "score_3": (
            "Het glas is functioneel maar upgraden naar triple glas kan nog voor verbetering "
            "zorgen in warmteverlies en geluidsisolatie. Controleer tegelijk of de kozijnen "
            "en afdichtingsrubbers nog goed afsluiten om infiltratie te voorkomen."
        ),
    },
}


def get_slottekst_kansen(scores: dict) -> str:
    """
    Geeft de slottekst voor het hoofdstuk 'Kansen en verbeterpotentieel'.
    Als alle scores ≤ 2 → SCORE_GOED_TEKST, anders → SCORE_VERBETER_TEKST.
    """
    waarden = [v for v in scores.values() if v is not None]
    if waarden and all(v <= 2 for v in waarden):
        return SCORE_GOED_TEKST
    return SCORE_VERBETER_TEKST


def get_element_tekst(element: str, score: int | None) -> str:
    """
    Geeft de volledige tekst voor een element bij een bepaalde score.
    Altijd: basis-uitleg. Gevolgd door score-specifieke toelichting bij score 3, 4 of 5.
    Bij score 1 of 2 (goed/redelijk) alleen de basis-uitleg.
    """
    data = ELEMENTEN.get(element.lower())
    if not data:
        return ""

    basis = data["basis"]

    if score is None or score <= 2:
        return basis

    score_tekst = data.get(f"score_{score}", "")
    if score_tekst:
        return f"{basis}\n\n{score_tekst}"
    return basis
