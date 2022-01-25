from datetime import datetime, timedelta
from typing import Iterable
from decimal import Decimal
import dateparser
from opentelemetry.trace import Status, StatusCode

from .task import Task
from .utils import Account, Category, Transaction, call_lunchmoney, parse_date


class LinkTransfersTask(Task):
    def __init__(
        self,
        transfer_category: str = "Transfers",
        max_offset_days: int = 14,
        create_if_missing: bool = False,
    ) -> None:
        super().__init__()

        now = datetime.utcnow().date()

        self.start_date = (now - timedelta(days=30)).isoformat()
        self.end_date = now.isoformat()

        self.transfer_category = transfer_category
        self.max_offset_days = max_offset_days
        self.create_if_missing = create_if_missing

    def run(self):
        with self.tracer.start_as_current_span("link_transfers"):
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

            transactions = sorted(
                [t for t in transactions if t.group_id is None], key=lambda t: t.date
            )
            self.log.debug(f"{len(transactions)} transactions not yet linked")

            from_transactions = [t for t in transactions if t.payee.startswith("From ")]
            to_transactions = [t for t in transactions if t.payee.startswith("To ")]

            from_transactions = [
                ft for ft in from_transactions if self._link_transaction(
                    "From",
                    ft,
                    "To",
                    to_transactions,
                    category=category,
                    accounts=accounts,
                    max_offset_days=self.max_offset_days,
                    create_if_missing=self.create_if_missing,
                )
            ]   

            to_transactions = [
                tt for tt in to_transactions if self._link_transaction(
                    "To",
                    tt,
                    "From",
                    from_transactions,
                    category=category,
                    accounts=accounts,
                    max_offset_days=self.max_offset_days,
                    create_if_missing=self.create_if_missing,
                )
            ]

    def _link_transaction(
        self,
        kind: str,
        transaction: Transaction,
        candidate_kind: str,
        candidates: Iterable[Transaction],
        category: Category,
        accounts: Iterable[Account],
        max_offset_days: int = 1,
        create_if_missing: bool = False,
    ) -> bool:
        with self.tracer.start_as_current_span(
            "link_transaction", attributes={"transaction": transaction.id}
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
                return False

            # Find candidate transactions which are from the correct account
            account_candidates = list(
                filter(
                    lambda t: getattr(t, f"{to_account.kind}_id") == to_account.id,
                    candidates,
                )
            )

            # Find candidate transactions which are the complement of one another in value
            amount_candidates = list(
                filter(
                    lambda t: Decimal(t.amount) == -Decimal(transaction.amount),
                    account_candidates,
                )
            )

            # Find candidates which use the correct payee naming scheme
            named_candidates = list(
                filter(
                    lambda t: t.payee == f"{candidate_kind} {ft_account.alias}",
                    amount_candidates,
                )
            )

            # Find candidates which are within the max day offset of one another
            time_offset = timedelta(days=max_offset_days)
            date_candidates = list(
                filter(
                    lambda t: abs(parse_date(t.date) - parse_date(transaction.date))
                    <= time_offset,
                    named_candidates,
                )
            )

            # Order the transactions by "nearness"
            final_candidates = sorted(
                date_candidates,
                key=lambda t: abs(parse_date(t.date) - parse_date(transaction.date)),
            )

            best_link = next((c for c in final_candidates), None)
            if best_link is None and not create_if_missing:
                self.log.warning(
                    f"No match for {transaction} (account:{len(account_candidates)}, +amount:{len(amount_candidates)}, +name:{len(named_candidates)}, +time:{len(date_candidates)})"
                )
                span.set_status(Status(StatusCode.ERROR, "No match"))
                return False

            if best_link is None:
                with self.tracer.start_as_current_span("lunchmoney.create_transaction"):
                    created_ids = call_lunchmoney(
                        "POST",
                        "/v1/transactions",
                        json={
                            "apply_rules": True,
                            "skip_duplicates": False,
                            "transactions": [
                                {
                                    "id": transaction.id,
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
                                        tag.id for tag in transaction.tags
                                    ],
                                }
                            ],
                        },
                    )["ids"]

                self.log.info(f"Created new pair for {transaction}: {created_ids}")

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
                            "notes": transaction.notes,
                            "tags": [
                                tag.id for tag in transaction.tags
                            ],  # We exclude the original trigger tag
                            "transactions": [transaction.id, *created_ids],
                        },
                    )

                self.log.debug(
                    "Created group with ID/error: %s",
                    group_id,
                )
                return True

            self.log.info(f"Found link {transaction} => {best_link}")
            candidates.remove(best_link)

            bl_account = next(
                account
                for account in accounts
                if account.id in [best_link.asset_id, best_link.plaid_account_id]
            )

            with self.tracer.start_as_current_span("lunchmoney.group", attributes={"transactions": [transaction.id, best_link.id]}):
                group_id = call_lunchmoney(
                    "POST",
                    "/v1/transactions/group",
                    json={
                        "date": min(transaction.date, best_link.date),
                        "payee": f"{bl_account.alias} {candidate_kind.lower()} {ft_account.alias}",
                        "category_id": category.id,
                        "notes": "; ".join(
                            filter(
                                lambda x: x,
                                [
                                    f"{transaction.currency.upper()} {abs(Decimal(transaction.amount))}",
                                    transaction.notes,
                                    best_link.notes,
                                ],
                            )
                        ),
                        "tags": [
                            tag.id
                            for tag in [
                                *transaction.tags,
                                *best_link.tags,
                            ]
                        ],  # We exclude the original trigger tag
                        "transactions": [transaction.id, best_link.id],
                    },
                )
            self.log.debug(f" ---> {group_id}")
            return True
