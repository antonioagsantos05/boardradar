"""Read-only merged BGG snapshots; metadata is never official rule evidence."""
from functools import lru_cache
import re
from .catalog import load,DEFAULT_CATALOG
from .nlp.normalizer import name_key
from .nlp import apply_entities
from .game_index import search

SEARCH_TERMS={'economia':'economic','economico':'economic','negociacao':'negotiation',
              'fantasia':'fantasy','terror':'horror','aventura':'adventure','animais':'animals',
              'cartas':'card game','dados':'dice','civilizacoes':'civilization',
              'espacial':'space exploration','ficcao cientifica':'science fiction',
              'deducao':'deduction','cooperativo':'cooperative game','cooperativos':'cooperative game',
              'deck building':'deckbuilding','alocacao de trabalhadores':'worker placement',
              'construcao de cidades':'city building','trens':'trains'}


def search_query(message,state,parsed):
    """Explicit full-library discovery; never bypass curated recommendation policy."""
    text=name_key(message)
    if not re.search(r'\b(busque|busca|procure|pesquise|mostre|encontre)\b',text):return None
    if not re.search(r'\b(catalogo|base completa|base ampliada|banco de jogos)\b',text):return None
    if parsed.errors or parsed.ambiguities or parsed.intent in ('rule','offer','comparison','reset','commercial'):return None
    current=apply_entities(state,parsed)
    preferences=current['preferences']
    terms=list(dict.fromkeys(value for key,value in SEARCH_TERMS.items() if re.search(r'\b'+re.escape(key)+r'\b',text)))
    if not terms and not any(preferences.get(k) for k in ('players','duration','complexity','budget','mode')) and not re.search(r'\b(todos|todas)\b',text):
        return {'text':'Qual categoria ou mecânica você quer pesquisar? Posso buscar fantasia, terror, cartas, economia, exploração espacial ou alocação de trabalhadores, além de filtrar jogadores e duração.',
                'state':current,'preferences':preferences,'recommendations':[],'ids':[],
                'suggestions':['Busque no catálogo jogos de fantasia','Busque no catálogo jogos de cartas'],'is_demo':True,'engine':'python-catalog'}
    # Unsupported taste/mode restrictions cannot silently disappear in an informational query.
    if current.get('excluded') or current.get('excluded_games') or preferences.get('mode')=='competitive':
        return {'text':'A busca ampliada ainda não verifica exclusões de tema ou modo competitivo com segurança. Posso usar a seleção editorial para respeitar essas condições.',
                'state':current,'preferences':preferences,'recommendations':[],'ids':[],
                'suggestions':['Quero recomendações','Recomeçar'],'is_demo':True,'engine':'python-catalog'}
    if preferences.get('mode')=='cooperative' and 'cooperative game' not in terms:terms.append('cooperative game')
    if preferences.get('budget') is not None:
        return {'text':'O catálogo ampliado não tem preços verificados, então não consigo garantir esse orçamento. Posso consultar as ofertas DEMO da seleção editorial ou pesquisar informações sem uma condição de preço.',
                'state':current,'preferences':preferences,'recommendations':[],'ids':[],
                'suggestions':['Quero recomendações','Sem limite de orçamento'],'is_demo':True,'engine':'python-catalog'}
    total,rows=search(terms,players=preferences.get('players'),duration=preferences.get('duration'),complexity=preferences.get('complexity'))
    current.pop('last_topic',None)
    current['library_subject_ids']=[r['id'] for r in rows]
    criteria=[]
    if preferences.get('players'):criteria.append(f"{preferences['players']} jogadores")
    if preferences.get('duration'):criteria.append(f"até {preferences['duration']} minutos")
    if preferences.get('complexity'):criteria.append(f"complexidade BGG até {preferences['complexity']}/5")
    condition=(' para '+', '.join(criteria)) if criteria else ''
    answer=(f'Encontrei {total} registros{condition} e mostrei os primeiros por nome. ' if total else f'Não encontrei registros com dados que confirmem essas condições{condition}. ')
    answer+='A busca usa categorias e mecânicas cadastradas. São opções informativas, sem avaliação editorial de compra; expansões identificadas foram excluídas, mas alguns formatos ainda não foram informados pela origem.'
    return {'text':answer,'state':current,'preferences':preferences,'recommendations':[],'ids':[],
            'library_games':[card(r) for r in rows],'library_total':total,'answer_confidence':'partial',
            'suggestions':['Qual deles dura menos?','Qual deles é mais complexo?','Recomeçar'] if rows else ['Recomeçar'],
            'is_demo':True,'engine':'python-catalog','intent':'information'}


@lru_cache(maxsize=1)
def records():
    rows=load('library')
    return {r['id']:r for r in rows}


@lru_cache(maxsize=1)
def names():
    return sorted([(name_key(n),r['id']) for r in records().values() if not r.get('curated_game_id')
                   for n in [r['name'],*r['aliases']] if len(name_key(n))>=5],key=lambda item:-len(item[0]))


def find_named(message):
    text=' '+name_key(message)+' ';selected=[];occupied=[];groups={}
    for name,gid in names():
        at=text.find(' '+name+' ')
        end=at+len(name)+1
        if at<0 or any(a<=at<b and (a,b)!=(at,end) for a,b in occupied):continue
        occupied.append((at,end));groups.setdefault((at,end),set()).add(gid)
        if gid not in selected:selected.append(gid)
        if len(selected)>=3:break
    return selected,any(len(gids)>1 for gids in groups.values())


