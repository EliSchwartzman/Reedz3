from models import Bet, Prediction


def distribute_reedz(bet: Bet, predictions: list[Prediction]):
    participants = len(predictions)
    if participants == 0:
        return

    if bet.answer_type == Bet.answer_type.NUMBER:
        _score_numeric(bet, predictions, participants)
    else:
        _score_text(bet, predictions, participants)


def _score_numeric(bet: Bet, predictions: list[Prediction], participants: int):
    resolved = bet.resolved_answer
    pred_dist = []
    for pred in predictions:
        dist = abs(pred.prediction - resolved)
        pred_dist.append((pred, dist))
    pred_dist.sort(key=lambda x: x[1])
    current_points = participants
    last_dist = None
    tied = []

    for i, (pred, dist) in enumerate(pred_dist):
        if dist != last_dist:
            for p in tied:
                _award_reedz(p.user_id, current_points)
            tied = []
            current_points = participants - i
        tied.append(pred)
        last_dist = dist

    for p in tied:
        _award_reedz(p.user_id, current_points)

    for pred in predictions:
        if pred.prediction == resolved:
            _award_reedz(pred.user_id, 5)


def _score_text(bet: Bet, predictions: list[Prediction], participants: int):
    answer = bet.resolved_answer.strip().lower()
    for pred in predictions:
        if pred.prediction.strip().lower() == answer:
            _award_reedz(pred.user_id, participants)
            _award_reedz(pred.user_id, 5)


def _award_reedz(user_id: str, reedz: int):
    import supabase_db
    supabase_db.increment_reedz(user_id, reedz)
