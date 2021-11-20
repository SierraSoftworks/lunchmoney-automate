import pytest
from unittest.mock import MagicMock, patch

@pytest.fixture
def lunchmoney_api_calls():
    return {
        "GET /v1/assets": {
            "assets": [
                {
                    "id": 72,
                    "type_name": "cash",
                    "subtype_name": "physical cash",
                    "name": "Test Asset 1",
                    "balance": "1201.0100",
                    "balance_as_of": "2020-01-26T12:27:22.000Z",
                    "currency": "cad",
                    "status": "active",
                    "institution_name": "Bank of Me",
                    "created_at": "2020-01-26T12:27:22.726Z",
                },
                {
                    "id": 73,
                    "type_name": "credit",
                    "subtype_name": "credit card",
                    "name": "Test Asset 2",
                    "balance": "0.0000",
                    "balance_as_of": "2020-01-26T12:27:22.000Z",
                    "currency": "usd",
                    "status": "active",
                    "institution_name": "Bank of You",
                    "created_at": "2020-01-26T12:27:22.744Z",
                },
                {
                    "id": 74,
                    "type_name": "vehicle",
                    "subtype_name": "automobile",
                    "name": "Test Asset 3",
                    "balance": "99999999999.0000",
                    "balance_as_of": "2020-01-26T12:27:22.000Z",
                    "currency": "jpy",
                    "status": "active",
                    "institution_name": "Bank of Mom",
                    "created_at": "2020-01-26T12:27:22.755Z",
                },
                {
                    "id": 75,
                    "type_name": "loan",
                    "subtype_name": None,
                    "name": "Test Asset 4",
                    "balance": "10101010101.0000",
                    "balance_as_of": "2020-01-26T12:27:22.000Z",
                    "currency": "twd",
                    "status": "active",
                    "institution_name": None,
                    "created_at": "2020-01-26T12:27:22.765Z",
                },
            ]
        },
        "GET /v1/plaid_accounts": {
            "plaid_accounts": [
                {
                    "id": 91,
                    "date_linked": "2020-01-28T14:15:09.111Z",
                    "name": "401k",
                    "type": "brokerage",
                    "subtype": "401k",
                    "mask": "7468",
                    "institution_name": "Vanguard",
                    "status": "inactive",
                    "last_import": "2019-09-04T12:57:09.190Z",
                    "balance": "12345.6700",
                    "currency": "usd",
                    "balance_last_update": "2020-01-27T01:38:11.862Z",
                    "limit": None,
                },
                {
                    "id": 89,
                    "date_linked": "2020-01-28T14:15:09.111Z",
                    "name": "Freedom",
                    "type": "credit",
                    "subtype": "credit card",
                    "mask": "1973",
                    "institution_name": "Chase",
                    "status": "active",
                    "last_import": "2019-09-04T12:57:03.250Z",
                    "balance": "0.0000",
                    "currency": "usd",
                    "balance_last_update": "2020-01-27T01:38:07.460Z",
                    "limit": 15000,
                },
            ]
        },
        "GET /v1/categories": {
            "categories": [
                {
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
                },
                {
                    "id": 84,
                    "name": "Test 2",
                    "description": None,
                    "is_income": True,
                    "exclude_from_budget": False,
                    "exclude_from_totals": True,
                    "updated_at": "2020-01-28T09:49:03.238Z",
                    "created_at": "2020-01-28T09:49:03.238Z",
                    "is_group": False,
                    "group_id": 83,
                },
                {
                    "id": 85,
                    "name": "Transfers",
                    "description": None,
                    "is_income": False,
                    "exclude_from_budget": True,
                    "exclude_from_totals": True,
                    "updated_at": "2020-01-28T09:49:03.238Z",
                    "created_at": "2020-01-28T09:49:03.238Z",
                    "is_group": False,
                    "group_id": None,
                },
            ]
        },
        "GET /v1/transactions": {
            "transactions": [
                {
                    "id": 602,
                    "date": "2020-01-01",
                    "payee": "Starbucks",
                    "amount": "4.5000",
                    "currency": "cad",
                    "notes": "Frappuccino",
                    "category_id": None,
                    "recurring_id": None,
                    "asset_id": None,
                    "plaid_account_id": None,
                    "status": "cleared",
                    "is_group": False,
                    "group_id": None,
                    "parent_id": None,
                    "external_id": None,
                    "original_name": "STARBUCKS NW 32804",
                    "type": None,
                    "subtype": None,
                    "fees": None,
                    "price": None,
                    "quantity": None,
                },
                {
                    "id": 603,
                    "date": "2020-01-02",
                    "payee": "Walmart",
                    "amount": "20.9100",
                    "currency": "usd",
                    "notes": None,
                    "category_id": 83,
                    "recurring_id": None,
                    "asset_id": 153,
                    "plaid_account_id": None,
                    "status": "uncleared",
                    "is_group": False,
                    "group_id": None,
                    "parent_id": None,
                    "external_id": "jf2r3t98o943",
                    "original_name": "Walmart Superstore ON 39208",
                    "type": None,
                    "subtype": None,
                    "fees": None,
                    "price": None,
                    "quantity": None,
                },
                {
                    "id": 604,
                    "date": "2020-01-02",
                    "payee": "To Test Asset 1",
                    "amount": "100.0000",
                    "currency": "usd",
                    "notes": None,
                    "category_id": 85,
                    "recurring_id": None,
                    "asset_id": 73,
                    "plaid_account_id": None,
                    "status": "uncleared",
                    "is_group": False,
                    "group_id": None,
                    "parent_id": None,
                    "external_id": "jf2r3t98o943",
                    "original_name": "Cash Withdrawal",
                    "type": None,
                    "subtype": None,
                    "fees": None,
                    "price": None,
                    "quantity": None,
                },
                {
                    "id": 605,
                    "date": "2020-01-02",
                    "payee": "From Test Asset 2",
                    "amount": "-100.0000",
                    "currency": "usd",
                    "notes": None,
                    "category_id": 85,
                    "recurring_id": None,
                    "asset_id": 72,
                    "plaid_account_id": None,
                    "status": "uncleared",
                    "is_group": False,
                    "group_id": None,
                    "parent_id": None,
                    "external_id": "jf2r3t98o943",
                    "original_name": "Cash Withdrawal",
                    "type": None,
                    "subtype": None,
                    "fees": None,
                    "price": None,
                    "quantity": None,
                },
                {
                    "id": 606,
                    "date": "2020-01-02",
                    "payee": "To Test Asset 1",
                    "amount": "0.0900",
                    "currency": "usd",
                    "notes": None,
                    "category_id": None,
                    "recurring_id": None,
                    "asset_id": 73,
                    "plaid_account_id": None,
                    "status": "uncleared",
                    "is_group": False,
                    "group_id": 701,
                    "parent_id": None,
                    "external_id": "jf2r3t98o943",
                    "original_name": "Spare Change",
                    "type": None,
                    "subtype": None,
                    "fees": None,
                    "price": None,
                    "quantity": None,
                },
                {
                    "id": 607,
                    "date": "2020-01-02",
                    "payee": "From Test Asset 2",
                    "amount": "-0.0900",
                    "currency": "usd",
                    "notes": None,
                    "category_id": None,
                    "recurring_id": None,
                    "asset_id": 72,
                    "plaid_account_id": None,
                    "status": "uncleared",
                    "is_group": False,
                    "group_id": 701,
                    "parent_id": None,
                    "external_id": "jf2r3t98o943",
                    "original_name": "Spare Change",
                    "type": None,
                    "subtype": None,
                    "fees": None,
                    "price": None,
                    "quantity": None,
                    "tags": [
                        { "id": 802, "name": "Fun", "description": "This transaction has added fun" },
                    ]
                },
                {
                    "id": 608,
                    "date": "2020-01-03",
                    "payee": "From Test Asset 2",
                    "amount": "-5.0000",
                    "currency": "usd",
                    "notes": None,
                    "category_id": 85,
                    "recurring_id": None,
                    "asset_id": 72,
                    "plaid_account_id": None,
                    "status": "uncleared",
                    "is_group": False,
                    "group_id": None,
                    "parent_id": None,
                    "external_id": "jf2r3t98o943",
                    "original_name": "Savings",
                    "type": None,
                    "subtype": None,
                    "fees": None,
                    "price": None,
                    "quantity": None,
                    "tags": [
                        { "id": 801, "name": "needs-pair", "description": "This transaction needs a pair to be created for it automatically" },
                    ]
                },
            ]
        },
        "POST /v1/transactions": {"ids": [609]},
        "POST /v1/transactions/group": 84389,
        "DELETE /v1/transactions/group/701": {"transactions":[606, 607]}
    }

@pytest.fixture
def call_lunchmoney(lunchmoney_api_calls):
    def call(method: str, endpoint: str, headers: dict = None, **kwargs):
        call_spec = f"{method} {endpoint}"

        print(f"{call_spec}: {kwargs}")

        if call_spec in lunchmoney_api_calls:
            return lunchmoney_api_calls[call_spec]

        raise Exception("No mocked response has been registered for this call")
    
    return MagicMock(side_effect=call)