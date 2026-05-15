from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float
from datetime import datetime
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    match_name = Column(String, index=True)
    pick = Column(String)
    market = Column(String)
    confidence = Column(Float)
    risk = Column(String)
    is_safe_pick = Column(Boolean)
    result = Column(String, default="pending")
    is_correct = Column(Boolean, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)