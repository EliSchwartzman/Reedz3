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


def create_user(user: User):
    res = supabase.table("users").insert({
        "username": user.username,
        "password": user.password,
        "email": user.email,
        "reedzbalance": user.reedzbalance,
        "role": user.role,
        "createdat": user.createdat.isoformat() if isinstance(user.createdat, datetime) else user.createdat,
    }).execute()
    return res


def list_all_users():
    res = supabase.table("users").select("userid, username, email, role, reedzbalance").execute()
    return res.data


def get_user_by_username(username):
    res = supabase.table("users").select("*").eq("username", username).limit(1).execute()
    data = res.data
    if not data:
        return None
    user = data[0]
    return User(
        userid=user["userid"],
        username=user["username"],
        password=user["password"],
        email=user["email"],
        reedzbalance=user["reedzbalance"],
        role=user["role"],
        createdat=user["createdat"]
    )


def get_user_by_email(email):
    res = supabase.table("users").select("*").eq("email", email).limit(1).execute()
    data = res.data
    if not data:
        return None
    user = data[0]
    return User(
        userid=user["userid"],
        username=user["username"],
        password=user["password"],
        email=user["email"],
        reedzbalance=user["reedzbalance"],
        role=user["role"],
        createdat=user["createdat"]
    )


def get_user_by_id(userid):
    res = supabase.table("users").select("*").eq("userid", userid).execute()
    data = res.data
    if not data:
        return None
    user = data[0]
    return User(
        userid=user["userid"],
        username=user["username"],
        password=user["password"],
        email=user["email"],
        reedzbalance=user["reedzbalance"],
        role=user["role"],
        createdat=user["createdat"]
    )


def update_user_password(userid, hashed_password):
    res = supabase.table("users").update({"password": hashed_password}).eq("userid", userid).execute()
    return res


def update_user_password_by_email(email, hashed_password):
    res = supabase.table("users").update({"password": hashed_password}).eq("email", email).execute()
    return res


def update_user_email(userid, new_email):
    res = supabase.table("users").update({"email": new_email}).eq("userid", userid).execute()
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
    res = supabase.table("users").update({"reedzbalance": new_balance}).eq("userid", userid).execute()
    return res


def delete_user(userid):
    res = supabase.table("users").delete().eq("userid", userid).execute()
    return res


def change_role(userid, new_role):
    res = supabase.table("users").update({"role": new_role}).eq("userid", userid).execute()
    return res


def get_leaderboard():
    res = supabase.table("users").select("username, reedzbalance").order("reedzbalance", desc=True).execute()
    return res.data


def create_bet(bet: Bet):
    res = supabase.table("bets").insert({
        "createdbyuserid": bet.createdbyuserid,
        "title": bet.title,
        "description": bet.description,
        "answertype": bet.answertype,
        "isopen": bet.isopen,
        "isresolved": bet.isresolved,
        "is_closed": bet.is_closed,
        "createdat": bet.createdat.isoformat() if isinstance(bet.createdat, datetime) else bet.createdat,
        "closeat": bet.closeat.isoformat() if isinstance(bet.closeat, datetime) else bet.closeat,
        "resolvedat": bet.resolvedat.isoformat() if bet.resolvedat is not None and isinstance(bet.resolvedat, datetime) else bet.resolvedat,
        "correctanswer": bet.correctanswer,
    }).execute()
    return res


def get_bet(betid):
    res = supabase.table("bets").select("*").eq("bet_id", betid).execute()
    data = res.data
    if data:
        b = data[0]
        return Bet(
            betid=b["bet_id"],
            createdbyuserid=b.get("createdby_user_id"),
            title=b["title"],
            description=b["description"],
            answertype=b["answer_type"],
            isopen=b.get("is_open", True),
            isresolved=b.get("is_resolved", False),
            is_closed=b.get("is_closed", False),
            createdat=b.get("created_at"),
            closeat=b.get("close_at"),
            resolvedat=b.get("resolved_at"),
            correctanswer=b.get("correct_answer"),
        )
    return None


def get_bets_by_state(state):
    bets = supabase.table("bets").select(
        "bet_id, createdby_user_id, title, description, answer_type, correct_answer, "
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


def mark_bet_distributed(betid):
    res = supabase.table("bets").update({"distributed": True}).eq("bet_id", betid).execute()
    return res


def create_prediction(prediction: Prediction):
    res = supabase.table("predictions").insert({
        "userid": prediction.userid,
        "betid": prediction.betid,
        "prediction": prediction.prediction,
        "createdat": prediction.createdat.isoformat() if isinstance(prediction.createdat, datetime) else prediction.createdat,
    }).execute()
    return res


def get_predictions_for_bet(betid):
    res = supabase.table("predictions").select("prediction_id, userid, bet_id, prediction, created_at").eq("bet_id", betid).execute()
    data = res.data
    preds = []
    for p in data:
        preds.append(Prediction(
            predictionid=p["prediction_id"],
            userid=p["userid"],
            betid=p["bet_id"],
            prediction=p["prediction"],
            createdat=p["created_at"]
        ))
    return preds


def get_user_predictions(userid):
    res = supabase.table("predictions").select("*").eq("userid", userid).execute()
    return res.data


def has_prediction(userid, betid):
    res = supabase.table("predictions").select("prediction_id").eq("userid", userid).eq("bet_id", betid).limit(1).execute()
    return bool(res.data)
