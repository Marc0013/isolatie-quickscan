from __future__ import annotations
import os, zipfile, shutil
from lxml import etree
from pathlib import Path

NS = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
W  = f'{{{NS}}}'

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


def fill_docx(template_path: str, output_path: str, data: dict, sv_foto_pad: str | None = None):
    """
    Vult alle {{plaatshouders}} in en voegt optioneel een Street View foto in.
    Als sv_foto_pad None is of het invoegen mislukt, gaat het rapport gewoon door zonder foto.
    """
    # Bouw mapping: ook varianten met spaties meenemen
    expanded = {}
    for k, v in data.items():
        expanded[k] = v
        stripped = k.replace('{{ ', '{{').replace(' }}', '}}')
        if stripped != k:
            expanded[stripped] = v
        spaced = k.replace('{{', '{{ ').replace('}}', ' }}')
        if spaced != k:
            expanded[spaced] = v

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
        print(f"✅ Opgeslagen: {output_path}")

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
