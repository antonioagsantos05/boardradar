import unittest
from radar_ai.poc_catalog import respond
from radar_ai.catalog import raw
from radar_ai.journey import PROFILE
class ChatEvolutionTests(unittest.TestCase):
 def setUp(self):
  f=next(f for f in raw('franchises') if f['nome']=='Alien')
  self.profile={'consent':True,'videogames':[f['id']],'styles':['combate'],'budget':200,'display_name':'Ana Silva'}
  self.token=PROFILE.set(self.profile)
 def tearDown(self):PROFILE.reset(self.token)
 def test_profile_names_the_franchise_and_personalized_greeting(self):
  self.assertIn('Ana',respond('oi')['text'])
  result=respond('Usar meus gostos')
  self.assertTrue(any('Porque você gosta de Alien' in r['reason'] for r in result['recommendations']))
 def test_profile_does_not_add_hard_budget_or_player_limits(self):
  result=respond('Jogos para 4 pessoas até R$ 500')
  self.assertEqual(result['preferences']['budget'],500)
  for gid in result['ids']:
   g=next(g for g in raw('games') if g['game_id']==gid)
   self.assertLessEqual(g['jogadores_min'],4);self.assertGreaterEqual(g['jogadores_max'],4)
 def test_explicit_franchise_overrides_saved_franchise(self):
  result=respond('Gosto de Duna')
  self.assertTrue(result['recommendations'])
  self.assertTrue(any('Porque você gosta de Duna' in r['reason'] for r in result['recommendations']))
  self.assertTrue(all('Porque você gosta de Alien' not in r['reason'] for r in result['recommendations']))
 def test_why_and_comparison_follow_the_previous_recommendations(self):
  first=respond('Usar meus gostos');why=respond('Por que esses jogos?',first['state'])
  self.assertEqual(set(first['ids']),set(why['ids']))
  comparison=respond('Compare esses jogos',first['state']);self.assertIn('comparison',comparison)
 def test_franchise_is_remembered_on_show_more(self):
  first=respond('Gosto de Duna');second=respond('Mostrar mais',first['state'])
  self.assertFalse(set(first['ids'])&set(second['ids']))
  self.assertEqual(first['state']['preferences']['videogames'],second['state']['preferences']['videogames'])
 def test_sell_and_conversations_have_current_destinations(self):
  self.assertEqual(respond('Quero anunciar um jogo')['actions'][0]['href'],'/vender')
  self.assertEqual(respond('Minhas conversas')['actions'][0]['href'],'/mensagens')
 def test_no_consent_does_not_use_profile(self):
  token=PROFILE.set({**self.profile,'consent':False})
  try:self.assertTrue(all('Alien' not in r['reason'] for r in respond('Usar meus gostos').get('recommendations',[])))
  finally:PROFILE.reset(token)
 def test_reset_clears_conversational_filters(self):
  first=respond('Jogos para 4 pessoas até R$ 200');result=respond('Recomeçar',first['state']);self.assertEqual(result['preferences'],{});self.assertEqual(result['state']['last_ids'],[])
if __name__=='__main__':unittest.main()
