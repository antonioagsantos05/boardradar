import unittest
from contextlib import closing
from radar_ai.accounts import connect,AccountError
from radar_ai.marketplace import execute
import test_marketplace_phase2 as phase2


class MarketplacePhase3Tests(unittest.TestCase):
    setUp=phase2.MarketplacePhase2Tests.setUp
    create=phase2.MarketplacePhase2Tests.create
    add=phase2.MarketplacePhase2Tests.add
    pending=phase2.MarketplacePhase2Tests.pending
    grant=phase2.MarketplacePhase2Tests.grant

    def active(self):
        row=self.pending();self.grant(self.other)
        execute('approve',{'id':row['id'],'revision':row['revision'],'reason':'Fotos conferidas','edition_confirmed':True},self.other)
        return execute('mine',{},self.seller)['listings'][0]

    def test_private_drafts_not_public(self):
        row=self.create()
        self.assertEqual(execute('browse',{})['total'],0)
        row=self.add(row)
        with self.assertRaises(AccountError):execute('public_image',{'image_id':row['images'][0]['id']})

    def test_public_projection_and_exact_edition(self):
        row=self.active();result=execute('browse',{'edition_id':row['edition_id']})
        self.assertEqual(result['total'],1)
        self.assertFalse({'seller_id','review_reason','email','revision','status'}&set(result['listings'][0]))
        self.assertEqual(execute('browse',{'edition_id':'g2-pt-base'})['total'],0)
        self.assertEqual(execute('browse',{'q':'catan sao paulo'})['total'],1)
        self.assertEqual(execute('browse',{'q':"' OR 1=1 --"})['total'],0)
        self.assertTrue(execute('public_image',{'image_id':row['images'][0]['id']})['content'])

    def test_lifecycle_availability_and_photos(self):
        row=self.active();photo=row['images'][0]['id']
        for target in ('reserved','active','paused','active','sold'):
            row=execute('transition',{'id':row['id'],'revision':row['revision'],'status':target},self.seller)['listings'][0]
            self.assertEqual(execute('browse',{})['total'],1 if target=='active' else 0)
            if target!='active':
                with self.assertRaises(AccountError):execute('public_image',{'image_id':photo})
        with self.assertRaises(AccountError):execute('transition',{'id':row['id'],'revision':row['revision'],'status':'active'},self.seller)

    def test_role_and_stale_revision(self):
        row=self.active()
        for token,data in ((self.other,{'revision':row['revision']}),(self.seller,{'revision':1})):
            with self.assertRaises(AccountError):execute('transition',{'id':row['id'],'status':'sold',**data},token)
        self.assertEqual(execute('browse',{})['total'],1)

    def test_changed_content_requires_moderation(self):
        row=self.active()
        row=execute('update',{**self.data,'id':row['id'],'revision':row['revision']},self.seller)['listings'][0]
        self.assertEqual(execute('browse',{})['total'],0)
        with self.assertRaises(AccountError):execute('transition',{'id':row['id'],'revision':row['revision'],'status':'active'},self.seller)

    def test_active_removed_not_public(self):
        row=self.active();execute('remove',{'id':row['id']},self.seller)
        self.assertEqual(execute('browse',{})['total'],0)

    def test_search_validation_and_page_clamping(self):
        self.assertEqual(execute('browse',{'page':999})['page'],1)
        for data in ({'page':0},{'page':True},{'q':['bad']},{'edition_id':12}):
            with self.assertRaises(AccountError):execute('browse',data)


if __name__=='__main__':unittest.main()
