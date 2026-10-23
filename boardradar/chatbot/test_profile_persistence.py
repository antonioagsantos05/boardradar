import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
from radar_ai.accounts import execute,AccountError
from radar_ai.catalog import DEFAULT_CATALOG,raw
class ProfilePersistenceTests(unittest.TestCase):
    def setUp(self):
        directory=tempfile.TemporaryDirectory();self.addCleanup(directory.cleanup)
        override=patch('radar_ai.accounts.DATABASE',Path(directory.name)/'profile.sqlite3');override.start();self.addCleanup(override.stop)
        self.credentials={'name':'Ana Pereira','email':'ana@example.local','password':'senha-segura-123'}
        self.token=execute('register',self.credentials)['session_token']
    def test_all_visible_franchises_and_profile_survive_new_login(self):
        selected=[v['id'] for v in raw('franchises')]
        self.assertGreater(len(selected),13)
        profile={'experience':'intermediate','styles':['estratégia','cooperativo'],'videogames':selected,'references':'','budget':250,'consent':True}
        saved=execute('save_profile',profile,self.token)
        self.assertEqual(saved['profile'],profile)
        token=execute('login',self.credentials)['session_token']
        self.assertEqual(execute('me',{},token)['profile'],profile)
        other=execute('register',{**self.credentials,'email':'other@example.local'})['session_token']
        self.assertIsNone(execute('me',{},other)['profile'])
    def test_invalid_updates_do_not_erase_saved_choices(self):
        profile={'experience':'beginner','styles':['família'],'videogames':[],'references':'','budget':100,'consent':True}
        execute('save_profile',profile,self.token)
        for update in [{'consent':False},{'videogames':['unknown-franchise']}]:
            with self.assertRaises(AccountError):execute('save_profile',{**profile,**update},self.token)
        self.assertEqual(execute('me',{},self.token)['profile'],profile)

    def test_saved_franchise_adds_real_catalog_affinity(self):
        from radar_ai.journey import bonus
        game=next(g for g in DEFAULT_CATALOG.games if 'fantasia' in g['tags'])
        selected=next(f for f in raw('franchises') if f['nome']=='Harry Potter')
        self.assertGreater(bonus(game,{'videogames':[selected['id']]}),bonus(game,{}))
