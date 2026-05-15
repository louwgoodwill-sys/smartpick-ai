def average(a, b):
    return round((a + b) / 2)


def get_risk(confidence):
    if confidence >= 90:
        return "Very Low"
    if confidence >= 85:
        return "Low"
    if confidence >= 80:
        return "Medium"
    return "High"


def calculate_ai_scores(home, away):
    attack_rating = average(home["over05"], away["over05"])
    defense_rating = average(home["under45"], away["under45"])
    control_rating = average(home["cornersUnder125"], away["cornersUnder125"])
    momentum_rating = average(home["doubleChance"], away["doubleChance"])

    safety_score = round(
        (attack_rating + defense_rating + control_rating + momentum_rating) / 4
    )

    return {
        "attack_rating": attack_rating,
        "defense_rating": defense_rating,
        "control_rating": control_rating,
        "momentum_rating": momentum_rating,
        "safety_score": safety_score,
    }


def analyze_match(home, away):
    ai_scores = calculate_ai_scores(home, away)

    predictions = [
        {
            "market": "Goals",
            "pick": "Under 4.5 goals",
            "confidence": average(home["under45"], away["under45"]),
            "reason": "Both teams have strong low-scoring match trends.",
        },
        {
            "market": "Goals",
            "pick": "Under 3.5 goals",
            "confidence": average(home["under35"], away["under35"]),
            "reason": "This market is safer when both teams avoid high-scoring games.",
        },
        {
            "market": "Goals",
            "pick": "Over 0.5 goals",
            "confidence": average(home["over05"], away["over05"]),
            "reason": "Both teams show a high chance of at least one goal in the match.",
        },
        {
            "market": "Corners",
            "pick": "Under 12.5 corners",
            "confidence": average(home["cornersUnder125"], away["cornersUnder125"]),
            "reason": "Corner totals are projected to stay below the safer threshold.",
        },
        {
            "market": "Double Chance",
            "pick": f"{home['name']} or Draw",
            "confidence": home["doubleChance"],
            "reason": f"{home['name']} has strong home-side protection in this matchup.",
        },
    ]

    for prediction in predictions:
        prediction["risk"] = get_risk(prediction["confidence"])

    predictions.sort(key=lambda x: x["confidence"], reverse=True)

    safe_picks = [p for p in predictions if p["confidence"] >= 80]
    best_pick = safe_picks[0] if safe_picks else predictions[0]

    return {
        "best_pick": best_pick,
        "all_predictions": predictions,
        "ai_scores": ai_scores,
        "ai_summary": [
            f"Best market selected: {best_pick['market']}",
            f"Recommended pick: {best_pick['pick']}",
            f"Confidence level: {best_pick['confidence']}%",
            f"Risk rating: {best_pick['risk']}",
            f"Overall AI safety score: {ai_scores['safety_score']}%",
            best_pick["reason"],
        ],
    }