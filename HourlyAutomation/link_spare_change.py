from datetime import datetime, timedelta
from typing import Iterable, List
from decimal import Decimal
import dateparser
import math

from .task import Task
from .utils import Account, Category, Transaction, call_lunchmoney


class LinkSpareChangeTask(Task):
    def __init__(
        self,
        main_account: str,
        savings_account: str,
        multiplier: int = 1,
        ignore_categories: List[str] = ["Transfers"],
        max_offset_days: int = 1,
    ) -> None:
        super().__init__()

        now = datetime.utcnow().date()

        self.start_date = (now - timedelta(days=30)).isoformat()
        self.end_date = now.isoformat()

        self.main_account = main_account
        self.savings_account = savings_account

        self.multiplier = multiplier
        self.ignore_categories = ignore_categories

        self.max_offset_days = max_offset_days

    def run(self):
        accounts = [
            *(
                Account("asset", **asset)
                for asset in call_lunchmoney("GET", "/v1/assets")["assets"]
            ),
            *(
                Account("plaid_account", **asset)
                for asset in call_lunchmoney("GET", "/v1/plaid_accounts")[
                    "plaid_accounts"
                ]
            ),
        ]

        self.log.debug(f"{len(accounts)} accounts loaded from Lunch Money")
        for account in accounts:
            self.log.debug(" -", account.alias, f"({account.id})")

        categories = [
            Category(**cat)
            for cat in call_lunchmoney("GET", "/v1/categories")["categories"]
        ]
        self.log.debug(f"{len(categories)} categories loaded from Lunch Money")
        ignore_categories = list(
            cat for cat in categories if cat.name in self.ignore_categories
        )
        ignored_category_ids = [c.id for c in ignore_categories]
        for cat in categories:
            self.log.debug(f"{cat.name} ({cat.id}, ignored:{cat in ignore_categories})")

        main_account = next(a for a in accounts if a.alias == self.main_account)
        savings_account = next(a for a in accounts if a.alias == self.savings_account)

        main_transactions = [
            Transaction(**cat)
            for cat in call_lunchmoney(
                "GET",
                "/v1/transactions",
                params={
                    f"{main_account.kind}_id": main_account.id,
                    "start_date": self.start_date,
                    "end_date": self.end_date,
                    "is_group": "false",
                },
            )["transactions"]
        ]

        self.log.debug(
            f"{len(main_transactions)} transactions loaded from Lunch Money for {main_account.alias}"
        )
        main_transactions = list(
            filter(
                lambda t: t.category_id not in ignored_category_ids, main_transactions
            )
        )
        self.log.debug(
            f"{len(main_transactions)} transactions in {main_account.alias} account which aren't in the ignored categories"
        )

        savings_transactions = [
            Transaction(**cat)
            for cat in call_lunchmoney(
                "GET",
                "/v1/transactions",
                params={
                    f"{savings_account.kind}_id": savings_account.id,
                    "start_date": self.start_date,
                    "end_date": self.end_date,
                    "is_group": "false",
                },
            )["transactions"]
        ]

        self.log.debug(
            f"{len(savings_transactions)} transactions loaded from Lunch Money for {savings_account.alias}"
        )

        for t in main_transactions:
            if t.group_id is not None:
                # Don't attempt to group transactions which are already grouped
                self.log.debug(f"Skipping {t} because it is already grouped")
                continue

            if t.status == "recurring":
                # We can't group recurring transactions
                self.log.debug(
                    f"Skipping {t} because it is part of a recurring transaction (which can't be grouped)"
                )
                continue

            amt = Decimal(t.amount)
            if amt < 0:
                # Ignore incoming transactions since they don't generate spare change
                self.log.debug(
                    f"Skipping {t} because it is an inbound transfer which doesn't generate spare change"
                )
                continue

            spare_change = -self.multiplier * (
                (math.ceil(abs(amt)) - abs(amt)) or Decimal(1)
            )
            self.log.debug(f"{t} (spare change: {spare_change})")

            date_candidates = list(
                filter(
                    lambda c: abs(self._parse_date(c.date) - self._parse_date(t.date))
                    < timedelta(days=self.max_offset_days),
                    savings_transactions,
                )
            )
            value_candidates = list(
                filter(lambda c: Decimal(c.amount) == spare_change, date_candidates)
            )

            st = next((c for c in value_candidates), None)
            if not st:
                self.log.info(
                    f"Skipping {t} because no spare matching change transactions were found (in date range:{len(date_candidates)}, +amount:{len(value_candidates)})"
                )
                continue

            self.log.debug(t, " ---> ", st)
            savings_transactions.remove(st)

            transactions = set([t.id, st.id])

            if st.group_id is not None:
                old_group = call_lunchmoney(
                    "DELETE", f"/v1/transactions/group/{st.group_id}"
                )["transactions"]
                transactions = transactions.union(old_group)
                self.log.debug(f"Split old group containing {old_group}")

            new_group = call_lunchmoney(
                "POST",
                "/v1/transactions/group",
                json={
                    "date": t.date,
                    "payee": t.payee,
                    "category_id": t.category_id,
                    "notes": t.notes,
                    "tags": [tag["id"] for tag in (t.tags or [])],
                    "transactions": list(transactions),
                },
            )
            self.log.info(
                f"Completed {t} by forming new group {new_group} with transactions {list(transactions)}"
            )

    def _parse_date(self, date: str):
        return dateparser.parse(date, date_formats=["%Y-%m-%d"])
