import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
from radar_ai.accounts import execute,AccountError,connect


class AccountTests(unittest.TestCase):
    def setUp(self):
        self.directory=tempfile.TemporaryDirectory()
        self.override=patch('radar_ai.accounts.DATABASE',Path(self.directory.name)/'accounts.sqlite3');self.override.start()
        self.addCleanup(self.directory.cleanup);self.addCleanup(self.override.stop)
        self.credentials={'name':'Teste','email':'teste@example.local','password':'senha-segura-123'}
        self.game={'name':'Meu jogo','category':'Cartas','players':4,'duration':45,'description':'Minha edição'}

    def register(self):return execute('register',self.credentials)['session_token']

    def test_register_login_and_password_storage(self):
        token=self.register();self.assertEqual(execute('me',{},token)['user']['name'],'Teste')
        logged=execute('login',self.credentials);self.assertTrue(logged['session_token'])
        db=connect()
        try:
            row=db.execute('SELECT * FROM users').fetchone()
            self.assertNotEqual(row['password_hash'],self.credentials['password'])
            self.assertNotIn(self.credentials['password'],str(dict(row)))
        finally:db.close()

    def test_auth_failures(self):
        self.register()
        for action,data in [('register',self.credentials),('login',{**self.credentials,'password':'wrong-password'}),('me',{})]:
            with self.assertRaises(AccountError):execute(action,data)

    def test_game_lifecycle_and_ownership(self):
        token=self.register();created=execute('create_game',self.game,token);gid=created['games'][0]['id']
        other=execute('register',{**self.credentials,'email':'other@example.local'})['session_token']
        self.assertEqual(execute('me',{},other)['games'],[])
        for action in ('update_game','delete_game'):
            with self.assertRaises(AccountError) as error:execute(action,{**self.game,'id':gid},other)
            self.assertEqual(error.exception.status,404)
        self.assertEqual(execute('update_game',{**self.game,'id':gid,'name':'Editado'},token)['games'][0]['name'],'Editado')
        self.assertEqual(execute('delete_game',{'id':gid},token)['games'],[])

    def test_logout_invalidates_session(self):
        token=self.register();execute('logout',{},token)
        with self.assertRaises(AccountError):execute('me',{},token)

    def test_validation(self):
        token=self.register()
        for changes in ({'players':0},{'duration':-1},{'name':''},{'players':True}):
            with self.assertRaises(AccountError):execute('create_game',{**self.game,**changes},token)


if __name__=='__main__':unittest.main()
