import tempfile
from pathlib import Path
from contextlib import closing
from unittest.mock import patch
import unittest
from radar_ai.accounts import execute as account,connect,AccountError
from radar_ai.marketplace import execute,migrate
from radar_ai.catalog import DEFAULT_CATALOG


class MarketplacePhase1Tests(unittest.TestCase):
    def setUp(self):
        folder=tempfile.TemporaryDirectory();self.addCleanup(folder.cleanup)
        override=patch('radar_ai.accounts.DATABASE',Path(folder.name)/'accounts.sqlite3');override.start();self.addCleanup(override.stop)
        self.seller=account('register',{'name':'Seller','email':'seller@example.local','password':'test-password'})['session_token']
        self.other=account('register',{'name':'Other','email':'other@example.local','password':'test-password'})['session_token']
        self.data={'edition_id':DEFAULT_CATALOG.games[0]['editions'][0]['id'],'title':'Meu Catan','description':'Jogo em bom estado de conservação.','condition':'good','language':'Português','price_cents':15000,'region':'São Paulo','components':'Completo','delivery':'pickup','negotiable':False,'sealed':False,'defects':'Sem defeitos observados'}

    def create(self):return execute('create',self.data,self.seller)['listings'][0]

    def test_migration_preserves_accounts_and_collection(self):
        account('create_game',{'name':'Meu jogo','category':'Cartas','players':2,'duration':30,'description':''},self.seller)
        execute('mine',{},self.seller);execute('mine',{},self.seller)
        self.assertEqual(len(account('me',{},self.seller)['games']),1)
        with closing(connect()) as db:
            self.assertEqual([r[0] for r in db.execute('SELECT version FROM marketplace_migrations ORDER BY version')],[1,2])

    def test_creation_ignores_privileged_fields(self):
        row=execute('create',{**self.data,'status':'active','seller_id':'other','role':'moderator'},self.seller)['listings'][0]
        self.assertEqual(row['status'],'draft');self.assertEqual(row['revision'],1)
        self.assertFalse(execute('mine',{},self.seller)['is_moderator'])
        self.assertEqual(execute('mine',{},self.other)['listings'],[])

    def test_identity_and_price_validation(self):
        for change in ({'edition_id':'unknown'},{'price_cents':0},{'price_cents':1.2},{'price_cents':True},{'condition':'unknown'},{'description':'short'}):
            with self.assertRaises(AccountError):execute('create',{**self.data,**change},self.seller)
        self.assertEqual(execute('mine',{},self.seller)['listings'],[])

    def test_owner_edit_remove_and_audit(self):
        row=self.create()
        row=execute('update',{**self.data,'id':row['id'],'revision':row['revision'],'title':'Novo título'},self.seller)['listings'][0]
        self.assertEqual(row['title'],'Novo título');self.assertEqual(row['revision'],2)
        row=execute('remove',{'id':row['id']},self.seller)['listings'][0]
        self.assertEqual(row['status'],'removed')
        with closing(connect()) as db:
            actions=[r[0] for r in db.execute('SELECT action FROM moderation_actions ORDER BY id')]
            self.assertEqual(actions,['create','edit','remove'])

    def test_third_party_cannot_modify(self):
        row=self.create()
        for action in ('update','remove','submit'):
            with self.assertRaises(AccountError) as caught:execute(action,{**self.data,'id':row['id'],'revision':1},self.other)
            self.assertEqual(caught.exception.status,404)

    def test_stale_revision_does_not_overwrite(self):
        row=self.create()
        execute('update',{**self.data,'id':row['id'],'revision':1},self.seller)
        with self.assertRaises(AccountError) as caught:execute('update',{**self.data,'id':row['id'],'revision':1},self.seller)
        self.assertEqual(caught.exception.status,409)

    def test_publication_and_roles_are_gated(self):
        row=self.create()
        for action in ('queue','approve'):
            with self.assertRaises(AccountError) as caught:execute(action,{'id':row['id']},self.seller)
            self.assertEqual(caught.exception.status,403)
        with self.assertRaises(AccountError):execute('submit',{'id':row['id']},self.seller)
        with closing(connect()) as db,db:
            user=account('me',{},self.other)['user']
            db.execute("INSERT INTO user_roles VALUES (?,'moderator')",(user['id'],))
        self.assertEqual(execute('queue',{},self.other)['listings'],[])
        with self.assertRaises(AccountError) as caught:execute('approve',{'id':row['id']},self.other)
        self.assertEqual(caught.exception.status,409)
        self.assertEqual(execute('mine',{},self.seller)['listings'][0]['status'],'draft')

    def test_authentication_required(self):
        with self.assertRaises(AccountError) as caught:execute('mine',{})
        self.assertEqual(caught.exception.status,401)


if __name__=='__main__':unittest.main()
