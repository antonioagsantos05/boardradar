import copy
import json
from pathlib import Path
import unittest
from engine import respond,validate_state,GAMES
from radar_ai.catalog import DEFAULT_CATALOG
from radar_ai.nlp import interpret

FIXTURES=json.loads((Path(__file__).resolve().parents[1]/'tests/fixtures/nlp-cases.json').read_text(encoding='utf-8'))


class InterpretationScenarios(unittest.TestCase):pass


def make_scenario(case):
    def scenario(self):
        result=interpret(case['message'],validate_state(None),DEFAULT_CATALOG)
        public=result.public()
        if 'intent' in case:self.assertEqual(result.intent,case['intent'])
        for key,expected in case.get('entities',{}).items():self.assertEqual(getattr(result.entities,key),expected,key)
        if case.get('error'):self.assertTrue(result.errors)
        else:self.assertEqual(result.errors,[])
        if 'clarification_ids' in case:
            self.assertTrue(result.ambiguities)
            ids={c['id'] for a in result.ambiguities for c in a['candidates']}
            self.assertTrue(set(case['clarification_ids']).issubset(ids),ids)
            self.assertEqual(respond(case['message'])['recommendations'],[])
        else:self.assertEqual(result.ambiguities,[])
        self.assertEqual(public['confidence_kind'],'heuristic_not_calibrated');self.assertTrue(0<=public['confidence']<=1)
    return scenario


for case in FIXTURES['cases']:
    setattr(InterpretationScenarios,'test_'+case['id'].replace('-','_'),make_scenario(case))


