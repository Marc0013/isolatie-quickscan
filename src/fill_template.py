from __future__ import annotations
import os, zipfile, shutil
from lxml import etree
from pathlib import Path

NS = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
W  = f'{{{NS}}}'

# ── Subsidietabel configuratie ────────────────────────────────────────────────
_SUBSIDIE_SENTINEL = "##PANDIQ_SUBSIDIETABEL##"
_NAVY_HEX   = "5AAA00"   # titelbalk groen (PandIQ huisstijl)
_YELLOW_HEX = "FFFFFF"   # aanbevolen rij — wit (geen gele achtergrond)
_GREEN_BG   = "FFFFFF"   # warmtepomp blok — wit
_GREEN_HEAD = "5AAA00"   # warmtepomp header — PandIQ groen
_BLUE_BG    = "FFFFFF"   # noten — geen achtergrondkleur
_WARN_BG    = "FFFFFF"   # waarschuwingsnoot — geen achtergrondkleur

def _set_cel_achtergrond(cel, kleur_hex: str) -> None:
    """Zet een vaste achtergrondkleur op een Word-tabelcel via XML."""
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement
    tc = cel._tc
    tcPr = tc.get_or_add_tcPr()
    for old in tcPr.findall(qn('w:shd')):
        tcPr.remove(old)
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), kleur_hex.upper())
    tcPr.append(shd)


def _cel_tekst(cel, tekst: str, *, bold=False, size=11, kleur=None, italic=False):
    """Zet tekst in een cel met opmaak. Vervangt eventuele bestaande inhoud."""
    from docx.shared import Pt
    cel.text = ""
    run = cel.paragraphs[0].add_run(tekst)
    run.bold = bold
    run.italic = italic
    run.font.name = "Calibri"
    run.font.size = Pt(size)
    if kleur:
        run.font.color.rgb = kleur


def _voeg_subsidietabel_bouwperiode_in(docx_pad: str, bouwjaar: int, subsidie_indicatie: str = "") -> None:
    """
    Vervangt de sentinel-alinea door twee Word-tabellen (Isolatie + Glas)
    met periode-specifieke markering, warmtepomp combinatieblok en noten.
    Aanbevolen rijen: lichtgele achtergrond, vet. Minder relevant: grijze tekst.
    """
    try:
        from docx import Document
        from docx.shared import Pt, RGBColor
    except ImportError:
        print("  Let op: python-docx niet geïnstalleerd — subsidietabel niet ingevoegd.")
        return

    import sys, os
    sys.path.insert(0, os.path.dirname(__file__))
    from subsidies_isolatie_glas import (
        ISOLATIE_BEDRAGEN, GLAS_BEDRAGEN, MONUMENT_GLAS, MEERVOUDIG_DISCLAIMER,
        WARMTEPOMP, ALGEMENE_NOTEN, get_periode,
    )
    from teksten_bouwperiodes import SUBSIDIE_NUANCES

    periode        = get_periode(bouwjaar)
    aanbevolen_iso = set(periode["isolatie"])
    aanbevolen_glas = set(periode["glas"])

    WIT       = RGBColor(0xFF, 0xFF, 0xFF)
    ZWART     = RGBColor(0x1D, 0x1D, 0x1B)
    GRIJS     = RGBColor(0x99, 0x99, 0x99)
    GROEN_TXT = RGBColor(0x2E, 0x7D, 0x32)

    doc = Document(docx_pad)

    # Zoek sentinel
    target = None
    for para in doc.paragraphs:
        if _SUBSIDIE_SENTINEL in para.text:
            target = para
            break
    if target is None:
        return

    sentinel_elem = target._element
    parent        = sentinel_elem.getparent()
    positie       = list(parent).index(sentinel_elem)

    def _set_kolom_breedtes(tabel, breedtes: list) -> None:
        """Stelt expliciete kolombreedtes in (twips). Overschrijft auto-layout."""
        from docx.oxml.ns import qn as _qn
        from docx.oxml import OxmlElement as _el
        tbl = tabel._tbl
        # Totale tabelbreedte op fixed zetten
        tblPr = tbl.find(_qn('w:tblPr'))
        if tblPr is not None:
            for old in tblPr.findall(_qn('w:tblW')):
                tblPr.remove(old)
            tblW = _el('w:tblW')
            tblW.set(_qn('w:w'), str(sum(breedtes)))
            tblW.set(_qn('w:type'), 'dxa')
            tblPr.insert(0, tblW)
        # tblGrid vervangen
        for old in tbl.findall(_qn('w:tblGrid')):
            tbl.remove(old)
        tblGrid = _el('w:tblGrid')
        for b in breedtes:
            gc = _el('w:gridCol'); gc.set(_qn('w:w'), str(b)); tblGrid.append(gc)
        tblPr_elem = tbl.find(_qn('w:tblPr'))
        if tblPr_elem is not None:
            tblPr_elem.addnext(tblGrid)
        else:
            tbl.insert(0, tblGrid)
        # Breedte per cel per rij
        for rij in tabel.rows:
            for cel, b in zip(rij.cells, breedtes):
                tcPr = cel._tc.get_or_add_tcPr()
                for old in tcPr.findall(_qn('w:tcW')):
                    tcPr.remove(old)
                tcW = _el('w:tcW'); tcW.set(_qn('w:w'), str(b)); tcW.set(_qn('w:type'), 'dxa')
                tcPr.insert(0, tcW)

    def _set_rij_hoogte(rij, twips=400):
        """Minimale rijhoogte instellen (twips = 1/20 pt; 400 ≈ 7 mm)."""
        from docx.oxml.ns import qn as _qn
        from docx.oxml import OxmlElement as _el
        trPr = rij._tr.get_or_add_trPr()
        for old in trPr.findall(_qn('w:trHeight')):
            trPr.remove(old)
        trH = _el('w:trHeight')
        trH.set(_qn('w:val'), str(twips))
        trH.set(_qn('w:hRule'), 'atLeast')
        trPr.append(trH)

    def _header_rij(tabel, kolommen, achtergrond=_NAVY_HEX):
        rij = tabel.rows[0]
        for j, kop in enumerate(kolommen):
            cel = rij.cells[j]
            _cel_tekst(cel, kop, bold=True, kleur=WIT)
            _set_cel_achtergrond(cel, achtergrond)
        _set_rij_hoogte(rij)

    def _data_rij(tabel, cellen: list, aanbevolen: bool):
        """Voegt een datarij toe. Aanbevolen = gele bg + vet; anders grijs."""
        rij = tabel.add_row()
        kleur = ZWART if aanbevolen else GRIJS
        for j, (tekst, bold) in enumerate(cellen):
            _cel_tekst(rij.cells[j], tekst, bold=(bold and aanbevolen), kleur=kleur)
            if aanbevolen:
                _set_cel_achtergrond(rij.cells[j], _YELLOW_HEX)
        _set_rij_hoogte(rij)

    # ── Tabel 1: Isolatie ─────────────────────────────────────────────────────
    ISO_VOLGORDE = ["gevel", "dakisolatie", "zoldervloer", "spouwmuur", "vloer", "bodem"]
    ISO_COLS     = ["Maatregel", "ISDE 2026 (€/m²)", "Biobased bonus", "Min. Rc/Rd"]

    tabel_iso = doc.add_table(rows=1, cols=len(ISO_COLS))
    try: tabel_iso.style = doc.styles['Table Grid']
    except KeyError: pass
    # Kolom 1 (Maatregel) 3200 tw, overige 3 kolommen elk ~1942 tw  (totaal 9026)
    _set_kolom_breedtes(tabel_iso, [3200, 1942, 1942, 1942])
    _header_rij(tabel_iso, ISO_COLS)

    for sleutel in ISO_VOLGORDE:
        m = ISOLATIE_BEDRAGEN[sleutel]
        bio = f"+ € {m['bio']:.2f}/m²" if m.get("bio") else "—"
        _data_rij(tabel_iso, [
            (m["naam"],               True),
            (f"€ {m['bedrag']:.2f}/m²",  True),
            (bio,                      False),
            (m["rd"],                  False),
        ], aanbevolen=sleutel in aanbevolen_iso)

    # ── Tabel 2: Glas ─────────────────────────────────────────────────────────
    GLAS_VOLGORDE = ["hrpp", "vacuum", "triple", "deuren"]
    GLAS_COLS     = ["Type glas", "ISDE 2026 (€/m²)", "Min. U-waarde"]

    spatie1 = doc.add_paragraph("")

    tabel_glas = doc.add_table(rows=1, cols=len(GLAS_COLS))
    try: tabel_glas.style = doc.styles['Table Grid']
    except KeyError: pass
    # Kolom 1 (Type glas) 3200 tw, overige 2 kolommen elk ~2913 tw  (totaal 9026)
    _set_kolom_breedtes(tabel_glas, [3200, 2913, 2913])
    _header_rij(tabel_glas, GLAS_COLS)

    for sleutel in GLAS_VOLGORDE:
        g = GLAS_BEDRAGEN[sleutel]
        _data_rij(tabel_glas, [
            (g["naam"],               True),
            (f"€ {g['bedrag']:.2f}/m²",  True),
            (g["ug"],                  False),
        ], aanbevolen=sleutel in aanbevolen_glas)

    # ── Warmtepomp combinatieblok ──────────────────────────────────────────────
    spatie2 = doc.add_paragraph("")

    wp = WARMTEPOMP
    wp_toel = periode.get("warmtepomp_toelichting", wp["toelichting"])

    tabel_wp = doc.add_table(rows=3, cols=4)
    try: tabel_wp.style = doc.styles['Table Grid']
    except KeyError: pass
    # Kolom 1 (Combinatie) 3200 tw, overige 3 kolommen elk ~1942 tw  (totaal 9026)
    _set_kolom_breedtes(tabel_wp, [3200, 1942, 1942, 1942])

    # Header
    _header_rij(tabel_wp, ["Combinatie", "Startbedrag", "Per kW vermogen", "A+++ bonus"],
                achtergrond=_GREEN_HEAD)

    # Bedragen rij
    rij_wp = tabel_wp.rows[1]
    for cel, tekst in zip(rij_wp.cells, [
        "Isolatie + warmtepomp",
        f"€ {wp['startbedrag']:,}",
        f"+ € {wp['per_kw']} per kW",
        f"+ € {wp['aplus_bonus']}",
    ]):
        _cel_tekst(cel, tekst, bold=(tekst == "Isolatie + warmtepomp"), kleur=GROEN_TXT)
        _set_cel_achtergrond(cel, _GREEN_BG)
    _set_rij_hoogte(rij_wp)

    # Toelichting rij (samengevoegde cel)
    rij_toel = tabel_wp.rows[2]
    cel_toel = rij_toel.cells[0]
    for i in range(1, 4):
        cel_toel = cel_toel.merge(rij_toel.cells[i])
    _cel_tekst(cel_toel, wp_toel, italic=True, kleur=GROEN_TXT)
    _set_cel_achtergrond(rij_toel.cells[0], _GREEN_BG)

    # ── Noten ─────────────────────────────────────────────────────────────────
    spatie3 = doc.add_paragraph("")

    tabel_noten = doc.add_table(rows=0, cols=1)
    try: tabel_noten.style = doc.styles['Table Grid']
    except KeyError: pass

    # Persoonlijk indicatief subsidietotaal bovenaan de noten (indien beschikbaar)
    if subsidie_indicatie:
        rij = tabel_noten.add_row()
        _cel_tekst(rij.cells[0], subsidie_indicatie, bold=True, kleur=GROEN_TXT)
        _set_cel_achtergrond(rij.cells[0], _YELLOW_HEX)
        _set_rij_hoogte(rij)

    # Disclaimer meervoudig tarief
    rij = tabel_noten.add_row()
    _cel_tekst(rij.cells[0], MEERVOUDIG_DISCLAIMER, italic=True)
    _set_cel_achtergrond(rij.cells[0], _BLUE_BG)
    _set_rij_hoogte(rij)

    if periode.get("notitie"):
        rij = tabel_noten.add_row()
        _cel_tekst(rij.cells[0], f"Let op: {periode['notitie']}", italic=True)
        _set_cel_achtergrond(rij.cells[0], _WARN_BG)

    for noot in SUBSIDIE_NUANCES:
        rij = tabel_noten.add_row()
        _cel_tekst(rij.cells[0], f"• {noot}")
        _set_cel_achtergrond(rij.cells[0], _BLUE_BG)

    # ── Verplaats alles naar sentinel-positie ──────────────────────────────────
    elementen = [
        tabel_iso._tbl,
        spatie1._element,
        tabel_glas._tbl,
        spatie2._element,
        tabel_wp._tbl,
        spatie3._element,
        tabel_noten._tbl,
    ]
    for i, elem in enumerate(elementen):
        parent.insert(positie + i, elem)

    parent.remove(sentinel_elem)
    doc.save(docx_pad)


