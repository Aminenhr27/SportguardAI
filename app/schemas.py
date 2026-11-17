import datetime

from pydantic import BaseModel, Field


class AthleteCreate(BaseModel):
    name: str
    email: str
    password: str
    age: int | None = None
    weight: float | None = None
    height: float | None = None
    sport: str | None = None
    position: str | None = None


class SessionCreate(BaseModel):
    athlete_id: int
    date: datetime.date
    duration: int = Field(gt=0)
    intensity: int = Field(ge=1, le=10)
    training_type: str | None = None



class WellnessCreate(BaseModel):
    athlete_id: int
    date: datetime.date
    sleep_hours: float = Field(ge=0, le=24)
    fatigue: int = Field(ge=1, le=10)
    stress: int = Field(ge=1, le=10)
    muscle_soreness: int = Field(ge=1, le=10)