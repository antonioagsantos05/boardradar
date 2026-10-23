"""Typed deterministic interpretation; approximate identity always needs confirmation."""
import copy
import re
from .models import Interpretation,Entities
from .normalizer import normalize,name_key,contains
from .intents import classify
from .entities import extract,negated
from .names import choices,match_names


def _pending_choice(text,pending,catalog):
    records=choices(catalog)
    offered=[r for candidate in pending['candidates'] for r in records if r['id']==candidate['id'] and r['entity_type']==candidate['entity_type']]
    if len(offered)==1 and text in ('sim','isso','correto','confirmo'):return offered[0]
    if re.fullmatch(r'[1-5]',text) and 0<int(text)<=len(offered):return offered[int(text)-1]
    for record in offered:
        if any(name_key(text)==name_key(alias) for alias in record['aliases']):return record
    return None


def interpret(message,state,catalog):
    if not isinstance(message,str) or not 0<len(message.strip())<=1000:raise ValueError('A mensagem deve ter entre 1 e 1000 caracteres.')
    text=normalize(message);intent=classify(text)
    result=Interpretation(intent=intent)
    if intent in ('reset','greeting','thanks','commercial'):
        result.confidence=.95;return result
    pending=state.get('pending_clarification')
    if pending:
        chosen=_pending_choice(text,pending,catalog)
        if chosen:
            result.intent=pending['intent'];result.confidence=.95
            result.entities.game_ids=list(pending.get('game_ids',[]))
            result.entities.videogame_ids=list(pending.get('videogame_ids',[]))
            slot='game_ids' if chosen['entity_type']=='game' else 'videogame_ids'
            setattr(result.entities,slot,list(dict.fromkeys([*getattr(result.entities,slot),chosen['id']])))
            if result.intent in ('rule','edition'):result.missing_information.append('edition_id')
            return result
        if text in ('nao','nenhum','cancelar'):
            result.intent='clarification';result.entities.remove=['pending_clarification'];result.missing_information=['game_or_videogame'];result.confidence=.6
            return result
    entities,errors=extract(text,state,intent)
    result.entities=entities;result.errors=errors
    exact,fuzzy=match_names(text,catalog)
    key=name_key(text)
    for record in exact:
        # Names use the punctuation-normalized representation for negation offsets.
        if record['entity_type']=='game' and negated(key,record['start']):entities.excluded_game_ids.append(record['id'])
        elif record['entity_type']=='game':entities.game_ids.append(record['id'])
        elif not negated(key,record['start']):entities.videogame_ids.append(record['id'])
    for game in catalog.games:
        for edition in game['editions']:
            if contains(text,edition['id']):
                entities.edition_ids.append(edition['id'])
                if game['id'] not in entities.game_ids:entities.game_ids.append(game['id'])
    if fuzzy:
        ambiguous_games={c['id'] for c in fuzzy if c['entity_type']=='game'}
        ambiguous_videos={c['id'] for c in fuzzy if c['entity_type']=='videogame'}
        entities.game_ids=[i for i in entities.game_ids if i not in ambiguous_games]
        entities.videogame_ids=[i for i in entities.videogame_ids if i not in ambiguous_videos]
        result.ambiguities=[{'kind':'name','candidates':fuzzy}]
        result.missing_information=['confirmed_name'];result.confidence=.45
    elif pending and not exact:
        records=choices(catalog)
        offered=[{k:r[k] for k in ('entity_type','id','title')} for c in pending['candidates'] for r in records if r['id']==c['id'] and r['entity_type']==c['entity_type']]
        result.ambiguities=[{'kind':'name','candidates':offered}];result.missing_information=['confirmed_name'];result.confidence=.45
    if errors:
        result.missing_information=list(dict.fromkeys([*result.missing_information,*[e['field'] for e in errors]]));result.confidence=.35
    result.cheaper=bool(re.search(r'\b(?:barat[oa]\w*|menor preco|economico)\b',text))
    result.more=bool(re.search(r'outr[oa]s? (?:opco|jog|sugest)|mais (?:opco|jog|sugest)|nao gostei',text))
    recognized=any(value not in (None,[]) for value in vars(entities).values()) or result.cheaper or result.more
    if result.intent=='unknown' and recognized:result.intent='refinement'
    if result.intent in ('rule','edition','offer','information','explanation') and not entities.game_ids and not state.get('last_ids') and not state.get('subject_ids'):
        result.missing_information.append('game_id')
    if result.intent=='comparison' and len(entities.game_ids)<2 and not result.ambiguities:
        result.missing_information.append('two_game_ids')
    if result.intent in ('rule','edition') and not entities.edition_ids:result.missing_information.append('edition_id')
    if len(entities.game_ids)>3:
        result.errors.append({'field':'game_ids','message':'Consulte até três jogos por vez para eu identificar cada um com segurança.'})
        result.missing_information.append('at_most_three_games');result.confidence=.35
    if not result.confidence:
        result.confidence=.95 if exact else .9 if any(v is not None for v in (entities.players,entities.max_price_cents,entities.duration_minutes)) else .8 if recognized else .6 if intent!='unknown' else 0.0
    return result


def apply_entities(state,result):
    updated=copy.deepcopy(state);e=result.entities;p=updated['preferences']
    preference_intent=result.intent not in ('information','explanation','comparison','rule','offer','edition')
    for field in e.remove:
        if field=='interests':updated['interests']=[]
        elif field=='pending_clarification':updated.pop(field,None)
        else:p.pop(field,None)
        if field=='budget':updated['budget_unlimited']=True
        if field=='mode':updated['excluded']=[t for t in updated['excluded'] if t!='cooperativo']
    if e.players is not None:p['players']=e.players
    if e.max_price_cents is not None:p['budget']=e.max_price_cents/100;updated['budget_unlimited']=False
    if e.duration_minutes is not None:p['duration']=e.duration_minutes
    if e.max_complexity is not None:p['complexity']=e.max_complexity
    if preference_intent and e.mode is not None and 'mode' not in e.remove:p['mode']=e.mode
    if e.videogame_ids:p['videogames']=list(dict.fromkeys(e.videogame_ids));updated['interests']=[]
    # Descriptive questions must not turn their vocabulary into taste preferences.
    thematic=[t for t in e.preferred_tags if t!='cooperativo'] if preference_intent else []
    if thematic:
        updated['interests']=thematic
        if not e.videogame_ids:p.pop('videogames',None)
    if preference_intent:
        updated['excluded']=[t for t in updated['excluded'] if t not in e.preferred_tags]
        updated['excluded']=list(dict.fromkeys([*updated['excluded'],*e.excluded_tags]))
        updated['interests']=[t for t in updated['interests'] if t not in e.excluded_tags]
    if p.get('mode')=='cooperative':updated['excluded']=[t for t in updated['excluded'] if t!='cooperativo']
    updated['excluded_games']=list(dict.fromkeys([*updated.get('excluded_games',[]),*e.excluded_game_ids]))
    if result.ambiguities:
        candidates=result.ambiguities[0]['candidates']
        updated['pending_clarification']={'kind':'name','candidates':[{k:c[k] for k in ('entity_type','id')} for c in candidates],'intent':result.intent if result.intent not in ('unknown','clarification') else 'recommendation','game_ids':e.game_ids,'videogame_ids':e.videogame_ids}
    elif 'pending_clarification' in updated:updated.pop('pending_clarification')
    return updated
