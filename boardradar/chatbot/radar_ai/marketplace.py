"""Local listing drafts, private photos and revision-bound moderation."""
import base64
import secrets
import time
import re
from contextlib import closing
from .accounts import connect, user_for, text, AccountError
from .catalog import DEFAULT_CATALOG
from .nlp.normalizer import name_key
from .journey import TERMS_VERSION,notify_listing

STATES=('draft','pending_review','active','reserved','paused','sold','rejected','removed','expired')


def migrate(db):
    db.executescript('''
        CREATE TABLE IF NOT EXISTS marketplace_migrations(version INTEGER PRIMARY KEY);
        CREATE TABLE IF NOT EXISTS user_roles(user_id TEXT PRIMARY KEY REFERENCES users(id),role TEXT NOT NULL CHECK(role='moderator'));
        CREATE TABLE IF NOT EXISTS marketplace_games(id TEXT PRIMARY KEY,name TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS marketplace_editions(id TEXT PRIMARY KEY,game_id TEXT NOT NULL REFERENCES marketplace_games(id),name TEXT NOT NULL,language TEXT NOT NULL,verified INTEGER NOT NULL DEFAULT 0);
        CREATE TABLE IF NOT EXISTS listings(
            id TEXT PRIMARY KEY,seller_id TEXT NOT NULL REFERENCES users(id),
            edition_id TEXT NOT NULL REFERENCES marketplace_editions(id),title TEXT NOT NULL,
            description TEXT NOT NULL,condition TEXT NOT NULL CHECK(condition IN ('new','like_new','good','fair')),
            language TEXT NOT NULL,price_cents INTEGER NOT NULL CHECK(price_cents>0),
            currency TEXT NOT NULL CHECK(currency='BRL'),region TEXT NOT NULL,components TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('draft','pending_review','active','reserved','paused','sold','rejected','removed','expired')),
            revision INTEGER NOT NULL DEFAULT 1,created_at INTEGER NOT NULL,updated_at INTEGER NOT NULL);
        CREATE INDEX IF NOT EXISTS listings_edition_status_price ON listings(edition_id,status,price_cents);
        CREATE INDEX IF NOT EXISTS listings_seller ON listings(seller_id,updated_at);
        CREATE TABLE IF NOT EXISTS moderation_actions(id INTEGER PRIMARY KEY,listing_id TEXT NOT NULL REFERENCES listings(id),actor_id TEXT NOT NULL REFERENCES users(id),action TEXT NOT NULL,previous_status TEXT,new_status TEXT,reason TEXT NOT NULL,created_at INTEGER NOT NULL);
        INSERT OR IGNORE INTO marketplace_migrations VALUES(1);
        CREATE TABLE IF NOT EXISTS listing_images(id TEXT PRIMARY KEY,listing_id TEXT NOT NULL REFERENCES listings(id),content BLOB NOT NULL,created_at INTEGER NOT NULL);
        CREATE INDEX IF NOT EXISTS images_listing ON listing_images(listing_id);
        INSERT OR IGNORE INTO marketplace_migrations VALUES(2);
        CREATE TABLE IF NOT EXISTS listing_details(listing_id TEXT PRIMARY KEY REFERENCES listings(id),delivery TEXT NOT NULL,negotiable INTEGER NOT NULL,sealed INTEGER NOT NULL,defects TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS listing_acceptances(listing_id TEXT NOT NULL REFERENCES listings(id),revision INTEGER NOT NULL,user_id TEXT NOT NULL REFERENCES users(id),version TEXT NOT NULL,accepted_at INTEGER NOT NULL,PRIMARY KEY(listing_id,revision));
        CREATE TABLE IF NOT EXISTS conversations(id TEXT PRIMARY KEY,listing_id TEXT NOT NULL REFERENCES listings(id),buyer_id TEXT NOT NULL REFERENCES users(id),seller_id TEXT NOT NULL REFERENCES users(id),UNIQUE(listing_id,buyer_id));
        CREATE TABLE IF NOT EXISTS messages(id INTEGER PRIMARY KEY,conversation_id TEXT NOT NULL REFERENCES conversations(id),author_id TEXT NOT NULL REFERENCES users(id),body TEXT NOT NULL,created_at INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS listing_reports(id INTEGER PRIMARY KEY,listing_id TEXT NOT NULL REFERENCES listings(id),reporter_id TEXT NOT NULL REFERENCES users(id),reason TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'open',decision TEXT,created_at INTEGER NOT NULL,UNIQUE(listing_id,reporter_id));
        CREATE TABLE IF NOT EXISTS catalog_requests(id INTEGER PRIMARY KEY,user_id TEXT NOT NULL REFERENCES users(id),name TEXT NOT NULL,edition TEXT NOT NULL,notes TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'pending',decision TEXT,created_at INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS marketplace_events(user_id TEXT NOT NULL,kind TEXT NOT NULL,created_at INTEGER NOT NULL);
    ''')
    # Preserve references; refresh labels without replacing records or user data.
    for game in DEFAULT_CATALOG.games:
        db.execute('INSERT INTO marketplace_games VALUES (?,?) ON CONFLICT(id) DO UPDATE SET name=excluded.name',(game['id'],game['name']))
        for edition in game['editions']:
            db.execute('INSERT INTO marketplace_editions(id,game_id,name,language) VALUES (?,?,?,?) ON CONFLICT(id) DO UPDATE SET name=excluded.name,language=excluded.language',
                       (edition['id'],game['id'],edition['name'],edition['language']))


