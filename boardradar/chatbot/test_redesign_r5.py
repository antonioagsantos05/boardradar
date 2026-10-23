import unittest
from radar_ai.accounts import AccountError
from radar_ai.marketplace import execute
import test_marketplace_phase3 as phase3


class PublicListingDetailTests(unittest.TestCase):
    setUp = phase3.MarketplacePhase3Tests.setUp
    create = phase3.MarketplacePhase3Tests.create
    add = phase3.MarketplacePhase3Tests.add
    pending = phase3.MarketplacePhase3Tests.pending
    grant = phase3.MarketplacePhase3Tests.grant
    active = phase3.MarketplacePhase3Tests.active

    def test_public_detail_has_only_browse_projection(self):
        row = self.active()
        detail = execute('public_detail', {'id': row['id']})['listing']
        self.assertEqual(detail, execute('browse', {})['listings'][0])
        self.assertFalse({'seller_id', 'email', 'review_reason', 'revision', 'status'} & set(detail))
        self.assertEqual(detail['edition_id'], row['edition_id'])

    def test_unavailable_states_and_unknown_id_are_hidden(self):
        row = self.create()
        for lid in (row['id'], 'unknown', "' OR 1=1 --"):
            with self.assertRaises(AccountError):
                execute('public_detail', {'id': lid}, self.seller)

    def test_inactive_lifecycle_is_hidden(self):
        row = self.active()
        for state in ('reserved', 'active', 'paused', 'active', 'sold'):
            row = execute('transition', {'id': row['id'], 'revision': row['revision'], 'status': state}, self.seller)['listings'][0]
            if state == 'active':
                self.assertEqual(execute('public_detail', {'id': row['id']})['listing']['id'], row['id'])
            else:
                with self.assertRaises(AccountError):
                    execute('public_detail', {'id': row['id']})

    def test_edits_hide_previously_public_detail(self):
        row = self.active()
        execute('update', {**self.data, 'id': row['id'], 'revision': row['revision']}, self.seller)
        with self.assertRaises(AccountError):
            execute('public_detail', {'id': row['id']})

    def test_detail_input_validation(self):
        for value in ('', 'x' * 81, None, 42, ['id']):
            with self.assertRaises(AccountError):
                execute('public_detail', {'id': value})


if __name__ == '__main__':
    unittest.main()
