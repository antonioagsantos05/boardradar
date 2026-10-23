"""Compatibility facade: deterministic NLP, state, policy and recommendations."""
from radar_ai.catalog import DEFAULT_CATALOG, DATA, load
from radar_ai.offers import best_offer
from radar_ai.recommendation import recommend as recommend_candidates, evaluate_game
from radar_ai.nlp.normalizer import normalize, contains, UNITS as WORDS
from radar_ai.nlp.entities import negative
from radar_ai.nlp.synonyms import INTERESTS
from radar_ai.state import validate_state
from radar_ai.conversation import handle_message, response

GAMES = DEFAULT_CATALOG.games
VIDEOS = DEFAULT_CATALOG.videos
RELATIONS = DEFAULT_CATALOG.relations
OFFERS = DEFAULT_CATALOG.offers


def best_price(game, edition_id=None, *, now=None):
    offer = best_offer(game, edition_id=edition_id, now=now)
    return offer['price_cents'] if offer else None


def rank(state, cheaper=False, *, catalog=None, now=None, policy=None):
    state = validate_state(state)
    return recommend_candidates(state, cheaper, catalog=catalog, now=now, policy=policy)


def respond(message, raw_state=None):
    return handle_message(message, validate_state(raw_state))