def _kopieer_alinea_opmaak(bron_para) -> etree._Element:
    """Maakt een lege kopie van een alinea met dezelfde opmaak (pPr)."""
    nieuwe = etree.Element(f'{W}p')
    ppr = bron_para.find(f'{W}pPr')
    if ppr is not None:
        nieuwe.append(etree.fromstring(etree.tostring(ppr)))
    return nieuwe


def _maak_run(tekst: str, bron_run) -> etree._Element:
    """Maakt een nieuwe run met dezelfde opmaak als de bronrun."""
    r = etree.Element(f'{W}r')
    rpr = bron_run.find(f'{W}rPr')
    if rpr is not None:
        r.append(etree.fromstring(etree.tostring(rpr)))
    t = etree.SubElement(r, f'{W}t')
    t.text = tekst
    t.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
    return r


def fill_xml(xml_bytes: bytes, mapping: dict) -> bytes:
    """
    Vervangt placeholders in Word XML.
    Teksten met \n worden automatisch opgesplitst in aparte Word-alinea's.
    """
    try:
        root = etree.fromstring(xml_bytes)
    except Exception:
        return xml_bytes

    body = root.find(f'{W}body')
    if body is None:
        body = root

    # Verzamel alle alinea's in volgorde (ook in tabellen)
    alle_alineas = list(root.iter(f'{W}p'))

    for para in alle_alineas:
        runs = para.findall(f'.//{W}r')
        if not runs:
            continue

        full_text = ''.join(
            (t.text or '')
            for r in runs
            for t in r.findall(f'{W}t')
        )

        new_text = full_text
        for key, value in mapping.items():
            new_text = new_text.replace(key, value)

        if new_text == full_text:
            continue

        # Geen newlines → gewoon vervangen
        if '\n' not in new_text:
            first_run = runs[0]
            t_els = first_run.findall(f'{W}t')
            if t_els:
                t_els[0].text = new_text
                t_els[0].set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
                for t in t_els[1:]:
                    first_run.remove(t)
            else:
                t_new = etree.SubElement(first_run, f'{W}t')
                t_new.text = new_text
                t_new.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
            for run in runs[1:]:
                for t in run.findall(f'{W}t'):
                    t.text = ''
            continue

        # Tekst bevat newlines → splits op in aparte alinea's
        regels = new_text.split('\n')
        bron_run = runs[0]
        parent = para.getparent()

        if parent is None:
            # Alinea zit niet direct in body (bijv. tabelcel) → gewoon spaties
            first_run = runs[0]
            t_els = first_run.findall(f'{W}t')
            vervang = new_text.replace('\n', ' ')
            if t_els:
                t_els[0].text = vervang
                t_els[0].set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
            for run in runs[1:]:
                for t in run.findall(f'{W}t'):
                    t.text = ''
            continue

        # Vind de positie van de huidige alinea in de parent
        positie = list(parent).index(para)

        # Eerste regel: zet in de bestaande alinea
        eerste_tekst = regels[0]
        for run in runs:
            for t in run.findall(f'{W}t'):
                t.text = ''
        if eerste_tekst.strip():
            t_els = bron_run.findall(f'{W}t')
            if t_els:
                t_els[0].text = eerste_tekst
                t_els[0].set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
            else:
                t_new = etree.SubElement(bron_run, f'{W}t')
                t_new.text = eerste_tekst
                t_new.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')

        # Volgende regels: voeg nieuwe alinea's in na de huidige
        # Lege regels (van \n\n) worden echte lege alinea's met spacing
        for i, regel in enumerate(regels[1:], 1):
            nieuwe_para = _kopieer_alinea_opmaak(para)
            if regel.strip():
                nieuwe_para.append(_maak_run(regel, bron_run))
            else:
                # Lege alinea: voeg minimale spacing toe zodat hij zichtbaar is
                ppr = nieuwe_para.find(f'{W}pPr')
                if ppr is None:
                    ppr = etree.SubElement(nieuwe_para, f'{W}pPr')
                    nieuwe_para.insert(0, ppr)
                spacing = ppr.find(f'{W}spacing')
                if spacing is None:
                    spacing = etree.SubElement(ppr, f'{W}spacing')
                spacing.set(f'{W}before', '120')
                spacing.set(f'{W}after', '120')
            parent.insert(positie + i, nieuwe_para)

    return etree.tostring(root, xml_declaration=True, encoding='UTF-8', standalone=True)


