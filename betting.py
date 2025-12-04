import supabase_db
from models import Bet, Prediction, User
from auth import is_admin, can_place_prediction
from datetime import datetime

def create_bet(admin_user: User, title: str, description: str, answertype: str, closeat):
    if not is_admin(admin_user):
        raise PermissionError("Only admin can create bets")
    bet = Bet(
        betid=None,
        createdbyuserid=admin_user.userid,
        title=title,
        description=description,
        answertype=answertype,
        isopen=True,
        isresolved=False,
        createdat=datetime.now(),
        closeat=closeat,
        resolvedat=None,
        correctanswer=None,
        is_closed=False
    )
    return supabase_db.create_bet(bet)

def close_bet(admin_user: User, betid):
    if not is_admin(admin_user):
        raise PermissionError("Only admin can close bets")
    return supabase_db.close_bet(betid)

def resolve_bet(admin_user: User, betid, correctanswer):
    if not is_admin(admin_user):
        raise PermissionError("Only admin can resolve bets")
    supabase_db.resolve_bet(betid, correctanswer)
    from scoring import distribute_reedz_on_resolution
    distribute_reedz_on_resolution(betid)

def place_prediction(user: User, betid, predictionvalue):
    if not can_place_prediction(user):
        raise PermissionError("User cannot place predictions")
    if supabase_db.has_prediction(user.userid, betid):
        raise Exception("Only one prediction per user per bet")
    prediction = Prediction(
        predictionid=None,
        userid=user.userid,
        betid=betid,
        prediction=str(predictionvalue),
        createdat=datetime.now()
    )
    return supabase_db.create_prediction(prediction)

def get_bet_overview(state: str):
    return supabase_db.get_bet_overview(state)
