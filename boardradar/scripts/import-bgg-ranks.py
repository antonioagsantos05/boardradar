"""Import only the supplied ranks CSV. No enrichment from historical datasets."""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import shutil
import zipfile

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'src/data'
COLUMNS=['id','name','yearpublished','rank','bayesaverage','average','usersrated','is_expansion','abstracts_rank','cgs_rank','childrensgames_rank','familygames_rank','partygames_rank','strategygames_rank','thematic_rank','wargames_rank']


def parse_archive(path):
    with zipfile.ZipFile(path) as archive:
        entries=[entry for entry in archive.infolist() if Path(entry.filename).name=='boardgames_ranks.csv']
        if len(entries)!=1 or entries[0].file_size>100_000_000:
            raise ValueError('Expected one bounded boardgames_ranks.csv')
        raw=archive.read(entries[0])
    reader=csv.DictReader(io.StringIO(raw.decode('utf-8-sig')))
    if reader.fieldnames!=COLUMNS:
        raise ValueError('Unexpected CSV columns')
    rows=[];ids=set()
    for number,r in enumerate(reader,2):
        if None in r or any(value is None for value in r.values()):
            raise ValueError(f'Malformed CSV row {number}')
        gid=int(r['id']);name=r['name'].strip()
        if gid<=0 or gid in ids or not name or r['is_expansion'] not in ('0','1'):
            raise ValueError(f'Invalid identity/format at row {number}')
        ids.add(gid)
        def integer(key):
            value=int(r[key]) if r[key] else 0
            return value or None
        def rating(key):
            value=float(r[key]) if r[key] else 0
            if not 0<=value<=10:raise ValueError(f'Invalid rating at row {number}')
            return value or None
        rows.append([gid,name,integer('yearpublished'),integer('rank'),rating('bayesaverage'),rating('average'),int(r['usersrated']),int(r['is_expansion']),*[integer(key) for key in COLUMNS[8:]]])
    if not rows:raise ValueError('Empty dataset')
    return rows,raw


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('archive',type=Path)
    args=parser.parse_args()
    rows,raw=parse_archive(args.archive)
    identities_path=DATA/'catalog-identities.json'
    if identities_path.exists():
        identities=json.loads(identities_path.read_text(encoding='utf-8'))
    else:
        identities={'ids':{},'slugs':{}}
        legacy=json.loads((DATA/'library.json').read_text(encoding='utf-8-sig'))
        games=json.loads((DATA/'games.json').read_text(encoding='utf-8-sig'))
        for record in legacy:
            bid=str(record['bgg_id'])
            identities['slugs'][record['slug']]=bid
            if record.get('curated_game_id'):identities['ids'][record['curated_game_id']]=bid
        for game in games:
            bid=game.get('bgg_id') or identities['ids'].get(game['id'])
            if bid:
                identities['ids'][game['id']]=str(bid)
                identities['slugs'][game['slug']]=str(bid)
        # Identity references only; no legacy game attributes are copied.
        identities_path.write_text(json.dumps(identities,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8')
    source=DATA/'sources'/args.archive.name
    source.parent.mkdir(parents=True,exist_ok=True)
    if source.resolve()!=args.archive.resolve():shutil.copy2(args.archive,source)
    destination=DATA/'bgg-ranks.json'
    temporary=destination.with_suffix('.tmp')
    temporary.write_text(json.dumps(rows,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8')
    temporary.replace(destination)
    manifest={'active_source':'bgg-ranks','archive':str(source.relative_to(ROOT)).replace('\\','/'),'archive_sha256':hashlib.sha256(args.archive.read_bytes()).hexdigest(),'csv_sha256':hashlib.sha256(raw).hexdigest(),'columns':COLUMNS,'records':len(rows),'unique_ids':len({r[0] for r in rows}),'base_games':sum(r[7]==0 for r in rows),'expansions':sum(r[7]==1 for r in rows),'unranked':sum(r[3] is None for r in rows),'names_with_replacement_character':sum('\ufffd' in r[1] for r in rows),'missing_fields':['players','duration','mechanics','description','images','complexity','commercial_editions','prices'],'legacy_metadata_used':False}
    (DATA/'bgg-ranks-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(manifest,ensure_ascii=True))


if __name__=='__main__':main()
