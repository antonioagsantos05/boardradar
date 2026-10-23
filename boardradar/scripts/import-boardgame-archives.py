"""Merge user-supplied snapshots by BGG ID; never import personal play records."""
import argparse
import collections
import csv
from datetime import datetime,timezone
import hashlib
import html
import io
import json
from pathlib import Path
import re
import unicodedata
import zipfile

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'src/data'


def key(value):
    return re.sub('[^a-z0-9]','',unicodedata.normalize('NFKD',value).encode('ascii','ignore').decode().lower())


def text(value):
    return '' if value is None or str(value).strip().upper() in ('NA','N/A','NULL','NAN','NONE') else html.unescape(str(value)).strip()


def integer(value):
    try:return int(value)
    except (ValueError,TypeError):return None


def number(value):
    try:
        n=float(value)
        return n if 0<=n<1e9 else None
    except (ValueError,TypeError):return None


def values(value):return [s.strip() for s in text(value).split(',') if s.strip()]


def csv_record(row):
    return {'bgg_id':row['game_id'],'name':text(row['name']),'aliases':[],
            'description':text(row['description']),'year':integer(row['year_published']),
            'min_players':integer(row['min_players']),'max_players':integer(row['max_players']),
            'min_minutes':integer(row['min_playtime']),'max_minutes':integer(row['max_playtime']),
            'min_age':integer(row['min_age']),'categories':values(row['category']),
            'mechanics':values(row['mechanic']),'designers':values(row['designer']),
            'publishers':values(row['publisher']),'rating':number(row['average_rating']),
            'rating_count':integer(row['users_rated']),'complexity':None,'complexity_votes':None,
            'image_url':text(row['image']),'thumbnail_url':text(row['thumbnail']),
            'kind':'unclassified','sources':['bgg_dataset_csv'],'field_sources':{}}


def api_record(item):
    attr=lambda name:item.get(name,[{}])[0].get('_attributes',{}).get('value')
    txt=lambda name:' '.join(item.get(name,[{}])[0].get('_text',[]))
    links=lambda kind:[r['_attributes']['value'] for r in item.get('link',[]) if r['_attributes'].get('type')==kind]
    names=[r['_attributes'] for r in item.get('name',[])]
    ratings=item.get('statistics',[{}])[0].get('ratings',[{}])[0]
    rating=lambda name:ratings.get(name,[{}])[0].get('_attributes',{}).get('value')
    return {'bgg_id':item['_attributes']['id'],
            'name':next((r['value'] for r in names if r.get('type')=='primary'),names[0]['value']),
            'aliases':[r['value'] for r in names if r.get('type')=='alternate'],
            'description':text(txt('description')),'year':integer(attr('yearpublished')),
            'min_players':integer(attr('minplayers')),'max_players':integer(attr('maxplayers')),
            'min_minutes':integer(attr('minplaytime')),'max_minutes':integer(attr('maxplaytime')),
            'min_age':integer(attr('minage')),'categories':links('boardgamecategory'),
            'mechanics':links('boardgamemechanic'),'designers':links('boardgamedesigner'),
            'publishers':links('boardgamepublisher'),'rating':number(rating('average')),
            'rating_count':integer(rating('usersrated')),'complexity':number(rating('averageweight')),
            'complexity_votes':integer(rating('numweights')),'image_url':txt('image'),
            'thumbnail_url':txt('thumbnail'),'kind':item['_attributes']['type'],
            'sources':['boardgames_api_json'],'field_sources':{}}


