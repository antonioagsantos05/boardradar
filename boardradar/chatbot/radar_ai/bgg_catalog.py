"""Active catalogue: approved 2019 JSON details joined to 2026 ranks by BGG ID."""
from functools import lru_cache
import json
from pathlib import Path
import re
import unicodedata

DATA=Path(__file__).resolve().parents[2]/'src/data'
GROUPS=['Abstratos','Cartas colecionáveis','Infantis','Família','Festa','Estratégia','Temáticos','Guerra']
TERMS={'fantasia':'fantasy','terror':'horror','aventura':'adventure','economia':'economic','cartas':'card game','dados':'dice','civilizacoes':'civilization','espacial':'space exploration','animais':'animals','cooperativo':'co-operative play','cooperativos':'co-operative play','deck building':'deck / pool building','alocacao de trabalhadores':'worker placement','guerra':'wargame','trens':'trains'}


def normal(text):
    value=''.join(c for c in unicodedata.normalize('NFD',text) if unicodedata.category(c)!='Mn').casefold()
    return re.sub(r'[^\w]+',' ',value).strip()


@lru_cache(maxsize=1)
def data():
    rows=json.loads((DATA/'bgg-ranks.json').read_text(encoding='utf-8'))
    ranks={str(r[0]):r for r in rows}
    details={r['bgg_id']:r for r in json.loads((DATA/'bgg-details.json').read_text(encoding='utf-8'))}
    identities=json.loads((DATA/'catalog-legacy-ids.json').read_text(encoding='utf-8'))
    return ranks,details,identities


def get_game(identifier):
    ranks,details,aliases=data();bid=aliases.get(identifier,identifier.removeprefix('bgg-'))
    row=ranks.get(bid);detail=details.get(bid)
    if row is None and detail is None:return None
    result=dict(detail) if detail else {'description':'','categories':[],'mechanics':[],'min_players':None,'max_players':None,'min_minutes':None,'max_minutes':None,'complexity':None,'details_date':None}
    result.update(id='bgg-'+bid,bgg_id=bid,slug='bgg-'+bid,historical_rating=detail.get('rating') if detail else None)
    result.update(name=row[1] if row else detail['name'],year=row[2] if row else detail['year'],rank=row[3] if row else None,rating=row[5] if row else None,rating_count=row[6] if row else None,bayes_average=row[4] if row else None,kind=('boardgameexpansion' if row[7] else 'boardgame') if row else detail['kind'],ranking_date='2026-10-20' if row else None)
    return result


@lru_cache(maxsize=1)
def names():
    ranks,details,_=data();result={}
    for bid in ranks.keys()|details.keys():
        for name in {ranks[bid][1] if bid in ranks else '',details[bid]['name'] if bid in details else ''}:
            if name:result.setdefault(normal(name),set()).add('bgg-'+bid)
    return result


def named(message):
    words=normal(message).split();found=[];ambiguous=False;occupied=set()
    for length in range(min(20,len(words)),0,-1):
        for start in range(len(words)-length+1):
            if occupied.intersection(range(start,start+length)):continue
            term=' '.join(words[start:start+length]);matches=names().get(term,set())
            if not matches or (len(term)<4 and term!=normal(message)):continue
            ambiguous|=len(matches)>1
            found.extend(sorted(matches,key=lambda gid:int(gid[4:])));occupied.update(range(start,start+length))
            if len(found)>=3:return found[:3],ambiguous
    return list(dict.fromkeys(found))[:3],ambiguous


@lru_cache(maxsize=1)
def ordered_ids():
    ranks,details,_=data()
    return sorted(ranks.keys()|details.keys(),key=lambda bid:(ranks.get(bid,[None,None,None,None])[3] or float('inf'),int(bid)))


