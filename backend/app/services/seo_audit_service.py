from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any

import requests
from bs4 import BeautifulSoup
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import Business


def _get_business_or_raise(session: Session, business_id: int) -> Business:
    business = session.get(Business, business_id)
    if business is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business not found")
    return business


class SeoAuditResult(dict):
    """Typed container for SEO audit result payloads."""


class SeoAuditModel:
    """Simple SEO audit payload stored per business."""


def _get_session() -> Session:
    return SessionLocal()


def _extract_meta_tags(html: str) -> dict[str, Any]:
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.get_text(strip=True) if soup.title else None
    meta_description = None
    meta_keywords = None
    canonical = None
    viewport = None
    charset = None
    og_title = None
    og_description = None
    twitter_card = None

    for meta in soup.find_all("meta"):
        name = (meta.get("name") or meta.get("property") or "").lower()
        content = meta.get("content", "")
        if name == "description":
            meta_description = content.strip() or None
        elif name == "keywords":
            meta_keywords = content.strip() or None
        elif name == "viewport":
            viewport = content.strip() or None
        elif name == "charset":
            charset = content.strip() or None
        elif name == "og:title":
            og_title = content.strip() or None
        elif name == "og:description":
            og_description = content.strip() or None
        elif name == "twitter:card":
            twitter_card = content.strip() or None

    canonical_tag = soup.find("link", rel=lambda value: value and "canonical" in value.lower())
    if canonical_tag:
        canonical = canonical_tag.get("href")

    return {
        "title": title,
        "meta_description": meta_description,
        "meta_keywords": meta_keywords,
        "canonical": canonical,
        "viewport": viewport,
        "charset": charset,
        "og_title": og_title,
        "og_description": og_description,
        "twitter_card": twitter_card,
    }


def _extract_headings(soup: BeautifulSoup) -> dict[str, int]:
    return {
        "h1": len(soup.find_all("h1")),
        "h2": len(soup.find_all("h2")),
        "h3": len(soup.find_all("h3")),
    }


def _extract_images(soup: BeautifulSoup) -> dict[str, int]:
    images = soup.find_all("img")
    alt_missing = sum(1 for image in images if not image.get("alt"))
    return {"total_images": len(images), "images_without_alt": alt_missing}


def _extract_technical_signals(html: str, soup: BeautifulSoup) -> dict[str, bool]:
    robots = bool(re.search(r"robots\.txt", html, re.IGNORECASE))
    sitemap = bool(re.search(r"sitemap\.xml", html, re.IGNORECASE))
    favicon = bool(soup.find("link", rel=lambda value: value and "icon" in value.lower()))
    schema = bool(soup.find_all(attrs={"type": "application/ld+json"}))
    og_tags = bool(soup.find_all("meta", attrs={"property": re.compile(r"og:")}))
    twitter_cards = bool(soup.find_all("meta", attrs={"name": re.compile(r"twitter:")}))
    return {
        "robots": robots,
        "sitemap": sitemap,
        "favicon": favicon,
        "schema": schema,
        "open_graph": og_tags,
        "twitter_cards": twitter_cards,
    }


def _extract_contact_details(html: str) -> dict[str, Any]:
    email_match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", html)
    phone_match = re.search(r"(?:\+\d[\d\s().-]{7,}|\(\d{3}\)[\s\-.]?\d{3}[\s\-.]?\d{4})", html)
    address_match = re.search(r"\d+\s+\w+", html)
    return {
        "email": email_match.group(0) if email_match else None,
        "phone": phone_match.group(0) if phone_match else None,
        "address": address_match.group(0) if address_match else None,
    }


def _extract_social_links(soup: BeautifulSoup) -> dict[str, Any]:
    links: dict[str, Any] = {}
    for link in soup.find_all("a", href=True):
        href = link["href"]
        if "facebook.com" in href:
            links["facebook"] = href
        if "instagram.com" in href:
            links["instagram"] = href
        if "linkedin.com" in href:
            links["linkedin"] = href
        if "twitter.com" in href or "x.com" in href:
            links["twitter"] = href
        if "youtube.com" in href:
            links["youtube"] = href
    return links


