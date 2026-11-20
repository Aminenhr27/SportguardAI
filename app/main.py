import bcrypt
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session
import datetime
from fastapi.middleware.cors import CORSMiddleware

from app import models, schemas
from app.database import SessionLocal
from app.services import risk_service, ml_service

app = FastAPI(title="SportGuard AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_methods=["*"],
    allow_headers=["*"],
)


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



@app.get("/athletes")
def list_athletes(db: Session = Depends(get_db)):
    athletes = db.query(models.Athlete).all()
    return [{"id": a.id, "name": a.user.name, "sport": a.sport} for a in athletes]


@app.get("/athletes/{athlete_id}/load-history")
def load_history(
    athlete_id: int,
    days: int = 28,
    on: datetime.date | None = None,
    db: Session = Depends(get_db),
):
    if not db.get(models.Athlete, athlete_id):
        raise HTTPException(status_code=404, detail="Athlète introuvable")

    end = on or datetime.date.today()
    start = end - datetime.timedelta(days=days - 1)
    sessions = (
        db.query(models.TrainingSession)
        .filter(
            models.TrainingSession.athlete_id == athlete_id,
            models.TrainingSession.date >= start,
            models.TrainingSession.date <= end,
        )
        .all()
    )

    totals = {}
    for s in sessions:
        totals[s.date] = totals.get(s.date, 0) + s.load

    result = []
    for i in range(days):
        day = start + datetime.timedelta(days=i)
        result.append({"date": day, "load": totals.get(day, 0)})
    return result


@app.get("/athletes/{athlete_id}/risk-history")
def risk_history(athlete_id: int, db: Session = Depends(get_db)):
    if not db.get(models.Athlete, athlete_id):
        raise HTTPException(status_code=404, detail="Athlète introuvable")

    rows = (
        db.query(models.RiskPrediction)
        .filter(models.RiskPrediction.athlete_id == athlete_id)
        .order_by(models.RiskPrediction.prediction_date, models.RiskPrediction.id)
        .all()
    )

    # On garde la dernière prédiction de chaque jour
    latest = {}
    for r in rows:
        latest[r.prediction_date] = r

    return [
        {"date": d, "risk_score": r.risk_score, "risk_level": r.risk_level}
        for d, r in latest.items()
    ]



@app.post("/movements")
def create_movement(data: schemas.MovementCreate, db: Session = Depends(get_db)):
    if not db.get(models.Athlete, data.athlete_id):
        raise HTTPException(status_code=404, detail="Athlète introuvable")
    if data.session_id is not None and not db.get(models.TrainingSession, data.session_id):
        raise HTTPException(status_code=404, detail="Séance introuvable")

    movement = models.MovementAnalysis(**data.model_dump())
    db.add(movement)
    db.commit()
    db.refresh(movement)
    return {"id": movement.id, "created_at": movement.created_at}


@app.get("/athletes/{athlete_id}/movements")
def list_movements(athlete_id: int, db: Session = Depends(get_db)):
    if not db.get(models.Athlete, athlete_id):
        raise HTTPException(status_code=404, detail="Athlète introuvable")

    rows = (
        db.query(models.MovementAnalysis)
        .filter(models.MovementAnalysis.athlete_id == athlete_id)
        .order_by(models.MovementAnalysis.created_at.desc())
        .all()
    )
    return [
        {
            "id": m.id,
            "created_at": m.created_at,
            "exercise": m.exercise,
            "reps": m.reps,
            "avg_min_angle": m.avg_min_angle,
            "posture_score": m.posture_score,
        }
        for m in rows
    ]