def validate(data):
    values={key:text(data,key,minimum,maximum) for key,minimum,maximum in (
        ('edition_id',1,80),('title',3,120),('description',10,3000),('language',2,80),('region',2,120),('components',2,1000))}
    price=data.get('price_cents')
    if type(price) is not int or not 1<=price<=100000000:raise AccountError('Preço inválido. Informe centavos inteiros.')
    if data.get('condition') not in ('new','like_new','good','fair'):raise AccountError('Estado de conservação inválido.')
    if re.search(r'[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}|(?:\+?\d[\s().-]*){10,}', ' '.join(values.values())+' '+str(data.get('defects',''))):raise AccountError('Remova telefone e e-mail do anúncio público. Use as mensagens protegidas.')
    if data.get('delivery','unspecified') not in ('unspecified','pickup','shipping','both'):raise AccountError('Entrega inválida.')
    if type(data.get('sealed',False)) is not bool or type(data.get('negotiable',False)) is not bool:raise AccountError('Condição inválida.')
    if data.get('sealed') and data.get('condition')!='new':raise AccountError('Um jogo lacrado deve ser novo.')
    text({'defects':data.get('defects','Não informado')},'defects',2,1000)
    return {**values,'price_cents':price,'condition':data['condition']}


def audit(db,lid,uid,action,before,after,reason=''):
    db.execute('INSERT INTO moderation_actions(listing_id,actor_id,action,previous_status,new_status,reason,created_at) VALUES (?,?,?,?,?,?,?)',
               (lid,uid,action,before,after,reason,int(time.time())))


