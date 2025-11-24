import supabase_db

def distribute_reedz_on_resolution(bet_id):
    bet = supabase_db.get_bet(bet_id)
    predictions = supabase_db.get_predictions_for_bet(bet_id)
    num_predictions = len(predictions)
    if num_predictions == 0:
        return

    # Only for number-type
    if bet.answer_type == 'number':
        correct = float(bet.correct_answer)
        # List of (abs error, pred object)
        sorted_preds = sorted(
            [(abs(float(pred.prediction) - correct), pred) for pred in predictions],
            key=lambda x: x[0]
        )

        # Group by error (for ties)
        from collections import defaultdict
        error_groups = defaultdict(list)
        for dist, pred in sorted_preds:
            error_groups[dist].append(pred)

        # Rank logic: go through sorted error keys, give N...1 points
        scores = {}
        rank = 1
        given = 0
        positions = sorted(error_groups.keys())
        for pos, error in enumerate(positions):
            users_in_group = error_groups[error]
            rank_points = num_predictions - given
            for pred in users_in_group:
                scores[pred.user_id] = rank_points
                # +5 bonus for exact match
                if float(pred.prediction) == correct:
                    scores[pred.user_id] += 5
            given += len(users_in_group)

        # Distribute scores
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
