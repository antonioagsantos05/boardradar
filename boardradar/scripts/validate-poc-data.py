"""Validate exact supplied bytes, counts, IDs and cross-file references."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'


def validate():
    hashes=json.loads((ROOT/'docs/v3/source-hashes.json').read_text(encoding='utf-8'))
    assert {p.name for p in DATA.glob('*.json')}==set(hashes), 'Unexpected or missing source file'
    for name,digest in hashes.items():
        assert hashlib.sha256((DATA/name).read_bytes()).hexdigest()==digest, name+': source modified'
    data={p.stem:json.loads(p.read_text(encoding='utf-8')) for p in DATA.glob('*.json')}
    counts={'games':100,'editions':124,'stores':10,'store_offers':300,'user_listings':100,'users':100,'themes':61,'experiences':27,'franchises':30}
    fields={'games':'game_id','editions':'edition_id','stores':'store_id','store_offers':'offer_id','user_listings':'listing_id','users':'user_id','themes':'id','experiences':'id','franchises':'id'}
    ids={}
    for name,count in counts.items():
        rows=data[name]; ids[name]={r[fields[name]] for r in rows}
        assert len(rows)==len(ids[name])==count, name+': count or duplicate IDs'
    games={g['game_id']:g for g in data['games']}
    assert len({g['bgg_id'] for g in games.values()})==100
    editions={e['edition_id']:e for e in data['editions']}
    for g in games.values():
        assert 1<=g['complexidade']['valor']<=5
        assert 0<g['jogadores_min']<=g['jogadores_max'] and g['duracao_minutos']>0
        assert g['descricao_pt'].strip()
        assert set(g['temas'])<=ids['themes'] and set(g['experiencias'])<=ids['experiences']
        assert any(e['game_id']==g['game_id'] for e in editions.values())
    for e in editions.values(): assert e['game_id'] in games and e['simulada'] is True
    for name in ('store_offers','user_listings'):
        for row in data[name]:
            assert row['game_id'] in games
            assert row['edition_id'] in editions and editions[row['edition_id']]['game_id']==row['game_id']
            assert row['moeda']=='BRL' and row['preco_brl']>0
            if name=='store_offers': assert row['store_id'] in ids['stores'] and row['ficticia'] is True
            else: assert row['seller_user_id'] in ids['users'] and row['ficticio'] is True
    for f in data['franchises']:
        assert set(f['temas'])<=ids['themes'] and set(f['experiencias'])<=ids['experiences']
    profile=data['perfil_exemplo']
    for section in ('gostos','nao_gosto'):
        for key,values in profile[section].items():
            assert set(values)<=ids[{'franquias':'franchises','temas':'themes','experiencias':'experiences'}[key]]
    warnings={
        'listings_without_own_photos':sum(not l['imagens_anuncio'] for l in data['user_listings']),
        'unverified_editions':sum(not e['edicao_oficial_verificada'] for e in editions.values()),
        'descriptions_marked_pending':sum(g['status_traducao_descricao']=='pendente' for g in games.values()),
        'image_urls_verified':False,
        'metadata_translation_notice_stale':True,
    }
    return {'status':'valid','sources':11,'counts':counts,'exact_source_hashes_verified':True,'warnings':warnings}


if __name__=='__main__': print(json.dumps(validate(),ensure_ascii=False,indent=2))
