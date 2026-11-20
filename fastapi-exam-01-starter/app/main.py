from fastapi import FastAPI
from app.database import Base, engine
from app.routers import auth,parcel,tracking

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Okwu Couriers API")

app.include_router(auth.router)
app.include_router(parcel.router)
app.include_router(tracking.router)


@app.get("/health")
def health():
    return {"status": "ok"}
