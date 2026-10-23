'use client';
import { useState } from 'react';
import Link from 'next/link';
export default function CommunityActions(props:{id:string;editionId:string}){
 if(props.id.startsWith('listing_'))return <DemoContact/>;
 return <LegacyActions {...props}/>;
}
function DemoContact(){const [notice,setNotice]=useState(false);return <div><button className="button light" onClick={()=>setNotice(true)}>Ver contato</button>{notice&&<p role="status">Este vendedor ainda não disponibilizou um canal de contato.</p>}</div>}
function LegacyActions({id,editionId}:{id:string;editionId:string}){
 const [message,setMessage]=useState('');const [reason,setReason]=useState('');const [notice,setNotice]=useState('');const [busy,setBusy]=useState(false);
 async function send(action:string,data:Record<string,unknown>,account=false){setBusy(true);setNotice('');try{const r=await fetch(account?'/api/account':'/api/listings',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action,data})});const b=await r.json();if(!r.ok)throw Error(r.status===401?'Entre em Minha conta para continuar.':b.error);setNotice(action==='inquire'?'Mensagem enviada. Acompanhe em Minhas conversas.':action==='report'?'Denúncia encaminhada à moderação.':'Jogo salvo na wishlist. Alertas podem ser ativados em Minha conta.');setMessage('');setReason('')}catch(e){setNotice(e instanceof Error?e.message:'Erro ao enviar.')}finally{setBusy(false)}}
 return <div className="community-actions"><button className="button light" disabled={busy} onClick={()=>void send('save_wishlist',{edition_id:editionId},true)}>Salvar na wishlist</button><details><summary>Falar com o vendedor</summary><form onSubmit={e=>{e.preventDefault();void send('inquire',{id,message})}}><label>Mensagem protegida<textarea required minLength={3} maxLength={1000} value={message} onChange={e=>setMessage(e.target.value)}/></label><button className="button amber" disabled={busy}>Enviar mensagem</button></form><Link href="/mensagens">Minhas conversas</Link></details><details><summary>Denunciar anúncio</summary><form onSubmit={e=>{e.preventDefault();void send('report',{id,reason})}}><label>Motivo<textarea required minLength={5} maxLength={1000} value={reason} onChange={e=>setReason(e.target.value)}/></label><button className="button light" disabled={busy}>Enviar denúncia</button></form></details>{notice&&<p role="status">{notice} <Link href="/conta">Minha conta</Link></p>}</div>;
}
