"""
SportGuard AI - Modèles de base de données (PostgreSQL via SQLAlchemy)

Place ce fichier dans : app/models.py
"""

from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    # On stocke un HASH (bcrypt/argon2), jamais le mot de passe en clair
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="athlete")  # athlete / coach / admin
    created_at = Column(DateTime, default=datetime.utcnow)

    athlete = relationship("Athlete", back_populates="user", uselist=False)


class Athlete(Base):
    __tablename__ = "athletes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    age = Column(Integer)
    weight = Column(Float)  # kg
    height = Column(Float)  # cm
    sport = Column(String(50))
    position = Column(String(50))

    user = relationship("User", back_populates="athlete")
    sessions = relationship("TrainingSession", back_populates="athlete", cascade="all, delete-orphan")
    wellness = relationship("DailyWellness", back_populates="athlete", cascade="all, delete-orphan")
    injuries = relationship("Injury", back_populates="athlete", cascade="all, delete-orphan")
    predictions = relationship("RiskPrediction", back_populates="athlete", cascade="all, delete-orphan")


class TrainingSession(Base):
    __tablename__ = "training_sessions"
    __table_args__ = (
        CheckConstraint("intensity BETWEEN 1 AND 10", name="ck_session_intensity"),
    )

    id = Column(Integer, primary_key=True, index=True)
    athlete_id = Column(Integer, ForeignKey("athletes.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    duration = Column(Integer, nullable=False)  # minutes
    intensity = Column(Integer, nullable=False)  # effort perçu de 1 à 10 (RPE)
    training_type = Column(String(50))  # force, cardio, match, technique...

    athlete = relationship("Athlete", back_populates="sessions")

    @property
    def load(self) -> int:
        """Charge de la séance = durée x intensité (base du calcul de risque)."""
        return self.duration * self.intensity


class DailyWellness(Base):
    __tablename__ = "daily_wellness"
    __table_args__ = (
        UniqueConstraint("athlete_id", "date", name="uq_wellness_athlete_date"),
        CheckConstraint("fatigue BETWEEN 1 AND 10", name="ck_wellness_fatigue"),
        CheckConstraint("stress BETWEEN 1 AND 10", name="ck_wellness_stress"),
        CheckConstraint("muscle_soreness BETWEEN 1 AND 10", name="ck_wellness_soreness"),
    )

    id = Column(Integer, primary_key=True, index=True)
    athlete_id = Column(Integer, ForeignKey("athletes.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(Date, nullable=False)
    sleep_hours = Column(Float)
    fatigue = Column(Integer)  # 1 (frais) à 10 (épuisé)
    stress = Column(Integer)  # 1 à 10
    muscle_soreness = Column(Integer)  # courbatures 1 à 10

    athlete = relationship("Athlete", back_populates="wellness")


class Injury(Base):
    __tablename__ = "injuries"

    id = Column(Integer, primary_key=True, index=True)
    athlete_id = Column(Integer, ForeignKey("athletes.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    body_part = Column(String(50), nullable=False)  # genou, cheville, ischio...
    injury_type = Column(String(50))  # entorse, déchirure, tendinite...
    severity = Column(String(20))  # mild / moderate / severe
    diagnosis_status = Column(String(20), default="suspected")  # suspected / confirmed / recovered

    athlete = relationship("Athlete", back_populates="injuries")


class RiskPrediction(Base):
    __tablename__ = "risk_predictions"
    __table_args__ = (
        CheckConstraint("risk_score BETWEEN 0 AND 1", name="ck_prediction_score"),
    )

    id = Column(Integer, primary_key=True, index=True)
    athlete_id = Column(Integer, ForeignKey("athletes.id", ondelete="CASCADE"), nullable=False, index=True)
    prediction_date = Column(Date, nullable=False, index=True)
    risk_score = Column(Float, nullable=False)  # probabilité entre 0 et 1
    risk_level = Column(String(10), nullable=False)  # low / medium / high
    model_version = Column(String(30))

    athlete = relationship("Athlete", back_populates="predictions")

    

class MovementAnalysis(Base):
    __tablename__ = "movement_analyses"
    __table_args__ = (
        CheckConstraint("posture_score BETWEEN 0 AND 100", name="ck_movement_score"),
    )

    id = Column(Integer, primary_key=True, index=True)
    athlete_id = Column(Integer, ForeignKey("athletes.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(Integer, ForeignKey("training_sessions.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    exercise = Column(String(30), nullable=False)  # squat, pompes...
    reps = Column(Integer, nullable=False)
    avg_min_angle = Column(Float)  # angle moyen du genou au point bas
    posture_score = Column(Float, nullable=False)  # 0 à 100

    athlete = relationship("Athlete")