def _voeg_foto_in_docx_toe(tmp_dir: Path, foto_pad: str) -> bool:
    """
    Voegt de Street View foto in als afbeelding in het document.
    Plaatst hem op het voorblad na de adres/datum regels.
    Geeft True terug als het gelukt is.
    """
    try:
        import shutil as _shutil

        # Kopieer foto naar word/media/
        media_dir = tmp_dir / "word" / "media"
        media_dir.mkdir(exist_ok=True)
        foto_doel = media_dir / "streetview.jpg"
        _shutil.copy(foto_pad, foto_doel)

        # Voeg relatie toe in document.xml.rels
        rels_pad = tmp_dir / "word" / "_rels" / "document.xml.rels"
        with open(rels_pad, "r", encoding="utf-8") as f:
            rels = f.read()

        rel_id = "rIdSV1"
        if rel_id not in rels:
            nieuwe_rel = f'<Relationship Id="{rel_id}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/streetview.jpg"/>'
            rels = rels.replace("</Relationships>", f"  {nieuwe_rel}\n</Relationships>")
            with open(rels_pad, "w", encoding="utf-8") as f:
                f.write(rels)

        # Voeg content type toe als nog niet aanwezig
        ct_pad = tmp_dir / "[Content_Types].xml"
        with open(ct_pad, "r", encoding="utf-8") as f:
            ct = f.read()
        if 'Extension="jpg"' not in ct and 'Extension="jpeg"' not in ct:
            ct = ct.replace("</Types>", '  <Default Extension="jpg" ContentType="image/jpeg"/>\n</Types>')
            with open(ct_pad, "w", encoding="utf-8") as f:
                f.write(ct)

        # Voeg afbeelding XML in na de datum-alinea op het voorblad
        # EMU: 1 inch = 914400, foto 600x400px bij 96dpi = 5715000 x 3810000 EMU
        breedte_emu = 5715000
        hoogte_emu  = 3810000

        foto_xml = f'''<w:p xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
             xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
             xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
             xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"
             xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <w:pPr><w:spacing w:before="160" w:after="160"/><w:jc w:val="left"/></w:pPr>
  <w:r>
    <w:rPr><w:noProof/></w:rPr>
    <w:drawing>
      <wp:inline distT="0" distB="0" distL="0" distR="0">
        <wp:extent cx="{breedte_emu}" cy="{hoogte_emu}"/>
        <wp:effectExtent l="0" t="0" r="0" b="0"/>
        <wp:docPr id="900" name="StreetView"/>
        <wp:cNvGraphicFramePr/>
        <a:graphic>
          <a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">
            <pic:pic>
              <pic:nvPicPr>
                <pic:cNvPr id="901" name="streetview.jpg"/>
                <pic:cNvPicPr/>
              </pic:nvPicPr>
              <pic:blipFill>
                <a:blip r:embed="{rel_id}"/>
                <a:stretch><a:fillRect/></a:stretch>
              </pic:blipFill>
              <pic:spPr>
                <a:xfrm><a:off x="0" y="0"/><a:ext cx="{breedte_emu}" cy="{hoogte_emu}"/></a:xfrm>
                <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
              </pic:spPr>
            </pic:pic>
          </a:graphicData>
        </a:graphic>
      </wp:inline>
    </w:drawing>
  </w:r>
</w:p>'''

        doc_pad = tmp_dir / "word" / "document.xml"
        with open(doc_pad, "r", encoding="utf-8") as f:
            doc = f.read()

        # Zoek de placeholder {{streetview}} en vervang die met de afbeelding XML
        if "{{streetview}}" in doc:
            # Vervang de hele alinea die {{streetview}} bevat
            import re
            doc = re.sub(
                r'<w:p\b[^>]*>(?:(?!<w:p\b).)*\{\{streetview\}\}(?:(?!<w:p\b).)*</w:p>',
                foto_xml,
                doc,
                flags=re.DOTALL
            )
        else:
            # Geen placeholder — voeg in na "Datum:" alinea op voorblad
            zoek = '<w:t>Indicatief rapport op basis van openbare registraties (BAG &amp; EP-Online)</w:t>'
            if zoek in doc:
                invoeg_na = doc.find(zoek)
                einde_alinea = doc.find('</w:p>', invoeg_na) + len('</w:p>')
                doc = doc[:einde_alinea] + '\n' + foto_xml + doc[einde_alinea:]

        with open(doc_pad, "w", encoding="utf-8") as f:
            f.write(doc)

        return True

    except Exception as e:
        print(f"  [Street View] Foto invoegen mislukt: {e} — rapport gaat door zonder foto.")
        return False


def _stijl_woninggegevens_tabel(docx_pad: str) -> None:
    """
    Vindt de Woninggegevens-tabel en past het blauwe huisstijl-thema toe.
    Herkent de tabel aan bekende labelcellen (adres, bouwjaar, energielabel …).
    Voegt een kopregel 'Woninggegevens' in als die ontbreekt.
    """
    try:
        from docx import Document
        from docx.shared import Pt, RGBColor
        from docx.oxml.ns import qn
        from docx.oxml import OxmlElement
    except ImportError:
        return

    TITELBLAUW = "5AAA00"
    LIJNKLEUR  = "D6E2EE"
    WIT        = "FFFFFF"
    TEKST_RGB  = RGBColor(0x1F, 0x29, 0x37)
    GROEN_RGB  = RGBColor(0x2E, 0x7D, 0x32)

    HERKENNING = {"adres", "bouwjaar", "energielabel", "datum", "oppervlakte",
                  "warmtebehoefte", "energiebehoefte", "gebouwtype", "bouwperiode"}

    def _borders(cel):
        tc   = cel._tc
        tcPr = tc.get_or_add_tcPr()
        for old in tcPr.findall(qn('w:tcBorders')):
            tcPr.remove(old)
        tcB = OxmlElement('w:tcBorders')
        for kant in ('top', 'left', 'bottom', 'right'):
            rand = OxmlElement(f'w:{kant}')
            rand.set(qn('w:val'),   'single')
            rand.set(qn('w:sz'),    '4')        # 0.5 pt
            rand.set(qn('w:space'), '0')
            rand.set(qn('w:color'), LIJNKLEUR)
            tcB.append(rand)
        tcPr.append(tcB)

    def _run_opmaak(run, *, bold=False, kleur=None):
        run.bold           = bold
        run.font.name      = "Calibri"
        run.font.size      = Pt(11)
        if kleur:
            run.font.color.rgb = kleur

    doc = Document(docx_pad)

    # ── Zoek de woninggegevens-tabel ──────────────────────────────────────────
    woningtabel = None
    for tabel in doc.tables:
        if len(tabel.columns) < 2:
            continue
        links_teksten = [rij.cells[0].text.strip().lower() for rij in tabel.rows]
        treffers = sum(
            1 for lt in links_teksten
            for h in HERKENNING if h in lt
        )
        if treffers >= 2:
            woningtabel = tabel
            break

    if woningtabel is None:
        return

    # ── Kopregel 'Woninggegevens' toevoegen als die ontbreekt ─────────────────
    if "woninggegevens" not in woningtabel.rows[0].cells[0].text.strip().lower():
        tbl        = woningtabel._tbl
        eerste_tr  = woningtabel.rows[0]._tr
        n_cols     = len(woningtabel.columns)

        nieuwe_tr = OxmlElement('w:tr')
        nieuwe_tc = OxmlElement('w:tc')
        tcPr      = OxmlElement('w:tcPr')

        if n_cols > 1:
            gs = OxmlElement('w:gridSpan')
            gs.set(qn('w:val'), str(n_cols))
            tcPr.append(gs)

        shd = OxmlElement('w:shd')
        shd.set(qn('w:val'),   'clear')
        shd.set(qn('w:color'), 'auto')
        shd.set(qn('w:fill'),  TITELBLAUW)
        tcPr.append(shd)
        nieuwe_tc.append(tcPr)

        p = OxmlElement('w:p')
        r = OxmlElement('w:r')
        rPr = OxmlElement('w:rPr')
        rFonts = OxmlElement('w:rFonts')
        for attr in ('w:ascii', 'w:hAnsi', 'w:cs'):
            rFonts.set(qn(attr), 'Calibri')
        rPr.append(rFonts)
        for tag, waarde in [('w:b', None), ('w:color', 'FFFFFF'),
                             ('w:sz', '22'), ('w:szCs', '22')]:
            el = OxmlElement(tag)
            if waarde:
                el.set(qn('w:val'), waarde)
            rPr.append(el)
        r.append(rPr)
        t = OxmlElement('w:t')
        t.text = "Woninggegevens"
        r.append(t)
        p.append(r)
        nieuwe_tc.append(p)
        nieuwe_tr.append(nieuwe_tc)
        tbl.insert(list(tbl).index(eerste_tr), nieuwe_tr)

    # ── Stijl de datarijen ─────────────────────────────────────────────────────
    for rij in woningtabel.rows:
        if len(rij.cells) < 2:
            continue
        cel_links  = rij.cells[0]
        cel_rechts = rij.cells[1]
        label_l    = cel_links.text.strip().lower()

        if "woninggegevens" in label_l:
            continue  # kopregel — niet aanraken

        # Linkerkolom: wit + semi-bold
        _set_cel_achtergrond(cel_links, WIT)
        _borders(cel_links)
        for para in cel_links.paragraphs:
            for run in para.runs:
                _run_opmaak(run, bold=True, kleur=TEKST_RGB)

        # Rechterkolom: wit
        _set_cel_achtergrond(cel_rechts, WIT)
        _borders(cel_rechts)

        # Energielabel A-klasse → groen + vet
        is_label_rij = "energielabel" in label_l
        waarde_tekst = cel_rechts.text.strip().upper()
        for para in cel_rechts.paragraphs:
            for run in para.runs:
                if is_label_rij and waarde_tekst.startswith("A"):
                    _run_opmaak(run, bold=True, kleur=GROEN_RGB)
                else:
                    _run_opmaak(run, bold=False, kleur=TEKST_RGB)

    # ── Verwijder achtergrondkleur van paragrafen direct na de tabel ──────────
    tbl_elem = woningtabel._tbl
    parent   = tbl_elem.getparent()
    if parent is not None:
        kinderen  = list(parent)
        tbl_index = kinderen.index(tbl_elem)
        # Controleer de eerstvolgende alinea's (maximaal 3) na de tabel
        for elem in kinderen[tbl_index + 1: tbl_index + 4]:
            if elem.tag.endswith('}p'):
                pPr = elem.find(f'{W}pPr')
                if pPr is not None:
                    for shd in pPr.findall(f'{W}shd'):
                        pPr.remove(shd)

    doc.save(docx_pad)


