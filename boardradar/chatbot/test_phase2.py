import copy
from datetime import datetime,timezone,timedelta
import json
from pathlib import Path
import unittest

from engine import respond,validate_state,rank
from radar_ai.catalog import Catalog,DEFAULT_CATALOG
from radar_ai.offers import select_offers,best_offer
from radar_ai.policies import POLICY,budget_to_cents,is_fresh,validate_policy
from radar_ai.recommendation import evaluate_game,recommend,CANDIDATE_ENGINE
from radar_ai.rules import Rule,RuleEngine,Layer,Effect,ExceptionCase,RuleConfigurationError,reject

NOW=datetime(2026,10,19,12,tzinfo=timezone.utc)


def catalog():return copy.deepcopy(DEFAULT_CATALOG)
def state(**preferences):return validate_state({'preferences':preferences})
def game(catalogue,gid='g31'):return next(g for g in catalogue.games if g['id']==gid)


class RuleRegistryTests(unittest.TestCase):
    def rule(self,identifier,**kwargs):
        defaults=dict(version='1.0',layer=Layer.USER_CONSTRAINT,priority=10,condition=lambda c,d:True,action=lambda c,d:(Effect(identifier,1),))
        return Rule(identifier,**{**defaults,**kwargs})

    def test_duplicate_ids_are_rejected(self):
        with self.assertRaises(RuleConfigurationError):RuleEngine([self.rule('A'),self.rule('A')])

    def test_missing_dependency_is_rejected(self):
        with self.assertRaises(RuleConfigurationError):RuleEngine([self.rule('A',depends_on=('missing',))])

    def test_dependency_cycle_is_rejected(self):
        with self.assertRaises(RuleConfigurationError):RuleEngine([self.rule('A',depends_on=('B',)),self.rule('B',depends_on=('A',))])

    def test_dependency_cannot_invert_hierarchy(self):
        with self.assertRaises(RuleConfigurationError):RuleEngine([self.rule('A',layer=Layer.SECURITY,depends_on=('B',)),self.rule('B')])

    def test_hierarchy_and_priority_are_stable(self):
        rules=[self.rule('R',layer=Layer.RANKING),self.rule('B',layer=Layer.BUSINESS),self.rule('S',layer=Layer.SECURITY),self.rule('U2',priority=20),self.rule('U1',priority=10),self.rule('C',layer=Layer.COMPATIBILITY),self.rule('P',layer=Layer.PREFERENCE)]
        self.assertEqual([r['rule_id'] for r in RuleEngine(rules).evaluate({}).trace],['S','B','U1','U2','C','P','R'])

    def test_dependency_is_run_before_dependent_rule(self):
        rules=[self.rule('A',priority=1,depends_on=('B',)),self.rule('B',priority=50)]
        self.assertEqual([r['rule_id'] for r in RuleEngine(rules).evaluate({}).trace],['B','A'])

    def test_explicit_exemption_is_traced(self):
        r=self.rule('A',exceptions=(ExceptionCase('no_budget',lambda c,d:True),))
        result=RuleEngine([r]).evaluate({});self.assertEqual(result.trace[0]['status'],'exempt');self.assertEqual(result.trace[0]['reason'],'no_budget');self.assertEqual(result.facts,{})

    def test_critical_rule_cannot_have_exemptions(self):
        for layer in (Layer.SECURITY,Layer.BUSINESS,Layer.COMPATIBILITY):
            with self.subTest(layer=layer),self.assertRaises(RuleConfigurationError):RuleEngine([self.rule('A',layer=layer,exceptions=(ExceptionCase('skip',lambda c,d:True),))])

    def test_conflicting_assignments_fail_closed_atomically(self):
        rules=[self.rule('A',action=lambda c,d:(Effect('value',1),)),self.rule('B',priority=20,action=lambda c,d:(Effect('other',2),Effect('value',2)))]
        result=RuleEngine(rules).evaluate({});self.assertFalse(result.eligible);self.assertEqual(result.facts,{'value':1});self.assertEqual(result.trace[-1]['status'],'conflict')

    def test_mutually_exclusive_active_rules_conflict(self):
        result=RuleEngine([self.rule('A',conflicts_with=('B',)),self.rule('B')]).evaluate({})
        self.assertFalse(result.eligible);self.assertEqual(result.rejections[0]['reason'],'rule_conflict')

    def test_execution_errors_block_ranking(self):
        def boom(c,d):raise RuntimeError('secret must not be returned')
        result=RuleEngine([self.rule('A',condition=boom),self.rule('R',layer=Layer.RANKING)]).evaluate({})
        self.assertFalse(result.eligible);self.assertEqual(result.trace[-1]['status'],'blocked');self.assertNotIn('secret',json.dumps(result.trace))

    def test_rejected_dependency_blocks_downstream(self):
        result=RuleEngine([self.rule('A',action=reject('forbidden')),self.rule('B',depends_on=('A',))]).evaluate({})
        self.assertEqual(result.trace[-1]['status'],'blocked')


