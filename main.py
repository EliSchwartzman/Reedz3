import unittest
from models import User, Role, Bet, AnswerType, Prediction
import scoring
import datetime


class TestScoring(unittest.TestCase):
    def test_numeric_scoring(self):
        bet = Bet("b1", "u1", "Test Bet", "Desc", AnswerType.NUMBER, datetime.datetime.utcnow())
        bet.resolved_answer = 100

        predictions = [
            Prediction("p1", "b1", "u1", 101, datetime.datetime.utcnow()),
            Prediction("p2", "b1", "u2", 105, datetime.datetime.utcnow()),
            Prediction("p3", "b1", "u3", 100, datetime.datetime.utcnow()),
            Prediction("p4", "b1", "u4", 98, datetime.datetime.utcnow()),
        ]

        # Use a mock for _award_reedz since it calls db
        awarded = {}

        def mock_award(user_id, points):
            awarded[user_id] = awarded.get(user_id, 0) + points

        scoring._award_reedz = mock_award

        scoring.distribute_reedz(bet, predictions)

        self.assertEqual(awarded["u3"], 5 + len(predictions))  # exact + bonus
        self.assertTrue("u1" in awarded)  # closest
        self.assertTrue("u4" in awarded)
        self.assertTrue("u2" in awarded)

    def test_text_scoring(self):
        bet = Bet("b1", "u1", "Test Bet", "Desc", AnswerType.TEXT, datetime.datetime.utcnow())
        bet.resolved_answer = "yes"

        predictions = [
            Prediction("p1", "b1", "u1", "yes", datetime.datetime.utcnow()),
            Prediction("p2", "b1", "u2", "no", datetime.datetime.utcnow()),
        ]

        awarded = {}

        def mock_award(user_id, points):
            awarded[user_id] = awarded.get(user_id, 0) + points

        scoring._award_reedz = mock_award

        scoring.distribute_reedz(bet, predictions)

        self.assertEqual(awarded["u1"], len(predictions) + 5)
        self.assertFalse("u2" in awarded)


if __name__ == "__main__":
    unittest.main()
