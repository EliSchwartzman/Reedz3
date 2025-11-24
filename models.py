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
    def __init__(self, bet_id, title, description, answer_type, close_at, correct_answer=None, is_open=True, is_resolved=False):
        self.bet_id = bet_id
        self.title = title
        self.description = description
        self.answer_type = answer_type
        self.close_at = close_at
        self.correct_answer = correct_answer
        self.is_open = is_open
        self.is_resolved = is_resolved
        self.created_at = None
        self.created_by_user_id = None
        