def execute(action,data,token=''):
    if not isinstance(data,dict):raise AccountError('Dados inválidos.')
    with closing(connect()) as db,db:
        migrate(db)
        if action=='browse':return browse(db,data)
        if action=='public_detail':
            lid=text(data,'id',1,80)
            rows=browse(db,{},listing_id=lid)['listings']
            if not rows:raise AccountError('Anuncio indisponivel.',404)
            return {'listing':rows[0]}
        if action=='public_image':
            image_id=text(data,'image_id',1,80)
            image=db.execute("SELECT i.content FROM listing_images i JOIN listings l ON l.id=i.listing_id WHERE i.id=? AND l.status='active' AND EXISTS(SELECT 1 FROM listing_acceptances a WHERE a.listing_id=l.id AND a.version=?)",(image_id,TERMS_VERSION)).fetchone()
            if image is None:raise AccountError('Foto não encontrada.',404)
            return {'content':base64.b64encode(image['content']).decode('ascii')}
        user=user_for(db,token)
        moderator=db.execute('SELECT 1 FROM user_roles WHERE user_id=?',(user['id'],)).fetchone() is not None
        if action in ('inquire','reply','inbox','report','reports','resolve_report','request_game','requests','decide_request'):
            return community_action(db,user,moderator,action,data)
        if action in ('create','update'):
            values=validate(data)
            if not db.execute('SELECT 1 FROM marketplace_editions WHERE id=?',(values['edition_id'],)).fetchone():raise AccountError('Edição não cadastrada.')
            if action=='create':
                lid=secrets.token_hex(16);now=int(time.time())
                db.execute('INSERT INTO listings(id,seller_id,edition_id,title,description,condition,language,price_cents,currency,region,components,status,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                           (lid,user['id'],values['edition_id'],values['title'],values['description'],values['condition'],values['language'],values['price_cents'],'BRL',values['region'],values['components'],'draft',now,now))
                audit(db,lid,user['id'],'create',None,'draft')
            else:
                row=owned(db,data,user)
                if row['status'] not in ('draft','rejected','paused','active','pending_review','reserved'):raise AccountError('Este anúncio não pode ser editado nesse estado.',409)
                if type(data.get('revision')) is not int or data['revision']!=row['revision']:raise AccountError('O anúncio foi alterado. Atualize a página.',409)
                db.execute('UPDATE listings SET edition_id=?,title=?,description=?,condition=?,language=?,price_cents=?,region=?,components=?,status=?,revision=revision+1,updated_at=? WHERE id=?',
                           (*[values[k] for k in ('edition_id','title','description','condition','language','price_cents','region','components')],'draft',int(time.time()),row['id']))
                audit(db,row['id'],user['id'],'edit',row['status'],'draft')
            db.execute('INSERT INTO listing_details VALUES (?,?,?,?,?) ON CONFLICT(listing_id) DO UPDATE SET delivery=excluded.delivery,negotiable=excluded.negotiable,sealed=excluded.sealed,defects=excluded.defects',
                       (lid if action=='create' else row['id'],data.get('delivery','unspecified'),int(data.get('negotiable',False)),int(data.get('sealed',False)),data.get('defects','Não informado')))
        elif action=='transition':
            row=owned(db,data,user);check_revision(row,data)
            target=data.get('status')
            allowed={'active':('reserved','paused','sold'),'reserved':('active','paused','sold'),'paused':('active',)}
            if target not in allowed.get(row['status'],()):raise AccountError('Transição de disponibilidade inválida.',409)
            # Only a previously approved revision can be reactivated.
            approval=db.execute("SELECT id FROM moderation_actions WHERE listing_id=? AND action='approve' ORDER BY id DESC LIMIT 1",(row['id'],)).fetchone()
            changed=db.execute("SELECT id FROM moderation_actions WHERE listing_id=? AND action IN ('edit','add_image','delete_image') ORDER BY id DESC LIMIT 1",(row['id'],)).fetchone()
            if not approval or (changed and changed['id']>approval['id']):raise AccountError('É necessária uma nova revisão.',409)
            db.execute('UPDATE listings SET status=?,revision=revision+1,updated_at=? WHERE id=?',(target,int(time.time()),row['id']))
            audit(db,row['id'],user['id'],'availability',row['status'],target)
        elif action=='remove':
            row=owned(db,data,user)
            if row['status'] in ('sold','removed'):raise AccountError('Anúncio já encerrado.',409)
            db.execute("UPDATE listings SET status='removed',revision=revision+1,updated_at=? WHERE id=?",(int(time.time()),row['id']))
            audit(db,row['id'],user['id'],'remove',row['status'],'removed')
        elif action=='queue':
            if not moderator:raise AccountError('Acesso restrito à moderação.',403)
        elif action in ('can_upload','add_image','delete_image'):
            row=owned(db,data,user)
            if row['status'] not in ('draft','rejected','paused','active','pending_review','reserved'):raise AccountError('Anúncio encerrado.',409)
            check_revision(row,data)
            if action=='can_upload':return {'ok':True}
            if action=='add_image':
                if db.execute('SELECT count(*) FROM listing_images WHERE listing_id=?',(row['id'],)).fetchone()[0]>=6:raise AccountError('Limite de seis fotos por anúncio.')
                encoded=text(data,'content',4,2800000)
                try:content=base64.b64decode(encoded,validate=True)
                except ValueError:raise AccountError('Foto inválida.')
                if not content.startswith(b'\xff\xd8\xff') or not content.endswith(b'\xff\xd9') or len(content)>2000000:raise AccountError('Foto inválida ou muito grande.')
                db.execute('INSERT INTO listing_images VALUES (?,?,?,?)',(secrets.token_hex(16),row['id'],content,int(time.time())))
            else:
                image_id=text(data,'image_id',1,80)
                if db.execute('DELETE FROM listing_images WHERE id=? AND listing_id=?',(image_id,row['id'])).rowcount!=1:raise AccountError('Foto não encontrada.',404)
            db.execute("UPDATE listings SET status='draft',revision=revision+1,updated_at=? WHERE id=?",(int(time.time()),row['id']))
            audit(db,row['id'],user['id'],action,row['status'],'draft')
        elif action=='image':
            image_id=text(data,'image_id',1,80)
            image=db.execute('SELECT i.content,l.seller_id,l.status FROM listing_images i JOIN listings l ON l.id=i.listing_id WHERE i.id=?',(image_id,)).fetchone()
            if image is None or (image['seller_id']!=user['id'] and not moderator):raise AccountError('Foto não encontrada.',404)
            return {'content':base64.b64encode(image['content']).decode('ascii')}
        elif action in ('submit','approve','reject'):
            if action in ('approve','reject'):
                if not moderator:raise AccountError('Acesso restrito à moderação.',403)
                lid=text(data,'id',1,80);row=db.execute('SELECT * FROM listings WHERE id=?',(lid,)).fetchone()
                if row is None:raise AccountError('Anúncio não encontrado.',404)
                if row['seller_id']==user['id']:raise AccountError('Outro moderador deve revisar seu anúncio.',403)
                if row['status']!='pending_review':raise AccountError('Anúncio fora da fila de revisão.',409)
                reason=text(data,'reason',5,1000)
                if action=='approve' and data.get('edition_confirmed') is not True:raise AccountError('Confirme a identificação da edição nas fotos.')
            else:
                row=owned(db,data,user);reason=''
                if row['status'] not in ('draft','rejected','paused'):raise AccountError('Estado inválido para envio.',409)
                if data.get('terms_accepted') is not True or data.get('terms_version')!=TERMS_VERSION:raise AccountError('Revise o anúncio e aceite a versão atual das regras antes de enviar.')
            check_revision(row,data)
            if action!='reject':
                detail=db.execute('SELECT delivery FROM listing_details WHERE listing_id=?',(row['id'],)).fetchone()
                if not detail or detail['delivery']=='unspecified':raise AccountError('Informe envio ou retirada antes da publicação.',409)
            if action=='approve' and not db.execute('SELECT 1 FROM listing_acceptances WHERE listing_id=? AND revision=? AND version=?',(row['id'],row['revision'],TERMS_VERSION)).fetchone():raise AccountError('É necessário novo aceite do vendedor.',409)
            if action!='reject' and not db.execute('SELECT 1 FROM listing_images WHERE listing_id=?',(row['id'],)).fetchone():raise AccountError('Adicione pelo menos uma foto antes de enviar.',409)
            status={'submit':'pending_review','approve':'active','reject':'rejected'}[action]
            db.execute('UPDATE listings SET status=?,revision=revision+1,updated_at=? WHERE id=?',(status,int(time.time()),row['id']))
            audit(db,row['id'],user['id'],action,row['status'],status,reason)
            if action=='submit':db.execute('INSERT OR REPLACE INTO listing_acceptances VALUES (?,?,?,?,?)',(row['id'],row['revision']+1,user['id'],TERMS_VERSION,int(time.time())))
            if action=='approve':notify_listing(db,row['id'])
        elif action!='mine':raise AccountError('Operação inválida.')
        queue=action in ('queue','approve','reject')
        rows=db.execute('SELECT l.*,g.name AS game_name,e.name AS edition_name,e.verified AS edition_verified FROM listings l JOIN marketplace_editions e ON e.id=l.edition_id JOIN marketplace_games g ON g.id=e.game_id WHERE '+("l.status='pending_review'" if queue else 'l.seller_id=?')+' ORDER BY l.updated_at DESC,l.id',() if queue else (user['id'],)).fetchall()
        result=[]
        for row in rows:
            item=dict(row);item['images']=[{'id':r['id']} for r in db.execute('SELECT id FROM listing_images WHERE listing_id=? ORDER BY created_at,id',(row['id'],))]
            detail=db.execute('SELECT delivery,negotiable,sealed,defects FROM listing_details WHERE listing_id=?',(row['id'],)).fetchone()
            item.update(dict(detail) if detail else {'delivery':'unspecified','negotiable':0,'sealed':0,'defects':'Não informado'})
            last=db.execute("SELECT reason FROM moderation_actions WHERE listing_id=? AND action IN ('approve','reject') ORDER BY id DESC LIMIT 1",(row['id'],)).fetchone()
            item['review_reason']=last['reason'] if last else None
            result.append(item)
        return {'listings':result,'is_moderator':moderator,'phase':3,**({'created_id':lid} if action=='create' else {})}


def owned(db,data,user):
    lid=text(data,'id',1,80)
    row=db.execute('SELECT * FROM listings WHERE id=? AND seller_id=?',(lid,user['id'])).fetchone()
    if row is None:raise AccountError('Anúncio não encontrado.',404)
    return row


def check_revision(row,data):
    if type(data.get('revision')) is not int or data['revision']!=row['revision']:raise AccountError('O anúncio foi alterado. Atualize a página.',409)


def browse(db,data,listing_id=''):
    query=data.get('q','');edition=data.get('edition_id','');page=data.get('page',1)
    if not isinstance(query,str) or len(query)>120 or not isinstance(edition,str) or len(edition)>80 or type(page) is not int or not 1<=page<=10000:raise AccountError('Busca inválida.')
    # Whitelist projection: no seller ID, e-mail, private review notes or contact fields.
    rows=db.execute("SELECT l.id,l.edition_id,l.title,l.description,l.condition,l.language,l.price_cents,l.currency,l.region,l.components,l.updated_at,g.name AS game_name,g.id AS game_id,e.name AS edition_name FROM listings l JOIN marketplace_editions e ON e.id=l.edition_id JOIN marketplace_games g ON g.id=e.game_id WHERE l.status='active' AND EXISTS(SELECT 1 FROM listing_acceptances a WHERE a.listing_id=l.id AND a.version=?) AND EXISTS(SELECT 1 FROM listing_details d WHERE d.listing_id=l.id AND d.delivery!='unspecified') AND (?='' OR l.edition_id=?) AND (?='' OR l.id=?) ORDER BY l.price_cents,l.id",(TERMS_VERSION,edition,edition,listing_id,listing_id)).fetchall()
    terms=name_key(query).split()
    matches=[dict(r) for r in rows if all(t in name_key(' '.join([r['title'],r['game_name'],r['region']])) for t in terms)]
    total=len(matches);pages=max(1,(total+23)//24);page=min(page,pages)
    items=matches[(page-1)*24:page*24]
    for item in items:
        item['images']=[{'id':r['id']} for r in db.execute('SELECT id FROM listing_images WHERE listing_id=? ORDER BY created_at,id',(item['id'],))]
        detail=db.execute('SELECT delivery,negotiable,sealed,defects FROM listing_details WHERE listing_id=?',(item['id'],)).fetchone()
        item.update(dict(detail) if detail else {'delivery':'unspecified','negotiable':0,'sealed':0,'defects':'Não informado'})
    return {'listings':items,'total':total,'page':page,'page_count':pages}


def throttle(db,uid,kind,limit=20):
    now=int(time.time());db.execute('DELETE FROM marketplace_events WHERE created_at<?',(now-86400,))
    if db.execute('SELECT count(*) FROM marketplace_events WHERE user_id=? AND kind=? AND created_at>?',(uid,kind,now-3600)).fetchone()[0]>=limit:raise AccountError('Limite de uso atingido. Tente mais tarde.',429)
    db.execute('INSERT INTO marketplace_events VALUES (?,?,?)',(uid,kind,now))


def community_action(db,user,moderator,action,data):
    uid=user['id'];now=int(time.time())
    if action=='inquire':
        lid=text(data,'id',1,80);body=text(data,'message',3,1000)
        listing=db.execute("SELECT seller_id FROM listings WHERE id=? AND status='active'",(lid,)).fetchone()
        if not listing:raise AccountError('Anúncio indisponível.',409)
        if listing['seller_id']==uid:raise AccountError('Este anúncio é seu.')
        throttle(db,uid,'message',40)
        cid=secrets.token_hex(16)
        db.execute('INSERT OR IGNORE INTO conversations VALUES (?,?,?,?)',(cid,lid,uid,listing['seller_id']))
        cid=db.execute('SELECT id FROM conversations WHERE listing_id=? AND buyer_id=?',(lid,uid)).fetchone()['id']
        db.execute('INSERT INTO messages(conversation_id,author_id,body,created_at) VALUES (?,?,?,?)',(cid,uid,body,now))
        return {'ok':True,'conversation_id':cid}
    if action=='reply':
        cid=text(data,'conversation_id',1,80);body=text(data,'message',1,1000)
        row=db.execute('SELECT listing_id FROM conversations WHERE id=? AND (buyer_id=? OR seller_id=?)',(cid,uid,uid)).fetchone()
        if not row:raise AccountError('Conversa não encontrada.',404)
        throttle(db,uid,'message',40)
        db.execute('INSERT INTO messages(conversation_id,author_id,body,created_at) VALUES (?,?,?,?)',(cid,uid,body,now))
        return {'ok':True}
    if action=='inbox':
        rows=db.execute('SELECT c.id,l.title,c.buyer_id,c.seller_id FROM conversations c JOIN listings l ON l.id=c.listing_id WHERE c.buyer_id=? OR c.seller_id=?',(uid,uid)).fetchall()
        return {'conversations':[{'id':r['id'],'title':r['title'],'messages':[{'id':m['id'],'body':m['body'],'mine':m['author_id']==uid,'created_at':m['created_at']} for m in db.execute('SELECT * FROM messages WHERE conversation_id=? ORDER BY id DESC LIMIT 100',(r['id'],))][::-1]} for r in rows]}
    if action=='report':
        lid=text(data,'id',1,80);reason=text(data,'reason',5,1000)
        if not db.execute("SELECT 1 FROM listings WHERE id=? AND status IN ('active','reserved')",(lid,)).fetchone():raise AccountError('Anúncio não encontrado.',404)
        throttle(db,uid,'report',10)
        db.execute('INSERT OR IGNORE INTO listing_reports(listing_id,reporter_id,reason,created_at) VALUES (?,?,?,?)',(lid,uid,reason,now))
        return {'ok':True}
    if action=='request_game':
        name=text(data,'name',2,120);edition=text(data,'edition',2,200);notes=text(data,'notes',0,1000)
        throttle(db,uid,'request',10)
        db.execute('INSERT INTO catalog_requests(user_id,name,edition,notes,created_at) VALUES (?,?,?,?,?)',(uid,name,edition,notes,now))
        return {'ok':True}
    if action=='requests':
        return {'requests':[dict(r) for r in db.execute('SELECT id,name,edition,notes,status,decision FROM catalog_requests'+('' if moderator else ' WHERE user_id=?')+' ORDER BY id DESC',() if moderator else (uid,))]}
    if not moderator:raise AccountError('Acesso restrito à moderação.',403)
    if action=='reports':return {'reports':[dict(r) for r in db.execute("SELECT r.id,r.listing_id,r.reason,l.title FROM listing_reports r JOIN listings l ON l.id=r.listing_id WHERE r.status='open' ORDER BY r.id")]}
    reason=text(data,'reason',5,1000);record_id=data.get('record_id')
    if type(record_id) is not int:raise AccountError('Registro inválido.')
    if action=='decide_request':
        status=data.get('status')
        if status not in ('reviewed','rejected'):raise AccountError('Decisão inválida.')
        if db.execute("UPDATE catalog_requests SET status=?,decision=? WHERE id=? AND status='pending'",(status,reason,record_id)).rowcount!=1:raise AccountError('Solicitação não encontrada.',404)
        return {'ok':True}
    if action=='resolve_report':
        report=db.execute("SELECT listing_id FROM listing_reports WHERE id=? AND status='open'",(record_id,)).fetchone()
        if not report:raise AccountError('Denúncia não encontrada.',404)
        if data.get('remove') is True:
            row=db.execute('SELECT status FROM listings WHERE id=?',(report['listing_id'],)).fetchone()
            db.execute("UPDATE listings SET status='removed',revision=revision+1,updated_at=? WHERE id=?",(now,report['listing_id']))
            audit(db,report['listing_id'],uid,'moderator_remove',row['status'],'removed',reason)
        db.execute("UPDATE listing_reports SET status='resolved',decision=? WHERE id=?",(reason,record_id))
        return {'ok':True}
    raise AccountError('Operação inválida.')
