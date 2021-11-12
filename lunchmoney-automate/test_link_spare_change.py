from unittest.mock import patch

from .link_spare_change import LinkSpareChangeTask


def test_link_spare_change(call_lunchmoney):
    task = LinkSpareChangeTask('Test Asset 2', 'Test Asset 1')
    
    with patch('HourlyAutomation.link_spare_change.call_lunchmoney', side_effect=call_lunchmoney) as lunchmoney_mock:
        task.run()

        for call in lunchmoney_mock.call_args_list:
            print(f"call_lunchmoney({call})")

        lunchmoney_mock.assert_any_call('GET', '/v1/assets')
        lunchmoney_mock.assert_any_call('GET', '/v1/plaid_accounts')
        lunchmoney_mock.assert_any_call('GET', '/v1/categories')
        lunchmoney_mock.assert_any_call('GET', '/v1/transactions', params={
            'asset_id': 72,
            'start_date': task.start_date,
            'end_date': task.end_date,
            'is_group': "false"
        })
        lunchmoney_mock.assert_any_call('POST', '/v1/transactions/group', json={
            'date': '2020-01-02',
            'payee': 'Walmart',
            'category_id': 83,
            'notes': None,
            'tags': [],
            'transactions': [603, 606, 607]
        })
