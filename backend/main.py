from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from predictor import analyze_match
from api_client import (
    get_live_upcoming_matches,
    simplify_fixture,
)
from database import (
    SessionLocal,
    engine,
)
from models import Base, PredictionHistory, User
from auth import (
    hash_password,
    verify_password,
    create_access_token,
)
from pydantic import BaseModel
from sqlalchemy.orm import Session

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://smartpick-eq6zdhsrz-louwgoodwill-sys-projects.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class PredictionResultRequest(BaseModel):
    result: str
    is_correct: bool


@app.get("/")
def home():
    return {
        "message": "SmartPick AI backend is running"
    }


@app.get("/fixtures/upcoming")
def upcoming_fixtures():
    try:
        fixtures = get_live_upcoming_matches()

        simplified = [
            simplify_fixture(match)
            for match in fixtures
        ]

        return {
            "fixtures": simplified,
            "source": "API-Football",
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


@app.get("/safe-pick")
def safe_pick(
    home_team: str,
    away_team: str,
):
    db: Session = SessionLocal()

    try:
        prediction = analyze_match(
            home_team,
            away_team,
        )

        if not prediction.get("error"):
            history = PredictionHistory(
                match_name=f"{home_team} vs {away_team}",
                pick=prediction["best_pick"][
                    "pick"
                ],
                market=prediction["best_pick"][
                    "market"
                ],
                confidence=prediction[
                    "best_pick"
                ]["confidence"],
                risk=prediction["risk"],
                result="pending",
                is_correct=False,
            )

            db.add(history)
            db.commit()

        return prediction

    finally:
        db.close()


@app.get("/predictions/history")
def prediction_history():
    db: Session = SessionLocal()

    try:
        predictions = (
            db.query(PredictionHistory)
            .order_by(
                PredictionHistory.created_at.desc()
            )
            .all()
        )

        results = []

        for item in predictions:
            results.append(
                {
                    "id": item.id,
                    "match_name": item.match_name,
                    "pick": item.pick,
                    "market": item.market,
                    "confidence": item.confidence,
                    "risk": item.risk,
                    "result": item.result,
                    "is_correct": item.is_correct,
                }
            )

        return {"predictions": results}

    finally:
        db.close()


@app.delete("/predictions/clear")
def clear_prediction_history():
    db: Session = SessionLocal()

    try:
        db.query(PredictionHistory).delete()

        db.commit()

        return {
            "message": "Prediction history cleared"
        }

    finally:
        db.close()


@app.put("/predictions/{prediction_id}/result")
def update_prediction_result(
    prediction_id: int,
    data: PredictionResultRequest,
):
    db: Session = SessionLocal()

    try:
        prediction = (
            db.query(PredictionHistory)
            .filter(
                PredictionHistory.id
                == prediction_id
            )
            .first()
        )

        if not prediction:
            raise HTTPException(
                status_code=404,
                detail="Prediction not found",
            )

        prediction.result = data.result
        prediction.is_correct = data.is_correct

        db.commit()

        return {
            "message": "Prediction updated"
        }

    finally:
        db.close()


@app.get("/admin/stats")
def admin_stats():
    db: Session = SessionLocal()

    try:
        total_predictions = (
            db.query(PredictionHistory).count()
        )

        correct_predictions = (
            db.query(PredictionHistory)
            .filter(
                PredictionHistory.is_correct
                == True
            )
            .count()
        )

        incorrect_predictions = (
            db.query(PredictionHistory)
            .filter(
                PredictionHistory.result == "lost"
            )
            .count()
        )

        total_users = db.query(User).count()

        accuracy = 0

        completed = (
            correct_predictions
            + incorrect_predictions
        )

        if completed > 0:
            accuracy = round(
                (
                    correct_predictions
                    / completed
                )
                * 100,
                2,
            )

        return {
            "total_predictions": total_predictions,
            "correct_predictions": correct_predictions,
            "incorrect_predictions": incorrect_predictions,
            "accuracy": accuracy,
            "total_users": total_users,
        }

    finally:
        db.close()


@app.post("/auth/register")
def register_user(
    user: RegisterRequest,
):
    db: Session = SessionLocal()

    try:
        existing = (
            db.query(User)
            .filter(User.email == user.email)
            .first()
        )

        if existing:
            return {
                "error": "Email already exists"
            }

        new_user = User(
            username=user.username,
            email=user.email,
            password=hash_password(
                user.password
            ),
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        token = create_access_token(
            {
                "sub": new_user.email,
            }
        )

        return {
            "message": "Registration successful",
            "access_token": token,
            "user": {
                "id": new_user.id,
                "username": new_user.username,
                "email": new_user.email,
            },
        }

    finally:
        db.close()


@app.post("/auth/login")
def login_user(
    credentials: LoginRequest,
):
    db: Session = SessionLocal()

    try:
        user = (
            db.query(User)
            .filter(
                User.email
                == credentials.email
            )
            .first()
        )

        if not user:
            return {
                "error": "Invalid credentials"
            }

        if not verify_password(
            credentials.password,
            user.password,
        ):
            return {
                "error": "Invalid credentials"
            }

        token = create_access_token(
            {
                "sub": user.email,
            }
        )

        return {
            "message": "Login successful",
            "access_token": token,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
            },
        }

    finally:
        db.close()