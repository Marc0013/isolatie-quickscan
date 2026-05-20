from __future__ import annotations
import argparse
import json
from pathlib import Path
from typing import Any, Optional
from dotenv import load_dotenv

from clients_pdok import resolve_address_docid, pdok_lookup
from clients_bag import get_adressen_uitgebreid
from energielabels import find_label_for_address
from narratives import narrative_from_facts
from subsidies import likely_isde_subsidies
from report import quickscan_scores, render_markdown
from advisor import build_advice
from fill_template import fill_docx
from streetview import haal_streetview_op, status as sv_status

def load_config() -> dict:
    with open("config.json","r",encoding="utf-8") as f:
        return json.load(f)

def pick_first_item(obj: dict) -> dict | None:
    if not isinstance(obj, dict): return None
    if isinstance(obj.get("items"), list) and obj["items"]:
        return obj["items"][0]
    emb = obj.get("_embedded")
    if isinstance(emb, dict):
        for _, v in emb.items():
            if isinstance(v, list) and v:
                return v[0]
    return None

def normalize_int(value: Any) -> Optional[int]:
    if value is None: return None
    if isinstance(value, list):
        for v in value:
            n = normalize_int(v)
            if n is not None: return n
        return None
    if isinstance(value, str):
        s=value.strip()
        if not s: return None
        digits="".join(ch for ch in s if ch.isdigit())
        return int(digits) if digits else None
    if isinstance(value,(int,float)): return int(value)
    return None


def _fmt_geldig(s):
    if not s: return "-"
    try:
        from datetime import datetime
        from narratives import MAANDEN
        dt = datetime.fromisoformat(str(s).split("T")[0])
        return f"{dt.day} {MAANDEN[dt.month]} {dt.year}"
    except Exception:
        return str(s).split("T")[0]

def _fmt_getal(v, suffix=""):
    if isinstance(v, (int, float)):
        return f"{v:.1f} {suffix}".strip()
    return "-"

def _strip_md(text: str) -> str:
    """Verwijdert markdown opmaak zodat het in Word als gewone tekst staat."""
    import re
    if not text:
        return text
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)   # **bold** → tekst
    text = re.sub(r'\*(.+?)\*', r'\1', text)         # *italic* → tekst
    text = re.sub(r'_(.+?)_', r'\1', text)           # _italic_ → tekst
    text = re.sub(r'`(.+?)`', r'\1', text)           # `code` → tekst
    return text

def _eur(v) -> str:
    """Formatteert een getal als euro-bedrag (€ 1.234)."""
    return f"\u20ac\u202f{round(v):,}".replace(",", ".")

def _tvt(netto, besparing) -> str:
    """Berekent terugverdientijd in jaren, of '-' als niet berekend."""
    if besparing and besparing > 0:
        return f"{round(netto / besparing)} jaar"
    return "-"

