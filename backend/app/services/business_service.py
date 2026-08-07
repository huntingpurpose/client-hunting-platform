from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status
from pydantic import BaseModel, ConfigDict, EmailStr, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import Business


class BusinessCreateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str
    category: str | None = None
    website: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    postal_code: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    google_maps_url: str | None = None
    google_rating: float | None = None
    review_count: int | None = None
    business_hours: str | None = None
    facebook: str | None = None
    instagram: str | None = None
    linkedin: str | None = None
    status: str | None = "active"

    @field_validator("website")
    @classmethod
    def validate_website(cls, value: str | None) -> str | None:
        if value is None or value == "":
            return value
        if not value.startswith(("http://", "https://")):
            raise ValueError("website must be a valid URL")
        return value

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str | None) -> str | None:
        if value is None or value == "":
            return value
        if len(value.replace("-", "").replace("+", "").replace(" ", "")) < 7:
            raise ValueError("phone must be at least 7 digits")
        return value


class BusinessUpdateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str | None = None
    category: str | None = None
    website: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    postal_code: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    google_maps_url: str | None = None
    google_rating: float | None = None
    review_count: int | None = None
    business_hours: str | None = None
    facebook: str | None = None
    instagram: str | None = None
    linkedin: str | None = None
    status: str | None = None

    @field_validator("website")
    @classmethod
    def validate_website(cls, value: str | None) -> str | None:
        if value is None or value == "":
            return value
        if not value.startswith(("http://", "https://")):
            raise ValueError("website must be a valid URL")
        return value

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str | None) -> str | None:
        if value is None or value == "":
            return value
        if len(value.replace("-", "").replace("+", "").replace(" ", "")) < 7:
            raise ValueError("phone must be at least 7 digits")
        return value


def _get_session() -> Session:
    return SessionLocal()


def _serialize_business(business: Business) -> dict[str, Any]:
    return {
        "id": business.id,
        "name": business.name,
        "category": business.category,
        "website": business.website,
        "email": business.email,
        "phone": business.phone,
        "address": business.address,
        "city": business.city,
        "state": business.state,
        "country": business.country,
        "postal_code": business.postal_code,
        "latitude": business.latitude,
        "longitude": business.longitude,
        "google_maps_url": business.google_maps_url,
        "google_rating": business.google_rating,
        "review_count": business.review_count,
        "business_hours": business.business_hours,
        "facebook": business.facebook,
        "instagram": business.instagram,
        "linkedin": business.linkedin,
        "status": business.status,
        "created_at": business.created_at.isoformat() if business.created_at else None,
        "updated_at": business.updated_at.isoformat() if business.updated_at else None,
    }


def create_business(payload: BusinessCreateRequest) -> dict[str, Any]:
    session = _get_session()
    try:
        business = Business(
            name=payload.name,
            category=payload.category,
            website=payload.website,
            email=payload.email.value if isinstance(payload.email, EmailStr) else payload.email,
            phone=payload.phone,
            address=payload.address,
            city=payload.city,
            state=payload.state,
            country=payload.country,
            postal_code=payload.postal_code,
            latitude=payload.latitude,
            longitude=payload.longitude,
            google_maps_url=payload.google_maps_url,
            google_rating=payload.google_rating,
            review_count=payload.review_count,
            business_hours=payload.business_hours,
            facebook=payload.facebook,
            instagram=payload.instagram,
            linkedin=payload.linkedin,
            status=payload.status or "active",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        session.add(business)
        session.commit()
        session.refresh(business)
        return _serialize_business(business)
    except Exception as exc:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
    finally:
        session.close()


def get_business(business_id: int) -> dict[str, Any]:
    session = _get_session()
    try:
        business = session.get(Business, business_id)
        if business is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business not found")
        return _serialize_business(business)
    finally:
        session.close()


def update_business(business_id: int, payload: BusinessUpdateRequest) -> dict[str, Any]:
    session = _get_session()
    try:
        business = session.get(Business, business_id)
        if business is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business not found")

        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == "email" and value is not None:
                setattr(business, field, value.value if isinstance(value, EmailStr) else value)
            else:
                setattr(business, field, value)

        business.updated_at = datetime.now(timezone.utc)
        session.commit()
        session.refresh(business)
        return _serialize_business(business)
    except Exception as exc:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
    finally:
        session.close()


def delete_business(business_id: int) -> dict[str, bool]:
    session = _get_session()
    try:
        business = session.get(Business, business_id)
        if business is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business not found")
        session.delete(business)
        session.commit()
        return {"deleted": True}
    except Exception as exc:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
    finally:
        session.close()


def list_businesses() -> list[dict[str, Any]]:
    session = _get_session()
    try:
        businesses = session.execute(select(Business).order_by(Business.id)).scalars().all()
        return [_serialize_business(item) for item in businesses]
    finally:
        session.close()
