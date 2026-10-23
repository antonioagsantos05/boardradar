import copy
import json
import unittest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

from engine import respond, validate_state
from radar_ai.catalog import DEFAULT_CATALOG
from radar_ai.media import WORKS, RELATIONS, integrity_errors, linked_candidates
from radar_ai.session import begin, expired, TTL_SECONDS
from radar_ai.tools import compare_games, offers_for, editions_for
from radar_ai.recommendation import evaluate_game

NOW = datetime(2026,10,19,12,tzinfo=timezone.utc)


def game(gid, catalog=None):
    return next(g for g in (catalog or DEFAULT_CATALOG).games if g['id']==gid)


class ContextTests(unittest.TestCase):
    def sequence(self, *messages):
        state=None
        for message in messages:
            result=respond(message,state);state=json.loads(json.dumps(result['state']))
        return result

    def test_acceptance_three_turns(self):
        r=self.sequence('4 pessoas','até 250 reais','prefiro estratégia')
        self.assertEqual(r['preferences']['players'],4)
        self.assertEqual(r['preferences']['budget'],250)
        self.assertIn('estratégia',r['state']['interests'])
        self.assertTrue(r['ids'])
        for card in r['recommendations']:
            g=game(card['id']);self.assertTrue(g['players']['min']<=4<=g['players']['max'])
            self.assertLessEqual(card['price_cents'],25000);self.assertIn('estratégia',g['tags'])

    def test_correction_replaces_only_players(self):
        r=self.sequence('4 pessoas até 250 reais','na verdade 2 pessoas')
        self.assertEqual(r['preferences'],{'players':2,'budget':250})

    def test_remove_budget_keeps_players_and_interest(self):
        r=self.sequence('estratégia para 4 pessoas até 250 reais','remova o orçamento')
        self.assertEqual(r['preferences']['players'],4);self.assertNotIn('budget',r['preferences'])
        self.assertIn('estratégia',r['state']['interests'])

    def test_subject_survives_informational_turn(self):
        r=self.sequence('Fale sobre Root','ofertas dele')
        self.assertEqual(r['intent'],'offer');self.assertEqual(r['offer_groups'][0]['game_id'],'g45')
        self.assertEqual(r['recommendations'],[])

    def test_partial_comparison_completes(self):
        first=respond('Compare Root');self.assertEqual(first['state']['pending_comparison'],['g45'])
        r=respond('Scythe',first['state'])
        self.assertEqual([g['id'] for g in r['comparison']['games']],['g45','g28'])
        self.assertNotIn('pending_comparison',r['state'])

    def test_comparison_subjects_used_for_editions(self):
        r=self.sequence('Compare Root com Scythe','edições deles')
        self.assertEqual([g['game_id'] for g in r['edition_details']],['g45','g28'])

    def test_new_explicit_request_replaces_partial_comparison(self):
        r=self.sequence('Compare Root','Compare Catan com Azul')
        self.assertEqual([g['id'] for g in r['comparison']['games']],['g1','g4'])

    def test_information_does_not_complete_partial_comparison(self):
        r=self.sequence('Compare Root','Fale sobre Scythe')
        self.assertNotIn('comparison',r);self.assertEqual(r['game_details'][0]['id'],'g28')

    def test_cancel_partial_keeps_preferences(self):
        r=self.sequence('4 pessoas até 250 reais','Compare Root','cancelar')
        self.assertNotIn('pending_comparison',r['state']);self.assertEqual(r['preferences']['players'],4)
        self.assertEqual(r['preferences']['budget'],250)

    def test_reset_removes_subject_and_media(self):
        r=self.sequence('Gosto do filme Duna','Fale sobre Root','recomeçar')
        self.assertEqual(r['preferences'],{});self.assertNotIn('media_ids',r['state']);self.assertNotIn('subject_ids',r['state'])

    def test_portable_context_no_process_memory(self):
        r=respond('4 pessoas até 250 reais')
        other=respond('2 pessoas')
        self.assertNotIn('budget',other['preferences'])
        reconstructed=json.loads(json.dumps(r['state']))
        final=respond('prefiro estratégia',reconstructed)
        self.assertEqual(final['preferences']['players'],4);self.assertEqual(final['preferences']['budget'],250)

    def test_context_not_mutated(self):
        state=respond('Fale sobre Root')['state'];snapshot=copy.deepcopy(state)
        respond('ofertas dele',state);self.assertEqual(state,snapshot)

    def test_expired_clears_filters_and_asks_reconstruction(self):
        state=respond('4 pessoas até 250 reais')['state'];state['session']=begin(NOW)
        with patch('radar_ai.session.timestamp',return_value=int(NOW.timestamp())+TTL_SECONDS):
            r=respond('prefiro estratégia',state)
        self.assertEqual(r['context_status'],'expired');self.assertEqual(r['preferences'],{})
        self.assertEqual(r['ids'],[]);self.assertIn('reconstruir',r['text'])

    def test_future_session_reconstructs(self):
        state=validate_state({'session':begin(datetime.now(timezone.utc)+timedelta(days=1))})
        self.assertEqual(respond('4 pessoas',state)['context_status'],'expired')

    def test_deadline_not_extended_by_turns(self):
        r=self.sequence('4 pessoas','até 250 reais')
        self.assertEqual(respond('estratégia',r['state'])['state']['session'],r['state']['session'])

    def test_invalid_duration_rejected(self):
        session=begin(NOW);session['expires_at']+=1
        with self.assertRaises(ValueError):validate_state({'session':session})

    def test_session_boolean_version_rejected(self):
        session=begin(NOW);session['version']=True
        with self.assertRaises(ValueError):validate_state({'session':session})

    def test_ttl_boundary(self):
        session=begin(NOW)
        self.assertFalse(expired(session,NOW+timedelta(seconds=TTL_SECONDS-1)))
        self.assertTrue(expired(session,NOW+timedelta(seconds=TTL_SECONDS)))

    def test_unknown_subject_rejected(self):
        with self.assertRaises(ValueError):validate_state({'subject_ids':['unknown']})

    def test_forged_state_cannot_enable_commerce(self):
        state=respond('4 pessoas')['state'];state['is_demo']=False;state['allow_checkout']=True
        r=respond('quero comprar em lojas reais',state)
        self.assertTrue(r['is_demo']);self.assertEqual(r['ids'],[])


