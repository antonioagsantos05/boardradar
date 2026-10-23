import json
import os
import sys
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine import GAMES, respond, validate_state


class ConversationTests(unittest.TestCase):
    def game(self, game_id):
        return next(g for g in GAMES if g["id"] == game_id)

    def test_fighting_never_returns_generic_civilization_games(self):
        reply = respond("Gosto de jogos de luta")
        self.assertTrue(reply["ids"])
        self.assertTrue(all("combate" in self.game(i)["tags"] for i in reply["ids"]))
        self.assertNotIn("g7", reply["ids"])
        self.assertNotIn("g60", reply["ids"])
        self.assertEqual(reply["state"]["waiting_for"], "players")
        self.assertIn("combos", reply["text"])

    def test_short_answer_refines_context(self):
        first = respond("Gosto de jogos de luta")
        second = respond("2", first["state"])
        self.assertEqual(second["preferences"]["players"], 2)
        self.assertEqual(second["state"]["interests"], ["combate"])
        for i in second["ids"]:
            self.assertLessEqual(self.game(i)["players"]["min"], 2)
            self.assertGreaterEqual(self.game(i)["players"]["max"], 2)

    def test_mass_effect_context_survives_followup(self):
        first = respond("Gosto de Mass Effect")
        second = respond("para quatro pessoas", first["state"])
        self.assertEqual(second["preferences"]["videogames"], ["v11"])
        self.assertEqual(second["preferences"]["players"], 4)
        self.assertTrue(second["ids"])

    def test_cooperative_refines_combat(self):
        first = respond("Gosto de jogos de luta")
        reply = respond("combate cooperativo para 4 pessoas", first["state"])
        self.assertTrue(reply["ids"])
        self.assertTrue(all({"combate", "cooperativo"}.issubset(self.game(i)["tags"]) for i in reply["ids"]))

    def test_negation_excludes_cooperative_games(self):
        first = respond("Combate cooperativo")
        reply = respond("Não quero cooperativo, duelos para 2 pessoas", first["state"])
        self.assertTrue(reply["ids"])
        self.assertTrue(all("cooperativo" not in self.game(i)["tags"] for i in reply["ids"]))

    def test_unknown_does_not_generate_random_recommendations(self):
        self.assertEqual(respond("gosto de jogos de corrida")["ids"], [])
        self.assertEqual(respond("gosto de flibberty")["ids"], [])
        self.assertEqual(respond("oi")["ids"], [])

    def test_no_results_does_not_relax_constraints(self):
        reply = respond("luta para 4 pessoas até R$ 1")
        self.assertEqual(reply["ids"], [])
        self.assertIn("Não encontrei", reply["text"])
        self.assertEqual(reply["preferences"]["budget"], 1)

    def test_duration_is_not_a_budget(self):
        reply = respond("Até 1 hora", respond("Combate")["state"])
        self.assertEqual(reply["preferences"]["duration"], 60)
        self.assertNotIn("budget", reply["preferences"])

    def test_brazilian_money_and_bare_budget(self):
        reply = respond("para duas pessoas até R$ 1.000,50")
        self.assertEqual(reply["preferences"]["budget"], 1000.50)
        first = respond("Combate para duas pessoas")
        second = respond("600", first["state"])
        self.assertEqual(second["preferences"]["budget"], 600)

    def test_more_returns_different_games(self):
        first = respond("Gosto de jogos de luta")
        second = respond("Outras opções", first["state"])
        self.assertTrue(second["ids"])
        self.assertTrue(set(first["ids"]).isdisjoint(second["ids"]))

    def test_explain_reuses_previous_suggestion(self):
        first = respond("Gosto de XCOM 2")
        second = respond("Por que esse?", first["state"])
        self.assertEqual(len(second["ids"]), 1)
        self.assertEqual(second["ids"][0], first["ids"][0])

    def test_reset_and_commercial_guard(self):
        first = respond("luta para 2 pessoas")
        self.assertEqual(respond("recomeçar", first["state"])["state"]["preferences"], {})
        self.assertEqual(respond("quero comprar", first["state"])["ids"], [])

    def test_bad_state_and_input(self):
        for value in ("", "a" * 1001, 42, None):
            with self.assertRaises(ValueError):
                respond(value)
        for state in ({"preferences": {"players": True}}, {"last_ids": ["fake"]}, {"preferences": {"budget": float("nan")}}, {"interests": ["bogus"]}):
            with self.assertRaises(ValueError):
                validate_state(state)

    def test_invalid_number_is_clarified(self):
        self.assertEqual(respond("Para 200 pessoas")["ids"], [])
        self.assertEqual(respond("Até R$ 0")["ids"], [])

    def test_context_is_not_mutated(self):
        state = respond("Combate")["state"]
        before = json.dumps(state, sort_keys=True)
        respond("4 pessoas", state)
        self.assertEqual(json.dumps(state, sort_keys=True), before)

    def test_declining_budget_does_not_ask_again(self):
        first = respond("Combate para duas pessoas")
        second = respond("não", first["state"])
        self.assertTrue(second["state"]["budget_unlimited"])
        self.assertIsNone(second["state"]["waiting_for"])
        self.assertTrue(second["ids"])

    def test_yes_prompts_for_budget_and_decimal_money(self):
        first = respond("Combate para duas pessoas")
        self.assertEqual(respond("sim", first["state"])["ids"], [])
        self.assertEqual(respond("até R$ 300.50")["preferences"]["budget"], 300.5)


if __name__ == "__main__":
    unittest.main(verbosity=2)
