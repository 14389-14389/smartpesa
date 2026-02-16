# app/init_db.py
from app.database import engine, Base
from app import models

def init_db():
    print("Creating database tables...")
    # This will create tables only if they don't exist
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

if __name__ == "__main__":
    init_db()