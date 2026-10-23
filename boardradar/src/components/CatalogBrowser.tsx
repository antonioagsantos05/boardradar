'use client';
import {useEffect,useRef,useState} from 'react';
import {usePathname,useRouter,useSearchParams} from 'next/navigation';
import {SlidersHorizontal,X} from 'lucide-react';
import {catalogSearchSchema} from '@/domain/catalog-search';
import type {LibrarySummary} from '@/domain/library';


import ImportedGameCard from './ImportedGameCard';
import {canonicalCatalogId} from '@/domain/catalog-identity';
import Pagination from './ui/Pagination';
import Button from './ui/Button';
import {EmptyState,LoadingSkeleton,StatusMessage} from './ui/States';

type Results={total:number;page:number;page_count:number;page_size:number;results:LibrarySummary[]};
const labels:Record<string,string>={q:'Busca',source:'Origem',players:'Jogadores',duration:'Duração',kind:'Formato',favoritos:'Favoritos locais'};
const names:Record<string,string>={all:'Todos',editorial:'Base anterior desativada',imported:'BGG',boardgame:'Jogo identificado',boardgameexpansion:'Expansão identificada',unclassified:'Formato não informado'};
export default function CatalogBrowser(){
 const params=useSearchParams();const router=useRouter();const path=usePathname();
 const raw=params.toString();const parsed=catalogSearchSchema.safeParse(Object.fromEntries(params));
 const p=parsed.success?parsed.data:null;
 const [query,setQuery]=useState(params.get('q')||'');const [saved,setSaved]=useState<string[]>([]);
 const [data,setData]=useState<Results|null>(null);const [busy,setBusy]=useState(true);const [error,setError]=useState('');const [retry,setRetry]=useState(0);
 const dialog=useRef<HTMLDialogElement>(null);const opener=useRef<HTMLButtonElement>(null);
 const requestKey=p?new URLSearchParams(Object.entries({...p,...p.favoritos?{ids:saved.join(',')}: {}}).filter(([,v])=>v!==undefined).map(([k,v])=>[k,String(v)])).toString():'';
 useEffect(()=>{setQuery(new URLSearchParams(raw).get('q')||'')},[raw]);
 useEffect(()=>{try{const value=JSON.parse(localStorage.getItem('boardradar-favorites')||'[]');if(Array.isArray(value))setSaved(value.filter(v=>typeof v==='string').map(canonicalCatalogId))}catch{}},[]);
 function toggle(id:string){setSaved(previous=>{const next=previous.includes(id)?previous.filter(v=>v!==id):[...previous,id];try{localStorage.setItem('boardradar-favorites',JSON.stringify(next))}catch{}return next})}
 function change(patch:Record<string,string|undefined>){const next=new URLSearchParams(raw);next.delete('page');for(const [k,v] of Object.entries(patch)){if(v===undefined||v===''||v==='all')next.delete(k);else next.set(k,v)}router.push(path+(next.size?'?'+next:''),{scroll:false})}
 useEffect(()=>{
  if(!requestKey){setBusy(false);setData(null);return;}
  const abort=new AbortController();setBusy(true);setError('');setData(null);
  fetch('/api/catalog?'+requestKey,{signal:abort.signal}).then(async r=>{const body=await r.json();if(!r.ok)throw Error(body.error||'Não foi possível consultar os jogos.');if(!abort.signal.aborted){setData(body);const actual=new URLSearchParams(raw);if(Number(actual.get('page')||1)!==body.page){actual.set('page',String(body.page));router.replace(path+'?'+actual,{scroll:false})}}}).catch(e=>{if(!abort.signal.aborted)setError(e instanceof Error?e.message:'Falha na consulta.')}).finally(()=>{if(!abort.signal.aborted)setBusy(false)});
  return()=>abort.abort();
 },[requestKey,retry,raw,path,router]);
 function closeFilters(){dialog.current?.close();document.body.style.overflow='';opener.current?.focus()}
 useEffect(()=>()=>{document.body.style.overflow=''},[]);
 const fields=<>
  <label>Jogadores<select value={p?.players||''} onChange={e=>change({players:e.target.value})}><option value="">Qualquer quantidade</option>{Array.from({length:20},(_,i)=>i+1).map(n=><option value={n} key={n}>{n===1?'Solo':n+' pessoas'}</option>)}</select></label>
  <label>Duração máxima<select value={p?.duration||''} onChange={e=>change({duration:e.target.value})}><option value="">Sem limite</option>{[...new Set([30,60,90,120,180,240,...p?.duration?[p.duration]:[]])].sort((a,b)=>a-b).map(n=><option key={n} value={n}>Até {n} minutos</option>)}</select></label>
  <label>Formato do produto<select value={p?.kind||'all'} onChange={e=>change({kind:e.target.value})}><option value="all">Todos os formatos</option><option value="boardgame">Jogo identificado pela origem</option><option value="boardgameexpansion">Expansão identificada</option><option value="unclassified">Não informado pela origem</option></select></label>
  <Button variant="secondary" onClick={()=>router.push(path,{scroll:false})}>Limpar filtros</Button>
 </>;
 return <main className="container catalog-browser home-vitrine"><div className="catalog-masthead"><div className="catalog-intro"><span className="eyebrow dark">ENCONTRE SUA PRÓXIMA PARTIDA</span><h1>{path==='/buscar'?'Encontre sua próxima partida':'Jogos para todas as mesas'}</h1><p>Explore os jogos, conheça suas características e compare suas opções.</p></div><form className="catalog-query" role="search" aria-label="Pesquisar catálogo" onSubmit={e=>{e.preventDefault();change({q:query.trim()})}}><label htmlFor="catalog-query">Nome, categoria ou mecânica</label><div><input id="catalog-query" type="search" maxLength={200} value={query} onChange={e=>setQuery(e.target.value)} placeholder="Ex.: Catan, fantasia, deck-building"/><Button type="submit">Pesquisar</Button></div></form>
 <div className="catalog-toolbar"><Button ref={opener} variant="secondary" onClick={()=>{dialog.current?.showModal();document.body.style.overflow='hidden'}} className="catalog-filter-toggle"><SlidersHorizontal size={18}/>Filtros</Button><label>Ordenar por<select value={p?.sort||'rank'} onChange={e=>change({sort:e.target.value})}><option value="rank">Ordem do cat?logo</option><option value="name">Nome: A–Z</option><option value="year">Ano: mais recentes</option><option value="duration">Menor duração</option></select></label><label>Jogos por página<select value={p?.page_size||24} onChange={e=>change({page_size:e.target.value})}>{[12,24,48,96].map(n=><option key={n} value={n}>{n} jogos</option>)}</select></label></div>
 </div><div className="catalog-chips" role="group" aria-label="Filtros ativos">{Object.entries(p||{}).filter(([k,v])=>labels[k]&&v&&v!=='all').map(([k,v])=><button key={k} onClick={()=>change({[k]:undefined})} aria-label={'Remover filtro '+labels[k]}>{labels[k]}: {k==='favoritos'?'Neste navegador':names[String(v)]||String(v)}<X size={15}/></button>)}</div>
 <div className="catalog-browser-layout"><aside className="catalog-sidebar" aria-label="Filtros do catálogo"><h2>Refine sua descoberta</h2>{fields}<p>Valores ausentes não são presumidos. Os filtros de jogadores e duração exigem dados informados.</p></aside><section aria-label="Resultados do catálogo" aria-busy={busy}><h2 className="sr-only">Resultados do catálogo</h2>
 {!p?<StatusMessage error>Filtros inválidos na URL. Limpe os filtros para consultar o catálogo.</StatusMessage>:busy?<LoadingSkeleton label="Buscando jogos…"/>:error?<StatusMessage error>{error} <Button variant="secondary" onClick={()=>setRetry(v=>v+1)}>Tentar novamente</Button></StatusMessage>:data&&<><p className="catalog-count" role="status">{data.total.toLocaleString('pt-BR')} jogos encontrados{data.total?` · Mostrando ${(data.page-1)*data.page_size+1}–${Math.min(data.page*data.page_size,data.total)}`:''}</p><div className="game-grid">{data.results.map(g=><ImportedGameCard key={g.id} game={g} saved={saved.includes(g.id)} onToggle={()=>toggle(g.id)}/>)}</div>{!data.total&&<EmptyState title="Nenhum jogo com essa combinação">Remova um filtro ou tente outro termo. <Button variant="secondary" onClick={()=>router.push(path,{scroll:false})}>Limpar filtros</Button></EmptyState>}{data.total>0&&<Pagination numbered page={data.page} pages={data.page_count} onChange={page=>{change({page:String(page)});document.querySelector('.catalog-count')?.scrollIntoView({behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth',block:'center'})}}/>}</>}
 </section></div><dialog ref={dialog} className="catalog-filter-dialog" aria-labelledby="catalog-filter-title" onCancel={e=>{e.preventDefault();closeFilters()}}><div><h2 id="catalog-filter-title">Filtros do catálogo</h2><Button variant="secondary" onClick={closeFilters}>Fechar filtros</Button></div>{fields}<Button onClick={closeFilters}>Ver resultados</Button></dialog></main>;
}
