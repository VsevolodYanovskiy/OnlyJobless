from app.chat.limits import today_range
from datetime import datetime

def test_today_range():
    start, end = today_range()
    assert start < end
    assert isinstance(start, datetime)
    assert isinstance(end, datetime)