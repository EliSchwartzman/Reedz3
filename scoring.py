import supabase_db
from collections import defaultdict


def distribute_reedz_on_resolution(bet_id):
    bet = supabase_db.get_bet(bet_id)
    predictions = supabase_db.get_predictions_for_bet(bet_id)
    num_predictions = len(predictions)
    if num_predictions == 0:
        return

    if bet.answer_type == 'number':
        correct = float(bet.correct_answer)
        sorted_preds = sorted(
            [(abs(float(pred.prediction) - correct), pred) for pred in predictions],
            key=lambda x: x[0]
        )
        error_groups = defaultdict(list)
        for dist, pred in sorted_preds:
            error_groups[dist].append(pred)
        scores = {}
        given = 0
        positions = sorted(error_groups.keys())
        for error in positions:
            users_in_group = error_groups[error]
            rank_points = num_predictions - given
            for pred in users_in_group:
                scores[pred.user_id] = rank_points
                if float(pred.prediction) == correct:
                    scores[pred.user_id] += 5
            given += len(users_in_group)
        for pred in predictions:
            supabase_db.add_reedz(pred.user_id, scores[pred.user_id])

    elif bet.answer_type == 'text':
        correct_answer = bet.correct_answer.strip().lower()
        matches = []
        nonmatches = []
        for pred in predictions:
            if pred.prediction.strip().lower() == correct_answer:
                matches.append(pred)
            else:
                nonmatches.append(pred)
        num = len(matches) + len(nonmatches)
        for pred in matches:
            supabase_db.add_reedz(pred.user_id, num + 5)
        for pred in nonmatches:
            supabase_db.add_reedz(pred.user_id, 0)

    supabase_db.mark_bet_distributed(bet_id)
