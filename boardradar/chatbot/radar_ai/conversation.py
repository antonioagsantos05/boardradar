"""Response dispatch for the typed NLP result; specialist tools remain deterministic."""
import re
from .catalog import DEFAULT_CATALOG
from .nlp import interpret,apply_entities
from .nlp.normalizer import normalize
from .recommendation import evaluate_game,recommend
from .state import empty_state,validate_state
from .session import begin,expired
from .templates import render
from .tools import compare_games,editions_for,offers_for
from .media import match_media,linked_candidates
from .knowledge import answer_query,is_document_query
from .library import handle_query as handle_library
from .dialogue import followup


def response(text,state,recommendations=None,suggestions=None,**extra):
    recommendations=recommendations or []
    return {'text':text,'state':state,'preferences':state['preferences'],'ids':[r['id'] for r in recommendations],'recommendations':recommendations,'suggestions':suggestions or [],'is_demo':True,'engine':'python-catalog',**extra}


def handle_message(message,state):
    parsed=interpret(message,state,DEFAULT_CATALOG);text=normalize(message)
    if parsed.intent!='reset' and state.get('session') and expired(state['session']):
        fresh=empty_state();fresh['session']=begin()
        return response(render('expired'),fresh,suggestions=['4 pessoas','Até R$ 250'],context_status='expired')
    state.setdefault('session',begin())
    library_answer=handle_library(message,state,parsed)
    if library_answer is not None:return library_answer
    continuation=followup(message,state,parsed)
    if continuation is not None:
        answer=continuation.pop('text');current=continuation.pop('state');cards=continuation.pop('recommendations',[])
        return response(answer,current,cards,**continuation)
    if text in ('cancelar','cancela','cancelar comparacao'):
        state.pop('pending_comparison',None);state.pop('pending_clarification',None)
        state.pop('pending_rule',None)
        return response('Consulta cancelada. Suas preferências foram mantidas.',state,suggestions=['Quero recomendações','Recomeçar'])
    media=match_media(text)
    if parsed.entities.game_ids or state.get('pending_comparison'):
        if not re.search(r'\b(filme|serie)\b',text):media=[]
    if media and parsed.intent not in ('commercial','reset','rule','comparison','offer','edition'):
        # Film/series identity wins over an incidental game-name fuzzy candidate.
        parsed.ambiguities=[];parsed.missing_information=[]
        parsed.entities.game_ids=[];parsed.entities.videogame_ids=[]
        parsed.entities.media_ids=[w['id'] for w in media]
        parsed.entities.preferred_tags=[]
        parsed.intent='recommendation'
    def say(answer,current=None,cards=None,suggestions=None,**extra):
        current=state if current is None else current
        current.setdefault('session',begin())
        return response(answer,current,cards,suggestions,intent=parsed.intent,interpretation=parsed.public(),**extra)
    if parsed.intent=='reset':return say('Vamos começar de novo. Qual experiência você procura: luta, terror, exploração ou algo para a família?',empty_state(),suggestions=['Gosto de jogos de luta','Terror cooperativo','Exploração espacial'])
    if parsed.intent=='commercial':return say('As lojas e os preços desta demonstração são fictícios. Posso ajudar a consultar as fichas, mas não faço compras nem abro lojas reais.',suggestions=['Ver opções mais baratas','Quero recomendações'])
    if parsed.intent=='greeting':return say('Oi! Vamos encontrar uma boa partida. Que videogame ou tipo de jogo você curte?',suggestions=['Gosto de jogos de luta','Gosto de Mass Effect','Quero algo para a família'])
    if parsed.intent=='thanks':return say('Boa partida! Posso buscar outras opções ou ajustar o tempo e o orçamento.',suggestions=['Outras opções','Mais barato','Recomeçar'])
    if parsed.errors:
        field=parsed.errors[0]['field']
        if field=='players':state['waiting_for']='players'
        elif field in ('budget','max_price_cents'):state['waiting_for']='budget'
        suggestions=['2 pessoas','4 pessoas'] if field=='players' else ['Até R$ 300','Sem limite de orçamento'] if field in ('budget','max_price_cents') else ['Recomeçar']
        return say(parsed.errors[0]['message'],suggestions=suggestions)
    if state['waiting_for']=='budget' and text in ('sim','quero','claro') and not state.get('pending_clarification'):
        return say('Qual é o valor máximo por jogo em reais? Vou usar apenas as ofertas DEMO recentes.',suggestions=['Até R$ 300','Até R$ 600','Sem limite de orçamento'])
    pending_rule=state.get('pending_rule')
    continuing_rule=bool(pending_rule and (parsed.entities.edition_ids or parsed.entities.game_ids)
                         and parsed.intent in ('unknown','refinement','edition')
                         and (not pending_rule.get('game_id') or parsed.entities.game_ids==[pending_rule['game_id']]))
    document_query=is_document_query(text) and (not parsed.entities.game_ids or 'document' in text)
    if (parsed.intent=='rule' or continuing_rule or document_query) and not parsed.ambiguities:
        query=pending_rule['query'] if continuing_rule else message
        game_ids=parsed.entities.game_ids or ([pending_rule['game_id']] if continuing_rule and pending_rule.get('game_id') else state.get('subject_ids') or state['last_ids'][:1])
        game_id=game_ids[0] if len(game_ids)==1 else None
        editions=parsed.entities.edition_ids or ([] if parsed.entities.game_ids and game_id not in state.get('subject_ids',[]) else state.get('subject_edition_ids',[]))
        edition_id=editions[0] if len(editions)==1 and game_id and any(e['id']==editions[0] for g in DEFAULT_CATALOG.games if g['id']==game_id for e in g['editions']) else None
        is_rule=parsed.intent=='rule' or continuing_rule
        # A generic concept does not inherit the previous game's edition.
        if document_query and not is_rule and not parsed.entities.game_ids:game_id=None;edition_id=None
        evidence=answer_query(query,game_id=game_id,edition_id=edition_id,is_rule=is_rule)
        if not is_rule and evidence.get('sources'):state['last_topic']=evidence['sources'][0]['chunk_id']
        if document_query and not is_rule:parsed.intent='information';parsed.missing_information=[]
        if is_rule:
            parsed.intent='rule'
            if game_id:state['subject_ids']=[game_id]
            if edition_id:state['subject_edition_ids']=[edition_id]
            if evidence['knowledge_status'] in ('needs_game','needs_edition'):
                state['pending_rule']={'query':query,'game_id':game_id}
            else:state.pop('pending_rule',None)
        answer=evidence.pop('text');evidence.pop('recommendations',None)
        return say(answer,**evidence,suggestions=['O que é deck-building?','O que é cooperativo?','Recomeçar'])
    if parsed.intent not in ('unknown','clarification'):state.pop('pending_rule',None)
    previous=state
    state=validate_state(apply_entities(state,parsed))
    if parsed.entities.game_ids or parsed.entities.videogame_ids or media or (parsed.intent=='recommendation' and parsed.entities.preferred_tags):
        state.pop('last_topic',None)
    if media and not parsed.errors and parsed.intent=='recommendation':
        state['media_ids']=[w['id'] for w in media]
        state['interests']=[];state['preferences'].pop('videogames',None)
    elif parsed.entities.videogame_ids or parsed.entities.preferred_tags or 'interests' in parsed.entities.remove or 'videogames' in parsed.entities.remove:
        state.pop('media_ids',None)
    if parsed.ambiguities:
        options=parsed.ambiguities[0]['candidates'];labels=[o['title'] for o in options]
        return say('Não tenho certeza do nome. Você quis dizer '+(' ou '.join(labels))+'? Confirme uma opção antes de eu recomendar.',suggestions=labels)
    if parsed.intent=='clarification':return say('Tudo bem. Diga o nome do jogo ou videogame que você tinha em mente.',suggestions=['Recomeçar'])
    e=parsed.entities
    if previous.get('pending_comparison') and len(e.game_ids)==1 and parsed.intent in ('unknown','refinement'):
        parsed.intent='comparison'
        e.game_ids=list(dict.fromkeys([*previous['pending_comparison'],*e.game_ids]))[:3]
        parsed.missing_information=[i for i in parsed.missing_information if i!='two_game_ids']
    if parsed.intent=='comparison' and len(e.game_ids)<2:
        if e.game_ids:
            state['pending_comparison']=e.game_ids
            name=next(g['name'] for g in DEFAULT_CATALOG.games if g['id']==e.game_ids[0])
            return say(render('compare_missing',name=name),suggestions=['Scythe','Root','Catan'])
        if len(state.get('subject_ids',[]))>=2:
            e.game_ids=state['subject_ids'];parsed.missing_information=[]
    if parsed.intent=='rule':
        evidence=answer_query(message,game_id=e.game_ids[0] if len(e.game_ids)==1 else None,
                              edition_id=e.edition_ids[0] if len(e.edition_ids)==1 else None,is_rule=True)
        answer=evidence.pop('text');evidence.pop('recommendations',None)
        return say(answer,**evidence,suggestions=['Recomeçar'])
    if 'two_game_ids' in parsed.missing_information:
        return say('Quais dois jogos você quer comparar? Escreva, por exemplo, “Compare Root com Scythe”.',suggestions=['Compare Root com Scythe','Compare Brass: Birmingham com Ark Nova'])
    if 'game_id' in parsed.missing_information:
        return say('De qual jogo você está falando? Diga o nome para eu consultar a ficha.',suggestions=['Fale sobre Catan','Fale sobre Gloomhaven'])
    targets=[g for gid in e.game_ids for g in DEFAULT_CATALOG.games if g['id']==gid]
    if not targets and parsed.intent in ('explanation','information','offer','edition'):
        target_ids=state.get('subject_ids') or state['last_ids'][:1]
        targets=[next(g for g in DEFAULT_CATALOG.games if g['id']==gid) for gid in target_ids]
    if targets:
        state['subject_ids']=[g['id'] for g in targets]
        if e.edition_ids:state['subject_edition_ids']=e.edition_ids
        elif e.game_ids:state.pop('subject_edition_ids',None)
        state.pop('pending_comparison',None)
        informational=parsed.intent in ('information','comparison','offer','edition')
        cards=[];details=[];evaluations=[]
        for game in targets[:3]:
            card,decision=evaluate_game(game,state)
            evaluations.append({'game_id':game['id'],'eligible':decision.eligible,'rejections':decision.rejections,'rule_trace':decision.trace})
            if informational:details.append({'id':game['id'],'name':game['name'],'description':game['description'],'players':game['players'],'duration':game['duration'],'complexity':game['complexity'],'kind':'information','eligible_for_preferences':decision.eligible,'rejections':decision.rejections})
            elif card is not None:cards.append(card)
        if informational:
            names=', '.join(g['name'] for g in targets)
            if parsed.intent=='comparison':
                return say(render('comparison',names=names),comparison=compare_games(targets,state),game_details=details,evaluation=evaluations,suggestions=['Ofertas deles','Edições deles','Recomeçar'])
            if parsed.intent=='edition':
                groups=editions_for(targets)
                return say(render('edition',names=names),edition_details=groups,game_details=details,
                           suggestions=['Ofertas '+edition['id'] for group in groups for edition in group['editions']][:5])
            if parsed.intent=='offer':
                return say(render('offer',names=names),offer_groups=offers_for(targets,state,state.get('subject_edition_ids')),game_details=details,evaluation=evaluations,suggestions=['Edições deles','Mais barato','Recomeçar'])
            answer='Estas são fichas informativas, não recomendações de compra. A compatibilidade com suas preferências é indicada separadamente; os metadados são preliminares.'
            if parsed.intent=='comparison':answer='Identifiquei os jogos para comparação. Por enquanto, mostro as fichas com os atributos cadastrados; não vou inventar diferenças de interação ou estratégia.'
            if parsed.intent=='edition':answer='Identifiquei uma consulta sobre edições. Confira a edição na ficha; idioma e produto ainda são preliminares. Não vou tratar versões diferentes como equivalentes.'
            if parsed.intent=='offer':answer='Consulte as ofertas DEMO na ficha e selecione a edição exata. Os preços são simulados e o frete não está incluído.'
            return say(answer,game_details=details,evaluation=evaluations,suggestions=['Outras opções','Recomeçar'])
        if not cards:return say('Não encontrei uma recomendação elegível entre os jogos citados com as condições atuais. Não vou ignorar seus filtros de jogadores, orçamento, tempo ou estilo.',evaluation=evaluations,suggestions=['Sem limite de orçamento','Sem limite de tempo','Recomeçar'])
        state['last_ids']=[card['id'] for card in cards]
        return say('Os jogos abaixo atendem às condições atuais. Abra a ficha para consultar os detalhes e as ofertas DEMO.',cards=cards,evaluation=evaluations,suggestions=['Outras opções','Mais barato','Até 1 hora'])
    changed=bool(media) or any(value not in (None,[]) for value in vars(e).values())
    discovery=bool(re.search(r'recomend|indic|sugest|opco|proximo jogo',text))
    if parsed.intent in ('explanation','information'):
        return say('Ainda não sei a qual jogo você se refere. Informe o nome ou peça uma recomendação primeiro.',suggestions=['Gosto de jogos de luta','Fale sobre Catan'])
    if not changed and not parsed.cheaper and not parsed.more and not discovery:
        if re.search(r'corrida|futebol|esporte|fifa|forza|gran turismo',text):return say('Ainda não temos uma relação editorial confiável para esse tipo de jogo. Você gosta mais da competição, da estratégia ou de jogar com amigos?',suggestions=['Competição para 2 pessoas','Estratégia','Algo para a família'])
        return say('Não consegui identificar uma preferência com segurança. Pode me contar um gênero, um videogame ou uma restrição?',suggestions=['Gosto de jogos de luta','Gosto de XCOM 2','Para quatro pessoas'])
    p=state['preferences'];has_interest=bool(state['interests'] or p.get('videogames') or p.get('mode') or state.get('media_ids'))
    from .journey import PROFILE
    if not has_interest and not PROFILE.get() and not any(k in p for k in ('players','budget','duration')):
        state['waiting_for']='interest'
        return say('Antes de sugerir, quero entender seu gosto. Você prefere combate, aventura, estratégia ou jogos mais leves?',suggestions=['Combate','Aventura','Jogos leves'])
    media_links=[]
    if state.get('media_ids'):
        candidate_ids,media_links=linked_candidates(state['media_ids'])
        ranked=recommend(state,parsed.cheaper,candidate_ids=candidate_ids)
        for card in ranked:
            card['editorial_links']=[r for r in media_links if r['game_id']==card['id']]
    else:
        ranked=recommend(state,parsed.cheaper)
        if state['preferences'].get('videogames'):
            _,media_links=linked_candidates(['media-'+vid for vid in state['preferences']['videogames']])
            for card in ranked:
                card['editorial_links']=[r for r in media_links if r['game_id']==card['id']]
    if parsed.more and not changed:ranked=[r for r in ranked if r['id'] not in state['last_ids']]
    chosen=ranked[:3]
    if not chosen:
        state['waiting_for']=None
        answer='Já mostrei as opções compatíveis disponíveis. Podemos mudar o tema ou ampliar os filtros.' if parsed.more and not changed else 'Não encontrei jogos que atendam a todas essas condições. Não vou ignorar seus filtros: podemos aumentar o orçamento, liberar o tempo ou mudar a experiência.'
        return say(answer,suggestions=['Sem limite de orçamento','Sem limite de tempo','Recomeçar'])
    state['last_ids']=list(dict.fromkeys([*state['last_ids'],*[r['id'] for r in chosen]]))[-60:] if parsed.more and not changed else [r['id'] for r in chosen]
    state['subject_ids']=[r['id'] for r in chosen[:1]]
    state.pop('subject_edition_ids',None)
    summary=[]
    if state['interests']:summary.append(', '.join(state['interests']))
    if p.get('videogames'):summary.append('afinidade com '+', '.join(v['franchise'] for v in DEFAULT_CATALOG.videos if v['id'] in p['videogames']))
    if p.get('players'):summary.append(f"{p['players']} pessoa(s)")
    if p.get('budget'):summary.append(f"até R$ {p['budget']:g} na simulação")
    answer=('Separei as opções mais baratas com oferta recente na simulação' if parsed.cheaper else 'Encontrei opções de '+(' · '.join(summary) or 'acordo com suas condições'))+'.'
    if media_links:answer+=' '+render('media',names=', '.join(dict.fromkeys(r['title'] for r in media_links)))
    if 'combate' in state['interests']:answer+=' Aqui a ponte com jogos de luta é o confronto e a decisão tática; não temos uma simulação de combos em tempo real.'
    if not p.get('players'):
        state['waiting_for']='players';answer+=' Quantas pessoas vão jogar?';suggestions=['2 pessoas','4 pessoas','Vou jogar solo']
    elif not p.get('budget') and not state['budget_unlimited'] and not parsed.cheaper:
        state['waiting_for']='budget';answer+=' Quer definir um orçamento para eu refinar as ofertas demonstrativas?';suggestions=['Até R$ 300','Até R$ 600','Sem limite de orçamento']
    else:
        state['waiting_for']=None;answer+=' Você pode abrir as fichas ou me pedir para ajustar a busca.';suggestions=['Outras opções','Mais barato','Até 1 hora']
    return say(answer,cards=chosen,suggestions=suggestions)
