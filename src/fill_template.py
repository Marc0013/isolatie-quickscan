from __future__ import annotations
import os, zipfile, shutil
from lxml import etree
from pathlib import Path

NS = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
W  = f'{{{NS}}}'

# ── Subsidietabel configuratie ────────────────────────────────────────────────
_SUBSIDIE_SENTINEL = "##PANDIQ_SUBSIDIETABEL##"
_NAVY_HEX   = "2F6FA3"   # titelbalk blauw (consistent met woningtabel)
_YELLOW_HEX = "FFFFFF"   # aanbevolen rij — wit (geen gele achtergrond)
_GREEN_BG   = "FFFFFF"   # warmtepomp blok — wit
_GREEN_HEAD = "2F6FA3"   # warmtepomp header — zelfde titelblauw
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


def _cel_tekst(cel, tekst: str, *, bold=False, size=9, kleur=None, italic=False):
    """Zet tekst in een cel met opmaak. Vervangt eventuele bestaande inhoud."""
    from docx.shared import Pt
    cel.text = ""
    run = cel.paragraphs[0].add_run(tekst)
    run.bold = bold
    run.italic = italic
    run.font.size = Pt(size)
    if kleur:
        run.font.color.rgb = kleur


def _voeg_subsidietabel_bouwperiode_in(docx_pad: str, bouwjaar: int) -> None:
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
        ISOLATIE_BEDRAGEN, GLAS_BEDRAGEN, MONUMENT_GLAS,
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

    def _header_rij(tabel, kolommen, achtergrond=_NAVY_HEX):
        for j, kop in enumerate(kolommen):
            cel = tabel.rows[0].cells[j]
            _cel_tekst(cel, kop, bold=True, kleur=WIT)
            _set_cel_achtergrond(cel, achtergrond)

    def _data_rij(tabel, cellen: list, aanbevolen: bool):
        """Voegt een datarij toe. Aanbevolen = gele bg + vet; anders grijs."""
        rij = tabel.add_row()
        kleur = ZWART if aanbevolen else GRIJS
        for j, (tekst, bold) in enumerate(cellen):
            _cel_tekst(rij.cells[j], tekst, bold=(bold and aanbevolen), kleur=kleur)
            if aanbevolen:
                _set_cel_achtergrond(rij.cells[j], _YELLOW_HEX)

    # ── Tabel 1: Isolatie ─────────────────────────────────────────────────────
    ISO_VOLGORDE = ["gevel", "dakisolatie", "zoldervloer", "spouwmuur", "vloer", "bodem"]
    ISO_COLS     = ["Maatregel", "Enkelvoudig", "Meervoudig", "Biobased bonus", "Min. Rc/Rd"]

    tabel_iso = doc.add_table(rows=1, cols=len(ISO_COLS))
    try: tabel_iso.style = doc.styles['Table Grid']
    except KeyError: pass
    _header_rij(tabel_iso, ISO_COLS)

    for sleutel in ISO_VOLGORDE:
        m = ISOLATIE_BEDRAGEN[sleutel]
        bio = f"+ € {m['bio']:.2f}/m²" if m.get("bio") else "—"
        _data_rij(tabel_iso, [
            (m["naam"],               True),
            (f"€ {m['enkel']:.2f}/m²", False),
            (f"€ {m['meer']:.2f}/m²",  True),
            (bio,                      False),
            (m["rd"],                  False),
        ], aanbevolen=sleutel in aanbevolen_iso)

    # ── Tabel 2: Glas ─────────────────────────────────────────────────────────
    GLAS_VOLGORDE = ["hrpp", "vacuum", "triple", "deuren"]
    GLAS_COLS     = ["Type glas", "Enkelvoudig", "Meervoudig", "Monument enkv.", "Monument meerv."]

    spatie1 = doc.add_paragraph("")

    tabel_glas = doc.add_table(rows=1, cols=len(GLAS_COLS))
    try: tabel_glas.style = doc.styles['Table Grid']
    except KeyError: pass
    _header_rij(tabel_glas, GLAS_COLS)

    for sleutel in GLAS_VOLGORDE:
        g = GLAS_BEDRAGEN[sleutel]
        _data_rij(tabel_glas, [
            (g["naam"],                               True),
            (f"€ {g['enkel']:.2f}/m²",               False),
            (f"€ {g['meer']:.2f}/m²",                True),
            (f"€ {MONUMENT_GLAS['enkel']:.2f}/m²",   False),
            (f"€ {MONUMENT_GLAS['meer']:.2f}/m²",    False),
        ], aanbevolen=sleutel in aanbevolen_glas)

    # ── Warmtepomp combinatieblok ──────────────────────────────────────────────
    spatie2 = doc.add_paragraph("")

    wp = WARMTEPOMP
    wp_toel = periode.get("warmtepomp_toelichting", wp["toelichting"])

    tabel_wp = doc.add_table(rows=3, cols=4)
    try: tabel_wp.style = doc.styles['Table Grid']
    except KeyError: pass

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

    # Toelichting rij (samengevoegde cel)
    rij_toel = tabel_wp.rows[2]
    cel_toel = rij_toel.cells[0]
    for i in range(1, 4):
        cel_toel = cel_toel.merge(rij_toel.cells[i])
    _cel_tekst(cel_toel, wp_toel, size=8, italic=True, kleur=GROEN_TXT)
    _set_cel_achtergrond(rij_toel.cells[0], _GREEN_BG)

    # ── Noten ─────────────────────────────────────────────────────────────────
    spatie3 = doc.add_paragraph("")

    tabel_noten = doc.add_table(rows=0, cols=1)
    try: tabel_noten.style = doc.styles['Table Grid']
    except KeyError: pass

    if periode.get("notitie"):
        rij = tabel_noten.add_row()
        _cel_tekst(rij.cells[0], f"Let op: {periode['notitie']}", size=8, italic=True)
        _set_cel_achtergrond(rij.cells[0], _WARN_BG)

    for noot in SUBSIDIE_NUANCES:
        rij = tabel_noten.add_row()
        _cel_tekst(rij.cells[0], f"• {noot}", size=8)
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

    TITELBLAUW = "2F6FA3"
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
        run.bold      = bold
        run.font.size = Pt(10.5)
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


def fill_docx(template_path: str, output_path: str, data: dict, sv_foto_pad: str | None = None, bouwjaar: int | None = None):
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
            _voeg_subsidietabel_bouwperiode_in(output_path, bouwjaar)
        _stijl_woninggegevens_tabel(output_path)
        print(f"✅ Opgeslagen: {output_path}")

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
