'use client';
import { useEffect,useState } from 'react';
import Link from 'next/link';
import UserListingCard from './UserListingCard';
import Pagination from './ui/Pagination';
import {EmptyState,LoadingSkeleton,StatusMessage} from './ui/States';

export type Listing={id:string;edition_id:string;title:string;description:string;game_id:string;game_name:string;edition_name:string;language:string;condition:string;price_cents:number;region:string;components:string;updated_at:number;delivery:string;negotiable:number;sealed:number;defects:string;images:{id:string}[]};
type Results={listings:Listing[];total:number;page:number;page_count:number};
export default function CommunityListings({editionId,preview=false}:{editionId?:string;preview?:boolean}){
 const [query,setQuery]=useState('');const [page,setPage]=useState(1);const [data,setData]=useState<Results>({listings:[],total:0,page:1,page_count:1});const [busy,setBusy]=useState(true);const [error,setError]=useState('');
 useEffect(()=>{setPage(1)},[query,editionId]);
 useEffect(()=>{
  const controller=new AbortController();setBusy(true);
  const timer=setTimeout(async()=>{try{const params=new URLSearchParams({view:'public',q:query,page:String(page)});if(editionId)params.set('edition_id',editionId);const r=await fetch('/api/listings?'+params,{signal:controller.signal,cache:'no-store'});const body=await r.json();if(!r.ok)throw Error(body.error);if(!controller.signal.aborted){setData(body);setError('')}}catch(e){if(!controller.signal.aborted)setError(e instanceof Error?e.message:'Erro ao buscar anúncios.')}finally{if(!controller.signal.aborted)setBusy(false)}},200);
  return()=>{clearTimeout(timer);controller.abort()};
 },[query,page,editionId]);
 return <section className="detail-section community-listings" aria-label="Anúncios da comunidade"><div className="section-heading"><h2>Anúncios da comunidade</h2><Link className="button light" href="/vender">Vender um jogo</Link></div><p className="chart-note">Encontre sua próxima partida nos anúncios da comunidade.</p>{!editionId&&!preview&&<label className="community-search">Buscar por jogo, título ou região<input value={query} maxLength={120} placeholder="Ex.: Catan, Campinas" onChange={e=>setQuery(e.target.value)}/></label>}
 {busy?<LoadingSkeleton label="Buscando anúncios…"/>:error?<StatusMessage error>{error}</StatusMessage>:<p role="status">{data.total} anúncio(s) disponível(is)</p>}
 <div className="community-grid" aria-busy={busy}>{!busy&&!error&&data.listings.slice(0,preview?3:undefined).map(item=><UserListingCard key={item.id} item={item} hideGameLink={Boolean(editionId)}/>)}</div>
 {!busy&&!error&&data.total===0&&<EmptyState title="Nenhum anúncio ativo para esta busca">Reservados, pausados e vendidos não aparecem como disponíveis.</EmptyState>}
 {!busy&&!error&&!preview&&data.page_count>1&&<Pagination page={data.page} pages={data.page_count} onChange={setPage} label="Páginas de anúncios"/>}
 {preview&&<Link className="button light" href="/marketplace">Explorar a comunidade</Link>}
 </section>;
}
