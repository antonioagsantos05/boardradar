"""Normalize the approved 1,000-game JSON without importing any other metadata."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil
from urllib.parse import urlsplit

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'src/data'


def positive(value):
    return value if type(value) in (int,float) and math.isfinite(value) and value>0 else None


def image_url(value):
    if not isinstance(value,str):return None
    parsed=urlsplit(value)
    return value if parsed.scheme=='https' and parsed.hostname=='cf.geekdo-images.com' and not parsed.username and not parsed.password else None


def normalize(record,date):
    gid=record['id']
    if type(gid) is not int or gid<=0 or not isinstance(record.get('name'),str):raise ValueError('Invalid game identity')
    raw=record.get('raw',{});rating=record.get('rating',{})
    def strings(key):
        value=record.get(key,[])
        if not isinstance(value,list) or any(not isinstance(v,str) for v in value):raise ValueError('Invalid list: '+key)
        return value
    players=[positive(record.get('minPlayers')),positive(record.get('maxPlayers'))]
    if all(players) and players[0]>players[1]:raise ValueError('Invalid player interval')
    return {'id':f'bgg-{gid}','bgg_id':str(gid),'slug':f'bgg-{gid}','name':record['name'].strip(),'year':positive(record.get('yearPublished')),'description':record.get('description',''),'aliases':[],
            'min_players':players[0],'max_players':players[1],'min_minutes':positive(raw.get('details.minplaytime')) or positive(record.get('playingTime')),'max_minutes':positive(raw.get('details.maxplaytime')) or positive(record.get('playingTime')),'min_age':positive(record.get('minAge')),
            'categories':strings('categories'),'mechanics':strings('mechanics'),'designers':strings('designers'),'publishers':strings('publishers'),
            'rating':positive(rating.get('average')),'bayes_average':positive(rating.get('bayesAverage')),'rating_count':positive(raw.get('stats.usersrated')),
            'complexity':positive(rating.get('averageWeight')),'complexity_votes':positive(raw.get('stats.numweights')),'rank':positive(raw.get('stats.subtype.boardgame.pos')),
            'kind':raw.get('game.type') if raw.get('game.type') in ('boardgame','boardgameexpansion') else 'unclassified',
            'sources':['bgg_details_2019'],'details_date':date,'rating_date':date,'image':image_url(record.get('image')),'thumbnail':image_url(record.get('thumbnail')),
            'bgg_url':f'https://boardgamegeek.com/boardgame/{gid}'}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('source',type=Path);args=parser.parse_args()
    payload=json.loads(args.source.read_text(encoding='utf-8-sig'))
    date=payload['metadata']['sourceDate'];rows=[normalize(r,date) for r in payload['games']]
    if len({r['id'] for r in rows})!=len(rows):raise ValueError('Duplicate BGG IDs')
    ranks=json.loads((DATA/'bgg-ranks.json').read_text(encoding='utf-8'))
    rank_ids={str(row[0]) for row in ranks}
    source=DATA/'sources'/args.source.name
    source.parent.mkdir(parents=True,exist_ok=True)
    if args.source.resolve()!=source.resolve():shutil.copy2(args.source,source)
    temporary=DATA/'bgg-details.tmp';temporary.write_text(json.dumps(rows,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8');temporary.replace(DATA/'bgg-details.json')
    report={'active_sources':['boardgames_ranks_2026-10-20.zip','bgg_1000_jogos.json'],'join_key':'BGG ID only','details_date':date,'rankings_date':'2026-10-20','details_sha256':hashlib.sha256(args.source.read_bytes()).hexdigest(),'rank_records':len(ranks),'detail_records':len(rows),'matched_ids':sum(r['bgg_id'] in rank_ids for r in rows),'details_only_ids':[r['bgg_id'] for r in rows if r['bgg_id'] not in rank_ids],'unique_games':len(rank_ids|{r['bgg_id'] for r in rows}),'old_metadata_used':False,'missing':{key:sum(r.get(key) in (None,'',[]) for r in rows) for key in ('categories','mechanics','description','max_minutes','min_age','image')},'notes':['Missing or zero values remain unknown.','Historical rating and 2026 rating remain separate.','Image URLs are historical and may fail; UI has a fallback.','Legacy identity aliases preserve existing links, not old game facts.']}
    (DATA/'active-catalog.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=True))


if __name__=='__main__':main()