def _totaalplaatje_placeholders(advies) -> dict:
    """
    Berekent totaalplaatje-waarden (totaal én per element) als {{placeholders}}.
    Elementen: dak, gevel, vloer, glas.
    Alle waarden zijn '-' als er geen adviesdata beschikbaar is.

    Totaal:
      {{tp_invest_min}}    {{tp_invest_gem}}    {{tp_invest_max}}
      {{tp_subsidie}}
      {{tp_netto_min}}     {{tp_netto_gem}}     {{tp_netto_max}}
      {{tp_besparing_min}} {{tp_besparing_gem}} {{tp_besparing_max}}
      {{tp_tvt_min}}       {{tp_tvt_gem}}       {{tp_tvt_max}}

    Per element (vervang [el] door dak / gevel / vloer / glas):
      {{tp_[el]_maatregel}}     naam van de maatregel
      {{tp_[el]_opp}}           geschatte oppervlakte in m²
      {{tp_[el]_subsidie}}      ISDE subsidie indicatie (enkelvoudig tarief)
      {{tp_[el]_invest_min}}    {{tp_[el]_invest_gem}}    {{tp_[el]_invest_max}}
      {{tp_[el]_besparing_min}} {{tp_[el]_besparing_gem}} {{tp_[el]_besparing_max}}
      {{tp_[el]_tvt_min}}       {{tp_[el]_tvt_gem}}       {{tp_[el]_tvt_max}}
    """
    ELEMENTEN = ["dak", "gevel", "vloer", "glas"]

    # Lege defaults voor alle placeholders (totaal + per element)
    leeg: dict = {
        "{{tp_invest_min}}":    "-", "{{tp_invest_gem}}":    "-", "{{tp_invest_max}}":    "-",
        "{{tp_subsidie}}":      "-",
        "{{tp_netto_min}}":     "-", "{{tp_netto_gem}}":     "-", "{{tp_netto_max}}":     "-",
        "{{tp_besparing_min}}": "-", "{{tp_besparing_gem}}": "-", "{{tp_besparing_max}}": "-",
        "{{tp_tvt_min}}":       "-", "{{tp_tvt_gem}}":       "-", "{{tp_tvt_max}}":       "-",
    }
    for el in ELEMENTEN:
        leeg.update({
            f"{{{{tp_{el}_maatregel}}}}":     "-",
            f"{{{{tp_{el}_opp}}}}":           "-",
            f"{{{{tp_{el}_subsidie}}}}":      "-",
            f"{{{{tp_{el}_invest_min}}}}":    "-",
            f"{{{{tp_{el}_invest_gem}}}}":    "-",
            f"{{{{tp_{el}_invest_max}}}}":    "-",
            f"{{{{tp_{el}_besparing_min}}}}": "-",
            f"{{{{tp_{el}_besparing_gem}}}}": "-",
            f"{{{{tp_{el}_besparing_max}}}}": "-",
            f"{{{{tp_{el}_tvt_min}}}}":       "-",
            f"{{{{tp_{el}_tvt_gem}}}}":       "-",
            f"{{{{tp_{el}_tvt_max}}}}":       "-",
        })

    if not advies or not advies.prioriteiten:
        return leeg

    prio      = advies.prioriteiten
    inv_min   = sum(p.kosten_min    for p in prio)
    inv_max   = sum(p.kosten_max    for p in prio)
    bes_min   = sum(p.besparing_min for p in prio)
    bes_max   = sum(p.besparing_max for p in prio)
    subsidie  = advies.subsidie_totaal_indicatie
    netto_min = max(0.0, inv_min - subsidie)
    netto_max = max(0.0, inv_max - subsidie)
    inv_gem   = round((inv_min + inv_max) / 2)
    bes_gem   = round((bes_min + bes_max) / 2)
    netto_gem = max(0.0, inv_gem - subsidie)

    result = {
        "{{tp_invest_min}}":    _eur(inv_min),
        "{{tp_invest_gem}}":    _eur(inv_gem),
        "{{tp_invest_max}}":    _eur(inv_max),
        "{{tp_subsidie}}":      _eur(subsidie),
        "{{tp_netto_min}}":     _eur(netto_min),
        "{{tp_netto_gem}}":     _eur(netto_gem),
        "{{tp_netto_max}}":     _eur(netto_max),
        "{{tp_besparing_min}}": _eur(bes_min),
        "{{tp_besparing_gem}}": _eur(bes_gem),
        "{{tp_besparing_max}}": _eur(bes_max),
        "{{tp_tvt_min}}":       _tvt(netto_min, bes_max),
        "{{tp_tvt_gem}}":       _tvt(netto_gem, bes_gem),
        "{{tp_tvt_max}}":       _tvt(netto_max, bes_min),
    }

    # Per element — lege defaults alvast in result, dan overschrijven indien data aanwezig
    prio_per_el = {p.element: p for p in prio}
    for el in ELEMENTEN:
        el_leeg = {
            f"{{{{tp_{el}_maatregel}}}}":     "-",
            f"{{{{tp_{el}_opp}}}}":           "-",
            f"{{{{tp_{el}_subsidie}}}}":      "-",
            f"{{{{tp_{el}_invest_min}}}}":    "-",
            f"{{{{tp_{el}_invest_gem}}}}":    "-",
            f"{{{{tp_{el}_invest_max}}}}":    "-",
            f"{{{{tp_{el}_besparing_min}}}}": "-",
            f"{{{{tp_{el}_besparing_gem}}}}": "-",
            f"{{{{tp_{el}_besparing_max}}}}": "-",
            f"{{{{tp_{el}_tvt_min}}}}":       "-",
            f"{{{{tp_{el}_tvt_gem}}}}":       "-",
            f"{{{{tp_{el}_tvt_max}}}}":       "-",
        }
        p = prio_per_el.get(el)
        if p is None:
            result.update(el_leeg)
            continue
        netto_el_min = max(0.0, p.kosten_min - p.subsidie_max)
        netto_el_max = max(0.0, p.kosten_max - p.subsidie_max)
        invest_gem   = round((p.kosten_min + p.kosten_max) / 2)
        besparing_gem = round((p.besparing_min + p.besparing_max) / 2)
        netto_el_gem = max(0.0, invest_gem - p.subsidie_max)
        result.update({
            f"{{{{tp_{el}_maatregel}}}}":     p.maatregel_naam,
            f"{{{{tp_{el}_opp}}}}":           f"ca. {p.opp_indicatief:.0f} m²" if p.opp_indicatief > 0 else "-",
            f"{{{{tp_{el}_subsidie}}}}":      _eur(p.subsidie_max),
            f"{{{{tp_{el}_invest_min}}}}":    _eur(p.kosten_min),
            f"{{{{tp_{el}_invest_gem}}}}":    _eur(invest_gem),
            f"{{{{tp_{el}_invest_max}}}}":    _eur(p.kosten_max),
            f"{{{{tp_{el}_besparing_min}}}}": _eur(p.besparing_min),
            f"{{{{tp_{el}_besparing_gem}}}}": _eur(besparing_gem),
            f"{{{{tp_{el}_besparing_max}}}}": _eur(p.besparing_max),
            f"{{{{tp_{el}_tvt_min}}}}":       _tvt(netto_el_min, p.besparing_max),
            f"{{{{tp_{el}_tvt_gem}}}}":       _tvt(netto_el_gem, besparing_gem),
            f"{{{{tp_{el}_tvt_max}}}}":       _tvt(netto_el_max, p.besparing_min),
        })

    return result


