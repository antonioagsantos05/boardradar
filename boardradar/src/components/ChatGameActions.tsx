'use client';
import {useState} from 'react';
import Link from 'next/link';
import {gameRepository} from '@/repositories/catalog';
export default function ChatGameActions({gameId,editionId}:{gameId:string;editionId?:string}){
 const game=gameRepository.byId(gameId);const edition=editionId?game?.editions.find(e=>e.id===editionId):game?.editions[0];
 const [busy,setBusy]=useState(false);const [saved,setSaved]=useState(false);const [error,setError]=useState('');const [guest,setGuest]=useState(false);
 if(!game)return null;
 const href='/jogos/'+game.slug+(edition?'?edition='+encodeURIComponent(edition.id):'');
 async function save(){if(!edition||busy)return;setBusy(true);setError('');try{const r=await fetch('/api/account',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action:'save_wishlist',data:{edition_id:edition.id}})});const b=await r.json();if(!r.ok){if(r.status===401)setGuest(true);throw Error(r.status===401?'Entre na sua conta para salvar esta edição.':b.error||'Não foi possível salvar.')}setSaved(true)}catch(e){setError(e instanceof Error?e.message:'Não foi possível salvar.')}finally{setBusy(false)}}
 return <div className="chat-game-actions">{edition&&<p>Edição: {edition.name} · dados preliminares</p>}<div><Link href={href}>Ver ficha</Link><Link href={href+'#ofertas'}>Ofertas</Link><Link href={href+'#comparar'}>Comparar jogos</Link>{edition&&<button type="button" disabled={busy||saved} onClick={()=>void save()}>{busy?'Salvando…':saved?'Edição salva':'Salvar edição na wishlist'}</button>}</div>{saved&&<p role="status">Edição salva na conta. <Link href="/favoritos">Gerenciar wishlist e alertas</Link></p>}{error&&<p role="alert">{error} {guest&&<Link href={'/entrar?next='+encodeURIComponent(href)}>Entrar</Link>}</p>}</div>;
}
