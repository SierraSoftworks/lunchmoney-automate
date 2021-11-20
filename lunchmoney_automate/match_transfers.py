from datetime import datetime, timedelta
from typing import Iterable
from decimal import Decimal
import dateparser
from opentelemetry.trace import Status, StatusCode

from .task import Task
from .utils import Account, Category, Transaction, call_lunchmoney, parse_date


class MatchTransfersTask(Task):
    def __init__(
        self,
        transfer_category: str = "Transfers",
        needs_match_tag: str = "needs-match"
    ) -> None:
        super().__init__()

        now = datetime.utcnow().date()

        self.start_date = (now - timedelta(days=30)).isoformat()
        self.end_date = now.isoformat()

        self.transfer_category = transfer_category
        self.needs_match_tag = needs_match_tag

    def run(self):
        with self.tracer.start_as_current_span("match_transfers"):
            with self.tracer.start_as_current_span("lunchmoney.accounts"):
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
                self.log.debug(f"{account.alias} ({account.id})")

            with self.tracer.start_as_current_span("lunchmoney.categories"):
                categories = [
                    Category(**cat)
                    for cat in call_lunchmoney("GET", "/v1/categories")["categories"]
                ]
            self.log.debug(f"{len(categories)} categories loaded from Lunch Money")
            category = next(cat for cat in categories if cat.name == self.transfer_category)
            for cat in categories:
                self.log.debug(f"{cat.name} ({cat.id}, selected:{category == cat})")

            with self.tracer.start_as_current_span("lunchmoney.transactions"):
                transactions = [
                    Transaction(**cat)
                    for cat in call_lunchmoney(
                        "GET",
                        "/v1/transactions",
                        params={
                            "category_id": category.id,
                            "start_date": self.start_date,
                            "end_date": self.end_date,
                            "is_group": "false",
                        },
                    )["transactions"]
                ]

            self.log.debug(f"{len(transactions)} transactions loaded from Lunch Money")

            transactions = [t for t in transactions if t.group_id is None]
            self.log.debug(f"{len(transactions)} transactions not yet linked")

            transactions = [t for t in transactions if any(tag.name == self.needs_match_tag for tag in t.tags)]
            self.log.debug(f"{len(transactions)} transactions tagged to have missing transaction created")

            from_transactions = [t for t in transactions if t.payee.startswith("From ")]
            to_transactions = [t for t in transactions if t.payee.startswith("To ")]

            for ft in from_transactions:
                self._match_transaction(
                    "From",
                    ft,
                    "To",
                    category=category,
                    accounts=accounts,
                )

            for tt in to_transactions:
                self._match_transaction(
                    "To",
                    tt,
                    "From",
                    category=category,
                    accounts=accounts,
                )

    def _match_transaction(
        self,
        kind: str,
        transaction: Transaction,
        candidate_kind: str,
        category: Category,
        accounts: Iterable[Account],
    ):
        with self.tracer.start_as_current_span(
            "match_transaction", attributes={"transaction": transaction.id}
        ) as span:
            ft_account = next(
                account
                for account in accounts
                if account.id in [transaction.asset_id, transaction.plaid_account_id]
            )

            to_account = next(
                (
                    account
                    for account in accounts
                    if f"{kind} {account.alias}" == transaction.payee
                ),
                None,
            )
            if to_account is None:
                self.log.warning(
                    f"No account matching '{transaction.payee[len(kind)+1:]}' for {transaction}"
                )
                span.set_status(Status(StatusCode.ERROR, "No account matching"))
                return

            with self.tracer.start_as_current_span("lunchmoney.create_transaction"):
                created_ids = call_lunchmoney(
                    "POST",
                    "/v1/transactions",
                    json={
                        "apply_rules": True,
                        "skip_duplicates": False,
                        "transactions": [
                            {
                                "date": transaction.date,
                                "payee": f"{candidate_kind} {ft_account.alias}",
                                "amount": (
                                    ""
                                    if transaction.amount.startswith("-")
                                    else "-"
                                )
                                + transaction.amount.lstrip("-"),
                                "currency": transaction.currency,
                                "notes": transaction.notes,
                                "category_id": category.id,
                                f"{to_account.kind}_id": to_account.id,
                                "tags": [
                                    tag.id for tag in transaction.tags if tag.name != self.needs_match_tag
                                ],
                            }
                        ],
                    },
                )["ids"]

                self.log.info(f"Created new matching transaction for {transaction}: {created_ids}")

                with self.tracer.start_as_current_span(
                    "lunchmoney.group",
                    attributes={"transactions": [transaction.id, *created_ids]},
                ):
                    group_id = call_lunchmoney(
                        "POST",
                        "/v1/transactions/group",
                        json={
                            "date": transaction.date,
                            "payee": f"{to_account.alias} {candidate_kind.lower()} {ft_account.alias}",
                            "category_id": category.id,
                            "notes": "; ".join(
                                filter(
                                    lambda x: x,
                                    [
                                        f"{transaction.currency.upper()} {abs(Decimal(transaction.amount))}",
                                        transaction.notes,
                                    ],
                                )
                            ),
                            "tags": [
                                tag.id for tag in transaction.tags
                                if tag.name != self.needs_match_tag
                            ],  # We exclude the original trigger tag
                            "transactions": [transaction.id, *created_ids],
                        },
                    )

                self.log.debug(
                    "Created group with ID/error: %s",
                    group_id,
                )
