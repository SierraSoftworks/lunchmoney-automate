from collections import defaultdict
import json
from typing import Any, Callable, Dict, Iterable, List, TypeVar
from os import getenv
import dateparser
from opentelemetry import trace

import requests

T = TypeVar("T")
S = TypeVar("S")

tracer = trace.get_tracer(__name__)

class Wrapper:
    def __init__(self, **data: dict) -> None:
        for k, v in data.items():
            setattr(self, k, v)

    def __repr__(self) -> str:
        return json.dumps(self.__dict__)

    def __getattribute__(self, name: str) -> Any:
        try:
            return super().__getattribute__(name)
        except AttributeError:
            return None


class Account(Wrapper):
    id: int
    name: str

    def __init__(self, kind: str, **data: dict):
        super().__init__(**data)
        self.kind = kind

    @property
    def alias(self):
        return getattr(self, 'display_name', None) or self.name


class Category(Wrapper):
    id: int
    name: str
    is_group: bool
    group_id: int

    def __init__(self, **data: dict) -> None:
        super().__init__(**data)

class Tag(Wrapper):
    id: str
    name: str
    description: str

    def __init__(self, **data: dict) -> None:
        super().__init__(**data)

    def __str__(self) -> str:
        return f"#{self.name}"

class Transaction(Wrapper):
    id: int
    date: str
    payee: str
    amount: str
    currency: str
    notes: str
    category_id: int
    asset_id: int
    plaid_account_id: int
    status: str
    parent_id: int
    is_group: bool
    group_id: int
    tags: List[Tag]

    def __init__(self, **data: dict) -> None:
        super().__init__(**data)
        self.tags = [Tag(**t) for t in (self.tags or [])]

    def __str__(self) -> str:
        return f"{self.date} {self.payee} [{self.currency.upper()} {self.amount}]"


def group(items: Iterable[T], key: Callable[[T], S]) -> Dict[S, List[T]]:
    out = defaultdict(lambda: [])
    for item in items:
        out[key(item)].append(item)

    return out


def call_lunchmoney(
    method: str, endpoint: str, headers: dict = None, **kwargs
) -> Dict[str, Any]:
    with tracer.start_as_current_span(f"{method} {endpoint}", attributes={
        "method": method,
        "endpoint": endpoint,
        "headers": headers,
    }) as span:
        token = getenv("LUNCHMONEY_TOKEN")
        assert token is not None

        headers = {
            **(headers or {}),
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }

        resp = requests.request(
            method, f"https://dev.lunchmoney.app{endpoint}", headers=headers, **kwargs
        )
        span.set_attribute("status_code", resp.status_code)

        resp.raise_for_status()

        return resp.json()

def parse_date(date: str):
    return dateparser.parse(date, date_formats=["%Y-%m-%d"])