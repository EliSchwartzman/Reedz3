import os
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise Exception("SUPABASE_URL and SUPABASE_KEY must be set in your .env file.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# User model...
class User:
    def __init__(self, user_id, username, password, email, reedz_balance, role, created_at):
        self.user_id = user_id
        self.username = username
        self.password = password
        self.email = email
        self.reedz_balance = reedz_balance
        self.role = role
        self.created_at = created_at

# Prediction model...
class Prediction:
    def __init__(self, prediction_id, user_id, bet_id, prediction, created_at):
        self.prediction_id = prediction_id
        self.user_id = user_id
        self.bet_id = bet_id
        self.prediction = prediction
        self.created_at = created_at

# Bet model...
class Bet:
    def __init__(self, bet_id, title, description, answer_type, close_at, correct_answer=None, is_open=True, is_resolved=False):
        self.bet_id = bet_id
        self.title = title
        self.description = description
        self.answer_type = answer_type
        self.close_at = close_at
        self.correct_answer = correct_answer
        self.is_open = is_open
        self.is_resolved = is_resolved

## ----------- USER FUNCTIONS ----------- ##
# ... (No changes needed for user-related functions from earlier) ...

## ----------- BET FUNCTIONS ----------- ##
def create_bet(user, title, description, answer_type, close_at):
    res = supabase.table("bets").insert({
        "title": title,
        "description": description,
        "answer_type": answer_type,
        "close_at": close_at.isoformat() if isinstance(close_at, datetime) else close_at,
        "created_by_user_id": user.user_id,
        "is_open": True,
        "is_resolved": False,
        "created_at": datetime.now().isoformat()
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
# ... (No changes needed from prior implementation) ...
def place_prediction(user, bet_id, prediction):
    res = supabase.table("predictions").insert({
        "user_id": user.user_id,
        "bet_id": bet_id,
        "prediction": prediction,
        "created_at": datetime.now().isoformat()
    }).execute()
    return res

def get_predictions_for_bet(bet_id):
    res = supabase.table("predictions").select("prediction_id", "user_id", "bet_id", "prediction", "created_at").eq("bet_id", bet_id).execute()
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
