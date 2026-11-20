from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(80), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)

    parcels = relationship("Parcel", back_populates="owner")


class Parcel(Base):
    __tablename__ = "parcels"

    id = Column(Integer, primary_key=True, index=True)
    tracking_code = Column(String(12), unique=True, index=True, nullable=False)
    sender_name = Column(String(80), nullable=False)
    recipient_name = Column(String(80), nullable=False)
    recipient_phone = Column(String(20), nullable=False)
    origin_city = Column(String(20), nullable=False)
    destination_city = Column(String(20), nullable=False)
    weight_kg = Column(Float, nullable=False)
    price = Column(Integer, nullable=False)
    status = Column(String(30), nullable=False, default="CREATED")
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    owner = relationship("User", back_populates="parcels")
    history = relationship(
        "StatusHistory",
        back_populates="parcel",
        cascade="all, delete-orphan",
        order_by="StatusHistory.id.asc()",
    )


class StatusHistory(Base):
    __tablename__ = "status_history"

    id = Column(Integer, primary_key=True, index=True)
    parcel_id = Column(Integer, ForeignKey("parcels.id"), nullable=False)
    status = Column(String(30), nullable=False)
    note = Column(String(200), nullable=True)
    timestamp = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    parcel = relationship("Parcel", back_populates="history")
