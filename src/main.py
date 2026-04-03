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
    if not s: return "—"
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
    return "—"

def _strip_md(text: str) -> str:
    """Verwijdert markdown opmaak zodat het in Word als gewone tekst staat."""
    import re
    if not text:
        return text
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)   # **bold** → tekst
    text = re.sub(r'\*(.+?)\*', r'\1', text)         # *italic* → tekst
    text = re.sub(r'`(.+?)`', r'\1', text)           # `code` → tekst
    return text

def main(postcode: str, huisnummer: str, toevoeging: Optional[str] = None, huisletter: Optional[str] = None):
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

    facts = {"adres": adres, "postcode": postcode, "huisnummer": huisnummer, "bouwjaar": bouwjaar, "opp_bag": opp}
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

    # ── Street View afbeelding ophalen ────────────────────────
    sv_foto: bytes | None = None
    if sv_lat and sv_lng:
        sv_foto, sv_status = haal_streetview_op(sv_lat, sv_lng)
        if sv_status not in ("ok", "cache"):
            print(f"  Street View niet beschikbaar ({sv_status}) — rapport wordt zonder foto aangemaakt.")
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
    )


    outdir = Path(config["report"]["output_folder"])
    outdir.mkdir(parents=True, exist_ok=True)
    outfile = outdir / f"quickscan_{postcode}_{huisnummer}.md"
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
            "{{oppervlakte}}":           f"{opp} m²" if opp else "—",
            "{{energielabel}}":          label.get("labelklasse", "—") if label else "—",
            "{{registratiedatum}}":      _fmt_geldig(label.get("registratiedatum") if label else None),
            "{{energiebehoefte}}":       _fmt_getal(label.get("energiebehoefte") if label else None, "kWh/m².jr"),
            "{{warmtebehoefte}}":        _fmt_getal(label.get("warmtebehoefte") if label else None, "kWh/m².jr"),
            "{{gebouwtype}}":            label.get("gebouwtype", "—") if label else "—",
            "{{ geldig_tot }}":          _fmt_geldig(label.get("geldig_tot") if label else None),
            # Narratives
            "{{narrative_gebouw}}":      _strip_md(narrative.get("gebouw", "") if narrative else ""),
            "{{ narrative_gebouw }}":    _strip_md(narrative.get("gebouw", "") if narrative else ""),
            "{{narrative_energie}}":     _strip_md(narrative.get("energie", "") if narrative else ""),
            "{{ narrative_energie }}":   _strip_md(narrative.get("energie", "") if narrative else ""),
            "{{narrative_aanpak}}":      _strip_md(narrative.get("aanpak", "") if narrative else ""),
            "{{ narrative_aanpak }}":    _strip_md(narrative.get("aanpak", "") if narrative else ""),
            "{{narrative_bouwperiode}}": _strip_md(narrative.get("bouwperiode_inleiding", "") if narrative else ""),
            # Scores
            "{{score_dak}}":             str(scores.get("dak", "—")),
            "{{ score_dak }}":           str(scores.get("dak", "—")),
            "{{score_gevel}}":           str(scores.get("gevel", "—")),
            "{{ score_gevel }}":         str(scores.get("gevel", "—")),
            "{{score_vloer}}":           str(scores.get("vloer", "—")),
            "{{ score_vloer }}":         str(scores.get("vloer", "—")),
            "{{score_glas}}":            str(scores.get("glas", "—")),
            "{{ score_glas }}":          str(scores.get("glas", "—")),
            "{{score_dak_tekst}}":       narrative.get("score_dak_tekst", "—") if narrative else "—",
            "{{score_gevel_tekst}}":     narrative.get("score_gevel_tekst", "—") if narrative else "—",
            "{{score_vloer_tekst}}":     narrative.get("score_vloer_tekst", "—") if narrative else "—",
            "{{score_glas_tekst}}":      narrative.get("score_glas_tekst", "—") if narrative else "—",
            # Aandachtspunten, subsidies, vervolgstappen
            "{{risicos}}":               _strip_md(narrative.get("risicos", "") if narrative else ""),
            "{{subsidies}}":             _strip_md(narrative.get("subsidies_blok", sub_tekst) if narrative else sub_tekst),
            "{{subsidies_isolatie}}":    _strip_md(narrative.get("subsidies_isolatie", "") if narrative else ""),
            "{{vervolgstappen}}":        _strip_md(narrative.get("vervolgstappen_blok", "") if narrative else ""),
            # Streetview: altijd leeg als er geen foto is
            "{{streetview}}":            "",
        }
        docx_out = outdir / f"quickscan_{postcode}_{huisnummer}.docx"
        # Sla Street View foto tijdelijk op als het beschikbaar is
        sv_pad = None
        if sv_foto:
            sv_pad = outdir / f"streetview_{postcode}_{huisnummer}.jpg"
            sv_pad.write_bytes(sv_foto)

        fill_docx(str(template_path), str(docx_out), docx_data, sv_foto_pad=str(sv_pad) if sv_pad else None, bouwjaar=bouwjaar)

        # Tijdelijk Street View bestand opruimen
        if sv_pad and sv_pad.exists():
            sv_pad.unlink()

        # ── PDF maken via LibreOffice ──────────────────────────
        import subprocess, sys, os, tempfile
        pdf_out = outdir / f"quickscan_{postcode}_{huisnummer}.pdf"

        lo_candidates = [
            r"C:\Program Files\LibreOffice\program\soffice.exe",
            r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
            "soffice",
        ]
        lo_exe = next((p for p in lo_candidates if Path(p).exists() or p == "soffice"), "soffice")

        # UserInstallation in temp-map zonder spaties (fix voor Windows paden met spaties)
        tmp_profile = Path(tempfile.mkdtemp())
        env = os.environ.copy()
        env["UserInstallation"] = tmp_profile.as_uri()

        # Verwijder bestaande PDF zodat LibreOffice hem niet probeert te overschrijven
        if pdf_out.exists():
            try:
                pdf_out.unlink()
            except Exception:
                pass

        result = subprocess.run(
            [lo_exe, "--headless", "--norestore", "--convert-to", "pdf",
             "--outdir", str(outdir), str(docx_out)],
            capture_output=True, text=True, env=env
        )
        try:
            import shutil as _shutil
            _shutil.rmtree(str(tmp_profile), ignore_errors=True)
        except Exception:
            pass

        if result.returncode == 0:
            print(f"OK: PDF geschreven: {pdf_out}")
        else:
            print(f"Let op: PDF-conversie mislukt: {result.stderr or result.stdout}")
    else:
        print(f"Let op: template niet gevonden op {template_path} — alleen .md gegenereerd.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="PandIQ Isolatie Quickscan – genereer een verduurzamingsrapport op basis van postcode en huisnummer.",
        usage="python src/main.py <postcode> <huisnummer> [--toevoeging X] [--huisletter Y]",
    )
    parser.add_argument("postcode", help="Postcode, bijv. 9746CR")
    parser.add_argument("huisnummer", help="Huisnummer, bijv. 107")
    parser.add_argument("--toevoeging", default=None, help="Huisnummertoevoeging (optioneel)")
    parser.add_argument("--huisletter", default=None, help="Huisletter (optioneel)")
    args = parser.parse_args()
    main(
        args.postcode.replace(" ", "").upper(),
        args.huisnummer,
        toevoeging=args.toevoeging,
        huisletter=args.huisletter,
    )
