import re
from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field, field_validator

ALLOWED_CITIES = {"Awka", "Onitsha", "Nnewi", "Enugu", "Asaba", "Owerri"}


class ParcelStatus(str, Enum):
    CREATED = "CREATED"
    PICKED_UP = "PICKED_UP"
    IN_TRANSIT = "IN_TRANSIT"
    OUT_FOR_DELIVERY = "OUT_FOR_DELIVERY"
    DELIVERED = "DELIVERED"
    FAILED_DELIVERY = "FAILED_DELIVERY"
    RETURNED = "RETURNED"
    CANCELLED = "CANCELLED"


class UserCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=80)
    email: EmailStr
    password: str = Field(..., min_length=8)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    name: str
    email: str

    model_config = {"from_attributes": True}


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ParcelCreate(BaseModel):
    sender_name: str = Field(..., min_length=2, max_length=80)
    recipient_name: str = Field(..., min_length=2, max_length=80)
    recipient_phone: str
    origin_city: str
    destination_city: str
    weight_kg: float = Field(..., gt=0, le=50)

    @field_validator("recipient_phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        if not re.fullmatch(r"^(0\d{10}|\+234\d{10})$", v):
            raise ValueError("Invalid Nigerian mobile number")
        return v

    @field_validator("origin_city", "destination_city")
    @classmethod
    def validate_city(cls, v: str) -> str:
        formatted = v.strip().title()
        if formatted not in ALLOWED_CITIES:
            raise ValueError(f"City must be one of: {', '.join(sorted(ALLOWED_CITIES))}")
        return formatted


class ParcelOut(BaseModel):
    id: int
    tracking_code: str
    sender_name: str
    recipient_name: str
    recipient_phone: str
    origin_city: str
    destination_city: str
    weight_kg: float
    price: int
    status: ParcelStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class ParcelListOut(BaseModel):
    items: List[ParcelOut]
    total: int
    page: int
    size: int


class StatusUpdate(BaseModel):
    status: ParcelStatus
    note: Optional[str] = Field(default=None, max_length=200)


class HistoryItemOut(BaseModel):
    status: ParcelStatus
    note: Optional[str]
    timestamp: datetime

    model_config = {"from_attributes": True}


class PublicTrackingOut(BaseModel):
    tracking_code: str
    status: ParcelStatus
    origin_city: str
    destination_city: str
    history: List[HistoryItemOut]

    model_config = {"from_attributes": True}
