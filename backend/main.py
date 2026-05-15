from fastapi import FastAPI, Depends, Body
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel

from predictor import analyze_match
from api_client import get_live_upcoming_matches, simplify_fixture
from database import engine, get_db
from models import Base, Prediction, User
from auth import hash_password, verify_password, create_access_token

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SAFE_PICK_THRESHOLD = 80


class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


fallback_fixtures = [
    {
        "fixture_id": 1,
        "date": "2026-05-18T16:00:00",
        "league": "Premier League",
        "home": "Arsenal",
        "away": "Everton",
        "home_logo": "https://media.api-sports.io/football/teams/42.png",
        "away_logo": "https://media.api-sports.io/football/teams/45.png",
        "status": "NS",
    },
    {
        "fixture_id": 2,
        "date": "2026-05-18T18:30:00",
        "league": "Premier League",
        "home": "Manchester City",
        "away": "West Ham",
        "home_logo": "https://media.api-sports.io/football/teams/50.png",
        "away_logo": "https://media.api-sports.io/football/teams/48.png",
        "status": "NS",
    },
    {
        "fixture_id": 3,
        "date": "2026-06-11T21:00:00",
        "league": "FIFA World Cup 2026",
        "home": "Mexico",
        "away": "Brazil",
        "home_logo": "https://media.api-sports.io/football/teams/16.png",
        "away_logo": "https://media.api-sports.io/football/teams/6.png",
        "status": "NS",
    },
]

demo_teams = [
    {
        "name": "Arsenal",
        "under45": 90,
        "under35": 72,
        "over05": 100,
        "cornersUnder125": 84,
        "doubleChance": 91,
    },
    {
        "name": "Everton",
        "under45": 86,
        "under35": 70,
        "over05": 92,
        "cornersUnder125": 81,
        "doubleChance": 62,
    },
    {
        "name": "Manchester City",
        "under45": 76,
        "under35": 58,
        "over05": 100,
        "cornersUnder125": 70,
        "doubleChance": 94,
    },
    {
        "name": "West Ham",
        "under45": 80,
        "under35": 61,
        "over05": 94,
        "cornersUnder125": 75,
        "doubleChance": 64,
    },
    {
        "name": "Mexico",
        "under45": 88,
        "under35": 73,
        "over05": 93,
        "cornersUnder125": 79,
        "doubleChance": 80,
    },
    {
        "name": "Brazil",
        "under45": 84,
        "under35": 68,
        "over05": 96,
        "cornersUnder125": 78,
        "doubleChance": 86,
    },
]


def find_team(name):
    return next((team for team in demo_teams if team["name"] == name), None)


@app.get("/")
def home():
    return {
        "message": "SmartPick AI backend is running",
        "mode": "Safe Pick Mode",
        "safe_pick_threshold": SAFE_PICK_THRESHOLD,
        "database": "connected",
        "auth": "enabled",
        "disclaimer": "Predictions are probability-based and not guaranteed.",
    }


@app.post("/auth/register")
def register_user(user: RegisterRequest, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(
        (User.email == user.email) | (User.username == user.username)
    ).first()

    if existing_user:
        return {
            "error": "User already exists"
        }

    new_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hash_password(user.password),
        is_admin=False,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "User registered successfully",
        "user": {
            "id": new_user.id,
            "username": new_user.username,
            "email": new_user.email,
            "is_admin": new_user.is_admin,
        },
    }


@app.post("/auth/login")
def login_user(user: LoginRequest, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user.email).first()

    if not existing_user:
        return {
            "error": "Invalid email or password"
        }

    if not verify_password(user.password, existing_user.hashed_password):
        return {
            "error": "Invalid email or password"
        }

    token = create_access_token({
        "sub": existing_user.email,
        "user_id": existing_user.id,
        "is_admin": existing_user.is_admin,
    })

    return {
        "message": "Login successful",
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": existing_user.id,
            "username": existing_user.username,
            "email": existing_user.email,
            "is_admin": existing_user.is_admin,
        },
    }


@app.get("/fixtures/upcoming")
def upcoming():
    try:
        fixtures = get_live_upcoming_matches()
        simplified = [simplify_fixture(f) for f in fixtures]

        if len(simplified) > 0:
            return {
                "source": "live_api",
                "fixtures": simplified,
            }

        return {
            "source": "fallback_demo",
            "note": "API returned no current fixtures on this plan, so fallback fixtures are shown.",
            "fixtures": fallback_fixtures,
        }

    except Exception as error:
        return {
            "source": "fallback_demo",
            "error": str(error),
            "fixtures": fallback_fixtures,
        }