def card(record):
    return {k:record[k] for k in ('id','name','slug','year','min_players','max_players','min_minutes','max_minutes','complexity','rating','kind','bgg_url')}|{'description':record['description'][:700],'is_recommendation':False}


def handle_query(message,state,parsed):
    if parsed.intent in ('reset','commercial','greeting','thanks') or parsed.errors:return None
    discovery=search_query(message,state,parsed)
    if discovery is not None:return discovery
    native=parsed.entities.game_ids
    if parsed.ambiguities or state.get('pending_clarification'):return None
    if parsed.entities.videogame_ids and not re.search(r'\b(tabuleiro|bgg|base ampliada)\b',name_key(message)):return None
    if native and (parsed.intent!='comparison' or len(native)>=2):
        state.pop('library_subject_ids',None);return None
    text=name_key(message)
    named_request=bool(re.search(r'\b(fale|conte|sobre|compare|comparar|recomende|busque|procure|informacoes|gosto de|curto)\b',text))
    external,ambiguous=find_named(message) if named_request or any(text==n for n,_ in names()) else ([],False)
    if native:
        native_names={name_key(n) for g in DEFAULT_CATALOG.games if g['id'] in native for n in [g['name'],*g.get('aliases',[])]}
        external=[gid for gid in external if name_key(records()[gid]['name']) not in native_names]
    previous=state.get('library_subject_ids',[])
    if not external and native:
        state.pop('library_subject_ids',None);return None
    contextual=bool(previous and re.search(r'\b(dele|deles|esse|esses|desses|deles|qual|ofertas|rapido|complexo)\b',text))
    if not external and not contextual:return None
    ids=list(dict.fromkeys([*native,*external])) if external else previous
    if not ids:return None
    if external:state.pop('last_topic',None)
    state['library_subject_ids']=ids[:3]
    rows=[records()[gid] for gid in ids if gid in records()]
    output={'state':state,'preferences':state['preferences'],'recommendations':[],'ids':[],
            'suggestions':['Compare dois jogos','Recomeçar'],'is_demo':True,'engine':'python-catalog',
            'library_games':[card(r) for r in rows],'intent':parsed.intent}
    if not external and not native and rows and re.search(r'\b(dura menos|mais rapido|mais curto|mais complexo|mais simples|mais leve)\b',text):
        key='max_minutes' if re.search(r'dura menos|mais rapido|mais curto',text) else 'complexity'
        known=[r for r in rows if r.get(key)]
        if len(known)!=len(rows):
            return {**output,'text':'Faltam dados comparáveis para pelo menos um desses jogos. Não consigo afirmar qual é a melhor opção nesse critério.','answer_confidence':'unknown'}
        reverse='mais complexo' in text
        winner=sorted(known,key=lambda r:r[key],reverse=reverse)[0]
        values='; '.join(f"{r['name']}: {r[key]}"+(' minutos' if key=='max_minutes' else '/5 na avaliação da comunidade BGG') for r in rows)
        return {**output,'text':f"Entre os registros consultados, {winner['name']} tem o {'maior' if reverse else 'menor'} valor cadastrado. {values}. Esses dados são do snapshot importado, e não confirmam regras ou edição comercial.",'answer_confidence':'partial'}
    if ambiguous:
        state.pop('library_subject_ids',None)
        return {**output,'text':'Há registros diferentes com esse nome na base. Confira o ano e o ID BGG nas fichas para identificar o produto correto; não vou juntar jogos distintos como se fossem um só.','library_status':'ambiguous'}
    if parsed.intent=='rule':
        return {**output,'text':'Tenho dados de catálogo do BGG, mas eles não são um manual oficial. Para confirmar uma ação preciso do jogo, da edição e de documentação autorizada dessa edição.','sources':[],'answer_confidence':'unknown'}
    if parsed.intent=='offer':
        return {**output,'text':'Não há ofertas verificadas para esses registros importados. A base contém informações sobre jogos, sem preços ou estoque; não vou inventar uma oferta.'}
    if parsed.intent=='comparison' and len(ids)>=2:
        games=[];columns=[]
        for gid in ids[:3]:
            r=records().get(gid)
            if r:
                games.append({'id':r['id'],'name':r['name']})
                columns.append([f"{r['min_players']}–{r['max_players']}" if r['min_players'] and r['max_players'] else 'Não informado',
                                f"{r['min_minutes']}–{r['max_minutes']}" if r['min_minutes'] and r['max_minutes'] else 'Não informado',
                                f"{r['complexity']:.2f} (comunidade BGG)" if r['complexity'] else 'Não informado',', '.join(r['mechanics']) or 'Não informado'])
            else:
                g=next(g for g in DEFAULT_CATALOG.games if g['id']==gid);games.append({'id':g['id'],'name':g['name']})
                columns.append([f"{g['players']['min']}–{g['players']['max']}",g['duration'],f"{g['complexity']} (editorial)",', '.join(g['tags'])])
        comparison={'games':games,'rows':[{'attribute':a,'values':[c[i] for c in columns]} for i,a in enumerate(['Jogadores','Duração (min)','Complexidade (1–5)','Etiquetas / mecânicas'])]}
        return {**output,'text':'Comparei os atributos disponíveis. Os dados BGG são snapshots da comunidade; complexidade editorial e avaliação BGG têm origens diferentes. A edição comercial precisa de confirmação.','comparison':comparison}
    summary=' '.join(f"{r['name']}: {r['description'][:500]}" for r in rows)
    return {**output,'text':summary+' Estes são registros informativos da base BGG, sujeitos a revisão de edição e atualização; não são recomendações de compra.'}
