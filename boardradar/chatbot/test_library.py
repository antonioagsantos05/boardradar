import importlib.util
import json
from pathlib import Path
import unittest
from engine import respond
from radar_ai.library import records

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('archive_import',ROOT/'scripts/import-boardgame-archives.py')
importer=importlib.util.module_from_spec(spec);spec.loader.exec_module(importer)


class MergedLibraryTests(unittest.TestCase):
    def test_all_ids_unique(self):
        data=json.loads((ROOT/'src/data/library.json').read_text(encoding='utf-8'))
        self.assertEqual(len(data),10682);self.assertEqual(len({g['bgg_id'] for g in data}),len(data))

    def test_same_id_merges_but_same_title_does_not(self):
        base={'bgg_id':'1','name':'Same name','sources':['csv'],'field_sources':{},'description':'Original','complexity':None}
        second={**base,'bgg_id':'2'};api={**base,'description':'New','complexity':2.4,'sources':['api']}
        result,conflicts=importer.merge_records([base,second],[api])
        self.assertEqual(len(result),2);self.assertEqual(result['1']['complexity'],2.4)
        self.assertEqual(result['1']['field_sources']['description'],'api');self.assertTrue(conflicts)

    def test_heat_old_game_not_attached_to_new_game(self):
        heat=records()['bgg-157815'];self.assertEqual(heat['year'],2015)
        self.assertNotIn('curated_game_id',heat)

    def test_wingspan_has_community_weight(self):
        wing=records()['bgg-266192'];self.assertTrue(1<=wing['complexity']<=5)
        self.assertEqual(wing['kind'],'boardgame');self.assertEqual(len(wing['sources']),1)

    def test_missing_complexity_is_not_invented(self):
        self.assertIsNone(records()['bgg-1']['complexity'])

    def test_expansions_kept_separate(self):
        manifest=json.loads((ROOT/'src/data/library-manifest.json').read_text(encoding='utf-8'))
        self.assertEqual(manifest['kinds']['boardgameexpansion'],61)
        self.assertEqual(manifest['overlapping_ids'],96)

    def test_personal_stats_not_imported(self):
        for r in records().values():
            self.assertFalse({'playRecords','winner','winCountHannah','source'}&set(r))

    def test_external_chat_lookup_is_informational(self):
        r=respond('Fale sobre Die Macher')
        self.assertEqual(r['library_games'][0]['id'],'bgg-1');self.assertEqual(r['ids'],[])
        self.assertFalse(r['library_games'][0]['is_recommendation'])

    def test_external_chat_no_fake_offer(self):
        r=respond('Fale sobre Die Macher');r=respond('Ofertas dele',r['state'])
        self.assertEqual(r['ids'],[]);self.assertIn('sem preços',r['text'])

    def test_external_metadata_not_rule_evidence(self):
        r=respond('Posso atacar em Die Macher?')
        self.assertEqual(r['answer_confidence'],'unknown');self.assertEqual(r['sources'],[])

    def test_comparison_alias_not_film(self):
        r=respond('Compare o Nemesis com o Duna Imperium')
        self.assertEqual({g['id'] for g in r['comparison']['games']},{'g35','g22'})
        self.assertNotIn('media_ids',r['state'])

    def test_partial_comparison_alias_not_film(self):
        r=respond('Compare Nemesis');r=respond('Duna:Imperium',r['state'])
        self.assertEqual({g['id'] for g in r['comparison']['games']},{'g35','g22'})

    def test_new_concept_followup_and_prose(self):
        r=respond('O que é deck-building?')
        self.assertTrue(r['text'].startswith('Deck-building'))
        r=respond('me fale outra mecanica',r['state'])
        self.assertEqual(r['sources'][0]['chunk_id'],'chunk-worker-placement')

    def test_4x_followup_does_not_become_filter(self):
        r=respond('O que é 4X?');r=respond('Isso significa que tem combate?',r['state'])
        self.assertEqual(r['ids'],[]);self.assertEqual(r['state']['interests'],[])
        self.assertIn('não informa sozinha',r['text'])

    def test_compare_short_question_uses_existing_pair(self):
        r=respond('Compare Root com Scythe');r=respond('Qual dos dois dura menos?',r['state'])
        self.assertIn('Root',r['text']);self.assertIn('Scythe',r['text']);self.assertEqual(r['ids'],[])

    def test_new_game_drops_previous_concept(self):
        r=respond('O que é 4X?');r=respond('Fale sobre Root',r['state'])
        self.assertNotIn('last_topic',r['state'])

    def test_external_game_drops_previous_concept(self):
        r=respond('O que é 4X?');r=respond('Fale sobre Die Macher',r['state'])
        self.assertNotIn('last_topic',r['state'])


if __name__=='__main__':unittest.main()
