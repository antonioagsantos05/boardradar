"""Local optional profiles, wishlist and consented internal notifications."""
import json
import time
from contextvars import ContextVar
from .catalog import raw
FRANCHISES=raw("franchises")

PROFILE=ContextVar('player_profile',default=None)
TERMS_VERSION='local-mvp-2026-10-20-v1'


def migrate(db):
    db.executescript('''
        CREATE TABLE IF NOT EXISTS player_profiles(user_id TEXT PRIMARY KEY REFERENCES users(id),payload TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS wishlist_items(user_id TEXT NOT NULL REFERENCES users(id),edition_id TEXT NOT NULL,alert_p2p INTEGER NOT NULL DEFAULT 0,target_price INTEGER,PRIMARY KEY(user_id,edition_id));
        CREATE TABLE IF NOT EXISTS notifications(id INTEGER PRIMARY KEY,user_id TEXT NOT NULL REFERENCES users(id),listing_id TEXT NOT NULL,title TEXT NOT NULL,read_at INTEGER,created_at INTEGER NOT NULL,UNIQUE(user_id,listing_id));
    ''')


def profile_for(db,uid):
    row=db.execute('SELECT payload FROM player_profiles WHERE user_id=?',(uid,)).fetchone()
    return json.loads(row['payload']) if row else None


def bonus(game,profile,state=None):
    if not profile:return 0
    from .nlp.normalizer import name_key
    from .catalog import DEFAULT_CATALOG
    state=state or {'preferences':{},'interests':[]}
    p=state['preferences'];score=0
    if not state.get('interests') and not p.get('videogames') and not state.get('media_ids'):
        tags={name_key(t) for t in game['tags']}
        score+=8*len(tags&{name_key(t) for t in profile.get('styles',[])})
        selected=profile.get('videogames',[])
        legacy_bonus=max((r['weight']*12 for r in DEFAULT_CATALOG.relations if r['game_id']==game['id'] and r['videogame_id'] in selected),default=0)
        franchise_bonus=max((min(1,len(tags&{name_key(t) for t in f['temas']+f['experiencias']})/4)*12 for f in FRANCHISES if f['id'] in selected),default=0)
        score+=max(legacy_bonus,franchise_bonus)
        from .media import match_media,linked_candidates
        works=match_media(name_key(profile.get('references','')))
        if works:
            ids,_=linked_candidates([w['id'] for w in works])
            if game['id'] in ids:score+=8
    if not p.get('complexity'):
        target={'beginner':1,'intermediate':3,'advanced':5}.get(profile.get('experience'))
        if target:score+=max(0,6-2*abs(target-game['complexity']))
    if profile.get('budget') and not p.get('budget'):
        from .offers import best_offer
        offer=best_offer(game)
        if offer and offer['price_cents']<=profile['budget']*100:score+=3
    return score


def account_action(db,user,action,data):
    from .accounts import AccountError,text
    from .catalog import DEFAULT_CATALOG
    uid=user['id']
    if action=='save_profile':
        if data.get('consent') is not True:raise AccountError('Autorize o uso das preferências ou pule esta etapa.')
        experience=data.get('experience','')
        if experience not in ('','beginner','intermediate','advanced'):raise AccountError('Experiência inválida.')
        styles=data.get('styles',[]);videos=data.get('videogames',[])
        if not isinstance(styles,list) or len(styles)>12 or any(not isinstance(t,str) or len(t)>60 for t in styles):raise AccountError('Estilos inválidos.')
        valid={v['id'] for v in DEFAULT_CATALOG.videos}|{f['id'] for f in FRANCHISES}
        if not isinstance(videos,list) or len(videos)>len(valid) or any(not isinstance(v,str) or v not in valid for v in videos):raise AccountError('Franquias inválidas.')
        references=text(data,'references',0,500);budget=data.get('budget')
        if budget is not None and (type(budget) not in (int,float) or not 0<budget<=100000):raise AccountError('Orçamento inválido.')
        payload={'experience':experience,'styles':styles,'videogames':videos,'references':references,'budget':budget,'consent':True}
        db.execute('INSERT INTO player_profiles VALUES (?,?) ON CONFLICT(user_id) DO UPDATE SET payload=excluded.payload',(uid,json.dumps(payload)))
    elif action=='delete_profile':db.execute('DELETE FROM player_profiles WHERE user_id=?',(uid,))
    elif action in ('save_wishlist','delete_wishlist'):
        edition=text(data,'edition_id',1,80)
        if edition not in {e['id'] for g in DEFAULT_CATALOG.games for e in g['editions']}:raise AccountError('Edição inválida.')
        if action=='delete_wishlist':
            db.execute('DELETE FROM wishlist_items WHERE user_id=? AND edition_id=?',(uid,edition))
        else:
            if 'alert_p2p' not in data and 'target_price' not in data:
                db.execute('INSERT OR IGNORE INTO wishlist_items(user_id,edition_id) VALUES (?,?)',(uid,edition))
                return
            alert=data.get('alert_p2p',False);target=data.get('target_price')
            if type(alert) is not bool or target is not None and (type(target) is not int or not 1<=target<=100000000):raise AccountError('Alerta ou preço-alvo inválido.')
            db.execute('INSERT INTO wishlist_items VALUES (?,?,?,?) ON CONFLICT(user_id,edition_id) DO UPDATE SET alert_p2p=excluded.alert_p2p,target_price=excluded.target_price',(uid,edition,int(alert),target))
        # Cancelling an alert withdraws unread notifications for this edition.
        if action=='delete_wishlist' or not data.get('alert_p2p'):
            exists=db.execute("SELECT 1 FROM sqlite_master WHERE name='listings'").fetchone()
            if exists:db.execute('DELETE FROM notifications WHERE user_id=? AND read_at IS NULL AND listing_id IN (SELECT id FROM listings WHERE edition_id=?)',(uid,edition))
    elif action=='read_notifications':db.execute('UPDATE notifications SET read_at=? WHERE user_id=? AND read_at IS NULL',(int(time.time()),uid))
    else:raise AccountError('Operação inválida.')


def details(db,uid):
    from .catalog import DEFAULT_CATALOG
    profile=profile_for(db,uid)
    games=sorted(DEFAULT_CATALOG.games,key=lambda g:-(bonus(g,profile)+g['editorialQuality'])) if profile else []
    return {'profile':profile,'recommended_ids':[g['id'] for g in games[:12]],
            'wishlist':[dict(r) for r in db.execute('SELECT edition_id,alert_p2p,target_price FROM wishlist_items WHERE user_id=?',(uid,))],
            'notifications':[dict(r) for r in db.execute('SELECT id,listing_id,title,read_at,created_at FROM notifications WHERE user_id=? ORDER BY id DESC LIMIT 100',(uid,))]}


def notify_listing(db,lid):
    row=db.execute("SELECT edition_id,price_cents,title,seller_id FROM listings WHERE id=? AND status='active'",(lid,)).fetchone()
    if not row:return
    db.execute('''INSERT OR IGNORE INTO notifications(user_id,listing_id,title,created_at)
        SELECT user_id,?,?,? FROM wishlist_items WHERE edition_id=? AND alert_p2p=1 AND user_id!=? AND (target_price IS NULL OR target_price>=?)''',
        (lid,'Novo anúncio: '+row['title'],int(time.time()),row['edition_id'],row['seller_id'],row['price_cents']))
