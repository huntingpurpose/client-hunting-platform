from __future__ import annotations

from typing import Any

import requests
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import Business


class SearchRequest(dict):
    """Compatibility shim for the milestone 3 request payload."""


class SearchRequestPayload(dict):
    """Compatibility shim for the milestone 3 request payload."""


def _get_session() -> Session:
    return SessionLocal()


def _build_overpass_query(query: str) -> str:
    escaped_query = query.strip().replace("\"", "")
    return f"""
[out:json][timeout:25];
(
  node["shop"~"{escaped_query}"](around:5000);
  node["amenity"~"{escaped_query}"](around:5000);
);
out center;
"""


def _extract_business_data(element: dict[str, Any]) -> dict[str, Any] | None:
    tags = element.get("tags") or {}
    name = tags.get("name") or "Unnamed Business"
    if not name or name == "Unnamed Business":
        return None

    lat = element.get("lat")
    lon = element.get("lon")
    if element.get("center"):
        lat = element["center"].get("lat")
        lon = element["center"].get("lon")

    if lat is None or lon is None:
        return None

    address_parts = [
        tags.get("addr:street"),
        tags.get("addr:city"),
        tags.get("addr:state"),
        tags.get("addr:country"),
        tags.get("addr:postcode"),
    ]
    address = ", ".join(part for part in address_parts if part)

    return {
        "name": name,
        "category": tags.get("amenity") or tags.get("shop") or None,
        "address": address or None,
        "city": tags.get("addr:city") or None,
        "state": tags.get("addr:state") or None,
        "country": tags.get("addr:country") or None,
        "postal_code": tags.get("addr:postcode") or None,
        "latitude": float(lat),
        "longitude": float(lon),
        "website": tags.get("website") or None,
        "phone": tags.get("phone") or None,
    }


def _business_exists(session: Session, name: str, latitude: float, longitude: float) -> bool:
    existing = session.execute(
        select(Business).where(
            Business.name == name,
            Business.latitude == latitude,
            Business.longitude == longitude,
        )
    ).scalar_one_or_none()
    return existing is not None


def collect_businesses(query: str) -> dict[str, int]:
    if not query or not query.strip():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="query is required")

    session = _get_session()
    try:
        response = requests.post(
            "https://overpass-api.de/api/interpreter",
            data=_build_overpass_query(query),
            headers={"User-Agent": "ClientHuntingPlatform/1.0", "Accept": "application/json"},
            timeout=20,
        )
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Unable to collect businesses: {exc}") from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Invalid response from collector") from exc

    elements = payload.get("elements", [])
    inserted = 0
    duplicates = 0

    for element in elements:
        business_data = _extract_business_data(element)
        if not business_data:
            continue

        if _business_exists(session, business_data["name"], business_data["latitude"], business_data["longitude"]):
            duplicates += 1
            continue

        business = Business(
            name=business_data["name"],
            category=business_data["category"],
            address=business_data["address"],
            city=business_data["city"],
            state=business_data["state"],
            country=business_data["country"],
            postal_code=business_data["postal_code"],
            latitude=business_data["latitude"],
            longitude=business_data["longitude"],
            website=business_data["website"],
            phone=business_data["phone"],
            status="active",
        )
        session.add(business)
        inserted += 1

    try:
        session.commit()
    except Exception as exc:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
    finally:
        session.close()

    return {
        "inserted": inserted,
        "duplicates": duplicates,
        "total": inserted + duplicates,
    }
