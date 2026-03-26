from __future__ import annotations

import os
from typing import Any, Optional

import requests


def get_adressen_uitgebreid(
    postcode: str,
    huisnummer: str,
    config: dict,
    exacte_match: bool = True,
    toevoeging: Optional[str] = None,
    huisletter: Optional[str] = None,
) -> dict[str, Any]:
    bag_cfg = config.get("bag", {})
    base_url = (bag_cfg.get("base_url") or "").rstrip("/")
    timeout = int(bag_cfg.get("timeout_seconds") or 15)

    endpoint = f"{base_url}/adressenuitgebreid"

    params: dict[str, Any] = {
        "postcode": postcode.replace(" ", "").upper(),
        "huisnummer": int(huisnummer),
    }
    if exacte_match:
        params["exacteMatch"] = "true"
    if toevoeging:
        params["huisnummertoevoeging"] = toevoeging
    if huisletter:
        params["huisletter"] = huisletter

    headers = {
        "Accept": "application/hal+json",
        "Accept-Crs": "epsg:28992",
    }

    api_key = os.getenv("BAG_API_KEY", "").strip()
    if api_key:
        headers["X-Api-Key"] = api_key
    else:
        import warnings
        warnings.warn(
            "BAG_API_KEY is niet ingesteld in .env. BAG-verzoeken kunnen mislukken (HTTP 401). "
            "Stel de sleutel in via BAG_API_KEY=... in uw .env bestand.",
            stacklevel=2,
        )

    r = requests.get(endpoint, params=params, headers=headers, timeout=timeout)
    r.raise_for_status()
    return r.json()
