import datetime

from sqlalchemy.orm import Session

from app import models


def _total_load(db: Session, athlete_id: int, start: datetime.date, end: datetime.date) -> int:
    sessions = (
        db.query(models.TrainingSession)
        .filter(
            models.TrainingSession.athlete_id == athlete_id,
            models.TrainingSession.date > start,
            models.TrainingSession.date <= end,
        )
        .all()
    )
    return sum(s.load for s in sessions)


def compute_workload(db: Session, athlete_id: int, on: datetime.date) -> dict:
    acute = _total_load(db, athlete_id, on - datetime.timedelta(days=7), on)
    total_28 = _total_load(db, athlete_id, on - datetime.timedelta(days=28), on)
    chronic = total_28 / 4
    acwr = round(acute / chronic, 2) if chronic > 0 else None
    return {
        "athlete_id": athlete_id,
        "date": on,
        "acute_load": acute,
        "chronic_load": chronic,
        "acwr": acwr,
    }



def wellness_averages(db: Session, athlete_id: int, on: datetime.date) -> dict | None:
    rows = (
        db.query(models.DailyWellness)
        .filter(
            models.DailyWellness.athlete_id == athlete_id,
            models.DailyWellness.date > on - datetime.timedelta(days=7),
            models.DailyWellness.date <= on,
        )
        .all()
    )
    if not rows:
        return None
    n = len(rows)
    return {
        "sleep_avg": sum(r.sleep_hours for r in rows) / n,
        "fatigue_avg": sum(r.fatigue for r in rows) / n,
        "stress_avg": sum(r.stress for r in rows) / n,
    }