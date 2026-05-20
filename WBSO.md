# WBSO-logboek PandIQ Isolatie Quickscan

**Project:** Geautomatiseerde verduurzamingsanalyse voor woningen op basis van openbare registraties
**Doel:** Ontwikkeling van een systeem dat per woning automatisch isolatiescores, financiële indicaties, subsidiebedragen en gepersonaliseerde adviesteksten berekent en als rapport genereert.

---

## Wat is de speur- en ontwikkelingsarbeid (S&O)?

Het technisch knelpunt zit in het combineren van meerdere heterogene databronnen (BAG, PDOK, EP-online) met bouwfysische rekenmodellen, om zonder handmatige tussenkomst een betrouwbare, persoonsgebonden energieanalyse te genereren. De uitdaging is niet het ophalen van data, maar het omzetten van incomplete en wisselende brondata naar fysisch onderbouwde uitspraken met expliciete onzekerheidsmarges.

---

## Ontwikkelde modules en technische activiteiten

### FASE 1 - Databronnen en adresresolutie
**Bestanden:** `clients_pdok.py`, `clients_bag.py`, `energielabels.py`, `streetview.py`

| Activiteit | Technische uitdaging |
|---|---|
| Koppeling PDOK Locatieserver | Adres naar coördinaten en document-ID omzetten; omgaan met ambigue adressen en toevoegingen |
| Koppeling BAG API (RVO) | Bouwjaar en gebruiksoppervlakte opvragen; normaliseren van wisselende veldnamen per BAG-versie |
| Koppeling EP-online | Ophalen energielabel en thermische woningkenmerken; ontbrekende labels afvangen zonder rekenfouten |
| Street View integratie | Coördinaten extraheren uit PDOK WKT-formaat; caching en fallback bij ontbrekende foto |

---

### FASE 2 - Scoringsmodel en beslislaag
**Bestanden:** `report.py`, `advisor.py`, `financials.py`

| Activiteit | Technische uitdaging |
|---|---|
| Quickscan-scoringsmodel | Combinatie van bouwjaar en energielabel naar per-element scores (dak/gevel/vloer/glas) zonder directe meting; bepalen van correctieregels bij conflicterende brondata |
| Centrale beslislaag `build_advice()` | Orchestratie van scores, warmtebehoefteberekening, subsidietoewijzing en teksten in één coherent resultaatobject (`AdviesResult`) |
| Warmtebehoefteschatting | Hiërarchische fallback: EP-online thermische zone → EP-online × BAG → bouwperiode-default × BAG → absolute fallback; transparant registreren welke bron gebruikt is |
| Financiële bandbreedteberekening | Omzetten van kwalitatieve scores naar EUR-bandbreedtes via verliesaandelen en verbeteringsefficienties; voorkomen van overprecisie door expliciete bandbreedte-output |
| Subsidietoewijzing ISDE 2026 | Koppeling van woningtype + bouwperiode + element aan de juiste ISDE-maatregelsleutel; meervoudig vs. enkelvoudig tarief automatisch bepalen |

---

### FASE 3 - Persoonlijke output (Markdown, Word, PDF)
**Bestanden:** `narratives.py`, `teksten_bouwperiodes.py`, `teksten_elementen.py`, `fill_template.py`, `main.py`

| Activiteit | Technische uitdaging |
|---|---|
| Narratieve teksten per bouwperiode | Parametrisering van vaste teksten met dynamische invulvelden (bouwjaar, scores, maatregelnamen); logica voor conditionele tekstblokken op basis van labelklasse en score |
| Word-template invulling | Betrouwbaar vervangen van `{{placeholders}}` in complexe DOCX-structuren met python-docx; afvangen van markdown-opmaak die niet in Word past |
| PDF-conversie + optimalisatie | LibreOffice headless aanroepen voor DOCX→PDF; Ghostscript post-processing voor font-embedding en printcompatibiliteit (PDF 1.4) |
| Samenvatting en prioriteitentekst | Genereren van contextuele executive summary die varieert op basis van gemiddelde score, beschikbare data en subsidiepotentieel |

---