def _voeg_element_teksten_in(docx_pad: str, data: dict, scores: dict | None = None) -> None:
    """
    Zoekt de scores-tabel (Dak/Gevel/Vloer/Glas) en voegt per element
    een subkop + beschrijvende tekst in direct ná de tabel.
    Herkent de teksten via de data-mapping die ook aan fill_docx is meegegeven.
    """
    try:
        from docx import Document
        from docx.oxml.ns import qn
        from docx.oxml import OxmlElement
    except ImportError:
        return

    ELEMENTEN = [
        ("Dak",   "{{element_tekst_dak}}",   "{{score_dak}}",   "{{score_dak_tekst}}"),
        ("Gevel", "{{element_tekst_gevel}}", "{{score_gevel}}", "{{score_gevel_tekst}}"),
        ("Vloer", "{{element_tekst_vloer}}", "{{score_vloer}}", "{{score_vloer_tekst}}"),
        ("Glas",  "{{element_tekst_glas}}",  "{{score_glas}}",  "{{score_glas_tekst}}"),
    ]

    invoegblokken = []
    for naam, tekst_key, score_key, label_key in ELEMENTEN:
        tekst = data.get(tekst_key, "").strip()
        score = data.get(score_key, "")
        label = data.get(label_key, "")
        if tekst:
            invoegblokken.append((naam, tekst, score, label))

    if not invoegblokken:
        return

    doc = Document(docx_pad)

    # Zoek scores-tabel: bevat "dak", "gevel", "vloer" of "glas" in eerste kolom
    HERKENNING = {"dak", "gevel", "vloer", "glas"}
    scoretabel = None
    for tabel in doc.tables:
        cel_teksten = {rij.cells[0].text.strip().lower() for rij in tabel.rows}
        if len(cel_teksten & HERKENNING) >= 2:
            scoretabel = tabel
            break

    if scoretabel is None:
        return

    tbl_elem = scoretabel._tbl
    parent   = tbl_elem.getparent()
    idx      = list(parent).index(tbl_elem)
    parent.remove(tbl_elem)  # scoretabel verwijderen

    def _maak_alinea(tekst: str, *, bold=False, pt_val="22", kleur_hex=None) -> etree._Element:
        p   = OxmlElement('w:p')
        pPr = OxmlElement('w:pPr')
        # Gebruik Normal-stijl zodat regelafstand en opmaak consistent zijn met de template
        pSt = OxmlElement('w:pStyle')
        pSt.set(qn('w:val'), 'Normal')
        pPr.append(pSt)
        spacing = OxmlElement('w:spacing')
        spacing.set(qn('w:before'), '0')
        spacing.set(qn('w:after'),  '160')
        pPr.append(spacing)
        p.append(pPr)

        r   = OxmlElement('w:r')
        rPr = OxmlElement('w:rPr')
        if bold:
            rPr.append(OxmlElement('w:b'))
        fonts = OxmlElement('w:rFonts')
        for attr in ('w:ascii', 'w:hAnsi', 'w:cs'):
            fonts.set(qn(attr), 'Calibri')
        rPr.append(fonts)
        sz = OxmlElement('w:sz');   sz.set(qn('w:val'), pt_val);   rPr.append(sz)
        szC = OxmlElement('w:szCs'); szC.set(qn('w:val'), pt_val); rPr.append(szC)
        if kleur_hex:
            kl = OxmlElement('w:color'); kl.set(qn('w:val'), kleur_hex); rPr.append(kl)
        r.append(rPr)

        t = OxmlElement('w:t')
        t.text = tekst
        t.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
        r.append(t)
        p.append(r)
        return p

    # Kleine witregel direct na de tabel
    parent.insert(idx, _maak_alinea(""))
    idx += 1

    for naam, tekst, score, label in invoegblokken:
        parent.insert(idx, _maak_alinea(naam, bold=True, pt_val="22", kleur_hex="5AAA00"))
        idx += 1
        if score and label:
            parent.insert(idx, _maak_alinea(f"Score {score}/5 — {label}", bold=True, pt_val="22"))
            idx += 1

        # Tekst (splits op dubbele newline voor aparte alinea's)
        for deel in tekst.split('\n\n'):
            deel = deel.strip()
            if deel:
                parent.insert(idx, _maak_alinea(deel, pt_val="22"))
                idx += 1

        # Witregel tussen elementen
        parent.insert(idx, _maak_alinea(""))
        idx += 1

    # Slottekst eenmalig onderaan het hoofdstuk
    if scores is not None:
        import sys, os as _os
        sys.path.insert(0, _os.path.dirname(__file__))
        from teksten_elementen import get_slottekst_kansen
        slottekst = get_slottekst_kansen(scores)
        for deel in slottekst.split('\n\n'):
            deel = deel.strip()
            if deel:
                parent.insert(idx, _maak_alinea(deel, pt_val="22"))
                idx += 1

    doc.save(docx_pad)


def _voeg_eindpagina_in(docx_pad: str, cta_primair: str | None = None, cta_url: str | None = None) -> None:
    """
    Vervangt de onopgemaakte PandIQ CTA-alinea's door een huisstijl eindpagina.
    Herkent de start aan 'regisseur in verduurzaming' in de tekst.
    """
    try:
        from docx import Document
        from docx.oxml.ns import qn
        from docx.oxml import OxmlElement
    except ImportError:
        return

    doc  = Document(docx_pad)
    body = doc.element.body
    kinderen = list(body)

    # ── Zoek startpunt van bestaande CTA-inhoud ───────────────────────────────
    start_elem = None
    for elem in kinderen:
        if elem.tag.endswith('}p'):
            text = ''.join(t.text or '' for t in elem.iter(f'{W}t')).lower()
            if 'regisseur in verduurzaming' in text:
                start_elem = elem
                break

    if start_elem is None:
        return

    start_idx = kinderen.index(start_elem)

    # Verwijder alles van startpunt t/m einde body (behalve w:sectPr)
    for elem in kinderen[start_idx:]:
        if elem.tag.endswith('}sectPr'):
            break
        body.remove(elem)

    # ── Hulpfuncties ──────────────────────────────────────────────────────────
    def _r(tekst, *, bold=False, italic=False, pt=11, kleur_hex):
        r = OxmlElement('w:r')
        rPr = OxmlElement('w:rPr')
        if bold:   rPr.append(OxmlElement('w:b'))
        if italic: rPr.append(OxmlElement('w:i'))
        fonts = OxmlElement('w:rFonts')
        for attr in ('w:ascii', 'w:hAnsi', 'w:cs'):
            fonts.set(qn(attr), 'Calibri')
        rPr.append(fonts)
        sz  = OxmlElement('w:sz');   sz.set(qn('w:val'), str(pt * 2));  rPr.append(sz)
        szC = OxmlElement('w:szCs'); szC.set(qn('w:val'), str(pt * 2)); rPr.append(szC)
        kl = OxmlElement('w:color'); kl.set(qn('w:val'), kleur_hex.upper()); rPr.append(kl)
        r.append(rPr)
        t = OxmlElement('w:t')
        t.text = tekst
        t.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
        r.append(t)
        return r

    def _p(space_before=0, space_after=160, bg_hex=None):
        p = OxmlElement('w:p')
        pPr = OxmlElement('w:pPr')
        sp = OxmlElement('w:spacing')
        sp.set(qn('w:before'), str(space_before))
        sp.set(qn('w:after'),  str(space_after))
        pPr.append(sp)
        if bg_hex:
            shd = OxmlElement('w:shd')
            shd.set(qn('w:val'), 'clear'); shd.set(qn('w:color'), 'auto')
            shd.set(qn('w:fill'), bg_hex.upper()); pPr.append(shd)
        p.append(pPr)
        return p

    def _tabel(bg_hex, hoogte, inhoud_fn, pad=(220, 320, 220, 320)):
        tbl = OxmlElement('w:tbl')
        tblPr = OxmlElement('w:tblPr')
        tblW = OxmlElement('w:tblW'); tblW.set(qn('w:w'), '5000'); tblW.set(qn('w:type'), 'pct')
        tblPr.append(tblW)
        tblBrd = OxmlElement('w:tblBorders')
        for kant in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
            el = OxmlElement(f'w:{kant}'); el.set(qn('w:val'), 'none'); tblBrd.append(el)
        tblPr.append(tblBrd)
        tbl.append(tblPr)
        tblGrid = OxmlElement('w:tblGrid')
        gc = OxmlElement('w:gridCol'); gc.set(qn('w:w'), '9026'); tblGrid.append(gc)
        tbl.append(tblGrid)
        tr = OxmlElement('w:tr')
        trPr = OxmlElement('w:trPr')
        trH = OxmlElement('w:trHeight'); trH.set(qn('w:val'), str(hoogte)); trH.set(qn('w:hRule'), 'atLeast')
        trPr.append(trH); tr.append(trPr)
        tc = OxmlElement('w:tc')
        tcPr = OxmlElement('w:tcPr')
        tcW = OxmlElement('w:tcW'); tcW.set(qn('w:w'), '5000'); tcW.set(qn('w:type'), 'pct')
        tcPr.append(tcW)
        shd = OxmlElement('w:shd'); shd.set(qn('w:val'), 'clear'); shd.set(qn('w:color'), 'auto')
        shd.set(qn('w:fill'), bg_hex.upper()); tcPr.append(shd)
        tcMar = OxmlElement('w:tcMar')
        for kant, val in zip(('top', 'left', 'bottom', 'right'), pad):
            el = OxmlElement(f'w:{kant}'); el.set(qn('w:w'), str(val)); el.set(qn('w:type'), 'dxa')
            tcMar.append(el)
        tcPr.append(tcMar); tc.append(tcPr)
        inhoud_fn(tc)
        tr.append(tc); tbl.append(tr)
        return tbl

    # ── Eindpagina opbouwen ───────────────────────────────────────────────────
    elems = []

    # Pagina-einde
    p_br = _p(space_before=0, space_after=0)
    r_br = OxmlElement('w:r')
    br = OxmlElement('w:br'); br.set(qn('w:type'), 'page')
    r_br.append(br); p_br.append(r_br)
    elems.append(p_br)

    # Logo-balk (donker, iets kleiner dan voorblad)
    def _logo(tc):
        p1 = _p(bg_hex="1A1A1A", space_before=0, space_after=60)
        p1.append(_r("Pand", bold=True, pt=22, kleur_hex="FFFFFF"))
        p1.append(_r("IQ",   bold=True, pt=22, kleur_hex="5AAA00"))
        tc.append(p1)
        p2 = _p(bg_hex="1A1A1A", space_before=0, space_after=0)
        p2.append(_r("WONEN", bold=True, pt=8, kleur_hex="5AAA00"))
        tc.append(p2)
    elems.append(_tabel("1A1A1A", 1100, _logo))

    # Limoen accent-streep
    def _accent(tc): tc.append(_p(bg_hex="D4E832"))
    elems.append(_tabel("D4E832", 80, _accent))

    # Witruimte
    elems.append(_p(space_before=400, space_after=0))

    # Hoofdtitel
    p = _p(space_before=0, space_after=100)
    p.append(_r("Uw regisseur in verduurzaming", bold=True, pt=22, kleur_hex="1A1A1A"))
    elems.append(p)

    # Intro tekst
    p = _p(space_before=0, space_after=200)
    p.append(_r(
        "Met de juiste keuzes haalt u meer uit uw woning en uw budget. "
        "Door maatregelen slim te combineren kan uw subsidie zelfs verdubbelen.",
        pt=11, kleur_hex="333333"
    ))
    elems.append(p)

    # Lichtgroen info-blok: PandIQ aanbod
    def _info(tc):
        p = _p(bg_hex="EEF6E0", space_before=0, space_after=0)
        p.append(_r(
            "PandIQ geeft u overzicht en helpt u met het inschatten van bouwkosten, "
            "het aanvragen van offertes, subsidieaanvragen en andere besparingen "
            "— alles in één dashboard.",
            pt=11, kleur_hex="1A4A00"
        ))
        tc.append(p)
    elems.append(_tabel("EEF6E0", 400, _info))

    # CTA-tekst
    elems.append(_p(space_before=200, space_after=0))
    p = _p(space_before=0, space_after=160)
    p.append(_r(
        "Maak een account aan en ontdek wat er mogelijk is. "
        "Het kost weinig moeite en levert vaak direct voordeel op.",
        pt=11, kleur_hex="333333"
    ))
    elems.append(p)

    # Groene slogan
    p = _p(space_before=80, space_after=280)
    p.append(_r(
        "Word geen slapende betaler, maar wees slim en bespaar.",
        bold=True, pt=13, kleur_hex="5AAA00"
    ))
    elems.append(p)

    # Limoen CTA-box: situatiegericht als advies beschikbaar, anders dashboard link
    _cta_label = cta_primair or "Bekijk uw mogelijkheden op pandiq.nl/dashboard"
    _cta_link  = cta_url or "pandiq.nl/dashboard"

    def _cta(tc):
        p = _p(bg_hex="D4E832", space_before=0, space_after=0)
        p.append(_r(_cta_label, bold=True, pt=11, kleur_hex="1A1A1A"))
        p.append(_r("  →", bold=True, pt=12, kleur_hex="1A1A1A"))
        tc.append(p)
        if cta_url:
            p2 = _p(bg_hex="D4E832", space_before=0, space_after=0)
            p2.append(_r(_cta_link, pt=9, kleur_hex="333333"))
            tc.append(p2)
    elems.append(_tabel("D4E832", 480, _cta, pad=(180, 320, 180, 320)))

    # Spacer voor disclaimer
    elems.append(_p(space_before=480, space_after=0))

    # Disclaimer
    p = _p(space_before=0, space_after=0)
    p.append(_r(
        "Disclaimer: dit rapport is indicatief en gebaseerd op registraties en aannames. "
        "Aan dit document kunnen geen rechten worden ontleend. "
        "Uitvoering vereist altijd verificatie op locatie en controle van actuele regelgeving.",
        italic=True, pt=9, kleur_hex="999999"
    ))
    elems.append(p)

    # ── Invoegen vóór w:sectPr ────────────────────────────────────────────────
    kinderen_na = list(body)
    insert_at = len(kinderen_na)
    for i, elem in enumerate(kinderen_na):
        if elem.tag.endswith('}sectPr'):
            insert_at = i
            break

    for i, elem in enumerate(elems):
        body.insert(insert_at + i, elem)

    doc.save(docx_pad)


