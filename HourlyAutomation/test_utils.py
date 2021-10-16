import pytest
from datetime import datetime
from .utils import parse_date, group, Category

@pytest.mark.parametrize(
    ["text", "expected"],
    [("2021-01-07", datetime(2021, 1, 7)), ("2019-12-01", datetime(2019, 12, 1))],
)
def test_parse_date(text: str, expected: datetime):
    assert parse_date(text) == expected

def test_group():
    assert group([1,2,3,4,5], key=lambda i: i%2) == {
        0: [2,4],
        1: [1,3,5]
    }

def test_category():
    category = Category(**{
                    "id": 83,
                    "name": "Test 1",
                    "description": "Test description",
                    "is_income": False,
                    "exclude_from_budget": True,
                    "exclude_from_totals": False,
                    "updated_at": "2020-01-28T09:49:03.225Z",
                    "created_at": "2020-01-28T09:49:03.225Z",
                    "is_group": True,
                    "group_id": None,
                })

    assert category.is_income == False
    assert category.is_group == True