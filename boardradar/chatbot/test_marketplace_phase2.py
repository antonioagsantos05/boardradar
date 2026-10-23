import base64
from contextlib import closing
import unittest
from radar_ai.accounts import connect,execute as account,AccountError
from radar_ai.marketplace import execute
import test_marketplace_phase1 as phase1


class MarketplacePhase2Tests(unittest.TestCase):
    setUp=phase1.MarketplacePhase1Tests.setUp
    create=phase1.MarketplacePhase1Tests.create

    def add(self,row,token=None):
        return execute('add_image',{'id':row['id'],'revision':row['revision'],'content':base64.b64encode(b'\xff\xd8\xfftest\xff\xd9').decode()},token or self.seller)['listings'][0]

    def grant(self,token):
        user=account('me',{},token)['user']
        with closing(connect()) as db,db:db.execute("INSERT OR IGNORE INTO user_roles VALUES (?,'moderator')",(user['id'],))

    def pending(self):
        row=self.add(self.create())
        return execute('submit',{'id':row['id'],'revision':row['revision'],'terms_accepted':True,'terms_version':'local-mvp-2026-10-20-v1'},self.seller)['listings'][0]

    def test_photo_required_for_submit(self):
        row=self.create()
        with self.assertRaises(AccountError):execute('submit',{'id':row['id'],'revision':row['revision'],'terms_accepted':True,'terms_version':'local-mvp-2026-10-20-v1'},self.seller)
        self.assertEqual(execute('mine',{},self.seller)['listings'][0]['status'],'draft')

    def test_photo_access_and_limit(self):
        row=self.create()
        for _ in range(6):row=self.add(row)
        self.assertEqual(len(row['images']),6)
        with self.assertRaises(AccountError):self.add(row)
        photo=row['images'][0]['id']
        self.assertTrue(execute('image',{'image_id':photo},self.seller)['content'])
        with self.assertRaises(AccountError):execute('image',{'image_id':photo},self.other)
        with self.assertRaises(AccountError):execute('image',{'image_id':photo})
        with self.assertRaises(AccountError):self.add(row,self.other)

    def test_invalid_photo_and_revision(self):
        row=self.create()
        for content in ('not-base64','PHN2Zz48L3N2Zz4='):
            with self.assertRaises(AccountError):execute('add_image',{'id':row['id'],'revision':1,'content':content},self.seller)
        row=self.add(row)
        with self.assertRaises(AccountError):execute('delete_image',{'id':row['id'],'revision':1,'image_id':row['images'][0]['id']},self.seller)

    def test_approve_requires_role_reason_confirmation_and_current_revision(self):
        row=self.pending();data={'id':row['id'],'revision':row['revision'],'reason':'Fotos conferidas','edition_confirmed':True}
        with self.assertRaises(AccountError):execute('approve',data,self.other)
        self.grant(self.other)
        for changed in ({'reason':''},{'edition_confirmed':False},{'revision':1}):
            with self.assertRaises(AccountError):execute('approve',{**data,**changed},self.other)
        self.assertEqual(len(execute('queue',{},self.other)['listings']),1)
        self.assertEqual(execute('approve',data,self.other)['listings'],[])
        self.assertEqual(execute('mine',{},self.seller)['listings'][0]['status'],'active')

    def test_self_approval_forbidden(self):
        row=self.pending();self.grant(self.seller)
        with self.assertRaises(AccountError) as e:execute('approve',{'id':row['id'],'revision':row['revision'],'reason':'Fotos conferidas','edition_confirmed':True},self.seller)
        self.assertEqual(e.exception.status,403)

    def test_rejection_reason_and_resubmission(self):
        row=self.pending();self.grant(self.other)
        execute('reject',{'id':row['id'],'revision':row['revision'],'reason':'Fotografe os componentes'},self.other)
        row=execute('mine',{},self.seller)['listings'][0]
        self.assertEqual(row['status'],'rejected');self.assertEqual(row['review_reason'],'Fotografe os componentes')
        row=self.add(row)
        self.assertEqual(row['status'],'draft')
        self.assertEqual(execute('submit',{'id':row['id'],'revision':row['revision'],'terms_accepted':True,'terms_version':'local-mvp-2026-10-20-v1'},self.seller)['listings'][0]['status'],'pending_review')

    def test_approved_edits_and_photo_removal_reset_review(self):
        row=self.pending();self.grant(self.other)
        execute('approve',{'id':row['id'],'revision':row['revision'],'reason':'Fotos conferidas','edition_confirmed':True},self.other)
        row=execute('mine',{},self.seller)['listings'][0]
        row=execute('update',{**self.data,'id':row['id'],'revision':row['revision']},self.seller)['listings'][0]
        self.assertEqual(row['status'],'draft')
        row=execute('delete_image',{'id':row['id'],'revision':row['revision'],'image_id':row['images'][0]['id']},self.seller)['listings'][0]
        self.assertEqual(row['images'],[])
        with self.assertRaises(AccountError):execute('submit',{'id':row['id'],'revision':row['revision'],'terms_accepted':True,'terms_version':'local-mvp-2026-10-20-v1'},self.seller)

    def test_moderation_cannot_use_stale_pending_snapshot(self):
        row=self.pending();self.grant(self.other)
        self.add(row)
        with self.assertRaises(AccountError):execute('approve',{'id':row['id'],'revision':row['revision'],'reason':'Fotos conferidas','edition_confirmed':True},self.other)


if __name__=='__main__':unittest.main()
