'use client';
import {useEffect,useState} from 'react';
import {canonicalCatalogId} from '@/domain/catalog-identity';
import type {LibrarySummary} from '@/domain/library';

import ImportedGameCard from './ImportedGameCard';
export default function LocalFavoriteCards({ids,onRemove}:{ids:string[];onRemove:(id:string)=>void}){
 const [imported,setImported]=useState<LibrarySummary[]>([]);const [error,setError]=useState('');const [retry,setRetry]=useState(0);
 const key=ids.join(',');
 useEffect(()=>{const abort=new AbortController();setError('');setImported([]);if(!key)return()=>abort.abort();async function load(){const all:LibrarySummary[]=[];const wanted=key.split(',');for(let i=0;i<wanted.length;i+=96){const query=new URLSearchParams({ids:wanted.slice(i,i+96).join(','),page_size:'96'});const r=await fetch('/api/catalog?'+query,{signal:abort.signal});if(!r.ok)throw Error('Não foi possível carregar os favoritos importados.');all.push(...(await r.json()).results)}if(!abort.signal.aborted)setImported(all)}void load().catch(e=>{if(!abort.signal.aborted)setError(e.message)});return()=>abort.abort()},[key,retry]);
 return <>{error&&<p role="alert">{error} <button onClick={()=>setRetry(n=>n+1)}>Tentar novamente</button></p>}<div className="game-grid favorite-game-grid">{ids.map(id=>{const other=imported.find(g=>g.id===canonicalCatalogId(id));return other?<ImportedGameCard key={id} game={other} saved onToggle={()=>onRemove(id)}/>:null})}</div></>;
}
