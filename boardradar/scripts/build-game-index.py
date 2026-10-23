"""Rebuild the derived local SQLite index and metadata coverage report."""
import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
from contextlib import closing

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'chatbot'))
from radar_ai.game_index import INDEX, populate, fingerprint
from radar_ai.catalog import load

INDEX.parent.mkdir(parents=True,exist_ok=True)
handle,temporary=tempfile.mkstemp(dir=INDEX.parent,suffix='.sqlite3')
os.close(handle)
try:
    with closing(sqlite3.connect(temporary)) as connection:
        populate(connection)
        assert connection.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
    os.replace(temporary,INDEX)
finally:
    Path(temporary).unlink(missing_ok=True)
rows=load('library')
report={'source_sha256':fingerprint(),'records':len(rows),'unique_bgg_ids':len({r['bgg_id'] for r in rows}),
        'missing':{key:sum(not r.get(key) for r in rows) for key in ('categories','mechanics','description','complexity','min_players','max_players','max_minutes')},
        'unclassified_format':sum(r['kind']=='unclassified' for r in rows),
        'limits':['Historical snapshots, not live BGG data','No official rules or commercial offers in this index','Unknown product format is not confirmed base game']}
destination=ROOT/'docs/v2/catalog-coverage.json'
destination.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,ensure_ascii=True))
