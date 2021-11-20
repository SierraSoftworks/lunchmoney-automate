from unittest.mock import patch

from .match_transfers import MatchTransfersTask


def test_match_transactions(call_lunchmoney):
    task = MatchTransfersTask(needs_match_tag="needs-pair")

    with patch(
        "lunchmoney_automate.match_transfers.call_lunchmoney",
        side_effect=call_lunchmoney,
    ) as lunchmoney_mock:
        task.run()

        for call in lunchmoney_mock.call_args_list:
            print(f"call_lunchmoney({call})")

        lunchmoney_mock.assert_any_call("GET", "/v1/assets")
        lunchmoney_mock.assert_any_call("GET", "/v1/plaid_accounts")
        lunchmoney_mock.assert_any_call("GET", "/v1/categories")
        lunchmoney_mock.assert_any_call(
            "GET",
            "/v1/transactions",
            params={
                "category_id": 85,
                "start_date": task.start_date,
                "end_date": task.end_date,
                "is_group": "false",
            },
        )
        lunchmoney_mock.assert_any_call(
            "POST",
            "/v1/transactions",
            json={
                "apply_rules": True,
                "skip_duplicates": False,
                "transactions": [
                    {
                        "date": "2020-01-03",
                        "payee": "To Test Asset 1",
                        "amount": "5.0000",
                        "currency": "usd",
                        "notes": None,
                        "category_id": 85,
                        "asset_id": 73,
                        "tags": [],
                    }
                ],
            },
        )
        lunchmoney_mock.assert_any_call(
            "POST",
            "/v1/transactions/group",
            json={
                "date": "2020-01-03",
                "payee": "Test Asset 2 to Test Asset 1",
                "category_id": 85,
                "notes": "USD 5.0000",
                "tags": [],
                "transactions": [608, 609],
            },
        )