@app.get("/safe-pick")
def safe_pick(home_team: str, away_team: str, db: Session = Depends(get_db)):
    home = find_team(home_team)
    away = find_team(away_team)

    if not home or not away:
        return {
            "error": "Team not found in current demo model",
            "message": "Live team stats will be added when full API access is available.",
        }

    result = analyze_match(home, away)
    best = result["best_pick"]

    risk = (
        "Low"
        if best["confidence"] >= 85
        else "Medium"
        if best["confidence"] >= 80
        else "High"
    )

    is_safe = best["confidence"] >= SAFE_PICK_THRESHOLD

    saved_prediction = Prediction(
        match_name=f"{home_team} vs {away_team}",
        pick=best["pick"],
        market=best["market"],
        confidence=best["confidence"],
        risk=risk,
        is_safe_pick=is_safe,
    )

    db.add(saved_prediction)
    db.commit()
    db.refresh(saved_prediction)

    return {
        "match": f"{home_team} vs {away_team}",
        "safe_pick_mode": True,
        "is_safe_pick": is_safe,
        "threshold": SAFE_PICK_THRESHOLD,
        "best_pick": best,
        "risk": risk,
        "ai_scores": result.get(
            "ai_scores",
            {
                "attack_rating": best["confidence"],
                "defense_rating": best["confidence"],
                "momentum_rating": best["confidence"],
                "safety_score": best["confidence"],
            },
        ),
        "ai_summary": result.get("ai_summary", []),
        "reason": [
            "Market selected from safer prediction categories.",
            "Confidence passed the Safe Pick threshold."
            if is_safe
            else "Confidence is below Safe Pick threshold.",
            "No pick is better than a risky pick.",
        ],
        "all_predictions": result["all_predictions"],
        "saved_prediction_id": saved_prediction.id,
        "disclaimer": "Predictions are probability-based and not guaranteed.",
    }


@app.get("/predictions/history")
def prediction_history(db: Session = Depends(get_db)):
    predictions = (
        db.query(Prediction)
        .order_by(Prediction.created_at.desc())
        .all()
    )

    return {
        "predictions": predictions
    }


@app.delete("/predictions/clear")
def clear_predictions(db: Session = Depends(get_db)):
    db.query(Prediction).delete()
    db.commit()

    return {
        "message": "Prediction history cleared successfully."
    }


@app.put("/predictions/{prediction_id}/result")
def update_prediction_result(
    prediction_id: int,
    result: str = Body(...),
    is_correct: bool = Body(...),
    db: Session = Depends(get_db),
):
    prediction = (
        db.query(Prediction)
        .filter(Prediction.id == prediction_id)
        .first()
    )

    if not prediction:
        return {
            "error": "Prediction not found"
        }

    prediction.result = result
    prediction.is_correct = is_correct

    db.commit()
    db.refresh(prediction)

    return {
        "message": "Prediction result updated successfully",
        "prediction": prediction,
    }


@app.get("/predictions/accuracy")
def prediction_accuracy(db: Session = Depends(get_db)):
    completed = (
        db.query(Prediction)
        .filter(Prediction.is_correct.isnot(None))
        .all()
    )

    total_completed = len(completed)

    correct = len([p for p in completed if p.is_correct])

    accuracy = (
        round((correct / total_completed) * 100, 2)
        if total_completed > 0
        else 0
    )

    return {
        "total_completed": total_completed,
        "correct_predictions": correct,
        "incorrect_predictions": total_completed - correct,
        "accuracy": accuracy,
    }


@app.get("/admin/stats")
def admin_stats(db: Session = Depends(get_db)):
    total_users = db.query(User).count()

    total_predictions = db.query(Prediction).count()

    completed = (
        db.query(Prediction)
        .filter(Prediction.is_correct.isnot(None))
        .all()
    )

    correct = len([p for p in completed if p.is_correct])

    incorrect = len(
        [p for p in completed if p.is_correct is False]
    )

    accuracy = (
        round((correct / len(completed)) * 100, 2)
        if completed
        else 0
    )

    return {
        "total_users": total_users,
        "total_predictions": total_predictions,
        "completed_predictions": len(completed),
        "correct_predictions": correct,
        "incorrect_predictions": incorrect,
        "accuracy": accuracy,
    }


@app.get("/admin/users")
def admin_users(db: Session = Depends(get_db)):
    users = (
        db.query(User)
        .order_by(User.created_at.desc())
        .all()
    )

    return {
        "users": users
    }


@app.get("/admin/predictions")
def admin_predictions(db: Session = Depends(get_db)):
    predictions = (
        db.query(Prediction)
        .order_by(Prediction.created_at.desc())
        .all()
    )

    return {
        "predictions": predictions
    }