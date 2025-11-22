from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class User:
    user_id: Optional[int]
    username: str
    password: str
    email: str
    reedz_balance: int
    role: str
    created_at: datetime

@dataclass
class Bet:
    bet_id: Optional[int]
    created_by_user_id: int
    title: str
    description: str
    answer_type: str
    is_open: bool
    is_resolved: bool
    created_at: datetime
    close_at: datetime
    resolved_at: Optional[datetime]
    correct_answer: Optional[str]

@dataclass
class Prediction:
    prediction_id: Optional[int]
    user_id: int
    bet_id: int
    prediction: str
    created_at: datetime
