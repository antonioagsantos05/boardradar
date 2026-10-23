"""Deterministic recommendations using only the eleven approved POC JSON files."""
import re
import unicodedata
from .catalog import raw
from .journey import PROFILE


def normal(text):
    return re.sub(r'[^\w]+', ' ', ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn').casefold()).strip()


def respond(message, raw_state=None):
    if not isinstance(message, str) or not 0 < len(message.strip()) <= 1000:
        raise ValueError('Mensagem inválida')
    if raw_state is not None and not isinstance(raw_state, dict):
        raise ValueError('Contexto inválido')
    old = raw_state or {}
    profile=PROFILE.get() or {}
    if not profile.get('consent'):profile={}
    franchises=raw('franchises')
    profile_franchises=[f for f in franchises if f['id'] in profile.get('videogames',[])]
    explicit_franchises=set(old.get('preferences',{}).get('videogames',[]))
    prefs = dict(old.get('preferences', {}))
    for key, maximum in [('players', 20), ('duration', 10000), ('complexity', 5), ('budget', 100000)]:
        if key in prefs and (type(prefs[key]) not in (int, float) or not 0 < prefs[key] <= maximum):
            raise ValueError('Filtro inválido')
    text = normal(message)
    interests = set(old.get('interests', []))
    excluded = set(old.get('excluded', []))
    seen = list(old.get('last_ids', []))
    games = raw('games')
    editions = raw('editions')
    offers = raw('store_offers')
    listings = raw('user_listings')
    state = {'preferences': prefs, 'interests': [], 'excluded': [], 'last_ids': []}
    if old.get('library_subject_ids'):state['library_subject_ids']=old['library_subject_ids'][:3]

    def answer(text, selected=(), **extra):
        state.update(interests=sorted(interests), excluded=sorted(excluded), last_ids=seen[-100:])
        return dict(text=text, state=state, preferences=prefs, recommendations=[], ids=[],
                    is_demo=True, engine='python-poc-v3', intent='information',
                    suggestions=['Usar meus gostos', 'Jogos para 4 pessoas', 'Mostrar mais'], **extra)

    if text in ('recomecar', 'reiniciar', 'reset', 'nova conversa'):
        prefs.clear(); interests.clear(); excluded.clear(); seen.clear();state.pop('library_subject_ids',None)
        return answer('Vamos começar de novo. Conte seus gostos ou diga quantas pessoas vão jogar.')
    if text in ('oi', 'ola', 'bom dia', 'boa tarde', 'boa noite'):
        return answer('Olá'+(', '+profile['display_name'].split()[0] if profile.get('display_name') else '')+'! Posso sugerir jogos pelos seus gostos, comparar opções ou ajudar a anunciar. O que vamos descobrir?')
    if re.search(r'como (?:vender|anunciar)|quero (?:vender|anunciar)|criar anuncio',text):
        return answer('Para anunciar, escolha o jogo e a edição, descreva o estado, defina preço e entrega e adicione as fotos. Você pode salvar um rascunho e continuar depois. Ao enviar, o anúncio segue para análise.',actions=[{'label':'Criar meu anúncio','href':'/vender'},{'label':'Meus anúncios','href':'/meus-anuncios'}])
    if re.search(r'meus anuncios|meu anuncio|status do anuncio',text):
        return answer('Em Meus anúncios você acompanha a análise, continua rascunhos e gerencia os jogos publicados.',actions=[{'label':'Ver meus anúncios','href':'/meus-anuncios'}])
    if re.search(r'minhas conversas|mensagens|falar com vendedor',text):
        return answer('Abra um anúncio para conversar com o vendedor. Suas conversas ficam reunidas na conta.',actions=[{'label':'Minhas conversas','href':'/mensagens'},{'label':'Explorar anúncios','href':'/marketplace'}])
    if re.search(r'(?:alterar|editar|salvar|mudar) (?:meus |minhas )?(?:gostos|preferencias|franquias)',text):
        return answer('Você pode ajustar estilos, franquias, experiência e orçamento no seu perfil. As escolhas ficam salvas para as próximas recomendações.',actions=[{'label':'Ajustar meus gostos','href':'/minha-conta?sec=perfil'}])
    if re.search(r'meus gostos|minhas preferencias|meu perfil|minhas afinidades',text) and not profile:
        return answer('Escolha seus estilos e franquias no perfil ou conte aqui o que você gosta. Posso recomendar dos dois jeitos.',actions=[{'label':'Escolher meus gostos','href':'/minha-conta?sec=perfil'}])
    for key, pattern in [('players', r'\b(\d{1,2})\s*(?:pessoas|jogadores)\b'), ('duration', r'\b(\d{1,4})\s*(?:minutos|min)\b'), ('budget', r'\br\s*\$\s*(\d+(?:[.,]\d{1,2})?)')]:
        match = re.search(pattern, message.casefold() if key == 'budget' else text)
        if match:
            value = float(match[1].replace(',', '.'))
            if not 0 < value <= {'players':20, 'duration':10000, 'budget':100000}[key]:
                raise ValueError('Filtro inválido')
            prefs[key] = int(value) if key != 'budget' else value
    budget = re.search(r'\b(\d+(?:[.,]\d{1,2})?)\s*reais\b', message.casefold())
    if budget: prefs['budget'] = float(budget[1].replace(',', '.'))
    complexity = re.search(r'complexidade\s*(?:at[eé]\s*)?([1-5](?:[.,]\d+)?)', message.casefold())
    if complexity: prefs['complexity'] = float(complexity[1].replace(',', '.'))
    if 'sem limite de tempo' in text: prefs.pop('duration', None)
    if 'sem limite de orcamento' in text: prefs.pop('budget', None)
    labels = {r['id']:r['nome'] for r in raw('themes')+raw('experiences')}
    aliases = {'cooperativo':'cooperacao', 'cooperativos':'cooperacao', 'cooperativa':'cooperacao', 'espacial':'espaco', 'ficcao cientifica':'ficcao_cientifica'}
    terms = [(normal(label), identifier) for identifier, label in labels.items()]+list(aliases.items())
    for term, identifier in terms:
        if re.search(r'\b'+re.escape(term)+r'\b', text):
            negative = re.search(r'(?:nao gosto de|nao quero|sem|evitar|odeio)\s+(?:jogos?\s+(?:de\s+)?)?'+re.escape(term)+r'\b', text)
            if negative: excluded.add(identifier); interests.discard(identifier)
            else: interests.add(identifier)
    for f in raw('franchises'):
        if normal(f['nome']) in text:
            if re.search(r'(?:nao gosto de|nao quero|sem|odeio)\s+'+re.escape(normal(f['nome'])), text):
                excluded.update(f['temas']);explicit_franchises.discard(f['id'])
            else:
                interests.update(f['temas']+f['experiencias']);explicit_franchises.add(f['id'])
    if explicit_franchises:prefs['videogames']=sorted(explicit_franchises)
    else:prefs.pop('videogames',None)
    named = [g for g in games if re.search(r'\b'+re.escape(normal(g['nome']))+r'\b', text)]
    if not named and re.search(r'\b(dele|deles|esses|esse|eles)\b', text):
        named = [g for g in games if 'bgg-'+str(g['bgg_id']) in old.get('library_subject_ids', [])]
    if not named and re.search(r'fale sobre|ofertas? (?:de|do)|preco (?:de|do)|compare ', text):
        return answer('Não encontrei esse nome no catálogo. Tente o título completo ou explore os jogos cadastrados.')
    if not named and re.search(r'por que|porque|motivo|afinidade',text):
        named=[g for g in games if g['game_id'] in old.get('last_ids',[])][:3]
    if named: state['library_subject_ids'] = ['bgg-'+str(g['bgg_id']) for g in named[:3]]
    if re.search(r'\b(regra|regras|manual|como jogar)\b', text):
        return answer('Os JSONs contêm fichas de catálogo, não manuais. Não consigo confirmar regras de uma edição com essas fontes.')
    if re.search(r'compar|diferenca|versus|\bvs\b',text) and len(named)<2:
        return answer('Quais dois jogos você quer comparar? Diga os nomes, por exemplo: Scythe e Pandemic.')
    if len(named) >= 2 and re.search(r'compar|diferenca|versus|\bvs\b', text):
        selected = named[:3]
        return answer('Veja as diferenças para escolher o que combina com a sua mesa.', comparison={
            'games':[{'id':g['game_id'],'name':g['nome']} for g in selected],
            'rows':[{'attribute':label,'values':[fn(g) for g in selected]} for label,fn in [
                ('Jogadores',lambda g:f"{g['jogadores_min']}–{g['jogadores_max']}"),
                ('Duração',lambda g:str(g['duracao_minutos'])+' min'),
                ('Complexidade /5',lambda g:g['complexidade']['valor']),('Ano',lambda g:g['ano_publicacao']),('Nota BGG · 2019',lambda g:g['avaliacao_bgg_2019']['average'])]]})
    explanation=bool(re.search(r'por que|porque|motivo|afinidade',text))
    if named and not explanation and not re.search(r'recomend|sugir|quero jogar', text):
        price_query = re.search(r'preco|oferta|comprar|barato', text)
        if price_query:
            groups=[]
            stores={s['store_id']:s['nome'] for s in raw('stores')}
            for g in named[:3]:
                for e in editions:
                    if e['game_id'] != g['game_id']: continue
                    groups.append(dict(game_id=g['game_id'],game_name=g['nome'],edition_id=e['edition_id'],edition_name='Edição base' if 'referência' in e['nome_edicao'] else e['nome_edicao'],language=e['idioma'],eligible_for_preferences=True,
                        offers=[dict(id=o['offer_id'],price_cents=round(o['preco_brl']*100),store_name=stores[o['store_id']],checked_at=raw('metadata')['gerado_em']+'T00:00:00Z',condition=o['condicao'],within_budget=prefs.get('budget',float('inf'))>=o['preco_brl']) for o in offers if o['edition_id']==e['edition_id']]))
            return answer('Confira os preços cadastrados por edição. Frete e disponibilidade devem ser conferidos na oferta.', offer_groups=groups)
        return answer('\n\n'.join(g['nome']+': '+g['descricao_pt'] for g in named[:3]), library_games=[{'id':'bgg-'+str(g['bgg_id']),'slug':'bgg-'+str(g['bgg_id']),'name':g['nome'],'year':g['ano_publicacao'],'kind':'boardgame'} for g in named[:3]])
    more = bool(re.search(r'mostrar mais|mostre mais|mais jogos|outras opcoes', text))
    if not more: seen.clear()
    affinity_franchises=[f for f in franchises if f['id'] in explicit_franchises] if explicit_franchises else (profile_franchises if not interests else [])
    def affinity(g):
        tags=set(g['temas']+g['experiencias'])
        matches=[]
        for f in affinity_franchises:
            shared_themes=tags & set(f['temas']);shared_experiences=tags & set(f['experiencias'])
            if shared_themes or shared_experiences:matches.append((3*len(shared_themes)+len(shared_experiences),f,shared_themes|shared_experiences))
        matches.sort(key=lambda item:-item[0])
        styles={normal({'cooperativo':'cooperacao','família':'familia'}.get(t,t)) for t in (profile.get('styles',[]) if not interests else [])}
        style_matches=[t for t in tags if normal(t.replace('_',' ')) in styles]
        score=(matches[0][0] if matches else 0)+4*len(style_matches)
        reason=('Porque você gosta de '+matches[0][1]['nome']+'. Em comum: '+', '.join(labels.get(t,t.replace('_',' ')) for t in sorted(matches[0][2]))+'. ') if matches else ('Combina com seu estilo: '+', '.join(labels.get(t,t) for t in style_matches)+'. ' if style_matches else '')
        if profile.get('budget'):
            prices=[o['preco_brl'] for o in offers if o['game_id']==g['game_id']]
            if prices and min(prices)<=profile['budget']:score+=1
        return score,reason
    candidates=[]
    for g in named or games:
        tags=set(g['temas']+g['experiencias'])
        if excluded & tags: continue
        if prefs.get('players') and not g['jogadores_min'] <= prefs['players'] <= g['jogadores_max']: continue
        if prefs.get('duration') and g['duracao_minutos'] > prefs['duration']: continue
        if prefs.get('complexity') and g['complexidade']['valor'] > prefs['complexity']: continue
        prices=[o['preco_brl'] for o in offers if o['game_id']==g['game_id']]+[l['preco_brl'] for l in listings if l['game_id']==g['game_id'] and l['status']=='ativo_simulado']
        price=min(prices) if prices else None
        if 'budget' in prefs and (price is None or price > prefs['budget']): continue
        matches=interests & tags
        if interests and not matches: continue
        if g['game_id'] in seen and not explanation: continue
        bonus,_=affinity(g)
        candidates.append((len(matches)*10+bonus,g,price,matches))
    candidates.sort(key=lambda row:(-row[0], row[1]['ordem_original']))
    selected=candidates[:3]
    seen.extend(g['game_id'] for _,g,_,_ in selected)
    if selected:state['library_subject_ids']=['bgg-'+str(g['bgg_id']) for _,g,_,_ in selected]
    result=answer('Estas opções combinam com sua busca. Veja abaixo o motivo de cada indicação.' if selected else 'Não encontrei outras opções com esses filtros. Podemos aumentar o tempo, mudar o número de jogadores ou ajustar o orçamento.')
    result.update(suggestions=['Por que esses jogos?', 'Compare esses jogos', 'Mostrar mais'] if selected else ['Sem limite de tempo','Sem limite de orçamento','Recomeçar'],intent='recommendation',ids=[g['game_id'] for _,g,_,_ in selected],recommendations=[{
        'id':g['game_id'],'name':g['nome'],'price_cents':round(price*100) if price is not None else None,
        'reason':affinity(g)[1]+('Afinidade por '+', '.join(labels.get(t,t) for t in sorted(matches))+'. ' if matches else '')+f"{g['jogadores_min']}–{g['jogadores_max']} jogadores, {g['duracao_minutos']} min, complexidade {g['complexidade']['valor']}/5."} for _,g,price,matches in selected])
    return result
