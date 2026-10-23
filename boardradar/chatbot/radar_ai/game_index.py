"""Local, derived SQLite index. Imported metadata is not rule or offer evidence."""
from functools import lru_cache
from hashlib import sha256
from pathlib import Path
import json
import sqlite3
from contextlib import closing
from .catalog import DATA
from .nlp.normalizer import name_key

INDEX = DATA.parents[1] / '.local' / 'games.sqlite3'
VERSION = '1'


def fingerprint():
    return sha256((DATA / 'library.json').read_bytes()).hexdigest()


def populate(connection):
    rows = json.loads((DATA / 'library.json').read_text(encoding='utf-8-sig'))
    connection.executescript('''
        CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE games (id TEXT PRIMARY KEY, name TEXT NOT NULL, terms TEXT NOT NULL,
            min_players INTEGER, max_players INTEGER, duration INTEGER,
            complexity REAL, kind TEXT NOT NULL, payload TEXT NOT NULL);
        CREATE INDEX games_constraints ON games(max_players, duration);
    ''')
    connection.executemany('INSERT INTO games VALUES (?,?,?,?,?,?,?,?,?)', [
        (r['id'], r['name'], name_key(' '.join([r['name'], *r['aliases'], *r['categories'], *r['mechanics']])),
         r['min_players'], r['max_players'], r['max_minutes'], r['complexity'], r['kind'], json.dumps(r, ensure_ascii=False))
        for r in rows])
    connection.executemany('INSERT INTO metadata VALUES (?,?)', [('sha256', fingerprint()), ('version', VERSION)])
    connection.commit()


@lru_cache(maxsize=1)
def persisted_index_valid():
    if not INDEX.exists():
        return False
    try:
        with closing(sqlite3.connect(INDEX.as_uri() + '?mode=ro', uri=True)) as connection:
            meta = dict(connection.execute('SELECT key,value FROM metadata'))
            return meta == {'sha256': fingerprint(), 'version': VERSION}
    except sqlite3.Error:
        return False


def search(terms=(), *, players=None, duration=None, complexity=None, limit=3):
    """Parameterized, bounded reads. Missing constraints never count as matching."""
    if type(limit) is not int or not 1 <= limit <= 24:
        raise ValueError('Invalid result limit')
    for value, maximum in ((players,20),(duration,10000),(complexity,5)):
        if value is not None and (type(value) not in (int,float) or not 0 < value <= maximum):
            raise ValueError('Invalid constraint')
    if len(terms)>8 or any(not isinstance(t,str) or len(t)>100 for t in terms):
        raise ValueError('Invalid search terms')
    connection = sqlite3.connect(INDEX.as_uri() + '?mode=ro', uri=True) if persisted_index_valid() else sqlite3.connect(':memory:')
    try:
        if not persisted_index_valid():
            populate(connection)
        clauses = ["kind != 'boardgameexpansion'"]
        args = []
        for term in terms:
            clauses.append("(' ' || terms || ' ') LIKE ? ESCAPE '\\'")
            escaped = name_key(term).replace('\\','\\\\').replace('%','\\%').replace('_','\\_')
            args.append('% '+escaped+' %')
        if players is not None:
            clauses.append('min_players <= ? AND max_players >= ?');args.extend([players,players])
        if duration is not None:
            clauses.append('duration > 0 AND duration <= ?');args.append(duration)
        if complexity is not None:
            clauses.append('complexity > 0 AND complexity <= ?');args.append(complexity)
        where=' AND '.join(clauses)
        total=connection.execute('SELECT count(*) FROM games WHERE '+where,args).fetchone()[0]
        rows=connection.execute('SELECT payload FROM games WHERE '+where+' ORDER BY name COLLATE NOCASE,id LIMIT ?',[*args,limit]).fetchall()
        return total,[json.loads(row[0]) for row in rows]
    finally:
        connection.close()
