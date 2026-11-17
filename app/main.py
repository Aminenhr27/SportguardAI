import bcrypt
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session
import datetime

from app import models, schemas
from app.database import SessionLocal
from app.services import risk_service, ml_service

app = FastAPI(title="SportGuard AI")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/athletes")
def create_athlete(data: schemas.AthleteCreate, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.email == data.email).first():
        raise HTTPException(status_code=400, detail="Email déjà utilisé")

    hashed = bcrypt.hashpw(data.password.encode(), bcrypt.gensalt()).decode()
    user = models.User(
        name=data.name, email=data.email, password_hash=hashed, role="athlete"
    )
    db.add(user)
    db.flush()

    athlete = models.Athlete(
        user_id=user.id,
        age=data.age,
        weight=data.weight,
        height=data.height,
        sport=data.sport,
        position=data.position,
    )
    db.add(athlete)
    db.commit()
    db.refresh(athlete)
    return {"id": athlete.id, "name": user.name, "sport": athlete.sport}



@app.post("/sessions")
def create_session(data: schemas.SessionCreate, db: Session = Depends(get_db)):
    athlete = db.get(models.Athlete, data.athlete_id)
    if not athlete:
        raise HTTPException(status_code=404, detail="Athlète introuvable")

    session = models.TrainingSession(
        athlete_id=data.athlete_id,
        date=data.date,
        duration=data.duration,
        intensity=data.intensity,
        training_type=data.training_type,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return {"id": session.id, "load": session.load}



@app.post("/wellness")
def create_wellness(data: schemas.WellnessCreate, db: Session = Depends(get_db)):
    if not db.get(models.Athlete, data.athlete_id):
        raise HTTPException(status_code=404, detail="Athlète introuvable")

    exists = (
        db.query(models.DailyWellness)
        .filter_by(athlete_id=data.athlete_id, date=data.date)
        .first()
    )
    if exists:
        raise HTTPException(status_code=400, detail="Bien-être déjà saisi ce jour")

    wellness = models.DailyWellness(**data.model_dump())
    db.add(wellness)
    db.commit()
    db.refresh(wellness)
    return {"id": wellness.id, "date": wellness.date}



@app.get("/athletes/{athlete_id}/workload")
def get_workload(
    athlete_id: int,
    on: datetime.date | None = None,
    db: Session = Depends(get_db),
):
    if not db.get(models.Athlete, athlete_id):
        raise HTTPException(status_code=404, detail="Athlète introuvable")
    return risk_service.compute_workload(db, athlete_id, on or datetime.date.today())



@app.get("/athletes/{athlete_id}/risk")
def get_risk(
    athlete_id: int,
    on: datetime.date | None = None,
    db: Session = Depends(get_db),
):
    if not db.get(models.Athlete, athlete_id):
        raise HTTPException(status_code=404, detail="Athlète introuvable")

    on = on or datetime.date.today()
    workload = risk_service.compute_workload(db, athlete_id, on)
    wellness = risk_service.wellness_averages(db, athlete_id, on)
    if workload["acwr"] is None or wellness is None:
        raise HTTPException(
            status_code=400,
            detail="Pas assez de données (séances ou bien-être) sur les 7 derniers jours",
        )

    features = {
        "acute_load": workload["acute_load"],
        "chronic_load": workload["chronic_load"],
        "acwr": workload["acwr"],
        **wellness,
    }
    score = ml_service.predict_risk(features)
    level = ml_service.risk_level(score)

    prediction = models.RiskPrediction(
        athlete_id=athlete_id,
        prediction_date=on,
        risk_score=round(score, 3),
        risk_level=level,
        model_version=ml_service.model_version(),
    )
    db.add(prediction)
    db.commit()

    return {
        "athlete_id": athlete_id,
        "date": on,
        "risk_score": round(score, 3),
        "risk_level": level,
        "features": features,
    }