def _stijl_voorblad(docx_pad: str, adres: str, datum: str) -> None:
    """
    Vervangt het bestaande voorblad door een PandIQ Wonen huisstijl-cover.
    Behoudt eventuele Street View afbeeldingen van het originele voorblad.
    Brand: #1a1a1a (donker), #5aaa00 (groen), #d4e832 (limoeneel).
    """
    try:
        from docx import Document
        from docx.oxml.ns import qn
        from docx.oxml import OxmlElement
    except ImportError:
        return

    doc  = Document(docx_pad)
    body = doc.element.body

    # ── Zoek eerste Heading-alinea ─────────────────────────────────────────────
    eerste_heading = None
    for elem in list(body):
        if elem.tag.endswith('}p'):
            pPr = elem.find(f'{W}pPr')
            if pPr is not None:
                pStyle = pPr.find(f'{W}pStyle')
                if pStyle is not None:
                    val = pStyle.get(f'{W}val', '').lower()
                    if 'heading' in val or 'kop' in val:
                        eerste_heading = elem
                        break

    if eerste_heading is None:
        return

    kinderen = list(body)
    stop = kinderen.index(eerste_heading)

    # ── Bewaar eventuele afbeeldingen van het originele voorblad ──────────────
    foto_paras = []
    for elem in kinderen[:stop]:
        if elem.tag.endswith('}p') and list(elem.iter(f'{W}drawing')):
            foto_paras.append(elem)

    # ── Verwijder bestaand voorblad ────────────────────────────────────────────
    for elem in kinderen[:stop]:
        body.remove(elem)

    # ── Hulpfuncties ───────────────────────────────────────────────────────────
    def _run_el(tekst, *, bold=False, pt=11, kleur_hex, char_spacing=None):
        r = OxmlElement('w:r')
        rPr = OxmlElement('w:rPr')
        if bold:
            rPr.append(OxmlElement('w:b'))
        fonts = OxmlElement('w:rFonts')
        for attr in ('w:ascii', 'w:hAnsi', 'w:cs'):
            fonts.set(qn(attr), 'Calibri')
        rPr.append(fonts)
        sz  = OxmlElement('w:sz');   sz.set(qn('w:val'), str(pt * 2));  rPr.append(sz)
        szC = OxmlElement('w:szCs'); szC.set(qn('w:val'), str(pt * 2)); rPr.append(szC)
        kl = OxmlElement('w:color'); kl.set(qn('w:val'), kleur_hex.upper()); rPr.append(kl)
        if char_spacing is not None:
            sp_cs = OxmlElement('w:spacing'); sp_cs.set(qn('w:val'), str(char_spacing)); rPr.append(sp_cs)
        r.append(rPr)
        t = OxmlElement('w:t')
        t.text = tekst
        t.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
        r.append(t)
        return r

    def _p_el(space_before=0, space_after=0, bg_hex=None, align=None):
        p = OxmlElement('w:p')
        pPr = OxmlElement('w:pPr')
        sp = OxmlElement('w:spacing')
        sp.set(qn('w:before'), str(space_before))
        sp.set(qn('w:after'),  str(space_after))
        pPr.append(sp)
        if align:
            jc = OxmlElement('w:jc'); jc.set(qn('w:val'), align); pPr.append(jc)
        if bg_hex:
            shd = OxmlElement('w:shd')
            shd.set(qn('w:val'), 'clear'); shd.set(qn('w:color'), 'auto')
            shd.set(qn('w:fill'), bg_hex.upper()); pPr.append(shd)
        p.append(pPr)
        return p

    def _tabel_balk(bg_hex, hoogte, inhoud_fn):
        """Volledige breedte tabel (100% paginabreedte) met één cel."""
        tbl = OxmlElement('w:tbl')

        tblPr = OxmlElement('w:tblPr')
        tblW = OxmlElement('w:tblW'); tblW.set(qn('w:w'), '5000'); tblW.set(qn('w:type'), 'pct')
        tblPr.append(tblW)
        tblBrd = OxmlElement('w:tblBorders')
        for kant in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
            el = OxmlElement(f'w:{kant}'); el.set(qn('w:val'), 'none'); tblBrd.append(el)
        tblPr.append(tblBrd)
        tbl.append(tblPr)

        tblGrid = OxmlElement('w:tblGrid')
        gc = OxmlElement('w:gridCol'); gc.set(qn('w:w'), '9026'); tblGrid.append(gc)
        tbl.append(tblGrid)

        tr = OxmlElement('w:tr')
        trPr = OxmlElement('w:trPr')
        trH = OxmlElement('w:trHeight')
        trH.set(qn('w:val'), str(hoogte)); trH.set(qn('w:hRule'), 'atLeast')
        trPr.append(trH); tr.append(trPr)

        tc = OxmlElement('w:tc')
        tcPr = OxmlElement('w:tcPr')
        tcW = OxmlElement('w:tcW'); tcW.set(qn('w:w'), '5000'); tcW.set(qn('w:type'), 'pct')
        tcPr.append(tcW)
        shd = OxmlElement('w:shd'); shd.set(qn('w:val'), 'clear'); shd.set(qn('w:color'), 'auto')
        shd.set(qn('w:fill'), bg_hex.upper()); tcPr.append(shd)
        tcMar = OxmlElement('w:tcMar')
        for kant, val in [('top', 240), ('left', 360), ('bottom', 240), ('right', 360)]:
            el = OxmlElement(f'w:{kant}'); el.set(qn('w:w'), str(val)); el.set(qn('w:type'), 'dxa')
            tcMar.append(el)
        tcPr.append(tcMar); tc.append(tcPr)

        inhoud_fn(tc)
        tr.append(tc); tbl.append(tr)
        return tbl

    # ── Cover-elementen opbouwen ────────────────────────────────────────────────

    cover = []

    # 1. Logo-balk (donker #1a1a1a)
    def _logo_inhoud(tc):
        p1 = _p_el(bg_hex="1A1A1A", space_before=0, space_after=80)
        p1.append(_run_el("Pand", bold=True, pt=30, kleur_hex="FFFFFF"))
        p1.append(_run_el("IQ",   bold=True, pt=30, kleur_hex="5AAA00"))
        tc.append(p1)
        p2 = _p_el(bg_hex="1A1A1A", space_before=0, space_after=0)
        p2.append(_run_el("WONEN", bold=True, pt=9, kleur_hex="5AAA00", char_spacing=40))
        tc.append(p2)

    cover.append(_tabel_balk("1A1A1A", 1600, _logo_inhoud))

    # 2. Limoen accent-streep (#d4e832)
    def _accent_inhoud(tc):
        tc.append(_p_el(bg_hex="D4E832"))

    cover.append(_tabel_balk("D4E832", 100, _accent_inhoud))

    # 3. Witruimte vóór titel
    cover.append(_p_el(space_before=600))

    # 4. Rapporttitel
    p = _p_el(space_before=0, space_after=120)
    p.append(_run_el("Isolatie Quickscan", bold=True, pt=32, kleur_hex="1A1A1A"))
    cover.append(p)

    # 5. Ondertitel
    p = _p_el(space_before=0, space_after=0)
    p.append(_run_el("Energierapport verduurzaming", pt=13, kleur_hex="666666"))
    cover.append(p)

    # 6. Spacer
    cover.append(_p_el(space_before=640))

    # 7. Adres (vet)
    p = _p_el(space_before=0, space_after=80)
    p.append(_run_el(adres, bold=True, pt=14, kleur_hex="1A1A1A"))
    cover.append(p)

    # 8. Datum
    p = _p_el(space_before=0, space_after=0)
    p.append(_run_el(datum, pt=11, kleur_hex="666666"))
    cover.append(p)

    # 9. Bewaard Street View foto (indien aanwezig in origineel voorblad)
    if foto_paras:
        cover.append(_p_el(space_before=240))
        for foto_p in foto_paras:
            pPr = foto_p.find(f'{W}pPr')
            if pPr is None:
                pPr = OxmlElement('w:pPr')
                foto_p.insert(0, pPr)
            for old_sp in pPr.findall(f'{W}spacing'):
                pPr.remove(old_sp)
            sp = OxmlElement('w:spacing')
            sp.set(qn('w:before'), '0'); sp.set(qn('w:after'), '0')
            pPr.append(sp)
            cover.append(foto_p)

    # 10. Grote spacer richting onderkant pagina
    cover.append(_p_el(space_before=800))

    # 11. Tagline onderaan
    p = _p_el(space_before=0, space_after=0)
    p.append(_run_el(
        "Indicatief rapport op basis van openbare registraties (BAG & EP-Online)",
        pt=9, kleur_hex="999999"
    ))
    cover.append(p)

    # 12. Pagina-einde vóór hoofdstuk 1
    p_br = _p_el(space_before=0, space_after=0)
    r_br = OxmlElement('w:r')
    br = OxmlElement('w:br'); br.set(qn('w:type'), 'page')
    r_br.append(br); p_br.append(r_br)
    cover.append(p_br)

    # ── Invoegen vóór de eerste heading ─────────────────────────────────────────
    for i, elem in enumerate(cover):
        body.insert(i, elem)

    # ── Koptekst: leeg op voorblad, huisstijl op overige pagina's ────────────
    section = doc.sections[0]
    section.different_first_page_header_footer = True

    # Eerste pagina: volledig lege koptekst
    fph_elem = section.first_page_header._element
    for child in list(fph_elem):
        fph_elem.remove(child)
    fph_elem.append(_p_el())

    # Standaard koptekst herbouwen met PandIQ Wonen huisstijl
    hdr_elem = section.header._element
    for child in list(hdr_elem):
        hdr_elem.remove(child)

    # Tabel: logo links | rapporttitel rechts
    tbl_kop = OxmlElement('w:tbl')
    tblPr_kop = OxmlElement('w:tblPr')
    tblW_kop = OxmlElement('w:tblW')
    tblW_kop.set(qn('w:w'), '9026'); tblW_kop.set(qn('w:type'), 'dxa')
    tblPr_kop.append(tblW_kop)
    # Alleen onderrand: limoen accent-streep
    tblBrd = OxmlElement('w:tblBorders')
    for kant in ('top', 'left', 'right', 'insideH', 'insideV'):
        el = OxmlElement(f'w:{kant}')
        el.set(qn('w:val'), 'none'); el.set(qn('w:sz'), '0')
        el.set(qn('w:space'), '0'); el.set(qn('w:color'), 'FFFFFF')
        tblBrd.append(el)
    btm = OxmlElement('w:bottom')
    btm.set(qn('w:val'), 'single'); btm.set(qn('w:sz'), '6')
    btm.set(qn('w:space'), '0'); btm.set(qn('w:color'), 'D4E832')
    tblBrd.append(btm)
    tblPr_kop.append(tblBrd)
    tcMar_kop = OxmlElement('w:tblCellMar')
    for kant in ('left', 'right'):
        el = OxmlElement(f'w:{kant}'); el.set(qn('w:w'), '10'); el.set(qn('w:type'), 'dxa')
        tcMar_kop.append(el)
    tblPr_kop.append(tcMar_kop)
    tbl_kop.append(tblPr_kop)

    tblGrid_kop = OxmlElement('w:tblGrid')
    for w in ('4513', '4513'):
        gc = OxmlElement('w:gridCol'); gc.set(qn('w:w'), w); tblGrid_kop.append(gc)
    tbl_kop.append(tblGrid_kop)

    tr_kop = OxmlElement('w:tr')

    def _kop_cel(breedte, align=None):
        tc = OxmlElement('w:tc')
        tcPr = OxmlElement('w:tcPr')
        tcW = OxmlElement('w:tcW'); tcW.set(qn('w:w'), str(breedte)); tcW.set(qn('w:type'), 'dxa')
        tcPr.append(tcW)
        tcBrd = OxmlElement('w:tcBorders')
        for kant in ('top', 'left', 'bottom', 'right'):
            el = OxmlElement(f'w:{kant}'); el.set(qn('w:val'), 'none')
            el.set(qn('w:sz'), '0'); el.set(qn('w:space'), '0'); el.set(qn('w:color'), 'FFFFFF')
            tcBrd.append(el)
        tcPr.append(tcBrd)
        va = OxmlElement('w:vAlign'); va.set(qn('w:val'), 'center'); tcPr.append(va)
        tc.append(tcPr)
        p = _p_el(space_before=0, space_after=0)
        if align:
            jc = OxmlElement('w:jc'); jc.set(qn('w:val'), align)
            p.find(f'{W}pPr').append(jc)
        return tc, p

    # Links: "PandIQ Wonen"
    tc_l, p_l = _kop_cel(4513)
    p_l.append(_run_el("Pand",   bold=True,  pt=14, kleur_hex="1A1A1A"))
    p_l.append(_run_el("IQ",     bold=True,  pt=14, kleur_hex="5AAA00"))
    p_l.append(_run_el(" Wonen", bold=False, pt=9,  kleur_hex="5AAA00"))
    tc_l.append(p_l)
    tr_kop.append(tc_l)

    # Rechts: "Isolatie Quickscan"
    tc_r, p_r = _kop_cel(4513, align='right')
    p_r.append(_run_el("Isolatie Quickscan", pt=9, kleur_hex="666666"))
    tc_r.append(p_r)
    tr_kop.append(tc_r)

    tbl_kop.append(tr_kop)
    hdr_elem.append(tbl_kop)

    # Kleine witruimte na de tabel in de koptekst
    p_na = _p_el(space_before=60, space_after=60)
    hdr_elem.append(p_na)

    doc.save(docx_pad)


