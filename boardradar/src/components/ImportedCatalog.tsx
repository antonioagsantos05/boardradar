'use client';
import { useEffect,useRef,useState } from 'react';
import Link from 'next/link';
import type { LibrarySummary } from '@/domain/library';
import type { Preferences } from '@/domain/models';
import { gameRepository } from '@/repositories/catalog';

const categoryLabels:Record<string,string>={Economic:'Economia',Negotiation:'Negociação',Political:'Política',Adventure:'Aventura',Exploration:'Exploração',Fantasy:'Fantasia',Fighting:'Combate',Medieval:'Medieval',Renaissance:'Renascimento',Animals:'Animais',Racing:'Corrida',Sports:'Esportes',Horror:'Terror',Humor:'Humor',Deduction:'Dedução',Civilization:'Civilizações',Abstract:'Abstrato','Abstract Strategy':'Estratégia abstrata','Card Game':'Cartas','City Building':'Construção de cidades','Dice':'Dados','Educational':'Educativo','Environmental':'Meio ambiente','Industry / Manufacturing':'Indústria','Memory':'Memória','Movies / TV / Radio theme':'Cinema e TV','Party Game':'Festa','Puzzle':'Quebra-cabeça','Science Fiction':'Ficção científica','Space Exploration':'Exploração espacial','Trains':'Trens','Trivia':'Perguntas e respostas','Wargame':'Guerra','Word Game':'Palavras','World War II':'Segunda Guerra Mundial','Territory Building':'Construção de território'};
const categoryLabel=(category:string)=>categoryLabels[category]||category;
type PageData={total:number;page:number;page_count:number;page_size:number;results:LibrarySummary[]};

function pageNumbers(current:number,total:number){
 const numbers=new Set([1,total]);
 for(let n=Math.max(1,current-2);n<=Math.min(total,current+2);n++)numbers.add(n);
 if(current<=3)for(let n=1;n<=Math.min(5,total);n++)numbers.add(n);
 if(current>=total-2)for(let n=Math.max(1,total-4);n<=total;n++)numbers.add(n);
 const result:(number|string)[]=[];
 for(const n of [...numbers].sort((a,b)=>a-b)){
  const last=result.at(-1);if(typeof last==='number'&&n-last>1)result.push('gap-'+n);
  result.push(n);
 }
 return result;
}

