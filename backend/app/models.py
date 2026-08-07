from __future__ import annotations

from sqlalchemy import Column, Float, Integer, String
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all ORM models in the platform."""


class Business(Base):
    __tablename__ = "businesses"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    website = Column(String(1024), nullable=True)
    phone = Column(String(64), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    email = Column(String(255), nullable=True)
    facebook = Column(String(1024), nullable=True)
    instagram = Column(String(1024), nullable=True)
    linkedin = Column(String(1024), nullable=True)