def _vervang_aanpak_sectie(docx_pad: str, advies) -> None:
    """
    Verwijdert de hardcoded 'Mogelijke aanpak' sectie (isolatietrias +
    lege alinea's + gevulde {{narrative_aanpak}}) en vervangt die door
    opgemaakte prioriteitenblokken op basis van AdviesResult.
    """
    try:
        from docx import Document
        from docx.oxml.ns import qn
        from docx.oxml import OxmlElement
    except ImportError:
        return

    if not advies:
        return

    doc  = Document(docx_pad)
    body = doc.element.body
    kinderen = list(body)

    # Zoek "Mogelijke aanpak" alinea als startpunt
    start_elem = None
    for elem in kinderen:
        if elem.tag.endswith('}p'):
            tekst = ''.join(t.text or '' for t in elem.iter(f'{W}t')).strip()
            if tekst == 'Mogelijke aanpak':
                start_elem = elem
                break

    if start_elem is None:
        return

    start_idx = kinderen.index(start_elem)

    # Zoek eerstvolgende Heading-alinea na start als eindgrens
    einde_idx = None
    for i, elem in enumerate(kinderen[start_idx + 1:], start_idx + 1):
        if elem.tag.endswith('}p'):
            pPr = elem.find(f'{W}pPr')
            if pPr is not None:
                pStyle = pPr.find(f'{W}pStyle')
                if pStyle is not None:
                    val = pStyle.get(f'{W}val', '').lower()
                    if 'heading' in val or 'kop' in val or val == '1':
                        einde_idx = i
                        break

    if einde_idx is None:
        return

    # Verwijder alles van start t/m einde-1 (de heading zelf blijft staan)
    te_verwijderen = list(kinderen[start_idx:einde_idx])
    invoeg_positie = start_idx
    for elem in te_verwijderen:
        body.remove(elem)

    # ── Bouw hulpfunctie voor alinea's ────────────────────────────────────────
    def _p(tekst='', *, bold=False, kleur='1D1D1B', pt='22', space_after=120):
        p   = OxmlElement('w:p')
        pPr = OxmlElement('w:pPr')
        pSt = OxmlElement('w:pStyle'); pSt.set(qn('w:val'), 'Normal'); pPr.append(pSt)
        sp  = OxmlElement('w:spacing')
        sp.set(qn('w:before'), '0'); sp.set(qn('w:after'), str(space_after))
        pPr.append(sp); p.append(pPr)
        if tekst:
            r   = OxmlElement('w:r')
            rPr = OxmlElement('w:rPr')
            if bold: rPr.append(OxmlElement('w:b'))
            f = OxmlElement('w:rFonts')
            for attr in ('w:ascii', 'w:hAnsi', 'w:cs'): f.set(qn(attr), 'Calibri')
            rPr.append(f)
            sz = OxmlElement('w:sz');   sz.set(qn('w:val'), pt);  rPr.append(sz)
            sc = OxmlElement('w:szCs'); sc.set(qn('w:val'), pt);  rPr.append(sc)
            kl = OxmlElement('w:color'); kl.set(qn('w:val'), kleur.upper()); rPr.append(kl)
            r.append(rPr)
            t = OxmlElement('w:t'); t.text = tekst
            t.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
            r.append(t); p.append(r)
        return p

    # ── Bouw nieuwe inhoud ────────────────────────────────────────────────────
    elems: list = []

    # Sectietitel (vervangt de verwijderde "Mogelijke aanpak" header)
    elems.append(_p('', space_after=200))

    hoge  = [item for item in advies.prioriteiten if item.score >= 3]
    lage  = [item for item in advies.prioriteiten if item.score < 3]
    urg_labels = {'hoog': 'Hoge urgentie', 'middel': 'Gemiddelde prioriteit', 'laag': 'Lage prioriteit'}

    if hoge:
        for rang, item in enumerate(hoge, 1):
            urg = urg_labels.get(item.urgentie, item.urgentie)
            elems.append(_p(
                f'{rang}. {item.element_naam}  \u2014  score {item.score}/5  \u2014  {urg}',
                bold=True, kleur='5AAA00', pt='22', space_after=60
            ))
            elems.append(_p(f'Aanbevolen maatregel: {item.maatregel_naam}', kleur='1D1D1B', space_after=60))
            if item.opp_indicatief > 0:
                elems.append(_p(f'Geschatte oppervlakte: ca. {item.opp_indicatief:.0f} m\u00b2', kleur='666666', space_after=60))
            if item.besparing_max > 0:
                elems.append(_p(
                    f'Indicatieve besparing: \u20ac{item.besparing_min:,.0f}\u2013\u20ac{item.besparing_max:,.0f} per jaar',
                    kleur='1D1D1B', space_after=60
                ))
            if item.kosten_max > 0:
                elems.append(_p(
                    f'Indicatieve investering: \u20ac{item.kosten_min:,.0f}\u2013\u20ac{item.kosten_max:,.0f}',
                    kleur='1D1D1B', space_after=60
                ))
            if item.subsidie_max > 0:
                elems.append(_p(
                    f'ISDE-subsidie indicatie: tot \u20ac{item.subsidie_max:,.0f}',
                    kleur='2E7D32', space_after=60
                ))
            tvt_space = 200 if rang < len(hoge) else 160
            if item.terugverdien_min is not None and item.terugverdien_max is not None:
                elems.append(_p(
                    f'Terugverdientijd na subsidie: ca. {item.terugverdien_min:.0f}\u2013{item.terugverdien_max:.0f} jaar',
                    kleur='1D1D1B', space_after=tvt_space
                ))
            else:
                elems.append(_p('', space_after=tvt_space))
    else:
        # Goede woning: geen isolatieprioriteiten
        elems.append(_p(
            'De gebouwschil is op orde. De meeste winst zit in het optimaliseren van '
            'installaties: ventilatie, verwarming en eventuele duurzame opwek.',
            kleur='1D1D1B', space_after=160
        ))

    # Score 1–2: korte positieve noot
    for item in lage:
        elems.append(_p(
            f'{item.element_naam} (score {item.score}/5) \u2014 dit onderdeel is goed op orde.',
            kleur='2E7D32', space_after=80
        ))
    if lage:
        elems.append(_p('', space_after=80))

    # Basis totstandkoming
    elems.append(_p(
        'Basis totstandkoming van dit rapport',
        bold=True, kleur='1D1D1B', pt='24', space_after=80,
    ))
    elems.append(_p(
        'Financiële indicaties zijn schattingen op basis van bouwjaar en gemiddelde '
        'woningkenmerken. Definitieve bedragen hangen af van de werkelijke situatie ter plaatse.',
        kleur='555555', pt='20', space_after=60,
    ))
    elems.append(_p(
        'Berekend op basis van woningtype, bouwjaar en isolatiewaarden per bouwperiode '
        '(ISSO 82.1, NEN 1068). Alle bedragen zijn indicatief.',
        kleur='555555', pt='20', space_after=160,
    ))

    # Invoegen op de vrijgekomen positie
    for i, elem in enumerate(elems):
        body.insert(invoeg_positie + i, elem)

    doc.save(docx_pad)


