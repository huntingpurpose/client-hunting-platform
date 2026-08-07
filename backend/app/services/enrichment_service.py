from __future__ import annotations

import re
from typing import Any

import requests
from bs4 import BeautifulSoup
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import Business


class EnrichmentResult(dict):
    """Typed result container for business enrichment."""


def _get_session() -> Session:
    return SessionLocal()


def _extract_email(html: str) -> str | None:
    matches = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", html)
    return matches[0] if matches else None


def _extract_phone(html: str) -> str | None:
    patterns = [
        r"tel:([+\d\-\s()]+)",
        r"\+[1-9]\d{1,14}(?:[-.\s]?\d{1,4})*",
        r"(?:\(0\d{3,4}\)|0\d{3,4})[\s\-.]?\d{3,4}[\s\-.]?\d{3,4}",
        r"(?:\(\d{3}\)[\s\-.]?\d{3}[\s\-.]?\d{4}|\d{3}[\s\-.]?\d{3}[\s\-.]?\d{4})",
    ]
    for pattern in patterns:
        matches = re.findall(pattern, html)
        if matches:
            value = matches[0].strip() if isinstance(matches[0], str) else str(matches[0]).strip()
            if len(re.sub(r"[^\d+]", "", value)) >= 7:
                return value
    return None


def _extract_social_links(html: str) -> tuple[str | None, str | None, str | None]:
    soup = BeautifulSoup(html, "html.parser")
    facebook = instagram = linkedin = None
    for link in soup.find_all("a", href=True):
        href = link["href"]
        if "facebook.com" in href and facebook is None:
            facebook = href
        if "instagram.com" in href and instagram is None:
            instagram = href
        if "linkedin.com" in href and linkedin is None:
            linkedin = href
    return facebook, instagram, linkedin


def _extract_owner_name(html: str) -> str | None:
    soup = BeautifulSoup(html, "html.parser")
    meta_author = soup.find("meta", attrs={"name": "author"})
    if meta_author and meta_author.get("content"):
        return meta_author.get("content").strip()
    return None


def enrich_business(business_id: int) -> dict[str, Any]:
    session = _get_session()
    try:
        business = session.get(Business, business_id)
        if business is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business not found")
        if not business.website:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Business has no website")

        try:
            response = requests.get(business.website, timeout=10)
            response.raise_for_status()
            html = response.text
        except requests.RequestException as exc:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Unable to fetch website: {exc}") from exc

        email = _extract_email(html)
        phone = _extract_phone(html)
        facebook, instagram, linkedin = _extract_social_links(html)
        owner_name = _extract_owner_name(html)

        business.email = email or business.email
        business.phone = phone or business.phone
        business.facebook = facebook or business.facebook
        business.instagram = instagram or business.instagram
        business.linkedin = linkedin or business.linkedin
        business.owner_name = owner_name or business.owner_name
        session.commit()
        session.refresh(business)

        return {
            "email": business.email,
            "phone": business.phone,
            "facebook": business.facebook,
            "instagram": business.instagram,
            "linkedin": business.linkedin,
            "owner_name": business.owner_name,
        }
    except HTTPException:
        raise
    except Exception as exc:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
    finally:
        session.close()
