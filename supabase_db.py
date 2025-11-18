from supabase import create_client, Client
from models import User, Bet, Prediction, Role, AnswerType
from datetime import datetime

import os

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

client: Client = create_client(url, key)


# User operations
def get_user_by_username(username: str) -> User:
    res = client.table("users").select("*").eq("username", username).single().execute()
    data = res.data
    if not data:
        return None
    return _user_from_dict(data)


def _user_from_dict(data) -> User:
    from models import Role
    return User(
        user_id=data["user_id"],
        username=data["username"],
        password_hash=data["password_hash"],
        email=data["email"],
        created_at=datetime.fromisoformat(data["created_at"]),
        role=Role(data["role"]),
        reedz=data.get("reedz", 0)
    )


def insert_bet(bet: Bet) -> Bet:
    res = client.table("bets").insert({
        "user_id": bet.user_id,
        "title": bet.title,
        "description": bet.description,
        "answer_type": bet.answer_type.value,
        "created_at": bet.created_at.isoformat(),
        "close_at": bet.close_at.isoformat() if bet.close_at else None,
        "is_closed": bet.is_closed,
        "is_resolved": bet.is_resolved
    }).execute()
    bet_id = res.data[0]["bet_id"]
    bet.bet_id = bet_id
    return bet


def get_bet(bet_id: str) -> Bet:
    res = client.table("bets").select("*").eq("bet_id", bet_id).single().execute()
    data = res.data
    from models import AnswerType
    return Bet(
        bet_id=data["bet_id"],
        user_id=data["user_id"],
        title=data["title"],
        description=data["description"],
        answer_type=AnswerType(data["answer_type"]),
        created_at=datetime.fromisoformat(data["created_at"]),
        close_at=datetime.fromisoformat(data["close_at"]) if data["close_at"] else None,
        is_closed=data["is_closed"],
        is_resolved=data["is_resolved"],
        resolve_at=datetime.fromisoformat(data["resolve_at"]) if data["resolve_at"] else None,
        resolved_answer=data.get("resolved_answer")
    )


def update_bet(bet: Bet):
    client.table("bets").update({
        "close_at": bet.close_at.isoformat() if bet.close_at else None,
        "is_closed": bet.is_closed,
        "is_resolved": bet.is_resolved,
        "resolve_at": bet.resolve_at.isoformat() if bet.resolve_at else None,
        "resolved_answer": bet.resolved_answer,
    }).eq("bet_id", bet.bet_id).execute()


def insert_prediction(prediction: Prediction):
    client.table("predictions").insert({
        "bet_id": prediction.bet_id,
        "user_id": prediction.user_id,
        "prediction": prediction.prediction,
        "created_at": prediction.created_at.isoformat()
    }).execute()


def get_predictions_by_bet(bet_id: str) -> list[Prediction]:
    res = client.table("predictions").select("*").eq("bet_id", bet_id).execute()
    from models import Prediction
    predictions = []
    for data in res.data:
        predictions.append(Prediction(
            prediction_id=data["prediction_id"],
            bet_id=data["bet_id"],
            user_id=data["user_id"],
            prediction=data["prediction"],
            created_at=datetime.fromisoformat(data["created_at"])
        ))
    return predictions


def get_prediction_by_bet_and_user(bet_id: str, user_id: str) -> Prediction:
    res = client.table("predictions").select("*").eq("bet_id", bet_id).eq("user_id", user_id).single().execute()
    data = res.data
    if not data:
        return None
    return Prediction(
        prediction_id=data["prediction_id"],
        bet_id=data["bet_id"],
        user_id=data["user_id"],
        prediction=data["prediction"],
        created_at=datetime.fromisoformat(data["created_at"])
    )


def increment_reedz(user_id: str, amount: int):
    # Read current reedz
    res = client.table("users").select("reedz").eq("user_id", user_id).single().execute()
    current = res.data.get("reedz", 0)
    client.table("users").update({"reedz": current + amount}).eq("user_id", user_id).execute()


# Additional user management for admin panel
def get_all_users() -> list[User]:
    res = client.table("users").select("*").execute()
    users = []
    for data in res.data:
        users.append(_user_from_dict(data))
    return users


def update_user_reedz(user_id: str, reedz: int):
    client.table("users").update({"reedz": reedz}).eq("user_id", user_id).execute()


def delete_user_account(user_id: str):
    client.table("users").delete().eq("user_id", user_id).execute()


def promote_demote_user(user_id: str, role: str):
    client.table("users").update({"role": role}).eq("user_id", user_id).execute()