def search(query='',players=None,duration=None,complexity=None,limit=3):
    if not isinstance(query,str) or len(query)>200 or type(limit) is not int or not 1<=limit<=96:raise ValueError('Busca inválida.')
    for value in (players,duration,complexity):
        if value is not None and (type(value) not in (int,float) or value<=0):raise ValueError('Filtro inválido.')
    ranks,details,_=data();terms=normal(query).split();result=[];total=0
    for bid in ordered_ids():
        detail=details.get(bid);row=ranks.get(bid)
        if players is not None and (not detail or not detail['min_players'] or not detail['max_players'] or not detail['min_players']<=players<=detail['max_players']):continue
        if duration is not None and (not detail or not detail['max_minutes'] or detail['max_minutes']>duration):continue
        if complexity is not None and (not detail or not detail['complexity'] or detail['complexity']>complexity):continue
        text=normal(' '.join([row[1] if row else detail['name'],*(detail['categories']+detail['mechanics'] if detail else [])]))
        if not all(term in text for term in terms):continue
        total+=1
        if len(result)<limit:result.append(get_game('bgg-'+bid))
    return total,result


def card(game):
    return {key:game.get(key) for key in ('id','name','slug','year','min_players','max_players','min_minutes','max_minutes','complexity','rating','rank','ranking_date','details_date','kind')}


