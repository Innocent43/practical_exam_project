from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Parcel
from app.schemas import PublicTrackingOut

router = APIRouter(prefix="/track", tags=["tracking"])


@router.get("/{tracking_code}", response_model=PublicTrackingOut)
def track_parcel(tracking_code: str, db: Session = Depends(get_db)):
    parcel = db.query(Parcel).filter(Parcel.tracking_code == tracking_code).first()
    if not parcel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tracking code not found")
    return parcel
