import os
from datetime import datetime
from typing import Optional, List
from dotenv import load_dotenv
from supabase import create_client
from models import User, Bet, Prediction

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set!")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# User functions
def create_user(user: User):
    data = {
        "username": user.username,
        "password": user.password,
        "email": user.email,
        "reedz_balance": user.reedz_balance,
        "role": user.role,
        "created_at": user.created_at.isoformat()
    }
    supabase.table("users").insert(data).execute()

def get_user_by_username(username: str) -> Optional[User]:
    res = supabase.table("users").select("*").eq("username", username).execute()
    if res.data and len(res.data) > 0:
        return User(**res.data[0])
    return None

def get_user_by_email(email: str) -> Optional[User]:
    res = supabase.table("users").select("*").eq("email", email).execute()
    if res.data and len(res.data) > 0:
        return User(**res.data[0])
    return None

def update_user_password(user_id: int, new_password_hashed: str) -> bool:
    res = supabase.table("users").update({"password": new_password_hashed}).eq("user_id", user_id).execute()
    return res is not None

def add_reedz(user_id: int, amount: int):
    res = supabase.table("users").select("reedz_balance").eq("user_id", user_id).execute()
    if res.data and len(res.data) > 0:
        current = res.data[0]["reedz_balance"]
        supabase.table("users").update({"reedz_balance": current + amount}).eq("user_id", user_id).execute()

def delete_user(user_id: int):
    supabase.table("users").delete().eq("user_id", user_id).execute()

def change_role(user_id: int, new_role: str):
    supabase.table("users").update({"role": new_role}).eq("user_id", user_id).execute()

def list_all_users():
    res = supabase.table("users").select("user_id", "username", "role", "reedz_balance").execute()
    return res.data

def get_leaderboard():
    res = supabase.table("users").select("username", "reedz_balance").order("reedz_balance", desc=True).execute()
    return res.data

# Bet functions
def create_bet(bet: Bet):
    data = {
        "created_by_user_id": bet.created_by_user_id,
        "title": bet.title,
        "description": bet.description,
        "answer_type": bet.answer_type,
        "is_open": bet.is_open,
        "is_resolved": bet.is_resolved,
        "created_at": bet.created_at.isoformat(),
        "close_at": bet.close_at.isoformat(),
        "resolved_at": bet.resolved_at.isoformat() if bet.resolved_at else None,
        "correct_answer": bet.correct_answer
    }
    supabase.table("bets").insert(data).execute()

def close_bet(bet_id: int):
    supabase.table("bets").update({"is_open": False}).eq("bet_id", bet_id).execute()

def resolve_bet(bet_id: int, correct_answer: str):
    now = datetime.now().isoformat()
    supabase.table("bets").update({
        "is_resolved": True,
        "resolved_at": now,
        "correct_answer": correct_answer
    }).eq("bet_id", bet_id).execute()

def get_bets_by_state(state: str):
    # state: 'open', 'closed', 'resolved'
    if state == "open":
        res = supabase.table("bets").select("*").eq("is_open", True).eq("is_resolved", False).execute()
    elif state == "closed":
        res = supabase.table("bets").select("*").eq("is_open", False).eq("is_resolved", False).execute()
    elif state == "resolved":
        res = supabase.table("bets").select("*").eq("is_resolved", True).execute()
    else:
        res = supabase.table("bets").select("*").execute()
    return res.data

def get_bet(bet_id: int) -> Optional[Bet]:
    res = supabase.table("bets").select("*").eq("bet_id", bet_id).execute()
    if res.data and len(res.data) > 0:
        return Bet(**res.data[0])
    return None

def mark_bet_distributed(bet_id: int):
    pass

# Prediction functions
def create_prediction(prediction: Prediction):
    data = {
        "user_id": prediction.user_id,
        "bet_id": prediction.bet_id,
        "prediction": prediction.prediction,
        "created_at": prediction.created_at.isoformat()
    }
    supabase.table("predictions").insert(data).execute()

def has_prediction(user_id: int, bet_id: int) -> bool:
    res = supabase.table("predictions").select("*").eq("user_id", user_id).eq("bet_id", bet_id).execute()
    return bool(res.data)

def get_predictions_for_bet(bet_id: int) -> List[Prediction]:
    res = supabase.table("predictions").select("*").eq("bet_id", bet_id).execute()
    return [Prediction(**p) for p in res.data]