### FASE 4 - Woningtype-parameter
**Bestanden:** `main.py`, `report.py`

| Activiteit | Technische uitdaging |
|---|---|
| Woningtype als invoervariabele | Toevoegen van `woningtype` (rijwoning/hoekwoning/vrijstaand/twee-onder-een-kap/appartement) als CLI-parameter en doorvoeren in de volledige rekenketen voor toekomstig gebruik in oppervlakte- en kostenberekeningen |

---

### FASE 5 - Bouwfysisch rekenmodel
**Bestanden:** `aannames.py`, `oppervlaktes.py`, `financials.py` (uitbreiding), `waarschuwingen.py`

| Activiteit | Technische uitdaging |
|---|---|
| Centrale aannames-registry (`aannames.py`) | Structureren van alle rekenparameters (24 stuks) met bronvermelding en aanpasbaarheidsmarkering; RC_TABEL en U_TABEL per bouwperiode op basis van ISSO 82.1 en SBR 2022 |
| Oppervlakteberekening per woningtype (`oppervlaktes.py`) | 9-stappen berekening van dak/vloer/gevel/spouw/glas-oppervlakten uit BAG-BVO en woningtype; geometrische afleiding van breedte/diepte per woningtype; expliciete logregel per stap voor traceerbaarheid |
| Warmteverliesreductie-formule | Implementatie van NEN 1068 vereenvoudigde formule `Q = A × (1/Rc_oud − 1/Rc_nieuw) × ΔT × t / 1000`; volledig parametervrij (alle waarden uit `aannames.py`); outputformat met formule als leesbare string voor auditbaarheid |
| Dynamische terugverdientijd | Cumulatieve TVT-formule met energieprijsstijging: `C(N) = B1 × ((1+p)^N − 1) / p`; doorkijk op 1/3/5/10/15/20 jaar; interpolatie voor subjarige TVT |
| Waarschuwingengenerator (`waarschuwingen.py`) | Regelgebaseerde checks op bouwfysische risico's (condensatie, massief metselwerk), subsidie-eligibiliteit (ISDE-minimum), procedurele risico's (VvE, welstand) en data-inconsistenties (recent label vs. lage Rc) |
| Integratie in `advisor.py` | Oppervlaktes en waarschuwingen berekend en meegegeven in `AdviesResult` zonder bestaande logica te wijzigen |

---

## Gebruikte externe normen en bronnen (relevant voor WBSO-onderbouwing)

| Norm / Bron | Toepassing in code |
|---|---|
| ISSO 82.1 tabel 3 | RC_TABEL, indicatieve Rc-waarden bestaande bouw per bouwperiode |
| NEN 1068 (vereenvoudigd) | Warmteverliesreductie-formule in `financials.warmteverlies_reductie()` |
| NEN 5060 referentieklimaatjaar | ΔT=10 K, verwarmingsuren=5500 h/jr in `aannames.py` |
| SBR referentiewoningen 2022 | U_TABEL glas, glasandelen per gevelzijde, woningafmetingen |
| CBS Woononderzoek 2021 | Breedte-aannames per woningtype |
| RVO ISDE 2026 | Rc/U-eisen voor subsidiabiliteit, subsidiebedragen per m² |
| PBL KEV 2024 | Energieprijsstijging 3%/jr als rekenparameter |

---

### FASE 6 - Integratie bouwfysische berekeningen in rapport output
**Bestanden:** `advisor.py` (uitbreiding), `report.py` (uitbreiding), `main.py` (uitbreiding)

| Activiteit | Technische uitdaging |
|---|---|
| Tekst-builder fysische analyse (`_bouw_fysische_analyse`) | Per bouwdeel: oppervlak uit `oppervlaktes.py`, Rc huidig uit `aannames.rc_oud()`, besparing via `warmteverlies_reductie()`, investering + subsidie via bestaande financials, dynamische TVT via `terugverdientijd_uitgebreid()`. Alles samengebracht in een Markdown-blok per element |
| Tekst-builder waarschuwingen (`_bouw_waarschuwingen_tekst`) | Omzetten van gestructureerde waarschuwingen-lijst naar leesbare Markdown met niveaucodering (info/let_op/risico) |
| Koppeling aan rapport (sectie 5 en 7) | Nieuwe secties in `render_markdown()`: bouwfysische analyse na maatregelen (§5), waarschuwingen gecombineerd met narratieve risico's (§7); sectienummers dynamisch |
| Docx-placeholders | `{{fysische_analyse}}` en `{{waarschuwingen}}` toegevoegd aan `docx_data` in `main.py` |