def _calculate_score(metrics: dict[str, Any]) -> int:
    score = 0
    if metrics.get("https_enabled"):
        score += 10
    if metrics.get("title"):
        score += 10
    if metrics.get("meta_description"):
        score += 10
    if metrics.get("h1"):
        score += 10
    if metrics.get("images_without_alt", 0) == 0:
        score += 10
    if metrics.get("robots"):
        score += 10
    if metrics.get("sitemap"):
        score += 10
    if metrics.get("canonical"):
        score += 10
    if metrics.get("open_graph"):
        score += 10
    if metrics.get("schema"):
        score += 10
    if metrics.get("viewport"):
        score += 10
    if metrics.get("email") or metrics.get("phone") or metrics.get("address"):
        score += 10
    return min(score, 100)


def _issues_found(metrics: dict[str, Any]) -> int:
    checks = [
        ("https_enabled", not metrics.get("https_enabled")),
        ("title", not metrics.get("title")),
        ("meta_description", not metrics.get("meta_description")),
        ("h1", not metrics.get("h1")),
        ("images_without_alt", metrics.get("images_without_alt", 0) > 0),
        ("robots", not metrics.get("robots")),
        ("sitemap", not metrics.get("sitemap")),
        ("canonical", not metrics.get("canonical")),
        ("open_graph", not metrics.get("open_graph")),
        ("schema", not metrics.get("schema")),
        ("viewport", not metrics.get("viewport")),
        ("contact_detected", not (metrics.get("email") or metrics.get("phone") or metrics.get("address"))),
    ]
    return sum(1 for _, is_issue in checks if is_issue)


def run_seo_audit(business_id: int) -> dict[str, Any]:
    session = _get_session()
    try:
        business = _get_business_or_raise(session, business_id)
        if not business.website:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Business has no website")

        try:
            response = requests.get(business.website, timeout=10)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Unable to fetch website: {exc}") from exc

        html = response.text
        final_url = response.url
        https_enabled = final_url.startswith("https://")
        soup = BeautifulSoup(html, "html.parser")
        meta_tags = _extract_meta_tags(html)
        headings = _extract_headings(soup)
        images = _extract_images(soup)
        technical_signals = _extract_technical_signals(html, soup)
        contact_details = _extract_contact_details(html)
        social_links = _extract_social_links(soup)

        metrics = {
            "website_reachable": True,
            "http_status": response.status_code,
            "https_enabled": https_enabled,
            "final_url": final_url,
            "title": bool(meta_tags.get("title")),
            "meta_description": bool(meta_tags.get("meta_description")),
            "meta_keywords": bool(meta_tags.get("meta_keywords")),
            "canonical": bool(meta_tags.get("canonical")),
            "h1": headings.get("h1", 0),
            "h2": headings.get("h2", 0),
            "h3": headings.get("h3", 0),
            "total_images": images.get("total_images", 0),
            "images_without_alt": images.get("images_without_alt", 0),
            "html_size": len(html.encode("utf-8")),
            "css_files": len(soup.find_all("link", rel=lambda value: value and "stylesheet" in value.lower())),
            "js_files": len(soup.find_all("script", src=True)),
            "robots": technical_signals.get("robots"),
            "sitemap": technical_signals.get("sitemap"),
            "favicon": technical_signals.get("favicon"),
            "viewport": bool(meta_tags.get("viewport")),
            "charset": bool(meta_tags.get("charset")),
            "open_graph": technical_signals.get("open_graph"),
            "twitter_cards": technical_signals.get("twitter_cards"),
            "schema": technical_signals.get("schema"),
            "email": contact_details.get("email"),
            "phone": contact_details.get("phone"),
            "address": contact_details.get("address"),
            **social_links,
        }
        metrics["score"] = _calculate_score(metrics)
        metrics["issues_found"] = _issues_found(metrics)
        payload = {
            "business_id": business_id,
            "status": "completed",
            "score": metrics["score"],
            "issues_found": metrics["issues_found"],
            "metrics": metrics,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        business.seo_audit = json.dumps(payload)
        business.seo_score = metrics["score"]
        business.seo_issues_found = metrics["issues_found"]
        session.commit()
        session.refresh(business)
        return payload
    except HTTPException:
        raise
    except Exception as exc:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
    finally:
        session.close()


def get_seo_audit(business_id: int) -> dict[str, Any]:
    session = _get_session()
    try:
        business = _get_business_or_raise(session, business_id)
        if not business.seo_audit:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SEO audit not found")
        return json.loads(business.seo_audit)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
    finally:
        session.close()
