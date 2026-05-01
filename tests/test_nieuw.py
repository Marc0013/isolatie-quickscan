"""
tests/test_nieuw.py
===================
Test de drie nieuwe modules: aannames.py, oppervlaktes.py,
financials (warmteverlies_reductie / terugverdientijd_uitgebreid)
en waarschuwingen.py.

Drie voorbeeldwoningen:
  W1: bvo=90,  type="rijwoning",  bouwjaar=2005, dak="plat"
  W2: bvo=90,  type="hoekwoning", bouwjaar=1954, dak="hellend"
  W3: bvo=200, type="vrijstaand", bouwjaar=1969, dak="hellend"

Gebruik: python tests/test_nieuw.py   (vanuit de projectroot)
         of:   cd src && python ../tests/test_nieuw.py
"""
from __future__ import annotations
import sys, os

# Windows-terminal ondersteunt niet altijd UTF-8; errors='replace' voorkomt crashes
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Zorg dat src/ in het zoekpad staat, ongeacht vanwaar het script wordt aangeroepen
_src = os.path.join(os.path.dirname(__file__), "..", "src")
sys.path.insert(0, os.path.abspath(_src))

from aannames import rc_oud, u_oud_glas, AANNAMES, get as aanname
from oppervlaktes import bereken_oppervlaktes
from financials import warmteverlies_reductie, terugverdientijd_uitgebreid
from waarschuwingen import genereer_waarschuwingen


# ── RC-eisen voor ISDE (gebruikt voor referentie in output) ──────────────────
RC_NIEUW: dict[str, float] = {
    "dak":   aanname("rc_eis_dak"),
    "vloer": aanname("rc_eis_vloer"),
    "gevel": aanname("rc_eis_gevel"),
    "spouw": aanname("rc_eis_spouw"),
}

WONINGEN = [
    {"naam": "W1 — Rijwoning 2005, plat dak",     "bvo": 90,  "type": "rijwoning",  "bouwjaar": 2005, "dak": "plat"},
    {"naam": "W2 — Hoekwoning 1954, hellend dak",  "bvo": 90,  "type": "hoekwoning", "bouwjaar": 1954, "dak": "hellend"},
    {"naam": "W3 — Vrijstaand 1969, hellend dak",  "bvo": 200, "type": "vrijstaand", "bouwjaar": 1969, "dak": "hellend"},
]


def _lijn(breedte: int = 70) -> str:
    return "-" * breedte


