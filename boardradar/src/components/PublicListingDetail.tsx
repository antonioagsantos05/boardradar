'use client';
import {useEffect,useState} from 'react';
import {displayText} from '@/domain/presentation';
import Link from 'next/link';
import type {Listing} from './CommunityListings';
import UserListingCard from './UserListingCard';
import {LoadingSkeleton,StatusMessage} from './ui/States';
import Button from './ui/Button';
export default function PublicListingDetail({id}:{id:string}){
 const [item,setItem]=useState<Listing|null>(null);const [busy,setBusy]=useState(true);const [error,setError]=useState('');const [retry,setRetry]=useState(0);
 useEffect(()=>{const abort=new AbortController();setBusy(true);setItem(null);setError('');fetch('/api/listings?view=detail&id='+encodeURIComponent(id),{signal:abort.signal,cache:'no-store'}).then(async r=>{const body=await r.json();if(!r.ok)throw Error(r.status===404?'Anúncio indisponível. Ele pode ter sido reservado, pausado, vendido ou removido.':body.error||'Falha ao consultar anúncio.');if(!abort.signal.aborted)setItem(body.listing)}).catch(e=>{if(!abort.signal.aborted)setError(e instanceof Error?e.message:'Falha na consulta.')}).finally(()=>{if(!abort.signal.aborted)setBusy(false)});return()=>abort.abort()},[id,retry]);
 return <main className="container listing-detail"><Link href="/marketplace">← Voltar à comunidade</Link>{busy?<LoadingSkeleton label="Consultando anúncio…"/>:error?<><h1>Anúncio indisponível</h1><StatusMessage error>{error}</StatusMessage><Button variant="secondary" onClick={()=>setRetry(v=>v+1)}>Tentar novamente</Button></>:item&&<><div className="section-heading"><div><span className="eyebrow">ANÚNCIO DA COMUNIDADE</span><h1>{displayText(item.title)}</h1><p>Confira os detalhes e o estado do exemplar.</p></div><Link className="button light" href="/meus-anuncios">Meus anúncios</Link></div><h2 className="sr-only">Detalhes do anúncio</h2><div className="listing-detail-layout"><div className="listing-gallery" role="group" aria-label="Fotos do anúncio">{item.images.map((photo,i)=><a href={'/api/listing-images?id='+photo.id} target="_blank" rel="noreferrer" key={photo.id}><img loading={i===0?'eager':'lazy'} decoding="async" width={640} height={480} src={'/api/listing-images?id='+photo.id} alt={'Foto '+(i+1)+' de '+item.title}/></a>)}</div><UserListingCard item={item}/></div></>}</main>;
}
