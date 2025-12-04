import os
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from supabase import create_client, Client
from models import User, Bet, Prediction

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise Exception("SUPABASE_URL and SUPABASE_KEY must be set in your .env file.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# USER FUNCTIONS
def create_user(user: User):
    res = supabase.table("users").insert({
        "username": user.username,
        "password": user.password,
        "email": user.email,
        "reedz_balance": user.reedzbalance,
        "role": user.role,
        "created_at": user.createdat.isoformat() if isinstance(user.createdat, datetime) else user.createdat,
    }).execute()
    return res

def list_all_users():
    res = supabase.table("users").select("user_id, username, email, role, reedz_balance").execute()
    return res.data

def get_user_by_username(username):
    res = supabase.table("users").select("*").eq("username", username).limit(1).execute()
    data = res.data
    if not data:
        return None
    user = data[0]
    return User(
        userid=user["user_id"],
        username=user["username"],
        password=user["password"],
        email=user["email"],
        reedzbalance=user["reedz_balance"],
        role=user["role"],
        createdat=user["created_at"]
    )

def get_user_by_email(email):
    res = supabase.table("users").select("*").eq("email", email).limit(1).execute()
    data = res.data
    if not data:
        return None
    user = data[0]
    return User(
        userid=user["user_id"],
        username=user["username"],
        password=user["password"],
        email=user["email"],
        reedzbalance=user["reedz_balance"],
        role=user["role"],
        createdat=user["created_at"]
    )

def get_user_by_id(userid):
    res = supabase.table("users").select("*").eq("user_id", userid).execute()
    data = res.data
    if not data:
        return None
    user = data[0]
    return User(
        userid=user["user_id"],
        username=user["username"],
        password=user["password"],
        email=user["email"],
        reedzbalance=user["reedz_balance"],
        role=user["role"],
        createdat=user["created_at"]
    )

def update_user_password(userid, hashed_password):
    res = supabase.table("users").update({"password": hashed_password}).eq("user_id", userid).execute()
    return res

def update_user_password_by_email(email, hashed_password):
    res = supabase.table("users").update({"password": hashed_password}).eq("email", email).execute()
    return res

def update_user_email(userid, new_email):
    res = supabase.table("users").update({"email": new_email}).eq("user_id", userid).execute()
    return res

def set_user_reset_code(email, code, expiry):
    res = supabase.table("users").update({
        "reset_code": code,
        "reset_code_expiry": expiry.isoformat() if isinstance(expiry, datetime) else expiry
    }).eq("email", email).execute()
    return res

def check_reset_code(email, code):
    res = supabase.table("users").select("reset_code, reset_code_expiry").eq("email", email).execute()
    if not res.data:
        return False
    user = res.data[0]
    stored_code = user.get("reset_code")
    expiry = user.get("reset_code_expiry")
    if not stored_code or not expiry or stored_code != code:
        return False
    try:
        expiry_dt = datetime.fromisoformat(expiry)
        if expiry_dt.tzinfo is None:
            expiry_dt = expiry_dt.replace(tzinfo=timezone.utc)
    except Exception:
        supabase.table("users").update({"reset_code": None, "reset_code_expiry": None}).eq("email", email).execute()
        return False
    now_utc = datetime.now(timezone.utc)
    if expiry_dt < now_utc - timedelta(minutes=5):
        supabase.table("users").update({"reset_code": None, "reset_code_expiry": None}).eq("email", email).execute()
        return False
    return True

def clear_reset_code(email):
    res = supabase.table("users").update({"reset_code": None, "reset_code_expiry": None}).eq("email", email).execute()
    return res

def add_reedz(userid, delta):
    user = get_user_by_id(userid)
    if not user:
        return None
    new_balance = user.reedzbalance + delta
    res = supabase.table("users").update({"reedz_balance": new_balance}).eq("user_id", userid).execute()
    return res

def delete_user(userid):
    res = supabase.table("users").delete().eq("user_id", userid).execute()
    return res

def change_role(userid, new_role):
    res = supabase.table("users").update({"role": new_role}).eq("user_id", userid).execute()
    return res

def get_leaderboard():
    res = supabase.table("users").select("username, reedz_balance").order("reedz_balance", desc=True).execute()
    return res.data

# BET FUNCTIONS
def create_bet(bet: Bet):
    res = supabase.table("bets").insert({
        "created_by_user_id": bet.createdbyuserid,
        "title": bet.title,
        "description": bet.description,
        "answer_type": bet.answertype,
        "is_open": bet.isopen,
        "is_resolved": bet.isresolved,
        "is_closed": bet.is_closed,
        "created_at": bet.createdat.isoformat() if isinstance(bet.createdat, datetime) else bet.createdat,
        "close_at": bet.closeat.isoformat() if isinstance(bet.closeat, datetime) else bet.closeat,
        "resolved_at": bet.resolvedat.isoformat() if bet.resolvedat is not None and isinstance(bet.resolvedat, datetime) else bet.resolvedat,
        "correct_answer": bet.correctanswer,
    }).execute()
    return res

def get_bet(betid):
    res = supabase.table("bets").select("*").eq("bet_id", betid).execute()
    data = res.data
    if data:
        b = data[0]
        return Bet(
            betid=b["bet_id"],
            createdbyuserid=b["created_by_user_id"],
            title=b["title"],
            description=b["description"],
            answertype=b["answer_type"],
            isopen=b["is_open"],
            isresolved=b["is_resolved"],
            is_closed=b.get("is_closed", False),
            createdat=b["created_at"],
            closeat=b["close_at"],
            resolvedat=b["resolved_at"],
            correctanswer=b["correct_answer"],
        )
    return None

def get_bets_by_state(state):
    bets = supabase.table("bets").select(
        "bet_id, created_by_user_id, title, description, answer_type, correct_answer, "
        "is_open, is_resolved, is_closed, created_at, close_at, resolved_at"
    )
    if state == "open":
        res = bets.eq("is_closed", False).eq("is_resolved", False).execute()
    elif state == "closed":
        res = bets.eq("is_closed", True).eq("is_resolved", False).execute()
    elif state == "resolved":
        res = bets.eq("is_resolved", True).execute()
    else:
        res = bets.execute()
    return res.data

def get_bet_overview(state):
    return get_bets_by_state(state)

def close_bet(betid):
    res = supabase.table("bets").update({"is_open": False, "is_closed": True}).eq("bet_id", betid).execute()
    return res

def resolve_bet(betid, correctanswer):
    res = supabase.table("bets").update({
        "is_resolved": True,
        "correct_answer": correctanswer
    }).eq("bet_id", betid).execute()
    return res

# PREDICTION FUNCTIONS
def create_prediction(prediction: Prediction):
    res = supabase.table("predictions").insert({
        "user_id": prediction.userid,
        "bet_id": prediction.betid,
        "prediction": prediction.prediction,
        "created_at": prediction.createdat.isoformat() if isinstance(prediction.createdat, datetime) else prediction.createdat,
    }).execute()
    return res

def get_predictions_for_bet(betid):
    res = supabase.table("predictions").select("*").eq("bet_id", betid).execute()
    data = res.data
    preds = []
    for p in data:
        preds.append(Prediction(
            predictionid=p["prediction_id"],
            userid=p["user_id"],
            betid=p["bet_id"],
            prediction=p["prediction"],
            createdat=p["created_at"]
        ))
    return preds

def get_user_predictions(userid):
    res = supabase.table("predictions").select("*").eq("user_id", userid).execute()
    return res.data

def has_prediction(userid, betid):
    res = supabase.table("predictions").select("prediction_id").eq("user_id", userid).eq("bet_id", betid).limit(1).execute()
    return bool(res.data)