class ToolTests(unittest.TestCase):
    def test_comparison_only_registered_attributes(self):
        r=respond('Compare Root com Scythe')
        rows={x['attribute']:x['values'] for x in r['comparison']['rows']}
        self.assertEqual(rows['Duração (min)'],[game('g45')['duration'],game('g28')['duration']])
        for field in ('Interação','Variabilidade','Curva de aprendizado','Estratégia detalhada'):
            self.assertEqual(rows[field],['Não cadastrado']*2)
        self.assertEqual(r['ids'],[])

    def test_comparison_ineligible_is_information(self):
        r=respond('Compare Root com Scythe para 20 pessoas')
        self.assertEqual(r['ids'],[])
        self.assertTrue(all(not d['eligible_for_preferences'] for d in r['game_details']))

    def test_editions_exact_records(self):
        r=respond('Edições de Catan')
        self.assertEqual(r['edition_details'][0]['editions'],game('g1')['editions'])
        self.assertEqual(r['edition_details'][0]['metadata_status'],'pending_verification')

    def test_offers_exact_edition(self):
        r=respond('Ofertas g1-pt-base')
        self.assertEqual(len(r['offer_groups']),1)
        self.assertEqual(r['offer_groups'][0]['edition_id'],'g1-pt-base')
        self.assertEqual(r['ids'],[])

    def test_budget_marks_expensive_records(self):
        rows=offers_for([game('g1')],validate_state({'preferences':{'budget':1}}),now=NOW)
        self.assertTrue(rows[0]['offers']);self.assertFalse(rows[0]['eligible_for_preferences'])
        self.assertTrue(all(not o['within_budget'] for o in rows[0]['offers']))

    def test_stale_unavailable_and_currency_never_eligible(self):
        c=copy.deepcopy(DEFAULT_CATALOG)
        for i,o in enumerate(c.offers):
            if o['edition_id']=='g1-pt-base':
                if i%3==0:o['checked_at']='2020-01-01T12:00:00Z'
                elif i%3==1:o['availability']='out_of_stock'
                else:o['currency']='USD'
        rows=offers_for([game('g1',c)],validate_state(None),catalog=c,now=NOW)
        self.assertEqual(rows[0]['offers'],[])

    def test_corrupt_catalog_no_prices(self):
        c=copy.deepcopy(DEFAULT_CATALOG);c.offers.append(copy.deepcopy(c.offers[0]))
        rows=offers_for([game('g1',c)],validate_state(None),catalog=c,now=NOW)
        self.assertEqual(rows[0]['offers'],[])

    def test_multiple_editions_never_aggregate(self):
        c=copy.deepcopy(DEFAULT_CATALOG);g=game('g1',c)
        g['editions'].append({'id':'g1-en-expansion','name':'Test expansion','language':'en','type':'expansion'})
        o=copy.deepcopy(c.offers[0]);o.update(id='test-exp',edition_id='g1-en-expansion',price_cents=1000)
        c.offers.append(o)
        rows=offers_for([g],validate_state({'preferences':{'budget':20}}),catalog=c,now=NOW)
        self.assertEqual(len(rows),2)
        self.assertFalse(rows[0]['eligible_for_preferences']);self.assertTrue(rows[1]['eligible_for_preferences'])
        self.assertTrue(all(x['id']!='test-exp' for x in rows[0]['offers']))
        self.assertEqual([x['id'] for x in rows[1]['offers']],['test-exp'])
        card,_=evaluate_game(g,validate_state(None),catalog=c,now=NOW,edition_id='g1-en-expansion')
        self.assertEqual(card['edition_id'],'g1-en-expansion');self.assertEqual(card['price_cents'],1000)

    def test_invalid_edition_no_fallback(self):
        card,decision=evaluate_game(game('g1'),validate_state(None),edition_id='g2-pt-base')
        self.assertIsNone(card);self.assertFalse(decision.eligible)

    def test_no_invented_shipping(self):
        rows=offers_for([game('g1')],validate_state(None),now=NOW)
        self.assertFalse(rows[0]['shipping_included']);self.assertTrue(rows[0]['is_demo'])
        self.assertTrue(all('checked_at' in o for o in rows[0]['offers']))

    def test_unknown_rules_still_abstain(self):
        r=respond('Posso atacar em Root?')
        self.assertEqual(r['sources'],[]);self.assertEqual(r['answer_confidence'],'unknown')


