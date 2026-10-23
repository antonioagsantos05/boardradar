"""Add explicitly fictional local listings without touching real sellers or listings."""
from contextlib import closing
from pathlib import Path
import hashlib
import json
import secrets
import sqlite3
import sys
import time

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'chatbot'))
from radar_ai import accounts,marketplace
from radar_ai.journey import TERMS_VERSION


def main():
    fixtures=json.load(sys.stdin)
    backup=None
    if accounts.DATABASE.exists():
        folder=accounts.DATABASE.parent/'backups'
        folder.mkdir(parents=True,exist_ok=True)
        backup=folder/f'accounts-before-demo-{time.time_ns()}.sqlite3'
        with closing(sqlite3.connect(accounts.DATABASE)) as source,closing(sqlite3.connect(backup)) as target:
            source.backup(target)
    tokens=[]

    def demo_session(email,name,moderator=False):
        with closing(accounts.connect()) as db,db:
            marketplace.migrate(db)
            row=db.execute('SELECT id,name FROM users WHERE email=?',(email,)).fetchone()
            # Fixed reserved fixture identities; refuse to attach these to another account.
            if row and row['name']!=name:
                raise RuntimeError('Reserved demo identity is already in use.')
            uid=row['id'] if row else secrets.token_hex(16)
            if not row:
                salt=secrets.token_hex(16)
                db.execute('INSERT INTO users VALUES (?,?,?,?,?)',(uid,name,email,salt,accounts.password_hash(secrets.token_urlsafe(48),salt)))
            if moderator:
                db.execute('INSERT OR IGNORE INTO user_roles VALUES (?,?)',(uid,'moderator'))
            token=secrets.token_urlsafe(32)
            digest=hashlib.sha256(token.encode()).hexdigest()
            tokens.append(digest)
            db.execute('INSERT INTO sessions VALUES (?,?,?)',(digest,uid,int(time.time())+600))
        return token

    created=[]
    try:
        seller=demo_session('fixtures-seller@boardradar.example','Vendedor de demonstração BoardRadar')
        moderator=demo_session('fixtures-moderator@boardradar.example','Moderação de demonstração BoardRadar',True)
        for item in fixtures:
            existing=marketplace.execute('mine',{},seller)['listings']
            if any(row['title']==item['title'] for row in existing):
                continue
            title=item['title']
            payload={key:item[key] for key in ('edition_id','title','price_cents')}
            payload.update(description='ANÚNCIO FICTÍCIO DE DEMONSTRAÇÃO. Não representa um item disponível para compra. Imagem ilustrativa criada para testar a interface e os fluxos locais.',condition='good',language='Português (exemplo)',region='Cidade de exemplo',components='Componentes fictícios para demonstração; nenhum produto real.',delivery='pickup',negotiable=False,sealed=False,defects='Dados genéricos de teste. Não existe exemplar real.')
            row=next(r for r in marketplace.execute('create',payload,seller)['listings'] if r['title']==title)
            lid=row['id']
            row=next(r for r in marketplace.execute('add_image',{'id':lid,'revision':row['revision'],'content':item['content']},seller)['listings'] if r['id']==lid)
            row=next(r for r in marketplace.execute('submit',{'id':lid,'revision':row['revision'],'terms_accepted':True,'terms_version':TERMS_VERSION},seller)['listings'] if r['id']==lid)
            # Fixture-only review: no real user's pending submission is approved here.
            marketplace.execute('approve',{'id':lid,'revision':row['revision'],'reason':'Fixture sintética explicitamente identificada como DEMO; não corresponde a uma venda real.','edition_confirmed':True},moderator)
            created.append(lid)
    finally:
        with closing(accounts.connect()) as db,db:
            db.executemany('DELETE FROM sessions WHERE token_hash=?',[(token,) for token in tokens])
    print(json.dumps({'created':len(created),'ids':created,'backup':str(backup) if backup else None,'real_listings_changed':False},ensure_ascii=False))


if __name__=='__main__':
    main()
