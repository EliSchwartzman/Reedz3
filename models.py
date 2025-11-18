from enum import Enum
from typing import Optional, Union
from datetime import datetime


class Role(Enum):
    ADMIN = "admin"
    MEMBER = "member"


class User:
    def __init__(self, user_id: Optional[str], username: str, password_hash: str,
                 email: str, created_at: datetime, role: Role, reedz: int = 0):
        self.user_id = user_id
        self.username = username
        self.password_hash = password_hash
        self.email = email
        self.created_at = created_at
        self.role = role
        self.reedz = reedz


class AnswerType(Enum):
    NUMBER = "number"
    TEXT = "text"


class Bet:
    def __init__(self, bet_id: Optional[str], user_id: str, title: str, description: str,
                 answer_type: AnswerType, created_at: datetime,
                 close_at: Optional[datetime] = None, resolve_at: Optional[datetime] = None,
                 is_closed: bool = False, is_resolved: bool = False,
                 resolved_answer: Optional[Union[int, str]] = None):
        self.bet_id = bet_id
        self.user_id = user_id
        self.title = title
        self.description = description
        self.answer_type = answer_type
        self.created_at = created_at
        self.close_at = close_at
        self.resolve_at = resolve_at
        self.is_closed = is_closed
        self.is_resolved = is_resolved
        self.resolved_answer = resolved_answer


class Prediction:
    def __init__(self, prediction_id: Optional[str], bet_id: str, user_id: str,
                 prediction: Union[int, str], created_at: datetime):
        self.prediction_id = prediction_id
        self.bet_id = bet_id
        self.user_id = user_id
        self.prediction = prediction
        self.created_at = created_at
