import supabase_db
from models import Bet, Prediction, User
from auth import is_admin, can_place_prediction
from datetime import datetime

def create_bet(admin_user: User, title: str, description: str, answer_type: str, close_at):
    if not is_admin(admin_user):
        raise PermissionError("Only admin can create bets")
    bet = Bet(
        bet_id=None,
        created_by_user_id=admin_user.user_id,
        title=title,
        description=description,
        answer_type=answer_type,
        is_open=True,
        is_resolved=False,
        created_at=datetime.now(),
        close_at=close_at,
        resolved_at=None,
        correct_answer=None,
        is_closed=False
    )
    return supabase_db.create_bet(bet)

def close_bet(admin_user: User, bet_id):
    if not is_admin(admin_user):
        raise PermissionError("Only admin can close bets")
    return supabase_db.close_bet(bet_id)

def resolve_bet(admin_user: User, bet_id, correct_answer):
    if not is_admin(admin_user):
        raise PermissionError("Only admin can resolve bets")
    supabase_db.resolve_bet(bet_id, correct_answer)
    from scoring import distribute_reedz_on_resolution
    distribute_reedz_on_resolution(bet_id)

def place_prediction(user: User, bet_id, prediction_value):
    if not can_place_prediction(user):
        raise PermissionError("User cannot place predictions")
    if supabase_db.has_prediction(user.user_id, bet_id):
        raise Exception("Only one prediction per user per bet")
    prediction = Prediction(
        prediction_id=None,
        user_id=user.user_id,
        bet_id=bet_id,
        prediction=str(prediction_value),
        created_at=datetime.now()
    )
    return supabase_db.create_prediction(prediction)

def get_bet_overview(state: str):
    return supabase_db.get_bet_overview(state)
