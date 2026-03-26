"""
streetview.py
=============
Haalt een Google Street View Static API afbeelding op voor een gegeven adres.

Veiligheid:
  - Lokale dagelijkse teller in streetview_counter.json (max 900/dag)
  - Cache: eenmaal opgehaalde foto wordt lokaal opgeslagen, nooit opnieuw aangevraagd
  - Bij limiet of fout: placeholder afbeelding wordt teruggegeven

URL-opbouw:
  https://maps.googleapis.com/maps/api/streetview
    ?size=600x400
    &location={lat},{lng}
    &fov=90
    &pitch=0
    &key={GOOGLE_STREETVIEW_API_KEY}

Dagelijkse teller:
  Opgeslagen in streetview_counter.json naast dit bestand:
  {"date": "2026-03-13", "count": 42}
  Elke dag om middernacht reset de teller automatisch.

Foutcodes van Google:
  403  → API-sleutel ongeldig of quota op Google-zijde overschreden
  404  → Geen Street View beschikbaar op dit adres (status: ZERO_RESULTS)
"""

from __future__ import annotations

import json
import os
import hashlib
import requests
from datetime import date
from pathlib import Path

# ── Configuratie ────────────────────────────────────────────
DAGELIJKSE_LIMIET = 900          # Harde stop om binnen $200 gratis krediet te blijven
IMG_BREEDTE       = 600
IMG_HOOGTE        = 400
FOV               = 90           # Field of view (gezichtshoek), 90 = normaal

# Paden
_BASIS_DIR   = Path(__file__).parent
COUNTER_FILE = _BASIS_DIR / "streetview_counter.json"
CACHE_DIR    = _BASIS_DIR / "cache" / "streetview"

PLACEHOLDER_URL = None  # Optioneel: pad naar een lokale placeholder afbeelding


# ── Teller ──────────────────────────────────────────────────

def _lees_teller() -> dict:
    """Leest de dagelijkse teller uit het JSON-bestand."""
    vandaag = str(date.today())
    if COUNTER_FILE.exists():
        try:
            data = json.loads(COUNTER_FILE.read_text(encoding="utf-8"))
            if data.get("date") == vandaag:
                return data
        except Exception:
            pass
    # Nieuw bestand of nieuwe dag → reset
    return {"date": vandaag, "count": 0}


def _sla_teller_op(teller: dict) -> None:
    COUNTER_FILE.write_text(json.dumps(teller, indent=2), encoding="utf-8")


def _teller_verhogen() -> int:
    """Verhoogt de teller met 1 en slaat op. Geeft nieuw aantal terug."""
    teller = _lees_teller()
    teller["count"] += 1
    _sla_teller_op(teller)
    return teller["count"]


def dagelijkse_limiet_bereikt() -> bool:
    """Geeft True terug als de dagelijkse limiet bereikt is."""
    return _lees_teller()["count"] >= DAGELIJKSE_LIMIET


def verzoeken_vandaag() -> int:
    """Geeft het aantal verzoeken van vandaag terug."""
    return _lees_teller()["count"]


# ── Cache ────────────────────────────────────────────────────

def _cache_pad(lat: float, lng: float) -> Path:
    """Geeft het pad naar de gecachte afbeelding terug."""
    sleutel = hashlib.md5(f"{lat:.6f},{lng:.6f}".encode()).hexdigest()
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR / f"{sleutel}.jpg"


def _in_cache(lat: float, lng: float) -> bool:
    return _cache_pad(lat, lng).exists()


def _uit_cache(lat: float, lng: float) -> bytes:
    return _cache_pad(lat, lng).read_bytes()


def _sla_in_cache(lat: float, lng: float, data: bytes) -> None:
    _cache_pad(lat, lng).write_bytes(data)


# ── Placeholder ──────────────────────────────────────────────

def _placeholder_bytes() -> bytes | None:
    """
    Geeft een eenvoudige placeholder terug als bytes.
    Als er een lokale placeholder beschikbaar is, gebruik die.
    Anders wordt None teruggegeven (geen afbeelding).
    """
    if PLACEHOLDER_URL and Path(PLACEHOLDER_URL).exists():
        return Path(PLACEHOLDER_URL).read_bytes()
    return None


# ── Hoofdfunctie ────────────────────────────────────────────

