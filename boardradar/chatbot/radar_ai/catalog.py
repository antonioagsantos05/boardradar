"""Read-only catalogue snapshots and reference integrity."""
from dataclasses import dataclass
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'data'


def raw(name):
    return json.loads((DATA / f'{name}.json').read_text(encoding='utf-8-sig'))


def load(name):
    if name == 'policy':
        return json.loads((ROOT / 'src/config/policy.json').read_text(encoding='utf-8'))
    if name == 'games':
        editions=raw('editions')
        return [dict(id=g['game_id'],slug='bgg-'+str(g['bgg_id']),name=g['nome'],aliases=[],
            category=g['categorias'][0] if g['categorias'] else 'Jogo de tabuleiro',
            players={'min':g['jogadores_min'],'max':g['jogadores_max']},duration=g['duracao_minutos'],
            complexity=g['complexidade']['valor'],tags=g['temas']+g['experiencias']+g['mecanicas'],
            description=g['descricao_pt'],editorialQuality=0,provenance={'source':g['origem'],'status':'editorial_poc'},
            editions=[{'id':e['edition_id'],'name':e['nome_edicao'],'language':e['idioma'],'type':e['tipo']} for e in editions if e['game_id']==g['game_id']]) for g in raw('games')]
    if name == 'offers':
        return [dict(id=o['offer_id'],edition_id=o['edition_id'],store_id=o['store_id'],price_cents=round(o['preco_brl']*100),currency=o['moeda'],condition=o['condicao'],availability=o['disponibilidade'],checked_at=raw('metadata')['gerado_em']+'T00:00:00Z',is_demo=o['ficticia']) for o in raw('store_offers')]
    if name == 'stores':
        return [dict(id=s['store_id'],name=s['nome'],is_demo=s['ficticia']) for s in raw('stores')]
    if name in ('videogames','game-relations','media-works','media-game-relations','library','knowledge-chunks','knowledge-sources'):
        return []  # No legacy facts are allowed to enter the v3 catalogue.
    return raw(name)


def number(value):
    return type(value) in (int,float) and math.isfinite(value)


@dataclass
class Catalog:
    games: list
    offers: list
    stores: list
    videos: list
    relations: list

    def integrity_errors(self):
        errors=[]
        for name,rows in [('games',self.games),('offers',self.offers),('stores',self.stores),('videos',self.videos)]:
            ids=[r.get('id') for r in rows if isinstance(r,dict)]
            if len(ids)!=len(rows) or any(not isinstance(i,str) or not i for i in ids) or len(set(ids))!=len(ids):
                errors.append(name+':invalid_or_duplicate_ids')
        if errors:return sorted(set(errors))
        editions=[]
        for g in self.games:
            try:
                p=g['players']
                if not all(type(p[k])==int and p[k]>0 for k in ('min','max')) or p['min']>p['max']:raise ValueError()
                if not number(g['duration']) or g['duration']<=0 or not number(g['complexity']) or not 1<=g['complexity']<=5:raise ValueError()
                if not number(g['editorialQuality']) or not 0<=g['editorialQuality']<=1:raise ValueError()
                if any(not isinstance(g[k],str) or not g[k] for k in ('name','category','description')) or not isinstance(g['tags'],list) or any(not isinstance(t,str) for t in g['tags']):raise ValueError()
                if not g['editions']:raise ValueError()
                for e in g['editions']:
                    if not isinstance(e['id'],str) or not e['id'] or e.get('type') not in ('base','expansion','colecionador','importada','premium'):raise ValueError()
                    editions.append(e['id'])
            except (KeyError,TypeError,ValueError):
                errors.append('games:invalid_metadata')
        if len(editions)!=len(set(editions)):errors.append('editions:duplicate_ids')
        for video in self.videos:
            if not isinstance(video.get('tags'),list) or any(not isinstance(t,str) for t in video['tags']):errors.append('videos:invalid_metadata')
        if errors:return sorted(set(errors))
        store_ids={s.get('id') for s in self.stores if isinstance(s,dict)}
        for offer in self.offers:
            if not isinstance(offer,dict) or offer.get('edition_id') not in editions or offer.get('store_id') not in store_ids:
                errors.append('offers:orphan_reference')
        game_ids={g.get('id') for g in self.games if isinstance(g,dict)}
        video_ids={v.get('id') for v in self.videos if isinstance(v,dict)}
        for relation in self.relations:
            if not isinstance(relation,dict) or relation.get('game_id') not in game_ids or relation.get('videogame_id') not in video_ids or not number(relation.get('weight')) or not 0<=relation['weight']<=1:
                errors.append('relations:invalid_reference_or_weight')
        return sorted(set(errors))


DEFAULT_CATALOG=Catalog(load('games'),load('offers'),load('stores'),load('videogames'),load('game-relations'))
