import math
import secrets
import string
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Parcel, StatusHistory, User
from app.schemas import ParcelCreate, ParcelListOut, ParcelOut, ParcelStatus, StatusUpdate
from app.security import get_current_user

router = APIRouter(prefix="/parcels", tags=["parcels"])

ALLOWED_TRANSITIONS = {
    ParcelStatus.CREATED: {ParcelStatus.PICKED_UP, ParcelStatus.CANCELLED},
    ParcelStatus.PICKED_UP: {ParcelStatus.IN_TRANSIT},
    ParcelStatus.IN_TRANSIT: {ParcelStatus.OUT_FOR_DELIVERY},
    ParcelStatus.OUT_FOR_DELIVERY: {ParcelStatus.DELIVERED, ParcelStatus.FAILED_DELIVERY},
    ParcelStatus.FAILED_DELIVERY: {ParcelStatus.OUT_FOR_DELIVERY, ParcelStatus.RETURNED},
    ParcelStatus.DELIVERED: set(),
    ParcelStatus.RETURNED: set(),
    ParcelStatus.CANCELLED: set(),
}


def calculate_price(weight_kg: float, origin_city: str, destination_city: str) -> int:
    billed_kg = math.ceil(weight_kg)
    price = 1500 + (400 * billed_kg)
    if origin_city != destination_city:
        price += 1000
    return price


def generate_tracking_code(db: Session) -> str:
    alphabet = string.ascii_uppercase + string.digits
    while True:
        code = "OKW-" + "".join(secrets.choice(alphabet) for _ in range(8))
        exists = db.query(Parcel.id).filter(Parcel.tracking_code == code).first()
        if not exists:
            return code


def get_owned_parcel(parcel_id: int, owner_id: int, db: Session) -> Parcel:
    parcel = db.query(Parcel).filter(Parcel.id == parcel_id, Parcel.owner_id == owner_id).first()
    if not parcel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parcel not found")
    return parcel


@router.post("", response_model=ParcelOut, status_code=status.HTTP_201_CREATED)
def create_parcel(
    payload: ParcelCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    parcel = Parcel(
        tracking_code=generate_tracking_code(db),
        sender_name=payload.sender_name.strip(),
        recipient_name=payload.recipient_name.strip(),
        recipient_phone=payload.recipient_phone,
        origin_city=payload.origin_city,
        destination_city=payload.destination_city,
        weight_kg=payload.weight_kg,
        price=calculate_price(payload.weight_kg, payload.origin_city, payload.destination_city),
        status=ParcelStatus.CREATED.value,
        owner_id=current_user.id,
    )
    db.add(parcel)
    db.flush()

    history_entry = StatusHistory(
        parcel_id=parcel.id,
        status=ParcelStatus.CREATED.value,
        note="Parcel created",
    )
    db.add(history_entry)
    db.commit()
    db.refresh(parcel)
    return parcel


@router.get("", response_model=ParcelListOut)
def list_parcels(
    status_filter: Optional[ParcelStatus] = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Parcel).filter(Parcel.owner_id == current_user.id)
    if status_filter is not None:
        query = query.filter(Parcel.status == status_filter.value)

    total = query.count()
    items = (
        query.order_by(Parcel.created_at.desc(), Parcel.id.desc())
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )
    return {"items": items, "total": total, "page": page, "size": size}


@router.get("/{parcel_id}", response_model=ParcelOut)
def get_parcel(
    parcel_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_owned_parcel(parcel_id, current_user.id, db)


@router.patch("/{parcel_id}/status", response_model=ParcelOut)
def update_parcel_status(
    parcel_id: int,
    payload: StatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    parcel = get_owned_parcel(parcel_id, current_user.id, db)
    current_status = ParcelStatus(parcel.status)

    if payload.status not in ALLOWED_TRANSITIONS[current_status]:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot transition from {current_status.value} to {payload.status.value}",
        )

    parcel.status = payload.status.value
    history_entry = StatusHistory(
        parcel_id=parcel.id,
        status=payload.status.value,
        note=payload.note,
    )
    db.add(history_entry)
    db.commit()
    db.refresh(parcel)
    return parcel


@router.delete("/{parcel_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_parcel(
    parcel_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    parcel = get_owned_parcel(parcel_id, current_user.id, db)
    if parcel.status != ParcelStatus.CREATED.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only parcels with CREATED status can be deleted",
        )
    db.delete(parcel)
    db.commit()
