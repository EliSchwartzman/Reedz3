from datetime import datetime
from typing import Optional
from models import Bet, Prediction, AnswerType, Role, User
import supabase_db
import auth
import scoring


def create_bet(user: User, title: str, description: str, answer_type: AnswerType, close_at: datetime):
    auth.require_admin(user)
    bet = Bet(
        bet_id=None,
        user_id=user.user_id,
        title=title,
        description=description,
        answer_type=answer_type,
        created_at=datetime.utcnow(),
        close_at=close_at,
        is_closed=False,
        is_resolved=False
    )
    return supabase_db.insert_bet(bet)


def close_bet(user: User, bet_id: str):
    auth.require_admin(user)
    bet = supabase_db.get_bet(bet_id)
    if bet.is_closed:
        raise ValueError("Bet already closed.")
    bet.is_closed = True
    bet.close_at = datetime.utcnow()
    supabase_db.update_bet(bet)


def resolve_bet(user: User, bet_id: str, resolved_answer: str):
    auth.require_admin(user)
    bet = supabase_db.get_bet(bet_id)
    if not bet.is_closed:
        raise ValueError("Bet must be closed before resolving.")
    if bet.is_resolved:
        raise ValueError("Bet already resolved.")
    bet.is_resolved = True
    bet.resolve_at = datetime.utcnow()
    if bet.answer_type == AnswerType.NUMBER:
        bet.resolved_answer = int(resolved_answer)
    else:
        bet.resolved_answer = resolved_answer.strip()
    supabase_db.update_bet(bet)

    # Distribute reedz based on scoring system
    predictions = supabase_db.get_predictions_by_bet(bet_id)
    scoring.distribute_reedz(bet, predictions)


def place_prediction(user: User, bet_id: str, prediction: str):
    auth.require_member_or_admin(user)
    bet = supabase_db.get_bet(bet_id)
    if bet.is_closed:
        raise ValueError("Bet is closed. Cannot place prediction.")
    # Check if user already predicted
    if supabase_db.get_prediction_by_bet_and_user(bet_id, user.user_id):
        raise ValueError("User has already placed a prediction on this bet.")

    if bet.answer_type == AnswerType.NUMBER:
        prediction_value = int(prediction)
    else:
        prediction_value = prediction.strip()

    pred = Prediction(
        prediction_id=None,
        bet_id=bet_id,
        user_id=user.user_id,
        prediction=prediction_value,
        created_at=datetime.utcnow()
    )
    supabase_db.insert_prediction(pred)
