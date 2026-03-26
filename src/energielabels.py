from __future__ import annotations
import os
from typing import Any, Optional
import requests

def _normalize_label_record(rec: dict[str, Any]) -> dict[str, Any]:
    return {
        "registratiedatum": rec.get("Registratiedatum"),
        "opnamedatum": rec.get("Opnamedatum"),
        "geldig_tot": rec.get("Geldig_tot"),
        "certificaathouder": rec.get("Certificaathouder"),
        "soort_opname": rec.get("Soort_opname"),
        "status": rec.get("Status"),
        "berekeningstype": rec.get("Berekeningstype"),
        "gebouwklasse": rec.get("Gebouwklasse"),
        "gebouwtype": rec.get("Gebouwtype"),
        "postcode": rec.get("Postcode"),
        "huisnummer": rec.get("Huisnummer"),
        "bag_verblijfsobject_id": rec.get("BAGVerblijfsobjectID"),
        "bag_pand_ids": rec.get("BAGPandIDs") or [],
        "bouwjaar": rec.get("Bouwjaar"),
        "labelklasse": rec.get("Energieklasse"),
        "energiebehoefte": rec.get("Energiebehoefte"),
        "warmtebehoefte": rec.get("Warmtebehoefte"),
        "opp_thermische_zone": rec.get("Gebruiksoppervlakte_thermische_zone"),
        "prim_fossiel": rec.get("PrimaireFossieleEnergie"),
        "compactheid": rec.get("Compactheid"),
        "aandeel_hernieuwbaar": rec.get("Aandeel_hernieuwbare_energie"),
    }

def find_label_for_address(
    postcode: str,
    huisnummer: str,
    config: dict,
    toevoeging: Optional[str] = None,
    huisletter: Optional[str] = None,
) -> Optional[dict[str, Any]]:
    labels_cfg = config.get("labels", {})
    base_url = (labels_cfg.get("base_url") or "").rstrip("/")
    path = labels_cfg.get("search_path") or "/api/v5/PandEnergielabel/Adres"
    timeout = int(labels_cfg.get("timeout_seconds") or 15)
    api_key_env = labels_cfg.get("api_key_env") or "EPONLINE_API_KEY"
    auth_prefix = labels_cfg.get("auth_prefix") or ""

    if not base_url.startswith("http"):
        raise ValueError("labels.base_url is ongeldig (verwacht https://...)")

    endpoint = f"{base_url}{path}"
    api_key = os.getenv(api_key_env, "").strip()

    headers = {"Accept": "application/json"}
    if api_key:
        headers["Authorization"] = f"{auth_prefix}{api_key}"

    params: dict[str, Any] = {
        "postcode": postcode.replace(" ", "").upper(),
        "huisnummer": int(huisnummer),
    }
    if huisletter:
        params["huisletter"] = huisletter
    if toevoeging:
        params["huisnummertoevoeging"] = toevoeging

    r = requests.get(endpoint, params=params, headers=headers, timeout=timeout)
    if r.status_code == 404:
        return None
    if r.status_code == 401:
        raise PermissionError("EP-Online 401 Unauthorized: controleer EPONLINE_API_KEY en labels.auth_prefix.")
    r.raise_for_status()

    data = r.json()
    if not isinstance(data, list) or not data:
        return None
    first = data[0]
    if not isinstance(first, dict):
        return None
    return _normalize_label_record(first)
