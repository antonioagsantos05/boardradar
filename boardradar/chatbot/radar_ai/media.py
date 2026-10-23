"""Allowlisted editorial entertainment links, independent of gameplay facts."""
import re
from .catalog import DEFAULT_CATALOG, load, number
from .nlp.normalizer import name_key
from .nlp.entities import negated

WORKS = load('media-works')
RELATIONS = load('media-game-relations')


def integrity_errors(works=None, relations=None, catalog=None):
    works = WORKS if works is None else works
    relations = RELATIONS if relations is None else relations
    catalog = catalog or DEFAULT_CATALOG
    errors = []
    ids = [w.get('id') for w in works if isinstance(w, dict)]
    if len(ids) != len(works) or any(not isinstance(i,str) or not i for i in ids) or len(set(ids)) != len(ids):
        return ['media:invalid_ids']
    for w in works:
        p = w.get('provenance', {})
        if (w.get('type') not in ('film','series','videogame') or not isinstance(w.get('title'),str) or not w['title']
            or not isinstance(w.get('aliases'),list) or any(not isinstance(a,str) for a in w['aliases'])
            or not isinstance(p,dict) or p.get('review_status') != 'editorial_draft' or not p.get('source') or p.get('license') != 'project-owned'):
            errors.append('media:invalid_metadata')
    games = {g['id'] for g in catalog.games}; seen = set()
    for r in relations:
        if not isinstance(r,dict):errors.append('media:invalid_relation');continue
        pair = (r.get('media_id'),r.get('game_id'))
        if (pair[0] not in ids or pair[1] not in games or pair in seen
            or not number(r.get('weight')) or not 0 <= r['weight'] <= 1
            or r.get('review_status') != 'editorial_draft'
            or r.get('connection_type') not in ('thematic','mechanical','thematic_and_mechanical')
            or not isinstance(r.get('rationale'),str) or not r['rationale']):errors.append('media:invalid_relation')
        seen.add(pair)
    return sorted(set(errors))


def match_media(text):
    """Explicit film/series labels disambiguate the existing videogame vocabulary."""
    key = name_key(text)
    kind = 'series' if re.search(r'\bserie\b',key) else 'film' if re.search(r'\bfilme\b',key) else None
    found = []
    for w in WORKS:
        if w['type'] == 'videogame' or kind and w['type'] != kind:continue
        for alias in [w['title'],*w['aliases']]:
            match = re.search(r'(?<!\w)'+re.escape(name_key(alias))+r'(?!\w)',key)
            if match and not negated(key,match.start()):
                found.append(w);break
    return found


def linked_candidates(ids, *, works=None, relations=None, catalog=None):
    if integrity_errors(works,relations,catalog):return [], []
    works = WORKS if works is None else works
    relations = RELATIONS if relations is None else relations
    selected = [w for w in works if w['id'] in ids]
    links = [{**r,'title':next(w['title'] for w in selected if w['id']==r['media_id']),
              'provenance':next(w['provenance'] for w in selected if w['id']==r['media_id'])}
             for r in relations if r['media_id'] in {w['id'] for w in selected}]
    return list(dict.fromkeys(r['game_id'] for r in sorted(links,key=lambda r:-r['weight']))), links
