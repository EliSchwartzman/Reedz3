import os
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client
from models import User, Bet, Prediction

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise Exception("SUPABASE_URL and SUPABASE_KEY must be set in your .env file.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

## ----------- USER FUNCTIONS ----------- ##
def create_user(user: User):
    res = supabase.table("users").insert({
        "username": user.username,
        "password": user.password,
        "email": user.email,
        "reedz_balance": user.reedz_balance,
        "role": user.role,
        "created_at": user.created_at.isoformat() if isinstance(user.created_at, datetime) else user.created_at
    }).execute()
    return res

def list_all_users():
    res = supabase.table("users").select("user_id", "username", "email", "role", "reedz_balance").execute()
    return res.data

def get_user_by_username(username):
    res = supabase.table("users").select("*").eq("username", username).execute()
    data = res.data
    if data:
        u = data[0]
        return User(
            user_id=u["user_id"], username=u["username"], password=u["password"],
            email=u.get("email", ""), reedz_balance=u["reedz_balance"],
            role=u["role"], created_at=u["created_at"]
        )
    return None

def get_user_by_email(email):
    res = supabase.table("users").select("*").eq("email", email).execute()
    data = res.data
    if data:
        u = data[0]
        return User(
            user_id=u["user_id"], username=u["username"], password=u["password"],
            email=u["email"], reedz_balance=u["reedz_balance"],
            role=u["role"], created_at=u["created_at"]
        )
    return None

def get_user_by_id(user_id):
    res = supabase.table("users").select("*").eq("user_id", user_id).execute()
    data = res.data
    if data:
        u = data[0]
        return User(
            user_id=u["user_id"], username=u["username"], password=u["password"],
            email=u["email"], reedz_balance=u["reedz_balance"],
            role=u["role"], created_at=u["created_at"]
        )
    return None

def update_user_password(user_id, new_password_hashed):
    res = supabase.table("users").update({"password": new_password_hashed}).eq("user_id", user_id).execute()
    return res is not None

def update_user_password_by_email(email, new_password_hashed):
    res = supabase.table("users").update({"password": new_password_hashed}).eq("email", email).execute()
    return res

def update_user_email(user_id, new_email):
    res = supabase.table("users").update({"email": new_email}).eq("user_id", user_id).execute()
    return res

def set_user_reset_code(email, code, expiry):
    res = supabase.table("users").update({
        "reset_code": code,
        "reset_code_expiry": expiry.isoformat() if isinstance(expiry, datetime) else expiry
    }).eq("email", email).execute()
    return res

def check_reset_code(email, code):
    res = supabase.table("users").select("reset_code", "reset_code_expiry").eq("email", email).execute()
    if not res.data:
        return False
    user = res.data[0]
    stored_code = user.get("reset_code")
    expiry = user.get("reset_code_expiry")
    if not stored_code or not expiry or stored_code != code:
        return False
    if datetime.fromisoformat(expiry) < datetime.now():
        return False
    return True

def clear_reset_code(email):
    res = supabase.table("users").update({"reset_code": None, "reset_code_expiry": None}).eq("email", email).execute()
    return res

def add_reedz(user_id, delta):
    user = get_user_by_id(user_id)
    if not user:
        return None
    new_balance = user.reedz_balance + delta
    res = supabase.table("users").update({"reedz_balance": new_balance}).eq("user_id", user_id).execute()
    return res

def delete_user(user_id):
    res = supabase.table("users").delete().eq("user_id", user_id).execute()
    return res

def change_role(user_id, new_role):
    res = supabase.table("users").update({"role": new_role}).eq("user_id", user_id).execute()
    return res

def get_leaderboard():
    res = supabase.table("users").select("username", "reedz_balance").order("reedz_balance", desc=True).execute()
    return res.data

## ----------- BET FUNCTIONS ----------- ##
def create_bet(bet: Bet):
    res = supabase.table("bets").insert({
        "created_by_user_id": bet.created_by_user_id,
        "title": bet.title,
        "description": bet.description,
        "answer_type": bet.answer_type,
        "is_open": bet.is_open,
        "is_resolved": bet.is_resolved,
        "created_at": bet.created_at.isoformat() if isinstance(bet.created_at, datetime) else bet.created_at,
        "close_at": bet.close_at.isoformat() if isinstance(bet.close_at, datetime) else bet.close_at,
        "resolved_at": bet.resolved_at.isoformat() if bet.resolved_at is not None and isinstance(bet.resolved_at, datetime) else bet.resolved_at,
        "correct_answer": bet.correct_answer
    }).execute()
    return res

def get_bet(bet_id):
    res = supabase.table("bets").select("*").eq("bet_id", bet_id).execute()
    data = res.data
    if data:
        b = data[0]
        return Bet(
            bet_id=b["bet_id"], title=b["title"], description=b["description"],
            answer_type=b["answer_type"], close_at=b["close_at"],
            correct_answer=b.get("correct_answer"),
            is_open=b.get("is_open", True),
            is_resolved=b.get("is_resolved", False)
        )
    return None

def get_bets_by_state(state):
    bets = supabase.table("bets").select(
        "bet_id", "title", "description", "answer_type", "correct_answer",
        "is_open", "is_resolved", "close_at"
    )
    if state == "open":
        res = bets.eq("is_open", True).eq("is_resolved", False).execute()
    elif state == "closed":
        res = bets.eq("is_open", False).eq("is_resolved", False).execute()
    elif state == "resolved":
        res = bets.eq("is_resolved", True).execute()
    else:
        res = bets.execute()
    return res.data

def get_bet_overview(state=""):
    return get_bets_by_state(state)

def close_bet(user, bet_id):
    res = supabase.table("bets").update({"is_open": False}).eq("bet_id", bet_id).execute()
    return res

def resolve_bet(user, bet_id, correct_answer):
    res = supabase.table("bets").update({
        "is_resolved": True, "correct_answer": correct_answer
    }).eq("bet_id", bet_id).execute()
    return res

def mark_bet_distributed(bet_id):
    res = supabase.table("bets").update({"distributed": True}).eq("bet_id", bet_id).execute()
    return res

## ----------- PREDICTION FUNCTIONS ----------- ##
def create_prediction(prediction: Prediction):
    res = supabase.table("predictions").insert({
        "user_id": prediction.user_id,
        "bet_id": prediction.bet_id,
        "prediction": prediction.prediction,
        "created_at": prediction.created_at if isinstance(prediction.created_at, str) else prediction.created_at.isoformat()
    }).execute()
    return res


def get_predictions_for_bet(bet_id):
    res = supabase.table("predictions").select(
        "prediction_id", "user_id", "bet_id", "prediction", "created_at"
    ).eq("bet_id", bet_id).execute()
    data = res.data
    preds = []
    for p in data:
        preds.append(Prediction(
            prediction_id=p["prediction_id"], user_id=p["user_id"], bet_id=p["bet_id"],
            prediction=p["prediction"], created_at=p["created_at"]
        ))
    return preds

def get_user_predictions(user_id):
    res = supabase.table("predictions").select("*").eq("user_id", user_id).execute()
    return res.data

def has_prediction(user_id, bet_id):
    res = supabase.table("predictions")\
        .select("prediction_id")\
        .eq("user_id", user_id)\
        .eq("bet_id", bet_id)\
        .limit(1)\
        .execute()
    return bool(res.data)
