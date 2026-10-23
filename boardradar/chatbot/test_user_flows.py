import unittest
from contextlib import closing
from radar_ai.accounts import execute as account,connect,AccountError
from radar_ai.marketplace import execute,throttle
from radar_ai.journey import PROFILE
from radar_ai.state import empty_state
from radar_ai.recommendation import recommend
import test_marketplace_phase3 as phase3


class UserFlowTests(unittest.TestCase):
    setUp=phase3.MarketplacePhase3Tests.setUp
    create=phase3.MarketplacePhase3Tests.create
    add=phase3.MarketplacePhase3Tests.add
    pending=phase3.MarketplacePhase3Tests.pending
    grant=phase3.MarketplacePhase3Tests.grant
    active=phase3.MarketplacePhase3Tests.active

    def test_profile_optional_consent_edit_and_delete(self):
        self.assertIsNone(account('me',{},self.seller)['profile'])
        data={'experience':'advanced','styles':['estratégia'],'videogames':[],'references':'Duna','budget':300,'consent':True}
        with self.assertRaises(AccountError):account('save_profile',{**data,'consent':False},self.seller)
        result=account('save_profile',data,self.seller)
        self.assertEqual(result['profile']['experience'],'advanced');self.assertTrue(result['recommended_ids'])
        self.assertIsNone(account('me',{},self.other)['profile'])
        self.assertIsNone(account('delete_profile',{},self.seller)['profile'])

    def test_current_constraints_override_history(self):
        state=empty_state();state['preferences']={'players':2,'duration':60,'complexity':2};state['interests']=['família']
        marker=PROFILE.set({'experience':'advanced','styles':['guerra'],'references':'Duna','budget':9999})
        try:
            rows=recommend(state)
            self.assertTrue(rows)
            from radar_ai.catalog import DEFAULT_CATALOG
            for row in rows:
                game=next(g for g in DEFAULT_CATALOG.games if g['id']==row['id'])
                self.assertLessEqual(game['complexity'],2);self.assertLessEqual(game['duration'],60);self.assertIn('família',game['tags'])
        finally:PROFILE.reset(marker)

    def test_terms_delivery_and_conservation_validation(self):
        row=self.add(self.create())
        for data in ({},{'terms_accepted':True},{'terms_accepted':True,'terms_version':'old'}):
            with self.assertRaises(AccountError):execute('submit',{'id':row['id'],'revision':row['revision'],**data},self.seller)
        with self.assertRaises(AccountError):execute('create',{**self.data,'sealed':True,'condition':'good'},self.seller)
        row=execute('update',{**self.data,'id':row['id'],'revision':row['revision'],'delivery':'unspecified'},self.seller)['listings'][0]
        with self.assertRaises(AccountError):execute('submit',{'id':row['id'],'revision':row['revision'],'terms_accepted':True,'terms_version':'local-mvp-2026-10-20-v1'},self.seller)

    def test_contact_private_to_participants(self):
        row=self.active()
        result=execute('inquire',{'id':row['id'],'message':'Olá, aceita retirada?'},self.other)
        self.assertTrue(result['conversation_id'])
        self.assertEqual(len(execute('inbox',{},self.seller)['conversations']),1)
        stranger=account('register',{'name':'Pessoa','email':'stranger@example.local','password':'password123'})['session_token']
        self.assertEqual(execute('inbox',{},stranger)['conversations'],[])
        with self.assertRaises(AccountError):execute('reply',{'conversation_id':result['conversation_id'],'message':'intruso'},stranger)
        execute('reply',{'conversation_id':result['conversation_id'],'message':'Sim, podemos combinar.'},self.seller)
        self.assertEqual(len(execute('inbox',{},self.other)['conversations'][0]['messages']),2)
        with self.assertRaises(AccountError):execute('inquire',{'id':row['id'],'message':'Teste'},self.seller)

    def test_inquiry_requires_active_listing(self):
        row=self.create()
        with self.assertRaises(AccountError):execute('inquire',{'id':row['id'],'message':'Olá!'},self.other)

    def test_reports_and_moderator_removal(self):
        row=self.active()
        execute('report',{'id':row['id'],'reason':'Foto não corresponde ao produto'},self.seller)
        with self.assertRaises(AccountError):execute('reports',{},self.seller)
        report=execute('reports',{},self.other)['reports'][0]
        execute('resolve_report',{'record_id':report['id'],'reason':'Anúncio removido para revisão','remove':True},self.other)
        self.assertEqual(execute('browse',{})['total'],0)
        self.assertEqual(execute('reports',{},self.other)['reports'],[])

    def test_catalog_request_is_private_and_not_auto_imported(self):
        execute('request_game',{'name':'Novo jogo','edition':'Edição em português','notes':'Desejo anunciar'},self.seller)
        self.assertEqual(execute('requests',{},self.other)['requests'],[])
        self.grant(self.other)
        request=execute('requests',{},self.other)['requests'][0]
        execute('decide_request',{'record_id':request['id'],'status':'reviewed','reason':'Fonte solicitada ao vendedor'},self.other)
        self.assertEqual(execute('requests',{},self.seller)['requests'][0]['status'],'reviewed')
        with closing(connect()) as db:self.assertIsNone(db.execute("SELECT id FROM marketplace_games WHERE name='Novo jogo'").fetchone())

    def test_wishlist_opt_in_exact_edition_and_dedupe(self):
        account('save_wishlist',{'edition_id':'g1-pt-base','alert_p2p':True,'target_price':20000},self.other)
        row=self.active()
        self.assertEqual(len(account('me',{},self.other)['notifications']),1)
        # Saving again through a public bookmark must not cancel existing consent.
        account('save_wishlist',{'edition_id':'g1-pt-base'},self.other)
        self.assertEqual(account('me',{},self.other)['wishlist'][0]['alert_p2p'],1)
        from radar_ai.journey import notify_listing
        with closing(connect()) as db,db:notify_listing(db,row['id'])
        self.assertEqual(len(account('me',{},self.other)['notifications']),1)
        account('delete_wishlist',{'edition_id':'g1-pt-base'},self.other)
        self.assertEqual(account('me',{},self.other)['notifications'],[])

    def test_wrong_edition_or_price_does_not_notify(self):
        account('save_wishlist',{'edition_id':'g2-pt-base','alert_p2p':True},self.other)
        account('save_wishlist',{'edition_id':'g1-pt-base','alert_p2p':True,'target_price':100},self.other)
        self.active();self.assertEqual(account('me',{},self.other)['notifications'],[])

    def test_no_consent_no_alert_and_mark_read(self):
        account('save_wishlist',{'edition_id':'g1-pt-base'},self.other)
        self.active();self.assertEqual(account('me',{},self.other)['notifications'],[])

    def test_spam_limit(self):
        execute('mine',{},self.seller)
        with closing(connect()) as db,db:
            throttle(db,'test','message',2);throttle(db,'test','message',2)
            with self.assertRaises(AccountError) as caught:throttle(db,'test','message',2)
            self.assertEqual(caught.exception.status,429)

    def test_public_contact_information_rejected(self):
        with self.assertRaises(AccountError):execute('create',{**self.data,'description':'Fale comigo em pessoa@example.com'},self.seller)
        with self.assertRaises(AccountError):execute('create',{**self.data,'defects':'Dúvidas em pessoa@example.com'},self.seller)


if __name__=='__main__':unittest.main()
