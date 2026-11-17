from app import models  # noqa: F401
from app.database import Base, engine

Base.metadata.create_all(engine)
print("Tables créées :")
for name in Base.metadata.tables:
    print(" -", name)