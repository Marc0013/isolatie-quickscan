from __future__ import annotations
import requests

def resolve_address_docid(postcode: str, huisnummer: str, config: dict) -> str:
    pdok = config.get("pdok", {})
    url = pdok.get("suggest_url")
    if not url:
        raise ValueError("pdok.suggest_url ontbreekt in config.json")
    timeout = int(pdok.get("timeout_seconds", 15))
    params = {"q": f"{postcode} {huisnummer}", "rows": 1}
    r = requests.get(url, params=params, timeout=timeout)
    r.raise_for_status()
    data = r.json()
    docs = data.get("response", {}).get("docs", [])
    if not docs:
        raise ValueError("PDOK suggest gaf geen adres-resultaat")
    return docs[0]["id"]

def pdok_lookup(docid: str, config: dict) -> dict:
    pdok = config.get("pdok", {})
    url = pdok.get("lookup_url")
    if not url:
        raise ValueError("pdok.lookup_url ontbreekt in config.json")
    timeout = int(pdok.get("timeout_seconds", 15))
    r = requests.get(url, params={"id": docid}, timeout=timeout)
    r.raise_for_status()
    return r.json()
