import os
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")  # Ensure this matches your .env

if not SUPABASE_URL or not SUPABASE_KEY:
    raise Exception("SUPABASE_URL and SUPABASE_KEY must be set in your .env file.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# User model
class User:
    def __init__(self, user_id, username, password, email, reedz_balance, role, created_at):
        self.user_id = user_id
        self.username = username
        self.password = password
        self.email = email
        self.reedz_balance = reedz_balance
        self.role = role
        self.created_at = created_at

# Prediction model
class Prediction:
    def __init__(self, prediction_id, user_id, bet_id, prediction, created_at):
        self.prediction_id = prediction_id
        self.user_id = user_id
        self.bet_id = bet_id
        self.prediction = prediction
        self.created_at = created_at

# Bet model
class Bet:
    def __init__(self, bet_id, title, description, answer_type, close_at, correct_answer=None, state=None):
        self.bet_id = bet_id
        self.title = title
        self.description = description
        self.answer_type = answer_type
        self.close_at = close_at
        self.correct_answer = correct_answer
        self.state = state

## ----------- USER FUNCTIONS ----------- ##
def create_user(user: User):
    res = supabase.table("users").insert({
        "username": user.username,
        "password": user.password,
        "email": user.email,
        "reedz_balance": user.reedz_balance,
        "role": user.role,
        "created_at": user.created_at
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
            email=u.get("email",""), reedz_balance=u["reedz_balance"],
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

def update_user_email(user_id, new_email):
    res = supabase.table("users").update({"email": new_email}).eq("user_id", user_id).execute()
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
def create_bet(user, title, description, answer_type, close_at):
    res = supabase.table("bets").insert({
        "title": title,
        "description": description,
        "answer_type": answer_type,
        "close_at": close_at,
        "creator_id": user.user_id,
        "state": "open",
        "created_at": datetime.now()
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
            state=b.get("state","open")
        )
    return None

def get_bet_overview(state=""):
    q = supabase.table("bets").select("bet_id", "title", "description", "answer_type", "correct_answer", "state")
    if state == "":
        res = q.execute()
    else:
        res = q.eq("state", state).execute()
    return res.data

def close_bet(user, bet_id):
    res = supabase.table("bets").update({"state": "closed"}).eq("bet_id", bet_id).execute()
    return res

def resolve_bet(user, bet_id, correct_answer):
    res = supabase.table("bets").update({
        "state": "resolved", "correct_answer": correct_answer
    }).eq("bet_id", bet_id).execute()
    return res

def mark_bet_distributed(bet_id):
    res = supabase.table("bets").update({"distributed": True}).eq("bet_id", bet_id).execute()
    return res

## ----------- PREDICTION FUNCTIONS ----------- ##
def place_prediction(user, bet_id, prediction):
    res = supabase.table("predictions").insert({
        "user_id": user.user_id,
        "bet_id": bet_id,
        "prediction": prediction,
        "created_at": datetime.now()
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