def merge_records(csv_rows,api_rows):
    result={};conflicts=[]
    for incoming in [*csv_rows,*api_rows]:
        gid=incoming['bgg_id']
        if not re.fullmatch(r'\d+',gid):raise ValueError('Invalid BGG ID')
        sid=incoming['sources'][0]
        if gid not in result:
            result[gid]={**incoming,'field_sources':{k:sid for k,v in incoming.items() if v not in (None,'',[]) and k not in ('sources','field_sources')}}
            continue
        current=result[gid]
        for field,value in incoming.items():
            if field in ('bgg_id','sources','field_sources'):continue
            if value in (None,'',[]):continue
            if field=='aliases':value=list(dict.fromkeys([*current.get(field,[]),*value]))
            if current.get(field) not in (None,'',[]) and current[field]!=value:
                conflicts.append({'bgg_id':gid,'field':field,'csv':current[field],'api':value})
            current[field]=value;current['field_sources'][field]=sid
        current['sources']=list(dict.fromkeys([*current['sources'],sid]))
    return result,conflicts


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--csv-zip',type=Path,required=True)
    parser.add_argument('--api-zip',type=Path,required=True)
    args=parser.parse_args()
    with zipfile.ZipFile(args.csv_zip) as z:
        name=next(n for n in z.namelist() if n.endswith('/data/board_games_2023.csv'))
        csv_rows=[csv_record(r) for r in csv.DictReader(io.TextIOWrapper(z.open(name),encoding='utf-8-sig',newline=''))]
    api_rows=[]
    with zipfile.ZipFile(args.api_zip) as z:
        for name in sorted(z.namelist()):
            if not re.fullmatch(r'[^/]+/boardgames/boardgame-\d+\.json',name):continue
            for wrapper in json.loads(z.read(name)).get('items',[]):
                api_rows.extend(api_record(i) for i in wrapper.get('item',[]))
    merged,conflicts=merge_records(csv_rows,api_rows)
    games=json.loads((DATA/'games.json').read_text(encoding='utf-8-sig'))
    primary=collections.defaultdict(list)
    for r in merged.values():primary[key(r['name'])].append(r)
    matched=[];review=[]
    for game in games:
        game.pop('bgg_id',None)
        candidates=primary.get(key(game['name']),[])
        if len(candidates)==1 and candidates[0]['kind']!='boardgameexpansion':
            record=candidates[0];record['curated_game_id']=game['id']
            game['bgg_id']=record['bgg_id'];matched.append({'game_id':game['id'],'bgg_id':record['bgg_id'],'name':game['name']})
        elif len(candidates)>1:review.append({'game_id':game['id'],'name':game['name'],'candidate_ids':[r['bgg_id'] for r in candidates]})
    for r in merged.values():
        slug=re.sub('[^a-z0-9]+','-',unicodedata.normalize('NFKD',r['name']).encode('ascii','ignore').decode().lower()).strip('-')[:100]
        r.update(id='bgg-'+r['bgg_id'],slug='bgg-'+r['bgg_id']+'-'+slug,bgg_url='https://boardgamegeek.com/boardgame/'+r['bgg_id'],metadata_status='external_snapshot_unverified')
        for field in ('image_url','thumbnail_url'):
            if r[field].startswith('//'):r[field]='https:'+r[field]
            if not r[field].startswith('https://'):r[field]=''
    rows=sorted(merged.values(),key=lambda r:int(r['bgg_id']))
    DATA.joinpath('library.json').write_text(json.dumps(rows,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8')
    DATA.joinpath('games.json').write_text(json.dumps(games,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    def snapshot(path):return {'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
    report={'imported_at':datetime.now(timezone.utc).date().isoformat(),'csv_rows':len(csv_rows),'api_rows':len(api_rows),
            'unique_bgg_ids':len(rows),'overlapping_ids':len(set(r['bgg_id'] for r in csv_rows)&set(r['bgg_id'] for r in api_rows)),
            'kinds':dict(collections.Counter(r['kind'] for r in rows)),
            'source_files':[snapshot(args.csv_zip),snapshot(args.api_zip)],'curated_matches':matched,'ambiguous_matches':review,
            'conflict_count':len(conflicts),'field_precedence':'API snapshot wins populated fields; missing values retain CSV. Not a claim of current accuracy.',
            'limits':['No personal play records imported','No license for third-party data inferred from source-code package licenses','Images are references only; no download or automatic embedding','No prices or stock imported','Unclassified CSV items are not assumed base games','Snapshots are not official rule evidence']}
    DATA.joinpath('library-manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    out=ROOT/'docs/catalog-import';out.mkdir(parents=True,exist_ok=True)
    (out/'field-conflicts.json').write_text(json.dumps(conflicts,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:report[k] for k in ('csv_rows','api_rows','unique_bgg_ids','overlapping_ids','kinds','conflict_count')}))


if __name__=='__main__':main()