class MediaTests(unittest.TestCase):
    def test_media_integrity(self):self.assertEqual(integrity_errors(),[])

    def test_film_dune_maps_only_registered_relations(self):
        r=respond('Gosto do filme Duna')
        self.assertEqual(r['state']['media_ids'],['media-dune-film']);self.assertTrue(r['ids'])
        self.assertTrue(set(r['ids'])<={'g22','g58','g16'})
        self.assertIn('não comprovam adaptação oficial',r['text'])
        for card in r['recommendations']:
            self.assertTrue(card['editorial_links'])
            self.assertTrue(all(x['connection_type']=='thematic' and x['review_status']=='editorial_draft' for x in card['editorial_links']))

    def test_series_witcher_does_not_select_videogame(self):
        r=respond('Gosto da série The Witcher')
        self.assertEqual(r['state']['media_ids'],['media-witcher-series'])
        self.assertNotIn('videogames',r['preferences'])

    def test_videogame_legacy_unchanged(self):
        r=respond('Gosto de The Witcher 3: Wild Hunt')
        self.assertEqual(r['preferences']['videogames'],['v1'])
        self.assertNotIn('media_ids',r['state'])

    def test_media_persists_across_filters(self):
        r=respond('Gosto do filme Duna');r=respond('4 pessoas',r['state']);r=respond('até 250 reais',r['state'])
        self.assertEqual(r['state']['media_ids'],['media-dune-film'])
        self.assertEqual(r['preferences']['players'],4);self.assertEqual(r['preferences']['budget'],250)
        self.assertTrue(all(c['price_cents']<=25000 for c in r['recommendations']))

    def test_media_never_relaxes_players(self):
        r=respond('Gosto do filme Alien para 20 pessoas')
        self.assertEqual(r['ids'],[]);self.assertEqual(r['preferences']['players'],20)

    def test_media_never_relaxes_budget(self):
        r=respond('Gosto do filme Duna até R$ 1')
        self.assertEqual(r['ids'],[]);self.assertEqual(r['preferences']['budget'],1)

    def test_new_theme_replaces_media(self):
        r=respond('Gosto do filme Duna');r=respond('prefiro família',r['state'])
        self.assertNotIn('media_ids',r['state']);self.assertIn('família',r['state']['interests'])

    def test_unknown_media_not_fabricated(self):
        r=respond('Gosto do filme InventadoXYZ')
        self.assertEqual(r['ids'],[]);self.assertNotIn('media_ids',r['state'])

    def test_negated_media_not_added(self):
        r=respond('Não gosto do filme Duna')
        self.assertNotIn('media_ids',r['state']);self.assertEqual(r['ids'],[])

    def test_bad_relation_fails_closed(self):
        links=copy.deepcopy(RELATIONS);links[0]['game_id']='unknown'
        self.assertEqual(linked_candidates(['media-dune-film'],relations=links),([],[]))

    def test_duplicate_relation_rejected(self):
        self.assertTrue(integrity_errors(relations=[*RELATIONS,RELATIONS[0]]))

    def test_invalid_provenance_rejected(self):
        works=copy.deepcopy(WORKS);works[0]['provenance']='invalid'
        self.assertTrue(integrity_errors(works=works))

    def test_invalid_weight_rejected(self):
        links=copy.deepcopy(RELATIONS);links[0]['weight']=float('nan')
        self.assertTrue(integrity_errors(relations=links))

    def test_unknown_media_context_rejected(self):
        with self.assertRaises(ValueError):validate_state({'media_ids':['fake']})


if __name__=='__main__':unittest.main()
