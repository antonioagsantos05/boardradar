import unittest
from engine import respond
from radar_ai.game_index import search
from radar_ai.library import records


class GameIndexTests(unittest.TestCase):
    def test_constraints_and_category(self):
        total,rows=search(['fantasy'],players=4,duration=90)
        self.assertGreater(total,0)
        for r in rows:
            self.assertIn('Fantasy',r['categories'])
            self.assertLessEqual(r['min_players'],4)
            self.assertGreaterEqual(r['max_players'],4)
            self.assertLessEqual(r['max_minutes'],90)
            self.assertNotEqual(r['kind'],'boardgameexpansion')

    def test_missing_complexity_not_eligible(self):
        _,rows=search(complexity=2,limit=24)
        self.assertTrue(rows)
        self.assertTrue(all(0<r['complexity']<=2 for r in rows))

    def test_sql_input_is_literal(self):
        total,rows=search(["' OR 1=1 --"])
        self.assertEqual((total,rows),(0,[]))

    def test_bounds(self):
        for kwargs in ({'limit':1000},{'players':0},{'complexity':6}):
            with self.assertRaises(ValueError):search(**kwargs)

    def test_chat_search_is_informational_and_contextual(self):
        r=respond('Busque no catalogo jogos de fantasia para 4 pessoas ate 90 minutos')
        self.assertTrue(r['library_games']);self.assertEqual(r['ids'],[])
        for item in r['library_games']:
            self.assertIn('Fantasy',records()[item['id']]['categories'])
            self.assertFalse(item['is_recommendation'])
        follow=respond('Qual deles dura menos?',r['state'])
        self.assertIn('menor valor',follow['text'])
        self.assertEqual(follow['state']['library_subject_ids'],r['state']['library_subject_ids'])

    def test_budget_never_ignored(self):
        r=respond('Busque no catalogo jogos ate R$ 150')
        self.assertEqual(r['ids'],[])
        self.assertFalse(r.get('library_games'))
        self.assertIn('orçamento',r['text'])

    def test_unknown_theme_does_not_return_everything(self):
        r=respond('Busque no catalogo jogos de assuntoinexistente')
        self.assertFalse(r.get('library_games'))
        self.assertIn('categoria',r['text'])

    def test_new_constraints_override_previous(self):
        r=respond('Busque no catalogo jogos de fantasia para 4 pessoas ate 90 minutos')
        r=respond('Busque no catalogo jogos de cartas para 2 pessoas ate 30 minutos',r['state'])
        self.assertEqual(r['preferences']['players'],2)
        self.assertEqual(r['preferences']['duration'],30)
        self.assertTrue(r['library_games'])
        for item in r['library_games']:
            data=records()[item['id']]
            self.assertIn('Card Game',data['categories'])
            self.assertLessEqual(data['max_minutes'],30)


if __name__=='__main__':unittest.main()