def _voeg_fysische_analyse_in(docx_pad: str, advies) -> None:
    """
    Injecteert de bouwfysische analyse (oppervlaktes, besparing, TVT per element)
    en waarschuwingen als gestileerde Word-alinea's, direct na de 'Aanbevolen
    maatregelen' sectie. Vereist geen placeholder in de template.
    """
    if not advies:
        return

    try:
        from docx import Document
        from docx.oxml.ns import qn
        from docx.oxml import OxmlElement
    except ImportError:
        return

    from aannames import rc_oud as _rc_oud, get as _aanname
    from financials import (
        warmteverlies_reductie, terugverdientijd_uitgebreid,
        bereken_kosten, bereken_subsidie_indicatie, bereken_besparing_glas,
    )

    doc  = Document(docx_pad)
    body = doc.element.body

    # ── Zoek anker: laatste alinea van _vervang_aanpak_sectie ─────────────────
    # Die eindigt altijd met de financiële-indicaties-disclaimer.
    anker = None
    for elem in list(body):
        if elem.tag.endswith('}p'):
            tekst = ''.join(t.text or '' for t in elem.iter(f'{W}t')).lower()
            if 'financi' in tekst and 'indicaties' in tekst and 'schattingen' in tekst:
                anker = elem

    # Fallback: zoek eerste heading die 'subsidie' bevat
    if anker is None:
        for elem in list(body):
            if elem.tag.endswith('}p'):
                pPr = elem.find(f'{W}pPr')
                if pPr is not None:
                    pStyle = pPr.find(f'{W}pStyle')
                    if pStyle is not None:
                        val = pStyle.get(f'{W}val', '').lower()
                        if 'heading' in val or 'kop' in val:
                            tekst = ''.join(t.text or '' for t in elem.iter(f'{W}t')).lower()
                            if 'subsidie' in tekst:
                                anker = elem
                                break

    if anker is None:
        return

    invoeg_idx = list(body).index(anker) + 1

    # ── Hulpfunctie voor alinea's ─────────────────────────────────────────────
    def _p(tekst='', *, bold=False, italic=False, kleur='1D1D1B', pt='22', space_after=120):
        p   = OxmlElement('w:p')
        pPr = OxmlElement('w:pPr')
        pSt = OxmlElement('w:pStyle'); pSt.set(qn('w:val'), 'Normal'); pPr.append(pSt)
        sp  = OxmlElement('w:spacing')
        sp.set(qn('w:before'), '0'); sp.set(qn('w:after'), str(space_after))
        pPr.append(sp); p.append(pPr)
        if tekst:
            r   = OxmlElement('w:r')
            rPr = OxmlElement('w:rPr')
            if bold:   rPr.append(OxmlElement('w:b'))
            if italic: rPr.append(OxmlElement('w:i'))
            f = OxmlElement('w:rFonts')
            for attr in ('w:ascii', 'w:hAnsi', 'w:cs'): f.set(qn(attr), 'Calibri')
            rPr.append(f)
            sz  = OxmlElement('w:sz');   sz.set(qn('w:val'), pt);  rPr.append(sz)
            szC = OxmlElement('w:szCs'); szC.set(qn('w:val'), pt); rPr.append(szC)
            kl  = OxmlElement('w:color'); kl.set(qn('w:val'), kleur.upper()); rPr.append(kl)
            r.append(rPr)
            t = OxmlElement('w:t'); t.text = tekst
            t.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
            r.append(t); p.append(r)
        return p

    elems: list = []

    # ── Sectietitel ───────────────────────────────────────────────────────────
    elems.append(_p('', space_after=200))
    elems.append(_p(
        'Berekend op basis van woningtype, bouwjaar en isolatiewaarden per bouwperiode '
        '(ISSO 82.1, NEN 1068). Alle bedragen zijn indicatief.',
        italic=True, kleur='666666', pt='20', space_after=200,
    ))

    # ── Per bouwdeel ──────────────────────────────────────────────────────────
    RC_NIEUW = {
        "dak":   _aanname("rc_eis_dak"),
        "vloer": _aanname("rc_eis_vloer"),
        "gevel": _aanname("rc_eis_gevel"),
        "spouw": _aanname("rc_eis_spouw"),
    }
    MAATREGEL_KEY = {
        "dak":   "dakisolatie",
        "vloer": "vloer",
        "gevel": "gevel",
        "spouw": "spouwmuur",
    }
    ELEMENT_NAAM = {
        "dak":   "Dak",
        "vloer": "Vloer",
        "gevel": "Gevelisolatie (buiten/binnen)",
        "spouw": "Spouwmuurisolatie",
    }

    oppervlaktes = advies.oppervlaktes or {}
    bouwjaar     = advies.bouwjaar

    for el in ("dak", "vloer", "spouw", "gevel"):
        opp_info    = oppervlaktes.get(el, {})
        opp_m2      = opp_info.get("opp_m2", 0.0)      if isinstance(opp_info, dict) else 0.0
        toelichting = opp_info.get("toelichting", "")   if isinstance(opp_info, dict) else ""

        rc_info   = _rc_oud(el, bouwjaar)
        rc_huidig = rc_info["rc"]
        rc_doel   = RC_NIEUW[el]
        naam      = ELEMENT_NAAM[el]

        elems.append(_p(
            naam,
            bold=True, kleur='5AAA00', pt='22', space_after=20,
        ))
        elems.append(_p(
            f'Aanname huidige situatie: {rc_info["toelichting"]}',
            kleur='888888', pt='20', space_after=40,
        ))

        if opp_m2 == 0.0:
            elems.append(_p(
                'Niet van toepassing voor dit woningtype.',
                italic=True, kleur='888888', pt='20', space_after=160,
            ))
            continue

        if rc_huidig >= rc_doel:
            elems.append(_p(
                f'Je Rc-waarde is {rc_huidig} m\u00b2K/W en voldoet aan de ISDE-eis '
                f'en komt hierom niet in aanmerking voor subsidie.',
                kleur='2E7D32', pt='20', space_after=60,
            ))
            elems.append(_p('', space_after=160))
            continue

        if toelichting:
            elems.append(_p(toelichting, italic=True, kleur='888888', pt='20', space_after=20))
        elems.append(_p(
            f'Huidige Rc: {rc_huidig} m\u00b2K/W',
            kleur='555555', pt='20', space_after=20,
        ))
        elems.append(_p(
            f'Streefwaarde Rc: {rc_doel} m\u00b2K/W (ISDE-minimumeis)',
            kleur='555555', pt='20', space_after=160,
        ))

    # Glas: toon alleen technische situatie
    from aannames import u_oud_glas as _u_oud_glas
    glas_info = oppervlaktes.get("glas", {})
    glas_opp  = glas_info.get("opp_m2", 0.0) if isinstance(glas_info, dict) else 0.0
    if glas_opp > 0:
        u_info = _u_oud_glas(bouwjaar)
        elems.append(_p('Glas', bold=True, kleur='5AAA00', pt='22', space_after=20))
        elems.append(_p(
            f'Aanname huidige situatie: {u_info.get("toelichting", "")}',
            kleur='888888', pt='20', space_after=40,
        ))
        glas_toel = glas_info.get("toelichting", "") if isinstance(glas_info, dict) else ""
        if glas_toel:
            elems.append(_p(glas_toel, italic=True, kleur='888888', pt='20', space_after=160))

    # ── Aandachtspunten / waarschuwingen ──────────────────────────────────────
    waarschuwingen = advies.waarschuwingen or []
    if waarschuwingen:
        elems.append(_p('', space_after=160))

        NIVEAU_KLEUR = {"info": "2E7D32", "let_op": "E65100", "risico": "B71C1C"}
        NIVEAU_LABEL = {"info": "Info", "let_op": "Let op", "risico": "Aandachtspunt"}

        for w in waarschuwingen:
            kleur = NIVEAU_KLEUR.get(w["niveau"], "555555")
            label = NIVEAU_LABEL.get(w["niveau"], w["niveau"].capitalize())
            elems.append(_p(
                f'{label} ({w["element"]}): {w["bericht"]}',
                bold=(w["niveau"] == "risico"),
                kleur=kleur, pt='20', space_after=60,
            ))
            elems.append(_p(
                f'  \u2192 {w["aanbeveling"]}',
                italic=True, kleur='555555', pt='20', space_after=120,
            ))

    # ── Invoegen op berekende positie ─────────────────────────────────────────
    for i, elem in enumerate(elems):
        body.insert(invoeg_idx + i, elem)

    doc.save(docx_pad)