def _parse_bullets(tekst: str) -> list:
    """
    Splits een markdown bullet-list (- item) in losse items.
    Strips het leading '- ' teken en plattet sub-regels.
    Behoudt **bold** markers zodat fill_xml ze als bold kan renderen.
    """
    import re
    if not tekst:
        return []
    # Splits op '- ' aan het begin van een regel
    delen = re.split(r'(?:^|\n)\s*-\s+', tekst)
    items = []
    for deel in delen:
        schoon = deel.strip()
        if not schoon:
            continue
        # Plattet inspring-regels (sub-tekst begint met spaties of _)
        schoon = re.sub(r'\n\s+', ' ', schoon)
        # Verwijder _italic_ markers maar bewaar de tekst
        schoon = re.sub(r'_(.+?)_', r'\1', schoon)
        items.append(schoon)
    return items


def _find_ghostscript() -> str | None:
    """Zoekt Ghostscript op Windows en Unix. Geeft pad terug of None."""
    import glob as _glob, subprocess as _sp
    candidates = [
        r"C:\Program Files\gs\gs*\bin\gswin64c.exe",
        r"C:\Program Files (x86)\gs\gs*\bin\gswin64c.exe",
        r"C:\Program Files\gs\gs*\bin\gswin32c.exe",
        "gswin64c", "gswin32c", "gs",
    ]
    for cand in candidates:
        if '*' in cand:
            matches = sorted(_glob.glob(cand))
            if matches:
                return matches[-1]
        else:
            try:
                r = _sp.run([cand, "--version"], capture_output=True, timeout=5)
                if r.returncode == 0:
                    return cand
            except (FileNotFoundError, _sp.TimeoutExpired):
                pass
    return None


