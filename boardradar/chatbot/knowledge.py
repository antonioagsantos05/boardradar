"""Compatibility facade for the former standalone lexical prototype."""
from radar_ai.knowledge.index import load_index


def retrieve(query,game_id=None,edition_id=None,limit=4,official_only=False):
    return load_index().search(query,game_id,edition_id,limit,official_only)


def citation(hit):
    # Resolve again: a caller-supplied excerpt cannot become a source citation.
    resolved=load_index().resolve(hit['id'])
    if resolved is None:raise ValueError('Trecho desconhecido.')
    return resolved
