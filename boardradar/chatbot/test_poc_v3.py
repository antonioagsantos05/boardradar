import unittest
from radar_ai.catalog import DEFAULT_CATALOG, raw
from radar_ai.poc_catalog import respond


class PocV3Tests(unittest.TestCase):
    def test_catalog_is_exactly_supplied_scope(self):
        self.assertEqual(len(DEFAULT_CATALOG.games),100)
        self.assertEqual(len(DEFAULT_CATALOG.offers),300)
        self.assertEqual(DEFAULT_CATALOG.integrity_errors(),[])
        self.assertEqual(DEFAULT_CATALOG.videos,[])

    def test_recommendations_and_more_are_valid_distinct_and_limited(self):
        first=respond('Jogos para 4 pessoas')
        more=respond('Mostrar mais',first['state'])
        self.assertEqual(len(first['ids']),3)
        self.assertEqual(len(more['ids']),3)
        self.assertFalse(set(first['ids'])&set(more['ids']))
        for result in (first,more):
            for gid in result['ids']:
                game=next(g for g in raw('games') if g['game_id']==gid)
                self.assertLessEqual(game['jogadores_min'],4)
                self.assertGreaterEqual(game['jogadores_max'],4)

    def test_budget_matches_real_simulated_offer(self):
        result=respond('Jogos até R$ 200')
        for rec in result['recommendations']:
            self.assertLessEqual(rec['price_cents'],20000)
            source=[o['preco_brl'] for o in raw('store_offers')+raw('user_listings') if o['game_id']==rec['id']]
            self.assertIn(rec['price_cents'],[round(p*100) for p in source])

    def test_rejection_is_preserved_on_more(self):
        first=respond('Não gosto de terror')
        self.assertIn('terror',first['state']['excluded'])
        more=respond('Mostrar mais',first['state'])
        for gid in first['ids']+more['ids']:
            self.assertNotIn('terror',next(g for g in raw('games') if g['game_id']==gid)['temas'])

    def test_empty_constraints_and_rules(self):
        self.assertEqual(respond('Jogos até R$ 1')['ids'],[])
        self.assertEqual(respond('Regras do Catan')['recommendations'],[])

    def test_offer_lookup_and_historical_comparison(self):
        result=respond('Ofertas de Scythe')
        self.assertTrue(result['offer_groups'])
        self.assertTrue(all(o['price_cents']>0 for group in result['offer_groups'] for o in group['offers']))
        comparison=respond('Compare Scythe com Pandemic')
        self.assertIn('comparison',comparison)
        self.assertNotIn('2026',comparison['text'])

    def test_invalid_input(self):
        for message,state in [('',None),('oi',{'preferences':{'players':-1}})]:
            with self.assertRaises(ValueError):respond(message,state)

    def test_pagination_exhausts_catalog_without_repeating(self):
        result=respond('Conhecer o catálogo')
        seen=[]
        for _ in range(35):
            seen.extend(result['ids'])
            result=respond('Mostrar mais',result['state'])
        self.assertEqual(len(seen),100)
        self.assertEqual(len(set(seen)),100)
        self.assertEqual(result['ids'],[])

    def test_duration_does_not_add_a_budget_and_complexity_keeps_decimals(self):
        result=respond('Jogos até 60 minutos com complexidade até 2,5')
        self.assertNotIn('budget',result['preferences'])
        self.assertEqual(result['preferences']['complexity'],2.5)
        for gid in result['ids']:
            game=next(g for g in raw('games') if g['game_id']==gid)
            self.assertLessEqual(game['duracao_minutos'],60)
            self.assertLessEqual(game['complexidade']['valor'],2.5)


if __name__=='__main__':unittest.main()