class ConversationNLPTests(unittest.TestCase):
    def test_known_audit_budget_gap_is_fixed(self):
        result=respond('Tenho 200 reais e quero algo para jogar com minha família.')
        self.assertEqual(result['preferences']['budget'],200)
        self.assertTrue(all(r['price_cents'] is not None and r['price_cents']<=20000 for r in result['recommendations']))

    def test_multi_turn_constraints_accumulate(self):
        a=respond('Quero um jogo para quatro pessoas.')
        b=respond('Até 250 reais.',a['state'])
        c=respond('Prefiro estratégia.',b['state'])
        self.assertEqual(c['preferences']['players'],4);self.assertEqual(c['preferences']['budget'],250);self.assertIn('estratégia',c['state']['interests'])
        for r in c['recommendations']:
            g=next(g for g in GAMES if g['id']==r['id']);self.assertTrue(g['players']['min']<=4<=g['players']['max']);self.assertLessEqual(r['price_cents'],25000)

    def test_fuzzy_confirmation_retains_numeric_constraints(self):
        first=respond('Recomende Termforming Mars para quatro pessoas até R$ 1000')
        self.assertEqual(first['ids'],[]);self.assertIn('pending_clarification',first['state'])
        second=respond('sim',first['state'])
        self.assertEqual(second['ids'],['g16']);self.assertEqual(second['preferences']['players'],4);self.assertEqual(second['preferences']['budget'],1000)

    def test_fuzzy_video_confirmation_and_short_followup(self):
        first=respond('Gosto de Civlization')
        second=respond('Civilization VI',first['state'])
        self.assertEqual(second['preferences']['videogames'],['v5']);self.assertTrue(second['ids'])
        third=respond('2',second['state']);self.assertEqual(third['preferences']['players'],2)

    def test_ambiguous_name_requires_choice(self):
        first=respond('Recomende 7 Wonders D')
        self.assertEqual(first['ids'],[])
        second=respond('7 Wonders Duel',first['state'])
        self.assertEqual(second['ids'],['g23'])

    def test_confirmation_cannot_override_budget(self):
        first=respond('Recomende Termforming Mars até R$ 1')
        second=respond('sim',first['state'])
        self.assertEqual(second['ids'],[]);self.assertEqual(second['preferences']['budget'],1)

    def test_correction_and_removal_preserve_other_fields(self):
        first=respond('Quero estratégia para quatro pessoas até R$ 300 em 1 hora')
        second=respond('Agora somos seis pessoas',first['state'])
        self.assertEqual(second['preferences']['players'],6);self.assertEqual(second['preferences']['budget'],300)
        third=respond('Remova o orçamento',second['state'])
        self.assertNotIn('budget',third['preferences']);self.assertEqual(third['preferences']['duration'],60);self.assertIn('estratégia',third['state']['interests'])

    def test_bad_numeric_input_keeps_existing_preferences(self):
        before=validate_state({'preferences':{'players':4,'budget':250}})
        reply=respond('Quero para 4,5 pessoas até R$ 0',before)
        self.assertEqual(reply['ids'],[]);self.assertEqual(reply['preferences'],before['preferences'])

    def test_named_exclusion_applies_to_later_recommendations(self):
        first=respond('Não quero Catan')
        second=respond('Para quatro pessoas',first['state'])
        self.assertNotIn('g1',second['ids']);self.assertIn('g1',second['state']['excluded_games'])

    def test_rule_question_has_no_fabricated_evidence(self):
        reply=respond('Posso fazer essa ação nesta edição de Root?')
        self.assertEqual(reply['intent'],'rule');self.assertEqual(reply['ids'],[]);self.assertEqual(reply['sources'],[]);self.assertEqual(reply['answer_confidence'],'unknown')

    def test_tampered_clarification_is_rejected(self):
        first=respond('Recomende Termforming Mars')
        state=copy.deepcopy(first['state']);state['pending_clarification']['candidates'][0]['id']='fake'
        with self.assertRaises(ValueError):respond('sim',state)

    def test_legacy_state_and_response_contract_remain_supported(self):
        legacy={'preferences':{'players':4},'interests':[],'excluded':[],'last_ids':[],'waiting_for':None,'budget_unlimited':False}
        reply=respond('Gosto de jogos de luta',legacy)
        self.assertTrue({'text','state','preferences','ids','recommendations','suggestions','is_demo','engine','interpretation'}.issubset(reply))

    def test_deterministic_parse_does_not_mutate_state(self):
        state=validate_state(None);before=copy.deepcopy(state)
        a=interpret('Tenho 200 reais para quatro pessoas.',state,DEFAULT_CATALOG)
        b=interpret('Tenho 200 reais para quatro pessoas.',state,DEFAULT_CATALOG)
        self.assertEqual(a.public(),b.public());self.assertEqual(state,before)

    def test_mixed_money_correction_uses_textual_order(self):
        parsed=interpret('Até 100, melhor 200 reais',validate_state(None),DEFAULT_CATALOG)
        self.assertEqual(parsed.entities.max_price_cents,20000)

    def test_returning_to_original_value_is_a_valid_correction(self):
        parsed=interpret('Para 4 pessoas, melhor 6 pessoas, na verdade 4 pessoas',validate_state(None),DEFAULT_CATALOG)
        self.assertEqual(parsed.entities.players,4)

    def test_negated_removal_does_not_remove_budget(self):
        state=validate_state({'preferences':{'budget':250,'players':4}})
        reply=respond('Não remova o orçamento',state)
        self.assertEqual(reply['preferences']['budget'],250)

    def test_rules_do_not_change_player_tastes(self):
        state=validate_state({'preferences':{'players':4},'interests':['família']})
        reply=respond('Qual regra de combate cooperativo uso em Root?',state)
        self.assertEqual(reply['preferences'],state['preferences']);self.assertEqual(reply['state']['interests'],['família'])

    def test_name_choice_can_be_cancelled(self):
        first=respond('Recomende Termforming Mars')
        reply=respond('não',first['state'])
        self.assertNotIn('pending_clarification',reply['state']);self.assertEqual(reply['ids'],[])

    def test_selection_by_index_preserves_budget_and_players(self):
        first=respond('Recomende Termforming Mars para quatro pessoas até R$ 1000')
        reply=respond('1',first['state'])
        self.assertEqual(reply['ids'],['g16']);self.assertEqual(reply['preferences']['players'],4)

    def test_no_arbitrary_execution_from_text(self):
        reply=respond('__import__("os").system("echo secret")')
        self.assertEqual(reply['ids'],[]);self.assertEqual(reply['interpretation']['entities']['game_ids'],[])

    def test_explicit_edition_id_maps_only_to_its_game(self):
        result=interpret('Qual regra uso na edição g45-pt-base?',validate_state(None),DEFAULT_CATALOG)
        self.assertEqual(result.entities.edition_ids,['g45-pt-base']);self.assertEqual(result.entities.game_ids,['g45']);self.assertNotIn('edition_id',result.missing_information)

    def test_rule_requires_edition_identity_without_guessing(self):
        result=interpret('Qual regra uso em Root?',validate_state(None),DEFAULT_CATALOG)
        self.assertIn('edition_id',result.missing_information);self.assertEqual(result.entities.edition_ids,[])

    def test_too_many_named_games_do_not_get_silently_truncated(self):
        reply=respond('Compare Catan com Azul com Root com Scythe')
        self.assertEqual(reply['ids'],[]);self.assertTrue(reply['interpretation']['errors'])

    def test_malformed_numeric_text_is_clarified_instead_of_crashing(self):
        for message in ('Para 1.2.3 pessoas','Até 1.2.3 horas','Até 1,2,3 minutos'):
            with self.subTest(message=message):
                reply=respond(message);self.assertEqual(reply['ids'],[]);self.assertTrue(reply['interpretation']['errors'])

    def test_conflicting_number_prompt_uses_human_labels(self):
        reply=respond('Até 100 ou 200 reais')
        self.assertIn('orçamento',reply['text']);self.assertNotIn('max_price_cents',reply['text'])


if __name__=='__main__':unittest.main(verbosity=2)