WONINGTYPE_OPTIES = ("tussenwoning", "hoekwoning", "vrijstaand", "twee-onder-een-kap", "appartement")

def main(postcode: str, huisnummer: str, toevoeging: Optional[str] = None, huisletter: Optional[str] = None, woningtype: Optional[str] = None):
    load_dotenv()
    config = load_config()

    use_bag = config.get("features", {}).get("use_bag", True)
    use_labels = config.get("features", {}).get("use_labels", True)
    use_narrative = config.get("features", {}).get("use_narrative", True)
    use_subsidies = config.get("features", {}).get("use_subsidies", True)

    adres = f"{postcode} {huisnummer}"
    try:
        docid = resolve_address_docid(postcode, huisnummer, config)
        lookup = pdok_lookup(docid, config)
        doc = lookup.get("response", {}).get("docs", [None])[0]
        if doc and doc.get("weergavenaam"):
            adres = doc["weergavenaam"]
        # Coordinaten opslaan voor Street View
        coords = doc.get("centroide_ll", "") if doc else ""
        if coords:
            # formaat: "POINT(6.5665 53.2194)"
            import re as _re
            m = _re.search(r'POINT[(]([0-9.]+)\s+([0-9.]+)[)]', coords)
            if m:
                sv_lng, sv_lat = float(m.group(1)), float(m.group(2))
            else:
                sv_lat, sv_lng = None, None
        else:
            sv_lat, sv_lng = None, None
    except Exception:
        sv_lat, sv_lng = None, None

    bouwjaar: Optional[int] = None
    opp: Optional[int] = None

    if use_bag:
        bag_resp = get_adressen_uitgebreid(postcode, huisnummer, config, exacte_match=True,
                                           toevoeging=toevoeging, huisletter=huisletter)
        item = pick_first_item(bag_resp)
        if not item:
            raise ValueError("Geen resultaat uit BAG /adressenuitgebreid (controleer postcode/huisnummer/toevoeging).")
        bouwjaar = normalize_int(item.get("oorspronkelijkBouwjaar") or item.get("oorspronkelijkBouwjaarPand") or item.get("bouwjaar"))
        opp = normalize_int(item.get("gebruiksoppervlakte") or item.get("oppervlakte"))

    label = None
    if use_labels:
        label = find_label_for_address(postcode, huisnummer, config,
                                       toevoeging=toevoeging, huisletter=huisletter)

    if bouwjaar is None:
        bouwjaar = 1995

    scan = quickscan_scores(bouwjaar, label)

    facts = {"adres": adres, "postcode": postcode, "huisnummer": huisnummer, "bouwjaar": bouwjaar, "opp_bag": opp, "woningtype": woningtype}
    if label:
        facts.update({
            "labelklasse": label.get("labelklasse"),
            "gebouwtype": label.get("gebouwtype"),
            "energiebehoefte": label.get("energiebehoefte"),
            "warmtebehoefte": label.get("warmtebehoefte"),
            "opp_thermische_zone": label.get("opp_thermische_zone"),
            "geldig_tot": label.get("geldig_tot"),
        })

    # Scores toevoegen aan facts voor narrative
    scores_dict = scan.get("scores", {})
    facts["score_dak"]   = scores_dict.get("dak")
    facts["score_gevel"] = scores_dict.get("gevel")
    facts["score_vloer"] = scores_dict.get("vloer")
    facts["score_glas"]  = scores_dict.get("glas")

    narrative = narrative_from_facts(facts) if use_narrative else None
    advies = build_advice(facts)

    # ── Street View afbeelding ophalen ────────────────────────
    sv_foto: bytes | None = None
    if sv_lat and sv_lng:
        sv_foto, sv_status = haal_streetview_op(sv_lat, sv_lng)
        if sv_status not in ("ok", "cache"):
            print(f"  Street View niet beschikbaar ({sv_status}), rapport wordt zonder foto aangemaakt.")
    else:
        print("  Geen coördinaten beschikbaar voor Street View.")
    subs = likely_isde_subsidies(facts) if use_subsidies else None

    md = render_markdown(
        adres=adres,
        bouwjaar=bouwjaar,
        opp_m2=opp,
        label=label,
        scan=scan,
        subsidies=subs,
        narrative=narrative,
        advies=advies,
        woningtype=woningtype,
    )


    outdir = Path(config["report"]["output_folder"])
    outdir.mkdir(parents=True, exist_ok=True)
    hnr_suffix = f"{huisnummer}{huisletter}" if huisletter else huisnummer
    outfile = outdir / f"quickscan_{postcode}_{hnr_suffix}.md"
    outfile.write_text(md, encoding="utf-8")
    print(f"OK: markdown geschreven: {outfile}")

    # ── Word rapport invullen ──────────────────────────────────
    from datetime import date
    from narratives import MAANDEN
    today = date.today()
    today_nl = f"{today.day} {MAANDEN[today.month]} {today.year}"

    template_path = Path("templates") / "Template_rapportage_quickscan.docx"
    if template_path.exists():
        scores = scan.get("scores", {})
        sub_tekst = ""
        if subs:
            sub_tekst = "\n".join(
                f"- {s['maatregel']}: {s['toelichting']}" for s in subs
            )

        scores = scan.get("scores", {})
        docx_data = {
            "{{adres}}":                 adres,
            "{{datum}}":                 today_nl,
            "{{bouwjaar}}":              str(bouwjaar),
            "{{bouwperiode}}":           scan["band"],
            "{{oppervlakte}}":           f"{opp} m²" if opp else "-",
            "{{energielabel}}":          label.get("labelklasse", "-") if label else "-",
            "{{registratiedatum}}":      _fmt_geldig(label.get("registratiedatum") if label else None),
            "{{energiebehoefte}}":       _fmt_getal(label.get("energiebehoefte") if label else None, "kWh/m².jr"),
            "{{warmtebehoefte}}":        _fmt_getal(label.get("warmtebehoefte") if label else None, "kWh/m².jr"),
            "{{gebouwtype}}":            label.get("gebouwtype", "-") if label else "-",
            "{{woningtype}}":            woningtype or "-",
            "{{ geldig_tot }}":          _fmt_geldig(label.get("geldig_tot") if label else None),
            # Narratives
            # Samenvatting wordt geprepend aan narrative_gebouw (geen aparte placeholder in template)
            "{{narrative_gebouw}}":      _strip_md(
                (advies.teksten.get("samenvatting", "") + "\n\n" if advies else "") +
                (narrative.get("gebouw", "") if narrative else "")
            ),
            "{{ narrative_gebouw }}":    _strip_md(
                (advies.teksten.get("samenvatting", "") + "\n\n" if advies else "") +
                (narrative.get("gebouw", "") if narrative else "")
            ),
            "{{narrative_energie}}":     _strip_md(narrative.get("energie", "") if narrative else ""),
            "{{ narrative_energie }}":   _strip_md(narrative.get("energie", "") if narrative else ""),
            # Persoonlijke maatregelen — geen _strip_md zodat **bold** bewaard blijft
            "{{narrative_aanpak}}":      (
                advies.teksten.get("prioriteiten_tekst", "") if advies
                else _strip_md(narrative.get("aanpak", "") if narrative else "")
            ),
            "{{ narrative_aanpak }}":    (
                advies.teksten.get("prioriteiten_tekst", "") if advies
                else _strip_md(narrative.get("aanpak", "") if narrative else "")
            ),
            "{{narrative_bouwperiode}}": _strip_md(narrative.get("bouwperiode_inleiding", "") if narrative else ""),
            # Scores
            "{{score_dak}}":             str(scores.get("dak", "-")),
            "{{ score_dak }}":           str(scores.get("dak", "-")),
            "{{score_gevel}}":           str(scores.get("gevel", "-")),
            "{{ score_gevel }}":         str(scores.get("gevel", "-")),
            "{{score_vloer}}":           str(scores.get("vloer", "-")),
            "{{ score_vloer }}":         str(scores.get("vloer", "-")),
            "{{score_glas}}":            str(scores.get("glas", "-")),
            "{{ score_glas }}":          str(scores.get("glas", "-")),
            "{{score_dak_tekst}}":       narrative.get("score_dak_tekst", "-") if narrative else "-",
            "{{score_gevel_tekst}}":     narrative.get("score_gevel_tekst", "-") if narrative else "-",
            "{{score_vloer_tekst}}":     narrative.get("score_vloer_tekst", "-") if narrative else "-",
            "{{score_glas_tekst}}":      narrative.get("score_glas_tekst", "-") if narrative else "-",
            # Element-specifieke uitleg
            "{{element_tekst_dak}}":     _strip_md(narrative.get("element_tekst_dak", "") if narrative else ""),
            "{{element_tekst_gevel}}":   _strip_md(narrative.get("element_tekst_gevel", "") if narrative else ""),
            "{{element_tekst_vloer}}":   _strip_md(narrative.get("element_tekst_vloer", "") if narrative else ""),
            "{{element_tekst_glas}}":    _strip_md(narrative.get("element_tekst_glas", "") if narrative else ""),
            # Bouwfysische analyse en waarschuwingen (nieuwe modules)
            "{{fysische_analyse}}":      _strip_md(advies.teksten.get("fysische_analyse", "") if advies else ""),
            "{{waarschuwingen}}":        _strip_md(advies.teksten.get("waarschuwingen_tekst", "") if advies else ""),
            # Aandachtspunten, subsidies, vervolgstappen
            "{{risicos}}":               _strip_md(narrative.get("risicos", "") if narrative else ""),
            "{{subsidies}}":             _strip_md(narrative.get("subsidies_blok", sub_tekst) if narrative else sub_tekst),
            "{{subsidies_isolatie}}":    _strip_md(narrative.get("subsidies_isolatie", "") if narrative else ""),
            "{{vervolgstappen}}":        _strip_md(narrative.get("vervolgstappen_blok", "") if narrative else ""),
            # Streetview: altijd leeg als er geen foto is
            "{{streetview}}":            "",
            # Totaalplaatje: losse placeholders per tabelcel
            **_totaalplaatje_placeholders(advies),
        }
        docx_out = outdir / f"quickscan_{postcode}_{hnr_suffix}.docx"
        # Sla Street View foto tijdelijk op als het beschikbaar is
        sv_pad = None
        if sv_foto:
            sv_pad = outdir / f"streetview_{postcode}_{hnr_suffix}.jpg"
            sv_pad.write_bytes(sv_foto)

        seed_items = {
            "##RISICOS_SEED##": _parse_bullets(
                narrative.get("risicos", "") if narrative else ""
            ),
        }
        fill_docx(str(template_path), str(docx_out), docx_data, sv_foto_pad=str(sv_pad) if sv_pad else None, bouwjaar=bouwjaar, scores=scan.get("scores"), advies=advies, seed_items=seed_items)

        # Tijdelijk Street View bestand opruimen
        if sv_pad and sv_pad.exists():
            sv_pad.unlink()

        # ── PDF maken via LibreOffice + optionele Ghostscript print-optimalisatie ──
        import subprocess, sys, os, tempfile
        pdf_out = outdir / f"quickscan_{postcode}_{hnr_suffix}.pdf"

        lo_candidates = [
            r"C:\Program Files\LibreOffice\program\soffice.exe",
            r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
            "soffice",
        ]
        lo_exe = next((p for p in lo_candidates if Path(p).exists() or p == "soffice"), "soffice")

        tmp_profile = Path(tempfile.mkdtemp())
        env = os.environ.copy()
        env["UserInstallation"] = tmp_profile.as_uri()

        if pdf_out.exists():
            try:
                pdf_out.unlink()
            except Exception:
                pass

        # Stap 1: LibreOffice, gebruik writer_pdf_Export filter voor volledige font-embedding
        lo_result = subprocess.run(
            [lo_exe, "--headless", "--norestore",
             "--convert-to", "pdf:writer_pdf_Export",
             "--outdir", str(outdir), str(docx_out)],
            capture_output=True, text=True, env=env
        )
        try:
            import shutil as _shutil
            _shutil.rmtree(str(tmp_profile), ignore_errors=True)
        except Exception:
            pass

        if lo_result.returncode != 0:
            print(f"Let op: PDF-conversie mislukt: {lo_result.stderr or lo_result.stdout}")
        else:
            print(f"OK: PDF geschreven: {pdf_out}")

            # Stap 2: Ghostscript post-processing (optioneel, vereist Ghostscript installatie)
            # Vlakt transparantie af, forceert font-embedding en zet PDF op versie 1.4.
            # PDF 1.4 is breed ondersteund door printercontrollers en -drivers.
            gs_exe = _find_ghostscript()
            if gs_exe and pdf_out.exists():
                pdf_tmp = pdf_out.with_suffix(".gs_tmp.pdf")
                gs_result = subprocess.run([
                    gs_exe,
                    "-dBATCH", "-dNOPAUSE", "-dQUIET",
                    "-sDEVICE=pdfwrite",
                    "-dCompatibilityLevel=1.4",      # PDF 1.4: transparantie geflattened, breed ondersteund
                    "-dPDFSETTINGS=/printer",        # 300 DPI downsampling, optimale compressie
                    "-dEmbedAllFonts=true",           # Alle fonts insluiten (voorkomt substitutie)
                    "-dSubsetFonts=true",             # Subset houdt bestandsgrootte beperkt
                    "-dHaveTransparency=false",       # Transparantiegroepen afvlakken
                    "-dColorConversionStrategy=/sRGB",# Uniforme kleurruimte voor printercompatibiliteit
                    "-dColorImageResolution=300",
                    "-dGrayImageResolution=300",
                    "-dMonoImageResolution=1200",
                    "-dDetectDuplicateImages=true",
                    f"-sOutputFile={pdf_tmp}",
                    str(pdf_out),
                ], capture_output=True, text=True)

                if gs_result.returncode == 0 and pdf_tmp.exists():
                    pdf_tmp.replace(pdf_out)
                    print(f"OK: PDF geoptimaliseerd voor afdrukken (Ghostscript)")
                else:
                    if pdf_tmp.exists():
                        pdf_tmp.unlink()
                    print(f"Let op: Ghostscript post-processing mislukt, basis-PDF gebruikt")
                    print(f"        {gs_result.stderr.strip()[:200]}" if gs_result.stderr else "")
            else:
                print(f"Info: Ghostscript niet gevonden, basis-PDF gebruikt (printproblemen mogelijk)")
                print(f"      Installeer Ghostscript via https://www.ghostscript.com/releases/")
    else:
        print(f"Let op: template niet gevonden op {template_path}, alleen .md gegenereerd.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="PandIQ Isolatie Quickscan, genereer een verduurzamingsrapport op basis van postcode en huisnummer.",
        usage="python src/main.py <postcode> <huisnummer> [--toevoeging X] [--huisletter Y]",
    )
    parser.add_argument("postcode", help="Postcode, bijv. 9746CR")
    parser.add_argument("huisnummer", help="Huisnummer, bijv. 107")
    parser.add_argument("--toevoeging", default=None, help="Huisnummertoevoeging (optioneel)")
    parser.add_argument("--huisletter", default=None, help="Huisletter (optioneel)")
    parser.add_argument(
        "--woningtype", default=None,
        choices=WONINGTYPE_OPTIES,
        help="Type woning: tussenwoning, hoekwoning, vrijstaand, twee-onder-een-kap, appartement",
    )
    args = parser.parse_args()

    # Splits "188a" automatisch op in huisnummer=188 en huisletter=A
    import re as _re
    hnr_raw = args.huisnummer.strip()
    m = _re.fullmatch(r'(\d+)([A-Za-z])', hnr_raw)
    if m:
        hnr = m.group(1)
        hletter = m.group(2).upper()
    else:
        hnr = hnr_raw
        hletter = args.huisletter.upper() if args.huisletter else None

    main(
        args.postcode.replace(" ", "").upper(),
        hnr,
        toevoeging=args.toevoeging,
        huisletter=hletter,
        woningtype=args.woningtype,
    )
