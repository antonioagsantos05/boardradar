"""Local accounts and user-owned game records, separate from the curated catalog."""
from contextlib import closing
import hashlib
import hmac
import os
from pathlib import Path
import re
import secrets
import sqlite3
import time

DATABASE=Path(os.environ['RADAR_ACCOUNT_DB']) if os.environ.get('RADAR_ACCOUNT_DB') else Path(__file__).resolve().parents[2]/'.local/accounts.sqlite3'


class AccountError(Exception):
    def __init__(self,message,status=400):
        super().__init__(message);self.status=status


def connect():
    DATABASE.parent.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(DATABASE,timeout=10)
    db.row_factory=sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    db.executescript('''
        CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY,name TEXT NOT NULL,email TEXT UNIQUE NOT NULL,salt TEXT NOT NULL,password_hash TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS sessions(token_hash TEXT PRIMARY KEY,user_id TEXT NOT NULL REFERENCES users(id),expires_at INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS user_games(id TEXT PRIMARY KEY,user_id TEXT NOT NULL REFERENCES users(id),name TEXT NOT NULL,category TEXT NOT NULL,players INTEGER NOT NULL,duration INTEGER NOT NULL,description TEXT NOT NULL,created_at INTEGER NOT NULL);
    ''')
    from .journey import migrate
    migrate(db)
    return db


def text(data,key,minimum,maximum):
    value=data.get(key)
    if not isinstance(value,str) or not minimum<=len(value.strip())<=maximum:
        raise AccountError('Campo inválido: '+key)
    return value.strip()


def password_hash(password,salt):
    return hashlib.pbkdf2_hmac('sha256',password.encode(),bytes.fromhex(salt),600000).hex()


def user_for(db,token):
    if not isinstance(token,str) or len(token)>100:raise AccountError('Entre na sua conta.',401)
    hashed=hashlib.sha256(token.encode()).hexdigest()
    row=db.execute('SELECT u.id,u.name,u.email FROM sessions s JOIN users u ON u.id=s.user_id WHERE s.token_hash=? AND s.expires_at>?',(hashed,int(time.time()))).fetchone()
    if row is None:raise AccountError('Entre na sua conta.',401)
    return dict(row)


def execute(action,data,token=''):
    if not isinstance(data,dict):raise AccountError('Dados inválidos.')
    with closing(connect()) as db, db:
        db.execute('DELETE FROM sessions WHERE expires_at<=?',(int(time.time()),))
        if action in ('register','login'):
            email=text(data,'email',3,254).casefold()
            if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',email):raise AccountError('E-mail inválido.')
            password=data.get('password')
            if not isinstance(password,str) or not 8<=len(password)<=128:raise AccountError('Use uma senha entre 8 e 128 caracteres.')
            if action=='register':
                name=text(data,'name',2,80);salt=secrets.token_hex(16)
                user={'id':secrets.token_hex(16),'name':name,'email':email}
                try:db.execute('INSERT INTO users VALUES (?,?,?,?,?)',(user['id'],name,email,salt,password_hash(password,salt)))
                except sqlite3.IntegrityError:raise AccountError('Não foi possível cadastrar esse e-mail.',409)
            else:
                row=db.execute('SELECT * FROM users WHERE email=?',(email,)).fetchone()
                # Same hashing work for unknown users avoids a cheap timing distinction.
                candidate=password_hash(password,row['salt'] if row else '00'*16)
                if row is None or not hmac.compare_digest(candidate,row['password_hash']):raise AccountError('E-mail ou senha incorretos.',401)
                user={k:row[k] for k in ('id','name','email')}
            session=secrets.token_urlsafe(32)
            db.execute('INSERT INTO sessions VALUES (?,?,?)',(hashlib.sha256(session.encode()).hexdigest(),user['id'],int(time.time())+604800))
            return {'user':user,'session_token':session}
        user=user_for(db,token)
        if action=='logout':
            db.execute('DELETE FROM sessions WHERE token_hash=?',(hashlib.sha256(token.encode()).hexdigest(),))
            return {'ok':True}
        if action in ('create_game','update_game'):
            name=text(data,'name',2,120);category=text(data,'category',2,100);description=text(data,'description',0,3000)
            players=data.get('players');duration=data.get('duration')
            if type(players) is not int or not 1<=players<=20 or type(duration) is not int or not 1<=duration<=10000:raise AccountError('Jogadores ou duração inválidos.')
            if action=='create_game':
                db.execute('INSERT INTO user_games VALUES (?,?,?,?,?,?,?,?)',(secrets.token_hex(16),user['id'],name,category,players,duration,description,int(time.time())))
            else:
                changed=db.execute('UPDATE user_games SET name=?,category=?,players=?,duration=?,description=? WHERE id=? AND user_id=?',(name,category,players,duration,description,data.get('id'),user['id']))
                if changed.rowcount!=1:raise AccountError('Jogo não encontrado.',404)
        elif action=='delete_game':
            changed=db.execute('DELETE FROM user_games WHERE id=? AND user_id=?',(data.get('id'),user['id']))
            if changed.rowcount!=1:raise AccountError('Jogo não encontrado.',404)
        elif action in ('save_profile','delete_profile','save_wishlist','delete_wishlist','read_notifications'):
            from .journey import account_action
            account_action(db,user,action,data)
        elif action!='me':raise AccountError('Operação inválida.')
        games=[dict(r) for r in db.execute('SELECT id,name,category,players,duration,description,created_at FROM user_games WHERE user_id=? ORDER BY created_at DESC,id',(user['id'],))]
        from .journey import details
        return {'user':user,'games':games,**details(db,user['id'])}
