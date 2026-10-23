"""Candidate filtering precedes scoring. Named games use this same pipeline."""
from .catalog import DEFAULT_CATALOG
from .offers import best_offer
from .policies import POLICY,budget_to_cents,validate_policy,validate_constraints
from .rules import Effect,ExceptionCase,Layer,Rule,RuleEngine,reject
from .scoring import score_candidate,explain

NO_BUDGET=ExceptionCase('no_budget_limit',lambda c,d:c['state']['preferences'].get('budget') is None)
NO_PLAYERS=ExceptionCase('no_player_constraint',lambda c,d:c['state']['preferences'].get('players') is None)
NO_DURATION=ExceptionCase('no_duration_constraint',lambda c,d:c['state']['preferences'].get('duration') is None)

CANDIDATE_ENGINE=RuleEngine([
    Rule('SEC-CATALOG-001','1.0',Layer.SECURITY,10,lambda c,d:bool(c['integrity_errors']),reject('catalog_integrity_failed'),description='Falha estrutural ou referencial impede recomendações comerciais.'),
    Rule('USR-PLAYERS-001','1.0',Layer.USER_CONSTRAINT,10,lambda c,d:not c['game']['players']['min']<=c['state']['preferences']['players']<=c['game']['players']['max'],reject('players_incompatible'),depends_on=('SEC-CATALOG-001',),exceptions=(NO_PLAYERS,),description='Quantidade explícita de jogadores é obrigatória.'),
    Rule('USR-DURATION-001','1.0',Layer.USER_CONSTRAINT,20,lambda c,d:c['game']['duration']>c['state']['preferences']['duration'],reject('duration_exceeded'),depends_on=('SEC-CATALOG-001',),exceptions=(NO_DURATION,),description='Não exceder o tempo máximo informado.'),
    Rule('USR-BUDGET-001','1.0',Layer.USER_CONSTRAINT,30,lambda c,d:c['offer'] is None or c['offer']['price_cents']>budget_to_cents(c['state']['preferences']['budget']),reject('budget_or_offer_unavailable'),depends_on=('SEC-CATALOG-001',),exceptions=(NO_BUDGET,),description='Preço ausente não é zero; teto monetário não é arredondado para cima.'),
    Rule('USR-COMPLEXITY-001','1.0',Layer.USER_CONSTRAINT,40,lambda c,d:bool(c['state']['preferences'].get('complexity')) and c['game']['complexity']>c['state']['preferences']['complexity'],reject('complexity_exceeded'),depends_on=('SEC-CATALOG-001',),description='Preservar limite de complexidade do perfil Python existente.'),
    Rule('USR-MODE-001','1.0',Layer.USER_CONSTRAINT,50,lambda c,d:(c['state']['preferences'].get('mode')=='cooperative' and 'cooperativo' not in c['game']['tags']) or (c['state']['preferences'].get('mode')=='competitive' and 'cooperativo' in c['game']['tags']),reject('mode_incompatible'),depends_on=('SEC-CATALOG-001',)),
    Rule('USR-EXCLUDED-001','1.0',Layer.USER_CONSTRAINT,60,lambda c,d:bool(set(c['game']['tags'])&set(c['state']['excluded'])),reject('excluded_tag'),depends_on=('SEC-CATALOG-001',)),
    Rule('USR-GAME-EXCLUDED-001','1.0',Layer.USER_CONSTRAINT,65,lambda c,d:c['game']['id'] in c['state'].get('excluded_games',[]),reject('excluded_game'),depends_on=('SEC-CATALOG-001',)),
    Rule('USR-INTEREST-001','1.0',Layer.USER_CONSTRAINT,70,lambda c,d:not all(t in c['game']['tags'] for t in c['state']['interests']),reject('required_interest_missing'),depends_on=('SEC-CATALOG-001',),description='Preservar estilos explícitos exigidos pelo perfil atual.'),
    Rule('CMP-EDITION-001','1.0',Layer.COMPATIBILITY,10,lambda c,d:c['offer'] is not None and c['offer']['edition_id']!=c['game']['editions'][0]['id'],reject('edition_mismatch'),depends_on=('SEC-CATALOG-001',),description='Preço exibido na recomendação pertence à edição escolhida, nunca mistura expansões.'),
    Rule('PREF-AFFINITY-001','1.0',Layer.PREFERENCE,10,lambda c,d:bool(c['selected_videos']) and not c['relations'] and not c['overlap'],reject('no_editorial_affinity'),depends_on=('SEC-CATALOG-001',),description='Preservar seleção editorial de candidatos do recomendador Python legado.'),
    Rule('RANK-SCORE-001','1.0',Layer.RANKING,10,lambda c,d:True,lambda c,d:(Effect('ranking',score_candidate(c)),),depends_on=('SEC-CATALOG-001',),description='Pontuar somente candidatos aprovados pelas regras anteriores.'),
])