class OfferPolicyTests(unittest.TestCase):
    def test_selected_price_uses_exact_edition(self):
        c=catalog();g=game(c);g['editions'].append({**g['editions'][0],'id':'other-edition','type':'expansion'})
        c.offers.append({**c.offers[0],'id':'cheaper-expansion','edition_id':'other-edition','price_cents':1})
        offer=best_offer(g,catalog=c,now=NOW)
        self.assertNotEqual(offer['price_cents'],1);self.assertEqual(offer['edition_id'],g['editions'][0]['id'])

    def test_edition_of_another_game_is_never_selected(self):
        c=catalog();self.assertEqual(select_offers(game(c),'g1-pt-base',catalog=c,now=NOW),[])

    def test_invalid_prices_currencies_demo_and_availability_are_excluded(self):
        for field,value in [('price_cents',0),('price_cents',-1),('price_cents',1.5),('price_cents',True),('price_cents',2**53),('currency','USD'),('is_demo',False),('availability','out_of_stock'),('checked_at','invalid'),('checked_at','2030-01-01T00:00:00Z')]:
            with self.subTest(field=field,value=value):
                c=catalog();g=game(c,'g1');c.offers=[{**c.offers[0],field:value}]
                self.assertIsNone(best_offer(g,catalog=c,now=NOW))

    def test_store_must_be_demonstrative(self):
        c=catalog();c.stores[0]['is_demo']=False;c.offers=[c.offers[0]]
        self.assertIsNone(best_offer(game(c,'g1'),catalog=c,now=NOW))

    def test_duplicate_offer_id_blocks_commercial_result(self):
        c=catalog();c.offers.append(copy.deepcopy(c.offers[0]));self.assertIsNone(best_offer(game(c),catalog=c,now=NOW));self.assertEqual(recommend(state(),catalog=c,now=NOW),[])

    def test_orphan_references_fail_closed(self):
        for field in ('edition_id','store_id'):
            with self.subTest(field=field):
                c=catalog();c.offers[0][field]='missing';self.assertEqual(recommend(state(),catalog=c,now=NOW),[])

    def test_corrupt_metadata_blocks_candidate_with_trace(self):
        c=catalog();g=game(c);g['complexity']=float('nan')
        card,decision=evaluate_game(g,state(),catalog=c,now=NOW);self.assertIsNone(card);self.assertFalse(decision.eligible);self.assertEqual(decision.trace[0]['rule_id'],'SEC-CATALOG-001')

    def test_freshness_boundaries(self):
        self.assertTrue(is_fresh((NOW-timedelta(days=7)).isoformat(),NOW));self.assertFalse(is_fresh((NOW-timedelta(days=7,seconds=1)).isoformat(),NOW));self.assertFalse(is_fresh((NOW+timedelta(seconds=1)).isoformat(),NOW));self.assertFalse(is_fresh('2026-10-19T12:00:00',NOW))

    def test_budget_conversion_never_rounds_up(self):
        self.assertEqual(budget_to_cents(.29),29);self.assertEqual(budget_to_cents(1000.50),100050);self.assertEqual(budget_to_cents(100.009),10000)
        for value in (0,-1,float('nan'),float('inf'),True):
            with self.subTest(value=value),self.assertRaises(ValueError):budget_to_cents(value)