def test_woning(w: dict) -> None:
    bvo      = w["bvo"]
    wtype    = w["type"]
    bouwjaar = w["bouwjaar"]
    dak      = w["dak"]

    print()
    print("=" * 70)
    print(f"  {w['naam']}")
    print("=" * 70)

    # -- 1. Oppervlaktes
    print("\n> OPPERVLAKTES\n" + _lijn())
    opp = bereken_oppervlaktes(bvo_m2=bvo, woningtype=wtype, bouwjaar=bouwjaar, dak_type=dak)

    meta = opp["_meta"]
    print(f"  BVO: {meta['bvo_m2']} m²  |  woningtype: {meta['woningtype']}  "
          f"|  bouwjaar: {meta['bouwjaar']}  |  dak: {meta['dak_type']}")
    print(f"  Footprint: {meta['footprint_m2']} m²  |  verdiepingen: {meta['verdiepingen']}  "
          f"|  totale hoogte: {meta['hoogte_totaal']} m\n")

    for element in ("dak", "vloer", "gevel", "spouw", "glas"):
        info = opp[element]
        aanname_tag = " [aanname]" if info["aanname_gebruikt"] else ""
        print(f"  {element.upper():6s}: {info['opp_m2']:6.1f} m²{aanname_tag}")
        print(f"          {info['toelichting']}")

    print("\n  ── Stappen log ──")
    for stap in opp["_stappen"]:
        print(f"  {stap}")

    # -- 2. Rc_oud waarden
    print("\n> RC-WAARDEN (huidig o.b.v. bouwjaar)\n" + _lijn())
    rc_waarden: dict[str, dict] = {}
    for element in ("dak", "vloer", "gevel", "spouw"):
        rc_info = rc_oud(element, bouwjaar)
        rc_waarden[element] = rc_info
        print(f"  {element.upper():6s}: Rc = {rc_info['rc']:.2f} m²K/W  "
              f"[{rc_info['periode_label']}]")
        print(f"          {rc_info['toelichting']}")
        print(f"          Bron: {rc_info['bron']}")

    u_glas = u_oud_glas(bouwjaar)
    print(f"  {'GLAS':6s}: U  = {u_glas['u']:.1f} W/m²K")
    print(f"          {u_glas['toelichting']}")
    print(f"          Bron: {u_glas['bron']}")

    # -- 3. Besparing per element
    print("\n> WARMTEVERLIES-REDUCTIE PER ELEMENT\n" + _lijn())
    for element in ("dak", "vloer", "gevel", "spouw"):
        opp_el  = opp[element]["opp_m2"]
        rc_huidig = rc_waarden[element]["rc"]
        rc_doel   = RC_NIEUW.get(element, 3.5)

        if opp_el == 0.0:
            print(f"  {element.upper():6s}: oppervlak = 0 m², overgeslagen")
            continue
        if rc_huidig >= rc_doel:
            print(f"  {element.upper():6s}: Rc huidig ({rc_huidig}) >= eis ({rc_doel}) — "
                  f"geen winst meer")
            continue

        result = warmteverlies_reductie(opp_el, rc_huidig, rc_doel)
        print(f"  {element.upper():6s}: {result['kwh_jr']:7.1f} kWh/jr  |  "
              f"{result['m3_gas_jr']:6.1f} m³ gas/jr  |  "
              f"€ {result['euro_jr']:6.2f}/jr")
        print(f"          Formule: {result['formule']}")
        print(f"          Aannames: ΔT={result['aannames_gebruikt']['temperatuurverschil_dt']['waarde']} K, "
              f"t={result['aannames_gebruikt']['verwarmingsuren_jr']['waarde']} h/jr, "
              f"gasprijs=€{result['aannames_gebruikt']['gasprijs']['waarde']}/m³, "
              f"η={result['aannames_gebruikt']['cv_rendement_oud']['waarde']}")

    # -- 4. Terugverdientijd uitgebreid
    print("\n> TERUGVERDIENTIJD (voorbeeld: dakisolatie)\n" + _lijn())
    dak_opp     = opp["dak"]["opp_m2"]
    dak_rc_huidig = rc_waarden["dak"]["rc"]
    dak_rc_nieuw  = RC_NIEUW["dak"]

    if dak_opp > 0 and dak_rc_huidig < dak_rc_nieuw:
        besparing_dak = warmteverlies_reductie(dak_opp, dak_rc_huidig, dak_rc_nieuw)
        # Indicatieve investering: €40/m² (middenprijs dakisolatie)
        investering   = dak_opp * 40
        subsidie_ind  = dak_opp * 9.0   # indicatief ISDE dakisolatie (meervoudig tarief)
        netto_inv     = max(0.0, investering - subsidie_ind)

        tvt = terugverdientijd_uitgebreid(netto_inv, besparing_dak["euro_jr"])
        print(f"  Dak: {dak_opp:.0f} m² × €40/m² = €{investering:.0f}  "
              f"− subsidie €{subsidie_ind:.0f} = netto €{netto_inv:.0f}")
        print(f"  Besparing jaar 1: €{besparing_dak['euro_jr']:.2f}/jr")
        print(f"  Terugverdientijd: {tvt['tvt_jaar']} jaar "
              f"(prijsstijging {tvt['prijsstijging_gebruikt']*100:.1f}%/jr)")
        print(f"  Formule: {tvt['formule']}")
        print()
        print(f"  {'Jaar':>5}  {'Cum. besparing':>16}  {'Saldo (cum-inv)':>16}")
        print(f"  {'':->5}  {'':->16}  {'':->16}")
        for jaar, data in tvt["doorkijk"].items():
            saldo_str = f"€{data['saldo']:+.2f}"
            print(f"  {jaar:>5}  €{data['cum_besparing']:>14.2f}  {saldo_str:>16}")
    else:
        print("  Dak: overgeslagen (opp=0 of Rc al voldoende)")

    # -- 5. Waarschuwingen
    print("\n> WAARSCHUWINGEN\n" + _lijn())
    facts_test = {
        "bouwjaar":   bouwjaar,
        "woningtype": wtype,
        "geldig_tot": None,
    }
    ws = genereer_waarschuwingen(facts_test, opp, rc_waarden)

    if not ws:
        print("  Geen waarschuwingen.")
    else:
        for i, w_item in enumerate(ws, 1):
            niveau_symbool = {"info": "i", "let_op": "!", "risico": "X"}.get(
                w_item["niveau"], "?"
            )
            print(f"  {i}. [{w_item['niveau'].upper():7s}] {niveau_symbool}  "
                  f"Element: {w_item['element']}")
            print(f"     Bericht:      {w_item['bericht']}")
            print(f"     Aanbeveling:  {w_item['aanbeveling']}")
            print()


def main() -> None:
    print("\nPandIQ Isolatie Quickscan — Test nieuwe modules")
    print("Datum: 2026-04-29  |  aannames.py / oppervlaktes.py / financials / waarschuwingen.py")

    print("\n-- Aannames-overzicht (selectie) --")
    for key in ("gasprijs", "energieinhoud_gas", "cv_rendement_oud",
                "temperatuurverschil_dt", "verwarmingsuren_jr",
                "energieprijsstijging_pct", "rc_eis_dak"):
        a = AANNAMES[key]
        print(f"  {key:30s}: {a['waarde']} {a['eenheid']:12s} | {a['bron'][:60]}")

    for woning in WONINGEN:
        test_woning(woning)

    print("\n" + "=" * 70)
    print("  Test voltooid.")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