export default function ImportedCatalog({preferences}:{preferences:Preferences}){
 const [kind,setKind]=useState('all');const [page,setPage]=useState(1);const [jump,setJump]=useState('');
 const [pageSize,setPageSize]=useState(24);
 const [data,setData]=useState<PageData>({total:0,page:1,page_count:1,page_size:24,results:[]});
 const [loading,setLoading]=useState(true);const [error,setError]=useState('');
 const headingRef=useRef<HTMLHeadingElement>(null);const scrollAfterLoad=useRef(false);
 const {query='',players,duration,budget,style}=preferences;
 useEffect(()=>{setPage(1);setJump('')},[query,players,duration,kind,style]);
 useEffect(()=>{
  const controller=new AbortController();setLoading(true);
  const timer=setTimeout(async()=>{
   try{
    const p=new URLSearchParams({q:query,kind,page:String(page),page_size:String(pageSize)});if(players)p.set('players',String(players));if(duration)p.set('duration',String(duration));
    const r=await fetch('/api/library?'+p,{signal:controller.signal});if(!r.ok)throw Error('Não foi possível consultar a base ampliada.');
    const json:PageData=await r.json();if(controller.signal.aborted)return;
    setData(json);setError('');
    if(scrollAfterLoad.current){headingRef.current?.scrollIntoView({behavior:'smooth',block:'start'});scrollAfterLoad.current=false}
   }catch(e){if(!controller.signal.aborted)setError(e instanceof Error?e.message:'Erro na busca.')}
   finally{if(!controller.signal.aborted)setLoading(false)}
  },250);
  return()=>{clearTimeout(timer);controller.abort()};
 },[query,players,duration,kind,page,pageSize]);
 function goTo(value:number){const next=Math.max(1,Math.min(data.page_count,value));if(next===data.page)return;scrollAfterLoad.current=true;setPage(next);setJump('')}
 const pagination=(position:string)=><nav className="library-pagination" aria-label={'Paginação do catálogo — '+position}>
  <button className="button light" disabled={data.page<=1||loading} onClick={()=>goTo(data.page-1)}>Anterior</button>
  <div className="library-page-numbers">{pageNumbers(data.page,data.page_count).map(n=>typeof n==='number'?<button key={n} className={'library-page '+(data.page===n?'current':'')} aria-label={'Página '+n} aria-current={data.page===n?'page':undefined} disabled={loading} onClick={()=>goTo(n)}>{n}</button>:<span key={n} aria-hidden="true">…</span>)}</div>
  <button className="button light" disabled={data.page>=data.page_count||loading} onClick={()=>goTo(data.page+1)}>Próxima</button>
 </nav>;
 return <section className="container imported-catalog" id="base-ampliada">
  <div className="section-heading"><div><h2 ref={headingRef}>Base ampliada de jogos</h2><p>{data.total.toLocaleString('pt-BR')} registros BGG encontrados · página {data.page} de {data.page_count}</p></div></div>
  <p className="chart-note">Pesquise por nome, jogadores e duração nos filtros da página. As categorias indicam o tema do jogo; o formato do produto distingue jogo e expansão quando a origem informa esse dado.</p>
  {(budget!==undefined||style||preferences.videogames?.length)&&<p className="notice">Os filtros de orçamento, estilo editorial e afinidade com videogames valem para a seleção acima. Esta base adicional oferece consulta por nome, jogadores, duração e formato; não tem preços nem afinidades verificadas.</p>}
  <label className="library-kind">Formato do produto<select value={kind} onChange={e=>setKind(e.target.value)}><option value="all">Todos os formatos</option><option value="boardgame">Jogos identificados pela origem</option><option value="boardgameexpansion">Expansões identificadas</option><option value="unclassified">Formato não informado pela origem</option></select></label>
  <label className="library-kind">Jogos por página<select value={pageSize} onChange={e=>{setPageSize(Number(e.target.value));setPage(1);setJump('')}}>{[12,24,48,96].map(size=><option key={size} value={size}>{size} jogos</option>)}</select></label>
  <div className="library-results-status" role="status" aria-live="polite">{loading?'Buscando na base ampliada…':!error&&data.total>0?`Mostrando ${(data.page-1)*data.page_size+1}–${Math.min(data.page*data.page_size,data.total)} de ${data.total.toLocaleString('pt-BR')} registros`:''}</div>
  {error&&<p role="alert">{error}</p>}
  <div className="library-grid" aria-busy={loading}>{data.results.map(g=>{
   const curated=g.curated_game_id?gameRepository.byId(g.curated_game_id):undefined;
   const categories=g.categories||[];const time=g.max_minutes?(g.min_minutes&&g.min_minutes!==g.max_minutes?`${g.min_minutes}–${g.max_minutes}`:String(g.max_minutes))+' min':'Tempo não informado';
   return <Link className="library-card" key={g.id} href={'/jogos/'+(curated?.slug||g.slug)}>
    <span className="library-category">{categories.length?categories.slice(0,2).map(categoryLabel).join(' · '):'Categoria não informada'}</span>
    <h3>{g.name}</h3><span>{g.year||'Ano não informado'}{g.kind==='boardgameexpansion'?' · Expansão':g.kind==='boardgame'?' · Jogo':''}</span>
    <p>{g.min_players&&g.max_players?`${g.min_players}–${g.max_players} jogadores`:'Jogadores não informados'} · {time}</p><strong>Ver informações e comparar →</strong>
   </Link>;
  })}</div>
  {!loading&&!error&&data.results.length===0&&<p>Nenhum registro com esses filtros.</p>}
  {data.total>0&&<>{pagination('abaixo dos jogos')}<form className="library-page-jump" onSubmit={e=>{e.preventDefault();const n=Number(jump);if(Number.isInteger(n)&&n>=1&&n<=data.page_count)goTo(n)}}><label>Ir para a página<input aria-label="Número da página" type="number" min={1} max={data.page_count} step={1} required value={jump} placeholder={String(data.page)} onChange={e=>setJump(e.target.value)} disabled={loading}/></label><button className="button light" disabled={loading||!jump}>Ir</button><span>de {data.page_count}</span></form></>}
 </section>;
}
