import pytest
from app.chat.utils import (
    get_current_question,
    mark_question_used,
    apply_evaluation,
)
def test_get_current_question():
    questions = [
        {"question_id": "1", "used": True},
        {"question_id": "2", "used": False},
    ]

    q = get_current_question(questions)

    assert q["question_id"] == "2"

def test_mark_question_used():
    questions = [
        {"question_id": "1", "used": False},
        {"question_id": "2", "used": False},
    ]

    mark_question_used(questions, "2")

    assert questions[1]["used"] is True
    assert questions[0]["used"] is False

def test_apply_evaluation():
    questions = [
        {"text": "Q1", "score": None, "mistakes": False},
    ]

    evaluation = [
        {"question": "Q1", "score": 4},
    ]

    apply_evaluation(questions, evaluation)

    assert questions[0]["score"] == 4
    assert questions[0]["mistakes"] is True