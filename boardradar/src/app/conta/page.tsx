'use client';
import { useEffect,useState } from 'react';
import Link from 'next/link';
import {useAppShell} from '@/components/layout/AppShell';
import AccountJourney from '@/components/AccountJourney';
type User={id:string;name:string;email:string};
type UserGame={id:string;name:string;category:string;players:number;duration:number;description:string};
const emptyGame={name:'',category:'',players:2,duration:60,description:''};

export default function AccountPage(){
 const {confirm}=useAppShell();
 const [user,setUser]=useState<User|null>(null);const [games,setGames]=useState<UserGame[]>([]);
 const [register,setRegister]=useState(false);const [busy,setBusy]=useState(true);const [error,setError]=useState('');const [notice,setNotice]=useState('');
 const [credentials,setCredentials]=useState({name:'',email:'',password:''});
 const [game,setGame]=useState(emptyGame);const [editing,setEditing]=useState<string|null>(null);
 useEffect(()=>{let alive=true;fetch('/api/account',{cache:'no-store'}).then(async r=>{const body=await r.json();if(!alive)return;if(r.ok){setUser(body.user);setGames(body.games)}else if(r.status!==401)setError(body.error)}).catch(()=>{if(alive)setError('Não foi possível acessar sua conta.')}).finally(()=>{if(alive)setBusy(false)});return()=>{alive=false}},[]);
 async function action(action:string,data:Record<string,unknown>={}){
  setBusy(true);setError('');setNotice('');
  try{
   const response=await fetch('/api/account',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action,data})});const body=await response.json();
   if(!response.ok){if(response.status===401&&user){setUser(null);setGames([])}throw Error(body.error||'Não foi possível concluir.')}
   if(['login','register','logout'].includes(action))window.dispatchEvent(new Event('boardradar-session-changed'));
   if(action==='logout'){setUser(null);setGames([]);setGame(emptyGame);setEditing(null)}
   else {setUser(body.user);if(body.games)setGames(body.games)}
   if(action==='register'||action==='login'){setCredentials({name:'',email:'',password:''});const result=await fetch('/api/account',{cache:'no-store'});if(result.ok)setGames((await result.json()).games)}
   if(action==='create_game'||action==='update_game'){setGame(emptyGame);setEditing(null);setNotice('Jogo salvo na sua conta.')}
   if(action==='delete_game'){if(editing===data.id){setGame(emptyGame);setEditing(null)}setNotice('Jogo removido.')}
  }catch(e){setError(e instanceof Error?e.message:'Erro ao salvar.')}finally{setBusy(false)}
 }
 return <main className="container account-page"><div className="account-top"><Link className="button light" href="/">Voltar ao catálogo</Link></div>
 <Link className="button light" href="/minha-conta">Nova área da conta</Link><h1>{user?'Minha conta':'Sua próxima partida começa aqui'}</h1>
 <p>{user?`Olá, ${user.name}. Escolha explorar ou vender; personalize quando quiser.`:'Crie uma conta local para guardar seus jogos nesta máquina.'}</p>
 {error&&<p className="notice" role="alert">{error}</p>}{notice&&<p role="status">{notice}</p>}
 {!user?<form className="account-form" onSubmit={e=>{e.preventDefault();void action(register?'register':'login',credentials)}}>
 <h2>{register?'Criar conta':'Entrar'}</h2>
 <fieldset disabled={busy}>{register&&<label>Nome<input required minLength={2} maxLength={80} autoComplete="name" value={credentials.name} onChange={e=>setCredentials({...credentials,name:e.target.value})}/></label>}
 <label>E-mail<input type="email" required maxLength={254} autoComplete="email" value={credentials.email} onChange={e=>setCredentials({...credentials,email:e.target.value})}/></label>
 <label>Senha<input type="password" required minLength={8} maxLength={128} autoComplete={register?'new-password':'current-password'} value={credentials.password} onChange={e=>setCredentials({...credentials,password:e.target.value})}/></label>
 <button className="button amber">{busy?'Aguarde…':register?'Criar conta':'Entrar'}</button><button className="button light" type="button" onClick={()=>{setRegister(!register);setError('')}}>{register?'Já tenho uma conta':'Quero criar uma conta'}</button></fieldset>
 </form>:<><div className="account-top"><span>{user.email}</span><Link className="button amber" href="/anuncios">Meus anúncios</Link><button className="button light" disabled={busy} onClick={()=>void action('logout')}>Sair</button></div>
 <AccountJourney/><details id="colecao"><summary>Minha coleção pessoal</summary><div className="account-columns"><form className="account-form" onSubmit={e=>{e.preventDefault();void action(editing?'update_game':'create_game',{...game,...editing?{id:editing}:{}})}}>
 <h2>{editing?'Editar jogo':'Cadastrar jogo'}</h2><p>Cadastro pessoal. Estes registros não são ofertas nem dados revisados do catálogo.</p>
 <fieldset disabled={busy}><label>Nome do jogo<input required minLength={2} maxLength={120} value={game.name} onChange={e=>setGame({...game,name:e.target.value})}/></label>
 <label>Categoria<input required minLength={2} maxLength={100} placeholder="Ex.: estratégia, cartas, aventura" value={game.category} onChange={e=>setGame({...game,category:e.target.value})}/></label>
 <label>Número de jogadores<input type="number" required min={1} max={20} value={game.players} onChange={e=>setGame({...game,players:Number(e.target.value)})}/></label>
 <label>Duração em minutos<input type="number" required min={1} max={10000} value={game.duration} onChange={e=>setGame({...game,duration:Number(e.target.value)})}/></label>
 <label>Descrição e observações<textarea maxLength={3000} rows={4} value={game.description} onChange={e=>setGame({...game,description:e.target.value})}/></label>
 <button className="button amber">{busy?'Salvando…':editing?'Salvar alterações':'Cadastrar jogo'}</button>{editing&&<button type="button" className="button light" onClick={()=>{setEditing(null);setGame(emptyGame)}}>Cancelar edição</button>}</fieldset></form>
 <section><h2>Meus jogos ({games.length})</h2>{games.length===0&&<p>Você ainda não cadastrou jogos.</p>}{games.map(g=><article className="account-game" key={g.id}><span className="eyebrow">{g.category}</span><h3>{g.name}</h3><p>{g.players} jogadores · {g.duration} min</p><p className="account-description">{g.description}</p><button className="button light" disabled={busy} onClick={()=>{setEditing(g.id);setGame({name:g.name,category:g.category,players:g.players,duration:g.duration,description:g.description})}}>Editar</button><button className="button light" disabled={busy} onClick={async()=>{if(await confirm({title:'Remover jogo da coleção?',description:g.name+' será removido apenas dos seus registros pessoais.',confirmLabel:'Remover jogo'}))void action('delete_game',{id:g.id})}}>Remover</button></article>)}</section></div></details></>}
 </main>;
}