def evaluate_game(game,state,*,catalog=None,now=None,policy=None,integrity_errors=None,edition_id=None):
    validate_constraints(state)
    catalog=catalog or DEFAULT_CATALOG;policy=validate_policy(policy or POLICY)
    errors=catalog.integrity_errors() if integrity_errors is None else integrity_errors
    canonical=next((g for g in catalog.games if isinstance(g,dict) and g.get('id')==game.get('id')),None)
    if canonical is None:errors=[*errors,'unknown_game']
    game=canonical or game
    if edition_id is not None and not any(e['id']==edition_id for e in game.get('editions',[])):
        errors=[*errors,'unknown_edition']
    # A local immutable view selects the requested product without changing the catalogue.
    if edition_id is not None and not errors:
        game={**game,'editions':sorted(game['editions'],key=lambda e:e['id']!=edition_id)}
    selected=[v for v in catalog.videos if v['id'] in state['preferences'].get('videogames',[])] if not errors else []
    themes={t for v in selected for t in v['tags']}
    relations=[r for r in catalog.relations if r['game_id']==game.get('id') and r['videogame_id'] in state['preferences'].get('videogames',[])] if not errors else []
    context={'game':game,'state':state,'policy':policy,'integrity_errors':errors,'offer':None,'selected_videos':selected,'overlap':set(game.get('tags',[]))&themes if not errors else set(),'relations':relations}
    if not errors:context['offer']=best_offer(game,edition_id=edition_id,catalog=catalog,now=now,integrity_errors=errors,policy=policy)
    decision=CANDIDATE_ENGINE.evaluate(context)
    if not decision.eligible:return None,decision
    offer=context['offer'];scoring=decision.facts['ranking']
    return {'id':game['id'],'name':game['name'],'reason':explain(context),'price_cents':offer['price_cents'] if offer else None,'score':scoring['score'],'score_breakdown':scoring,'policy_version':policy['version'],'edition_id':game['editions'][0]['id'],'offer_id':offer['id'] if offer else None,'is_demo':True,'eligible':True,'rule_trace':decision.trace,'offer_rule_trace':offer['rule_trace'] if offer else []},decision


def recommend(state,cheaper=False,*,catalog=None,now=None,policy=None,candidate_ids=None):
    validate_constraints(state)
    catalog=catalog or DEFAULT_CATALOG
    errors=catalog.integrity_errors()
    if errors:return []
    output=[]
    for game in catalog.games:
        if candidate_ids is not None and game.get('id') not in candidate_ids:continue
        card,_=evaluate_game(game,state,catalog=catalog,now=now,policy=policy,integrity_errors=errors)
        if card is not None and (not cheaper or card['price_cents'] is not None):output.append(card)
    return sorted(output,key=(lambda g:(g['price_cents'],-g['score'],g['name'])) if cheaper else (lambda g:(-g['score'],g['name'])))