def respond(message,raw_state=None):
    if not isinstance(message,str) or not 0<len(message.strip())<=1000:raise ValueError('Mensagem inválida.')
    if raw_state is not None and not isinstance(raw_state,dict):raise ValueError('Contexto inválido.')
    raw_state=raw_state or {};text=normal(message)
    previous=raw_state.get('library_subject_ids',[])
    if not isinstance(previous,list) or len(previous)>3 or any(not isinstance(gid,str) or not re.fullmatch(r'bgg-\d+',gid) for gid in previous):previous=[]
    preferences=raw_state.get('preferences',{})
    if not isinstance(preferences,dict):raise ValueError('Preferências inválidas.')
    preferences={key:value for key,value in preferences.items() if key in ('players','duration','complexity')}
    for key,value in preferences.items():
        if type(value) not in (int,float) or not 0<value<=({'players':20,'duration':10000,'complexity':5}[key]):raise ValueError('Filtro inválido.')
    players=re.search(r'\b(\d{1,2})\s*(?:pessoas|jogadores)\b',text);duration=re.search(r'\b(\d{1,4})\s*(?:minutos|min)\b',text)
    if players:
        if not 1<=int(players[1])<=20:raise ValueError('Jogadores inválidos.')
        preferences['players']=int(players[1])
    if duration:
        if int(duration[1])<1:raise ValueError('Duração inválida.')
        preferences['duration']=int(duration[1])
    if 'sem limite de tempo' in text:preferences.pop('duration',None)
    state={'preferences':preferences,'library_subject_ids':previous}
    output={'state':state,'preferences':preferences,'recommendations':[],'ids':[],'engine':'python-bgg-catalog','is_demo':False,'intent':'information','suggestions':['Jogos mais bem avaliados','Compare Catan com Pandemic','Jogos para 4 pessoas']}
    def answer(text,games=(),**extra):return {**output,'text':text,'library_games':[card(g) for g in games],**extra}
    if text in ('recomecar','reiniciar','reset','nova conversa'):
        state['library_subject_ids']=[];preferences.clear();return answer('Vamos começar de novo. Posso consultar os rankings de 2026 e os detalhes históricos dos jogos.')
    if text in ('oi','ola','bom dia','boa tarde','boa noite'):
        return answer('Olá! Posso buscar jogos, comparar dados e consultar notas e rankings. Os rankings são de 2026; os detalhes de 1.000 jogos são de 2019.')
    ids,ambiguous=named(message)
    if ambiguous:return answer('Encontrei jogos diferentes com esse nome. Informe o ID BGG para identificar o registro correto.',[get_game(gid) for gid in ids])
    direct=re.search(r'\bbgg\s*(\d+)\b',text)
    if direct:
        game=get_game('bgg-'+direct[1]);ids=[game['id']] if game else []
    if not ids and previous and not re.search(r'\b(busque|procure|mostre|jogos para|jogos de|jogos mais|ranking geral)\b',text) and re.search(r'\b(deles|dele|esses|esse|eles|a nota|o ranking|duracao|mecanicas)\b',text):ids=[gid for gid in previous if get_game(gid)]
    if ids:state['library_subject_ids']=ids[:3]
    games=[get_game(gid) for gid in ids if get_game(gid)]
    if re.search(r'\b(posso atacar|posso mover|quantas cartas|regra|regras|manual|como jogar)\b',text):return answer('As fontes atuais são dados de catálogo, não manuais oficiais. Não consigo confirmar ações ou regras da sua edição com esses arquivos.',games,answer_confidence='unknown')
    if re.search(r'\b(preco|precos|oferta|ofertas|comprar|orcamento|reais|barato)\b',text):return answer('Os arquivos de jogos não contêm preços, estoque ou edições comerciais. Não consigo garantir um orçamento com essas fontes. Os anúncios dos usuários continuam disponíveis separadamente no marketplace.',games,answer_confidence='unknown')
    if len(games)>=2 and (re.search(r'compar|diferenca|versus| vs ',text) or previous):
        columns=[]
        for g in games:
            columns.append([g['year'] or 'Não informado',g['rank'] or 'Sem ranking de 2026',g['rating'] if g['rating'] is not None else 'Não informada',f"{g['min_players']}–{g['max_players']}" if g['min_players'] and g['max_players'] else 'Não informado',f"{g['max_minutes']} min" if g['max_minutes'] else 'Não informado',g['complexity'] or 'Não informada',', '.join(g['mechanics']) or 'Não informadas'])
        comparison={'games':[{'id':g['id'],'name':g['name']} for g in games],'rows':[{'attribute':name,'values':[c[i] for c in columns]} for i,name in enumerate(['Ano','Ranking · 2026','Nota média · 2026','Jogadores · 2019','Duração · 2019','Complexidade · 2019','Mecânicas · 2019'])]}
        return answer('Comparei os campos disponíveis. Ranking e notas vêm do ZIP de 2026; jogadores, duração, complexidade e mecânicas vêm do JSON histórico de 2019. Campos ausentes não foram preenchidos com bases anteriores.',games,comparison=comparison)
    if games:
        parts=[]
        for g in games:
            facts=[g['name']+(f" ({g['year']})" if g['year'] else '')]
            facts.append(f"No arquivo de 2026, posição {g['rank']} no ranking." if g['rank'] else 'Sem posição no ranking de 2026.')
            if g['rating'] is not None:facts.append(f"Nota média de 2026: {g['rating']:.2f}/10.")
            if g['details_date']:
                facts.append(f"Os detalhes históricos de 2019 indicam {g['min_players']}–{g['max_players']} jogadores." if g['min_players'] and g['max_players'] else 'Jogadores não informados.')
                if g['max_minutes']:facts.append(f"Duração cadastrada: {g['max_minutes']} minutos (2019).")
                if g['mechanics']:facts.append('Mecânicas cadastradas em 2019: '+', '.join(g['mechanics'])+'.')
                if re.search(r'descreva|descricao|sobre|fale',text) and g.get('description'):facts.append('Descrição histórica em inglês: '+g['description'][:900].strip())
            else:facts.append('Este jogo só está no ZIP de rankings; ele não informa jogadores, duração, mecânicas ou descrição.')
            parts.append(' '.join(facts))
        return answer('\n\n'.join(parts),games)
    if re.search(r'\b(mass effect|witcher|resident evil|xcom|videogame)\b',text):return answer('Esses arquivos não contêm relações entre videogames e jogos de tabuleiro. Posso buscar por nome, categoria ou mecânica, sem reutilizar as associações das bases anteriores.')
    players=re.search(r'\b(\d{1,2})\s*(?:pessoas|jogadores)\b',text);duration=re.search(r'\b(\d{1,4})\s*(?:minutos|min)\b',text)
    query=' '.join(value for key,value in TERMS.items() if re.search(r'\b'+re.escape(key)+r'\b',text))
    top=bool(re.search(r'ranking|melhor|avaliad|top|todos',text))
    if not query and not preferences and not top:return answer('Diga o nome do jogo ou peça uma busca por categoria, jogadores ou duração. Posso também mostrar os mais bem posicionados no ranking de 2026.')
    total,results=search(query,players=preferences.get('players'),duration=preferences.get('duration'),complexity=preferences.get('complexity'))
    state['library_subject_ids']=[g['id'] for g in results]
    return answer(f'Encontrei {total} registros e mostrei os primeiros pelo ranking de 2026. Filtros de jogadores, duração e mecânicas consideram somente os detalhes disponíveis no JSON de 2019; não comprovam preferência pessoal ou disponibilidade para compra.',results,library_total=total)
