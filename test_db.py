from sqlalchemy import text
from app.database import engine

with engine.connect() as conn:
    print("Connexion OK :", conn.execute(text("SELECT version()")).scalar())