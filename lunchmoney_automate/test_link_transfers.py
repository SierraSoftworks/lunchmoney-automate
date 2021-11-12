from unittest.mock import patch

from .link_transfers import LinkTransfersTask


def test_link_transactions(call_lunchmoney):
    task = LinkTransfersTask(create_if_missing=False)

    with patch('lunchmoney_automate.link_transfers.call_lunchmoney', side_effect=call_lunchmoney) as lunchmoney_mock:
        task.run()

        for call in lunchmoney_mock.call_args_list:
            print(f"call_lunchmoney({call})")

        lunchmoney_mock.assert_any_call('GET', '/v1/assets')
        lunchmoney_mock.assert_any_call('GET', '/v1/plaid_accounts')
        lunchmoney_mock.assert_any_call('GET', '/v1/categories')
        lunchmoney_mock.assert_any_call('GET', '/v1/transactions', params={
            'category_id': 85,
            'start_date': task.start_date,
            'end_date': task.end_date,
            'is_group': "false"
        })
        lunchmoney_mock.assert_any_call('POST', '/v1/transactions/group', json={
            'date': '2020-01-02',
            'payee': 'Test Asset 2 to Test Asset 1',
            'category_id': 85,
            'notes': 'USD 100.0000',
            'tags': [],
            'transactions': [605, 604]
    })
