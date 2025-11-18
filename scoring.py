from models import Bet, Prediction
from collections import defaultdict


def distribute_reedz(bet: Bet, predictions: list[Prediction]):
    participants = len(predictions)
    if participants == 0:
        return  # No points to distribute

    if bet.answer_type.name == "NUMBER":
        _score_numeric(bet, predictions, participants)
    else:
        _score_text(bet, predictions, participants)


def _score_numeric(bet: Bet, predictions: list[Prediction], participants: int):
    # Sort predictions by absolute distance to resolved answer, ascending
    resolved_answer = bet.resolved_answer
    pred_tuples = []
    for p in predictions:
        distance = abs(p.prediction - resolved_answer)
        pred_tuples.append((p, distance))
    pred_tuples.sort(key=lambda x: x[1])

    # Assign reedz scores starting from highest (#participants)
    current_points = participants
    last_distance = None
    tied_preds = []

    for i, (pred, dist) in enumerate(pred_tuples):
        if dist != last_distance:
            # Distribute points to tied preds
            for tp in tied_preds:
                _award_reedz(tp.user_id, current_points)
            tied_preds.clear()
            current_points = participants - i

        tied_preds.append(pred)
        last_distance = dist

    # Award for tie group remaining in tied_preds
    for tp in tied_preds:
        _award_reedz(tp.user_id, current_points)

    # Bonus for exact match
    for pred in predictions:
        if pred.prediction == resolved_answer:
            _award_reedz(pred.user_id, 5)


def _score_text(bet: Bet, predictions: list[Prediction], participants: int):
    resolved_answer = bet.resolved_answer.strip().lower()
    for pred in predictions:
        if pred.prediction.strip().lower() == resolved_answer:
            _award_reedz(pred.user_id, participants)
            _award_reedz(pred.user_id, 5)  # Bonus for exact match
        else:
            continue


def _award_reedz(user_id: str, reedz: int):
    import supabase_db
    supabase_db.increment_reedz(user_id, reedz)
