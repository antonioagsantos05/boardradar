"""Validated legacy conversation envelope with optional clarification slots."""
import math
import re
from .catalog import DEFAULT_CATALOG
from .nlp.synonyms import INTERESTS
from .session import validate_session

INTENTS={'recommendation','refinement','information','comparison','rule','edition','offer','explanation'}


def empty_state():
    return {'preferences':{},'interests':[],'excluded':[],'excluded_games':[],'last_ids':[],'waiting_for':None,'budget_unlimited':False}


def validate_state(state):
    if state is None:return empty_state()
    if not isinstance(state,dict):raise ValueError('Contexto inválido.')
    out=empty_state();p=state.get('preferences',{})
    if not isinstance(p,dict):raise ValueError('Preferências inválidas.')
    if type(state.get('budget_unlimited',False))!=bool:raise ValueError('Orçamento inválido.')
    out['budget_unlimited']=state.get('budget_unlimited',False)
    for key,limit in (('players',20),('budget',100000),('duration',10000),('complexity',5)):
        if key in p:
            value=p[key]
            if type(value) not in (int,float) or not math.isfinite(value) or not 0<value<=limit or (key=='players' and int(value)!=value):raise ValueError('Preferência inválida: '+key)
            out['preferences'][key]=value
    if 'mode' in p:
        if p['mode'] not in ('cooperative','competitive'):raise ValueError('Modo inválido.')
        out['preferences']['mode']=p['mode']
    games={g['id'] for g in DEFAULT_CATALOG.games};videos={v['id'] for v in DEFAULT_CATALOG.videos}
    def ids(value,allowed,maximum=60):
        if not isinstance(value,list) or len(value)>maximum or any(not isinstance(i,str) or i not in allowed for i in value):raise ValueError('Referências inválidas no contexto.')
        return list(dict.fromkeys(value))
    videogames=ids(p.get('videogames',[]),videos,13)
    if videogames:out['preferences']['videogames']=videogames
    from .media import WORKS
    media_ids=ids(state.get('media_ids',[]),{w['id'] for w in WORKS},21)
    if media_ids:out['media_ids']=media_ids
    for key in ('subject_ids','pending_comparison'):
        if key in state:out[key]=ids(state[key],games,3)
    editions={e['id'] for g in DEFAULT_CATALOG.games for e in g['editions']}
    if 'subject_edition_ids' in state:out['subject_edition_ids']=ids(state['subject_edition_ids'],editions,3)
    if 'session' in state:out['session']=validate_session(state['session'])
    if 'last_topic' in state:
        if not isinstance(state['last_topic'],str) or not re.fullmatch(r'[a-zA-Z0-9_.-]{1,100}',state['last_topic']):raise ValueError('Conceito inválido.')
        out['last_topic']=state['last_topic']
    if 'library_subject_ids' in state:
        from .library import records
        out['library_subject_ids']=ids(state['library_subject_ids'],games|set(records()),3)
    if 'pending_rule' in state:
        pending=state['pending_rule']
        if (not isinstance(pending,dict) or set(pending)!={'query','game_id'}
            or not isinstance(pending.get('query'),str) or not 0<len(pending['query'].strip())<=1000
            or pending.get('game_id') is not None and (not isinstance(pending['game_id'],str) or pending['game_id'] not in games)):
            raise ValueError('Pergunta documental pendente inválida.')
        out['pending_rule']=dict(pending)
    for key in ('interests','excluded','excluded_games','last_ids'):
        out[key]=ids(state.get(key,[]),games if key in ('excluded_games','last_ids') else set(INTERESTS),20 if key in ('interests','excluded') else 60)
    if state.get('waiting_for') not in (None,'players','budget','interest'):raise ValueError('Pergunta pendente inválida.')
    out['waiting_for']=state.get('waiting_for')
    pending=state.get('pending_clarification')
    if pending is not None:
        if not isinstance(pending,dict) or pending.get('kind')!='name' or pending.get('intent') not in INTENTS:raise ValueError('Esclarecimento inválido.')
        candidates=pending.get('candidates')
        if not isinstance(candidates,list) or not 1<=len(candidates)<=5:raise ValueError('Candidatos inválidos.')
        checked=[]
        for c in candidates:
            if not isinstance(c,dict) or c.get('entity_type') not in ('game','videogame'):raise ValueError('Tipo de entidade inválido.')
            ids([c.get('id')],games if c['entity_type']=='game' else videos)
            checked.append({'entity_type':c['entity_type'],'id':c['id']})
        out['pending_clarification']={'kind':'name','intent':pending['intent'],'candidates':checked,'game_ids':ids(pending.get('game_ids',[]),games,3),'videogame_ids':ids(pending.get('videogame_ids',[]),videos,13)}
    return out
