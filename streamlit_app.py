import streamlit as st
from supabase import create_client, Client
from models import User, Bet, Prediction, Role, AnswerType
from datetime import datetime

# Use Streamlit secrets for sensitive info
url = st.secrets.get("SUPABASE_URL")
key = st.secrets.get("SUPABASE_KEY")
if not url or not key:
    st.error("Supabase URL or Key is not set in secrets!")
    st.stop()  # Stop the app if connection can't be established

if not url or not key:
    raise RuntimeError("Supabase URL and KEY must be set in Streamlit secrets")

client: Client = create_client(url, key)


def _user_from_dict(data) -> User:
    return User(
        user_id=data["user_id"],
        username=data["username"],
        password_hash=data["password_hash"],
        email=data["email"],
        created_at=datetime.fromisoformat(data["created_at"]),
        role=Role(data["role"]),
        reedz=data.get("reedz", 0)
    )

def get_user_by_username(username: str) -> User:
    if not username:
        return None
    try:
        res = client.table("users").select("*").eq("username", username).single().execute()
        data = res.data
        if not data:
            return None
        return _user_from_dict(data)
    except Exception as e:
        st.error(f"Error fetching user by username: {e}")
        return None


def insert_user(user: User) -> User:
    try:
        res = client.table("users").insert({
            "username": user.username,
            "password_hash": user.password_hash,
            "email": user.email,
            "created_at": user.created_at.isoformat(),
            "role": user.role.value,
            "reedz": user.reedz
        }).execute()
        user.user_id = res.data[0]["user_id"]
        return user
    except Exception as e:
        st.error(f"Error inserting user: {e}")
        raise


def insert_bet(bet: Bet) -> Bet:
    try:
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
    except Exception as e:
        st.error(f"Error inserting bet: {e}")
        raise


def get_bet(bet_id: str) -> Bet:
    try:
        res = client.table("bets").select("*").eq("bet_id", bet_id).single().execute()
        data = res.data
        if not data:
            return None
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
    except Exception as e:
        st.error(f"Error fetching bet: {e}")
        return None


def update_bet(bet: Bet):
    try:
        client.table("bets").update({
            "close_at": bet.close_at.isoformat() if bet.close_at else None,
            "is_closed": bet.is_closed,
            "is_resolved": bet.is_resolved,
            "resolve_at": bet.resolve_at.isoformat() if bet.resolve_at else None,
            "resolved_answer": bet.resolved_answer,
        }).eq("bet_id", bet.bet_id).execute()
    except Exception as e:
        st.error(f"Error updating bet: {e}")
        raise


def insert_prediction(prediction: Prediction):
    try:
        client.table("predictions").insert({
            "bet_id": prediction.bet_id,
            "user_id": prediction.user_id,
            "prediction": prediction.prediction,
            "created_at": prediction.created_at.isoformat()
        }).execute()
    except Exception as e:
        st.error(f"Error inserting prediction: {e}")
        raise


def get_predictions_by_bet(bet_id: str) -> list[Prediction]:
    try:
        res = client.table("predictions").select("*").eq("bet_id", bet_id).execute()
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
    except Exception as e:
        st.error(f"Error fetching predictions by bet: {e}")
        return []


def get_prediction_by_bet_and_user(bet_id: str, user_id: str) -> Prediction:
    try:
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
    except Exception as e:
        st.error(f"Error fetching prediction by bet and user: {e}")
        return None


def increment_reedz(user_id: str, amount: int):
    try:
        res = client.table("users").select("reedz").eq("user_id", user_id).single().execute()
        current = res.data.get("reedz", 0) if res.data else 0
        client.table("users").update({"reedz": current + amount}).eq("user_id", user_id).execute()
    except Exception as e:
        st.error(f"Error incrementing reedz: {e}")
        raise


def get_all_users() -> list[User]:
    try:
        res = client.table("users").select("*").execute()
        users = []
        for data in res.data:
            users.append(_user_from_dict(data))
        return users
    except Exception as e:
        st.error(f"Error fetching all users: {e}")
        return []


def update_user_reedz(user_id: str, reedz: int):
    try:
        client.table("users").update({"reedz": reedz}).eq("user_id", user_id).execute()
    except Exception as e:
        st.error(f"Error updating user reedz: {e}")
        raise


def delete_user_account(user_id: str):
    try:
        client.table("users").delete().eq("user_id", user_id).execute()
    except Exception as e:
        st.error(f"Error deleting user account: {e}")
        raise


def promote_demote_user(user_id: str, role: str):
    try:
        client.table("users").update({"role": role}).eq("user_id", user_id).execute()
    except Exception as e:
        st.error(f"Error promoting/demoting user: {e}")
        raise
