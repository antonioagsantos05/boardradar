import unittest
from radar_ai.bgg_catalog import data,get_game,respond,search


class BggCatalogTests(unittest.TestCase):
    def test_counts_and_details_only_record(self):
        ranks,details,_=data()
        self.assertEqual(len(ranks),182258);self.assertEqual(len(details),1000)
        self.assertEqual(set(details)-set(ranks),{'37759'})

    def test_ark_nova_has_no_invented_historical_metadata(self):
        game=get_game('bgg-342942')
        self.assertEqual(game['rank'],2);self.assertIsNone(game['min_players']);self.assertEqual(game['mechanics'],[])
        self.assertIn('só está no ZIP',respond('Fale sobre Ark Nova')['text'])

    def test_current_and_historical_ratings_are_separate(self):
        game=get_game('bgg-161936')
        self.assertEqual(game['rating'],8.49974);self.assertEqual(game['historical_rating'],8.66878)

    def test_filter_is_global_and_excludes_missing_fields(self):
        total,games=search(players=4,duration=60,limit=24)
        self.assertGreater(total,24)
        self.assertTrue(all(g['min_players']<=4<=g['max_players'] and g['max_minutes']<=60 for g in games))

    def test_comparison_uses_new_ids_and_labels_dates(self):
        result=respond('Compare Catan com Pandemic')
        self.assertEqual({g['id'] for g in result['comparison']['games']},{'bgg-13','bgg-30549'})
        self.assertTrue(any('2026' in row['attribute'] for row in result['comparison']['rows']))

    def test_filters_survive_followup_and_reset(self):
        result=respond('Jogos para 4 pessoas')
        following=respond('Até 60 minutos',result['state'])
        self.assertEqual(following['state']['preferences'],{'players':4,'duration':60})
        self.assertEqual(respond('Recomeçar',following['state'])['state']['preferences'],{})

    def test_no_legacy_offer_rule_or_video_affinity(self):
        for query in ('Posso atacar em Root?','Quero ofertas de Catan','Gosto de Mass Effect'):
            result=respond(query);self.assertEqual(result['recommendations'],[])
            self.assertNotIn('offer_groups',result);self.assertNotIn('sources',result)

    def test_unknown_does_not_use_legacy_data(self):
        game=get_game('bgg-37759');self.assertIsNone(game['rating']);self.assertIsNone(game['rank'])
        self.assertEqual(get_game('g1')['id'],'bgg-13')


if __name__=='__main__':unittest.main()
