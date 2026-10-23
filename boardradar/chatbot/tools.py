"""Allowlisted, read-only structured tools; validation stays outside the LLM."""
from datetime import datetime, timezone
from engine import GAMES, OFFERS, load, normalize, rank, validate_state
from knowledge import retrieve, citation


def game_by_id(game_id):
    game=next((g for g in GAMES if g['id']==game_id),None)
    if not game:
        raise ValueError('Jogo inexistente')
    return game


def offers_for(edition_id):
    game=next((g for g in GAMES if any(e['id']==edition_id for e in g['editions'])),None)
    if not game:
        raise ValueError('Edição inexistente')
    now=datetime.now(timezone.utc)
    max_age=load('policy')['max_offer_age_days']*86400
    offers=[]
    for offer in OFFERS:
        if offer['edition_id'] != edition_id:
            continue
        age=(now-datetime.fromisoformat(offer['checked_at'].replace('Z','+00:00'))).total_seconds()
        offers.append({**offer,'fresh':0<=age<=max_age,'shipping_included':False,'eligible':offer['availability']=='in_stock' and 0<=age<=max_age})
    return sorted(offers,key=lambda o:(not o['eligible'],o['price_cents']))


class ToolRouter:
    allowed={'search_games','recommend_games','get_game','get_offers','compare_games','retrieve','map_preferences'}

    def execute(self,name,args):
        if name not in self.allowed or not isinstance(args,dict):
            raise ValueError('Ferramenta não permitida')
        if name=='get_game':
            if set(args)!={'game_id'}:raise ValueError('Argumentos inválidos')
            return game_by_id(args['game_id'])
        if name=='get_offers':
            if set(args)!={'edition_id'}:raise ValueError('Argumentos inválidos')
            return offers_for(args['edition_id'])
        if name=='compare_games':
            if set(args)!={'game_ids'} or not isinstance(args['game_ids'],list) or not 2<=len(args['game_ids'])<=3:raise ValueError('Comparação exige 2 ou 3 jogos')
            return [game_by_id(i) for i in dict.fromkeys(args['game_ids'])]
        if name in ('search_games','recommend_games'):
            if set(args)-{'state','query','limit'}:raise ValueError('Argumentos inválidos')
            limit=args.get('limit',6)
            if type(limit)!=int or not 1<=limit<=12:raise ValueError('Limite inválido')
            state=validate_state(args.get('state'))
            results=rank(state)
            query=args.get('query','')
            if not isinstance(query,str) or len(query)>200:raise ValueError('Busca inválida')
            if query:results=[r for r in results if normalize(query) in normalize(r['name']+' '+game_by_id(r['id'])['category'])]
            return results[:limit]
        if name=='retrieve':
            if set(args)-{'query','game_id','edition_id','official_only'}:raise ValueError('Argumentos inválidos')
            if not isinstance(args.get('query'),str) or len(args['query'])>1000:raise ValueError('Busca inválida')
            gid=args.get('game_id');eid=args.get('edition_id')
            if gid:game_by_id(gid)
            if eid and (not gid or not any(e['id']==eid for e in game_by_id(gid)['editions'])):raise ValueError('Edição não pertence ao jogo')
            return [citation(h) for h in retrieve(**args)]
        if name=='map_preferences':
            ids=args.get('media_ids',[])
            if set(args)!={'media_ids'} or not isinstance(ids,list) or len(ids)>10 or any(not isinstance(i,str) for i in ids):raise ValueError('Obras inválidas')
            works=load('media-works');relations=load('media-game-relations')
            if any(i not in {m['id'] for m in works} for i in ids):raise ValueError('Obra não cadastrada')
            return {'works':[m for m in works if m['id'] in ids],'relations':[r for r in relations if r['media_id'] in ids]}
