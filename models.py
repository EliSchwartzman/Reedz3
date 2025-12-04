class User:
    def __init__(self, user_id, username, password, email, reedz_balance, role, created_at):
        self.user_id = user_id
        self.username = username
        self.password = password
        self.email = email
        self.reedz_balance = reedz_balance
        self.role = role
        self.created_at = created_at

class Prediction:
    def __init__(self, prediction_id, user_id, bet_id, prediction, created_at):
        self.prediction_id = prediction_id
        self.user_id = user_id
        self.bet_id = bet_id
        self.prediction = prediction
        self.created_at = created_at

class Bet:
    def __init__(
        self,
        bet_id,
        created_by_user_id,
        title,
        description,
        answer_type,
        is_open,
        is_resolved,
        created_at,
        close_at,
        resolved_at=None,
        correct_answer=None,
        is_closed=False,
    ):
        self.bet_id = bet_id
        self.created_by_user_id = created_by_user_id
        self.title = title
        self.description = description
        self.answer_type = answer_type
        self.is_open = is_open
        self.is_resolved = is_resolved
        self.created_at = created_at
        self.close_at = close_at
        self.resolved_at = resolved_at
        self.correct_answer = correct_answer
        self.is_closed = is_closed