---

### FASE 7 - Rapportage template herontwerp (scheiding opmaak en data)
**Bestanden:** `templates/Template_rapportage_quickscan.docx`, `src/fill_template.py`, `src/main.py`

| Activiteit | Technische uitdaging |
|---|---|
| Template als enige bron van opmaak | Redesign van `Template_rapportage_quickscan.docx` zodat alle huisstijl (kop/voettekst, sectieopmaak, kleurgebruik, voorblad) volledig in het Word-template zit; code levert uitsluitend data |
| Placeholder-architectuur `{{dubbele accolades}}` | `fill_template.py` vervangt alle `{{placeholder}}`-varianten (met en zonder spaties) in de XML van het docx-bestand via directe string-substitutie; geen externe template-engine nodig |
| Totaalplaatje verplaatst naar na de losse bouwdelen | `report.py`: blok met min/max investeringstabel verplaatst van vóór naar ná sectie 4 (prioriteiten per bouwdeel), zodat samenvatting na details staat |
| Verificatie volledige placeholder-dekking | Controle dat alle `{{placeholders}}` uit het nieuw ontworpen template gedekt worden door `docx_data` in `main.py`; geen onvervulde placeholders in output |

---

### FASE 8 - Aanpak gevelisolatie: altijd voorzetwanden
**Bestanden:** `advisor.py`, `fill_template.py`, `teksten_bouwperiodes.py`

| Activiteit | Technische uitdaging |
|---|---|
| Maatregel-label gevel gewijzigd | "Gevelisolatie (buiten/binnen)" vervangen door "Voorzetwanden (binnenisolatie)" in adviseur en template-invulling; keuze-presentatie aan eindgebruiker vereenvoudigd |
| Maatregel-tekst periode 1 (voor 1946) | Verwijzing naar buitenzijde-isolatie verwijderd; aanpak beschrijft nu uitsluitend voorzetwand als standaard aanpak bij massieve muren |

---

### FASE 9 - Totaalplaatje + per-element placeholders: min / gemiddeld / max
**Bestanden:** `src/fill_template.py`

| Activiteit | Technische uitdaging |
|---|---|
| Driekoloms scenario-tabel totaalplaatje | Uitbreiding van de min/max-tabel in het totaalplaatje naar drie scenario's (worst case, gemiddeld, best case); logica voor 'gemiddeld' als rekenkundig gemiddelde van de bandbreedtes |
| Automatische tabeluitbreiding van 3→4 kolommen | `_expand_seed_tabel_naar_4_kolommen()`: zoekt de seed-tabel in het Word-document via de marker, breidt de XML uit (tblGrid + elke rij) zonder templatewijziging; seed-rij kloont kolomopmaak automatisch |
| Kolomkop-update via XML | `_update_kolomkoppen_totaalplaatje()`: overschrijft de tekst in de koptekstrij boven de seed-rij programmatisch ("Worst case", "Gemiddeld", "Best case"); behoudt bestaande Word-opmaak van de koprij |
| Gemiddeld-placeholders per element | Uitbreiding van `_totaalplaatje_placeholders()` in `main.py` met `_gem` varianten voor investering, besparing en terugverdientijd — zowel totaal als per element (dak/gevel/vloer/glas); gemiddelde berekend als rekenkundig gemiddelde van min en max |

---

## Nog te ontwikkelen (geplande S&O)

- Rc-waarden en U-waarden gebruiken in de scoringslogica (nu nog op bouwjaar-band)
- Vervanging van verliesaandeel-methode door oppervlakte-gebaseerde warmteverliesberekening als primaire besparingsmethode in `_bouw_prioriteiten()`
- API-endpoint voor website-integratie (vervanging van CLI)