class RecommendationRulesTests(unittest.TestCase):
    def test_shared_invariant_fixtures(self):
        fixtures=json.loads((Path(__file__).resolve().parents[1]/'tests/fixtures/recommendation-invariants.json').read_text(encoding='utf-8'))
        for case in fixtures['cases']:
            with self.subTest(case=case['id']):
                ids={r['id'] for r in rank(state(**case['preferences']),now=NOW)}
                self.assertTrue(set(case.get('include',[])).issubset(ids));self.assertTrue(ids.isdisjoint(case.get('exclude',[])))
                if case.get('empty'):self.assertEqual(ids,set())

    def test_named_game_respects_player_constraint(self):
        reply=respond('Recomende Gloomhaven para 8 pessoas');self.assertEqual(reply['recommendations'],[]);self.assertIn('players_incompatible',[r['reason'] for r in reply['evaluation'][0]['rejections']])

    def test_named_game_respects_budget(self):
        reply=respond('Recomende Gloomhaven até R$ 1');self.assertEqual(reply['ids'],[]);self.assertIn('budget_or_offer_unavailable',[r['reason'] for r in reply['evaluation'][0]['rejections']])

    def test_named_game_respects_duration(self):
        self.assertEqual(respond('Me indica Gloomhaven para 2 pessoas em 30 minutos')['ids'],[])

    def test_named_game_respects_explicit_exclusion(self):
        self.assertEqual(respond('Recomende Gloomhaven, não quero cooperativo')['ids'],[])

    def test_named_recommendation_cannot_erase_previous_constraints(self):
        previous=state(players=8,budget=1)
        self.assertEqual(respond('Recomende Gloomhaven',previous)['ids'],[])

    def test_informational_card_is_not_recommendation_or_offer(self):
        reply=respond('Fale sobre Gloomhaven para 8 pessoas até R$ 1')
        self.assertEqual(reply['recommendations'],[]);self.assertEqual(reply['ids'],[])
        detail=reply['game_details'][0];self.assertEqual(detail['id'],'g31');self.assertFalse(detail['eligible_for_preferences']);self.assertNotIn('price_cents',detail)

    def test_eligible_named_game_has_trace(self):
        reply=respond('Recomende Gloomhaven para 4 pessoas')
        self.assertEqual(reply['ids'],['g31']);self.assertTrue(reply['recommendations'][0]['eligible']);self.assertEqual(reply['recommendations'][0]['rule_trace'][-1]['status'],'applied')

    def test_all_ranked_results_have_rule_and_offer_trails(self):
        for card in rank(state(players=4,budget=1000),now=NOW):
            self.assertTrue(card['rule_trace']);self.assertTrue(card['offer_rule_trace']);self.assertLessEqual(card['price_cents'],100000);self.assertIn(card['policy_version'],[POLICY['version']])

    def test_invalid_candidate_never_receives_score(self):
        c=catalog();card,decision=evaluate_game(game(c),state(players=8),catalog=c,now=NOW)
        self.assertIsNone(card);self.assertNotIn('ranking',decision.facts);self.assertEqual(decision.trace[-1]['status'],'blocked')

    def test_absent_offer_is_discoverable_but_never_zero(self):
        all_cards={r['id']:r for r in rank(state(),now=NOW)};self.assertIsNone(all_cards['g59']['price_cents'])
        self.assertNotIn('g59',[r['id'] for r in rank(state(budget=100000),now=NOW)])

    def test_python_ranking_profile_is_preserved(self):
        s=state();s['interests']=['combate'];cards=rank(s,now=NOW)
        self.assertEqual([(r['id'],r['score']) for r in cards[:3]],[('g32',52),('g31',49),('g48',48)])

    def test_weights_are_configurable_without_bypassing_filters(self):
        c=catalog();policy=copy.deepcopy(POLICY);policy['ranking']['weights']={'themes':0,'style':0,'videogame':0,'complexity':100,'editorial':0}
        cards=recommend(state(players=4),catalog=c,now=NOW,policy=policy)
        self.assertTrue(cards);self.assertEqual(cards[0]['score_breakdown']['components']['editorial'],0);self.assertNotIn('g23',[r['id'] for r in cards])

    def test_unsafe_policy_is_rejected(self):
        for field,value in [('demo_mode',False),('money_unit','float_reais'),('compare_editions','any')]:
            with self.subTest(field=field),self.assertRaises(ValueError):validate_policy({**POLICY,field:value})

    def test_rules_are_versioned_and_described(self):
        rules=CANDIDATE_ENGINE.describe();self.assertEqual(len(rules),len({r['id'] for r in rules}));self.assertTrue(all(r['version'] for r in rules))


if __name__=='__main__':unittest.main(verbosity=2)