def haal_streetview_op(
    lat: float,
    lng: float,
    api_key: str | None = None,
) -> tuple[bytes | None, str]:
    """
    Haalt een Street View afbeelding op voor de gegeven coördinaten.

    Parameters
    ----------
    lat     : Breedtegraad (bijv. 53.2194)
    lng     : Lengtegraad  (bijv. 6.5665)
    api_key : Google Street View Static API-sleutel.
              Als None: wordt gelezen uit omgevingsvariabele GOOGLE_STREETVIEW_API_KEY

    Geeft terug
    -----------
    (bytes | None, status_tekst)
      bytes       → JPEG-afbeeldingsdata
      status_tekst → "ok" | "cache" | "limiet" | "geen_streetview" | "fout"
    """

    # API-sleutel ophalen
    if api_key is None:
        api_key = os.environ.get("GOOGLE_STREETVIEW_API_KEY", "")
    if not api_key:
        return None, "fout: geen API-sleutel ingesteld (GOOGLE_STREETVIEW_API_KEY)"

    # ── Stap 1: Check cache ──────────────────────────────────
    if _in_cache(lat, lng):
        print(f"  [Street View] Cache hit voor ({lat}, {lng})")
        return _uit_cache(lat, lng), "cache"

    # ── Stap 2: Check dagelijkse limiet ─────────────────────
    if dagelijkse_limiet_bereikt():
        resterend = DAGELIJKSE_LIMIET - verzoeken_vandaag()
        print(
            f"  [Street View] Dagelijkse limiet bereikt ({DAGELIJKSE_LIMIET} verzoeken). "
            f"Resterend vandaag: {resterend}"
        )
        return _placeholder_bytes(), "limiet"

    # ── Stap 3: API aanroepen ────────────────────────────────
    # Eerst controleren of er Street View beschikbaar is (metadata endpoint = GEEN kosten)
    meta_url = "https://maps.googleapis.com/maps/api/streetview/metadata"
    meta_params = {"location": f"{lat},{lng}", "key": api_key}

    try:
        meta_resp = requests.get(meta_url, params=meta_params, timeout=10)
        meta_resp.raise_for_status()
        meta_data = meta_resp.json()

        if meta_data.get("status") != "OK":
            print(f"  [Street View] Geen Street View beschikbaar op ({lat}, {lng}): {meta_data.get('status')}")
            return _placeholder_bytes(), "geen_streetview"

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 403:
            print("  [Street View] FOUT 403: API-sleutel ongeldig of Google quota overschreden.")
            return _placeholder_bytes(), "fout_403"
        print(f"  [Street View] HTTP fout bij metadata: {e}")
        return _placeholder_bytes(), f"fout_http_{e.response.status_code}"
    except requests.exceptions.RequestException as e:
        print(f"  [Street View] Verbindingsfout: {e}")
        return _placeholder_bytes(), "fout_verbinding"

    # ── Stap 4: Afbeelding ophalen ───────────────────────────
    img_url = "https://maps.googleapis.com/maps/api/streetview"
    img_params = {
        "size":     f"{IMG_BREEDTE}x{IMG_HOOGTE}",
        "location": f"{lat},{lng}",
        "fov":      FOV,
        "pitch":    0,
        "key":      api_key,
    }

    try:
        img_resp = requests.get(img_url, params=img_params, timeout=15)
        img_resp.raise_for_status()

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 403:
            print("  [Street View] FOUT 403: API-sleutel ongeldig of Google quota overschreden.")
            return _placeholder_bytes(), "fout_403"
        print(f"  [Street View] HTTP fout bij afbeelding: {e}")
        return _placeholder_bytes(), f"fout_http_{e.response.status_code}"
    except requests.exceptions.RequestException as e:
        print(f"  [Street View] Verbindingsfout: {e}")
        return _placeholder_bytes(), "fout_verbinding"

    # ── Stap 5: Opslaan in cache + teller verhogen ───────────
    afbeelding = img_resp.content
    _sla_in_cache(lat, lng, afbeelding)
    aantal = _teller_verhogen()
    print(f"  [Street View] Opgehaald en gecached. Verzoeken vandaag: {aantal}/{DAGELIJKSE_LIMIET}")

    return afbeelding, "ok"


# ── Status opvragen ─────────────────────────────────────────

def status() -> dict:
    """Geeft een overzicht van de huidige teller en cache."""
    teller = _lees_teller()
    cache_bestanden = list(CACHE_DIR.glob("*.jpg")) if CACHE_DIR.exists() else []
    return {
        "datum":              teller["date"],
        "verzoeken_vandaag":  teller["count"],
        "limiet":             DAGELIJKSE_LIMIET,
        "resterend":          max(0, DAGELIJKSE_LIMIET - teller["count"]),
        "cache_bestanden":    len(cache_bestanden),
    }


# ── Standalone test ─────────────────────────────────────────
if __name__ == "__main__":
    import sys

    print("Street View module status:")
    s = status()
    for k, v in s.items():
        print(f"  {k}: {v}")

    # Test met coördinaten van Joeswerd 107 Groningen
    lat, lng = 53.2194, 6.5665
    print(f"\nTest ophalen voor ({lat}, {lng})...")

    data, status_code = haal_streetview_op(lat, lng)
    if data:
        pad = Path("test_streetview.jpg")
        pad.write_bytes(data)
        print(f"Opgeslagen als: {pad} ({len(data)} bytes) — status: {status_code}")
    else:
        print(f"Geen afbeelding beschikbaar — status: {status_code}")
