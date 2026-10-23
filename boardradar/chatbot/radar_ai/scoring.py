"""Preserve the existing Python profile; all coefficients come from policy.json."""


def score_candidate(context):
    game=context['game'];state=context['state'];policy=context['policy']['ranking']
    weights=policy['weights'];profile=policy['python'];tags=set(game['tags'])
    values={
        'themes':weights['themes']*min(1,len(context['overlap'])/3),
        'style':weights['style'] if state['interests'] else 0,
        'videogame':weights['videogame']*max((r['weight'] for r in context['relations']),default=0),
        'complexity':weights['complexity']*(1-(game['complexity']-1)/4),
        'editorial':weights['editorial']*game['editorialQuality'],
        'combat':0,
    }
    if 'combate' in state['interests']:
        values['combat']=profile['combat_tactical'] if 'tático' in tags else profile['combat_war'] if 'guerra' in tags else profile['combat_cooperative'] if 'cooperativo' in tags else 0
        if 'coleção' in tags:values['combat']-=profile['combat_collection_penalty']
    from .journey import PROFILE,bonus
    if PROFILE.get():values['saved_preferences']=bonus(game,PROFILE.get(),state)
    return {'score':round(sum(values.values())),'components':values,'version':policy['version'],'profile':'python'}


def explain(context):
    game=context['game'];state=context['state'];tags=set(game['tags'])
    if context['relations']:reason=context['relations'][0]['rationale']
    elif 'combate' in state['interests']:
        reason='Combate '+('cooperativo' if 'cooperativo' in tags else 'entre jogadores')+', com decisões e confronto na mesa; não reproduz combos de jogos de luta.'
    else:reason='Combina '+', '.join(state['interests'] or sorted(context['overlap'])[:3] or [game['category'].lower()])+'.'
    reason+=f" {game['players']['min']}–{game['players']['max']} jogadores, cerca de {game['duration']} min; metadados preliminares."
    from .journey import PROFILE,bonus
    if PROFILE.get() and bonus(game,PROFILE.get(),state):reason+=' Preferências salvas ajudam apenas na ordenação; seus filtros atuais prevalecem.'
    return reason
