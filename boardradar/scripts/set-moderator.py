"""Explicit local operator action; never grants a role through registration/API."""
import argparse
from contextlib import closing
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'chatbot'))
from radar_ai.accounts import connect
from radar_ai.marketplace import migrate

parser=argparse.ArgumentParser();parser.add_argument('email');parser.add_argument('--revoke',action='store_true');args=parser.parse_args()
with closing(connect()) as db,db:
    migrate(db)
    row=db.execute('SELECT id FROM users WHERE email=?',(args.email.strip().casefold(),)).fetchone()
    if not row:raise SystemExit('Conta local não encontrada.')
    if args.revoke:db.execute('DELETE FROM user_roles WHERE user_id=?',(row['id'],))
    else:db.execute("INSERT OR IGNORE INTO user_roles VALUES (?,'moderator')",(row['id'],))
print('Permissão local atualizada. Acesse /moderacao para revisar os anúncios enviados.')