def _verwijder_score_tabel(docx_pad: str) -> None:
    """
    Verwijdert de scores-tabel (Dak/Gevel/Vloer/Glas) en omliggende
    lege alinea's uit het document zodat er geen grote witruimte overblijft.
    """
    from docx import Document
    from docx.oxml.ns import qn as _qn
    doc = Document(docx_pad)
    HERKENNING = {"dak", "gevel", "vloer", "glas"}
    tabel_gevonden = None
    for tabel in doc.tables:
        cel_teksten = {rij.cells[0].text.strip().lower() for rij in tabel.rows}
        if len(cel_teksten & HERKENNING) >= 2:
            tabel_gevonden = tabel
            break
    if tabel_gevonden is None:
        doc.save(docx_pad)
        return

    tbl_elem = tabel_gevonden._tbl
    parent   = tbl_elem.getparent()
    kinderen = list(parent)
    idx      = kinderen.index(tbl_elem)

    # Verwijder lege alinea's direct vóór de tabel (max 5)
    voor = idx - 1
    verwijderd = 0
    while voor >= 0 and verwijderd < 5:
        elem = kinderen[voor]
        if elem.tag == _qn('w:p') and not elem.text_content().strip() if hasattr(elem, 'text_content') else elem.tag == _qn('w:p') and not ''.join(r.text or '' for r in elem.iter(_qn('w:t'))).strip():
            parent.remove(elem)
            kinderen = list(parent)
            idx = kinderen.index(tbl_elem)
            voor = idx - 1
            verwijderd += 1
        else:
            break

    # Verwijder de tabel zelf
    parent.remove(tbl_elem)
    kinderen = list(parent)

    # Verwijder lege alinea's direct ná de (verwijderde) tabelpositie (max 5)
    na = idx
    verwijderd = 0
    while na < len(kinderen) and verwijderd < 5:
        elem = kinderen[na]
        if elem.tag == _qn('w:p') and not ''.join(r.text or '' for r in elem.iter(_qn('w:t'))).strip():
            parent.remove(elem)
            kinderen = list(parent)
            verwijderd += 1
        else:
            break

    doc.save(docx_pad)


def fill_docx(template_path: str, output_path: str, data: dict, sv_foto_pad: str | None = None, bouwjaar: int | None = None, scores: dict | None = None, advies=None):
    """
    Vult alle {{plaatshouders}} in en voegt optioneel een Street View foto in.
    Als sv_foto_pad None is of het invoegen mislukt, gaat het rapport gewoon door zonder foto.
    """
    # Bouw mapping: ook varianten met spaties meenemen
    import re as _re
    expanded = {}
    for k, v in data.items():
        expanded[k] = v
        stripped = k.replace('{{ ', '{{').replace(' }}', '}}')
        if stripped != k:
            expanded[stripped] = v
        spaced = k.replace('{{', '{{ ').replace('}}', ' }}')
        if spaced != k:
            expanded[spaced] = v

    # Vervang de subsidies-waarde door een sentinel; de echte tabel
    # wordt na het opslaan ingevoegd via python-docx (_voeg_subsidietabel_in).
    for k in list(expanded.keys()):
        if _re.fullmatch(r'\{\{[\s]*subsidies[\s]*\}\}', k):
            expanded[k] = _SUBSIDIE_SENTINEL

    import tempfile
    tmp_dir = Path(tempfile.mkdtemp())

    try:
        # Uitpakken
        with zipfile.ZipFile(template_path, 'r') as zin:
            zin.extractall(tmp_dir)

        # Plaatshouders vervangen in alle word/*.xml bestanden
        for xml_bestand in (tmp_dir / "word").glob("*.xml"):
            raw = xml_bestand.read_bytes()
            nieuw = fill_xml(raw, expanded)
            xml_bestand.write_bytes(nieuw)

        # Street View foto invoegen als beschikbaar
        if sv_foto_pad and Path(sv_foto_pad).exists():
            _voeg_foto_in_docx_toe(tmp_dir, sv_foto_pad)
        elif sv_foto_pad is None:
            # Geen foto beschikbaar — {{streetview}} placeholder stilletjes verwijderen
            doc_pad = tmp_dir / "word" / "document.xml"
            doc = doc_pad.read_text(encoding="utf-8")
            import re
            doc = re.sub(
                r'<w:p\b[^>]*>(?:(?!<w:p\b).)*\{\{streetview\}\}(?:(?!<w:p\b).)*</w:p>',
                '',
                doc,
                flags=re.DOTALL
            )
            doc_pad.write_text(doc, encoding="utf-8")

        # Inpakken naar output
        tmp_zip = output_path + '.tmp.docx'
        with zipfile.ZipFile(tmp_zip, 'w', zipfile.ZIP_DEFLATED) as zout:
            for bestand in tmp_dir.rglob('*'):
                if bestand.is_file():
                    zout.write(bestand, bestand.relative_to(tmp_dir))

        os.replace(tmp_zip, output_path)
        if bouwjaar is not None:
            # Persoonlijk indicatief subsidietotaal als eerste noot in de tabel
            sub_indicatie = ""
            if advies and advies.subsidie_totaal_indicatie > 0:
                sub_indicatie = (
                    f"Indicatief ISDE-subsidietotaal voor uw woning: "
                    f"tot \u20ac{advies.subsidie_totaal_indicatie:,.0f} "
                    f"({'meervoudig' if advies.meervoudig_tarief else 'enkelvoudig'} tarief 2026, "
                    f"op basis van geschatte oppervlaktes)"
                )
            _voeg_subsidietabel_bouwperiode_in(output_path, bouwjaar, subsidie_indicatie=sub_indicatie)
        _stijl_woninggegevens_tabel(output_path)
        _verwijder_score_tabel(output_path)
        if advies:
            _vervang_aanpak_sectie(output_path, advies)
            _voeg_fysische_analyse_in(output_path, advies)
        else:
            _voeg_element_teksten_in(output_path, expanded, scores=scores)
        adres_str = expanded.get("{{adres}}", "")
        datum_str = expanded.get("{{datum}}", "")
        _stijl_voorblad(output_path, adres_str, datum_str)
        _voeg_eindpagina_in(
            output_path,
            cta_primair=advies.cta_primair if advies else None,
            cta_url=advies.cta_url if advies else None,
        )
        print(f"OK: Opgeslagen: {output_path}")

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
