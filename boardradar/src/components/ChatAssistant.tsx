'use client';
import { useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import {createPortal} from 'react-dom';
import {useRouter} from 'next/navigation';
import ChatGameActions from './ChatGameActions';
import { ArrowRight, Check, LoaderCircle, Maximize2, MessageCircle, Minimize2, RotateCcw, Send, Sparkles, X } from 'lucide-react';
import { gameRepository } from '@/repositories/catalog';
import {readProfile} from '@/domain/profile-storage';
import {displayText} from '@/domain/presentation';
import { money } from '@/domain/recommendation';

type EditorialLink={title:string;rationale:string;connection_type:string;review_status:string};
type Recommendation={id:string;name:string;reason:string;price_cents:number|null;editorial_links?:EditorialLink[]};
type InformationalGame={id:string;name:string;description:string;players:{min:number;max:number};duration:number;eligible_for_preferences:boolean};
type Comparison={games:{id:string;name:string}[];rows:{attribute:string;values:(string|number)[]}[]};
type EditionGroup={game_id:string;game_name:string;editions:{id:string;name:string;language:string;type:string}[]};
type OfferGroup={game_id:string;game_name:string;edition_id:string;edition_name:string;language:string;eligible_for_preferences:boolean;offers:{id:string;price_cents:number;store_name:string;checked_at:string;condition:string;within_budget:boolean}[]};
type Citation={source_id:string;chunk_id:string;title:string;section:string;page:number|null;game_id:string|null;edition_id:string|null;version:string;date:string;license:string;url:string|null;authority:'editorial'|'official';excerpt:string};
type LibraryCard={id:string;name:string;slug:string;year:number|null;kind:string};
type CommunityOffer={id:string;title:string;game_id:string;edition_id:string;edition_name:string;price_cents:number;condition:string;language:string};
type Message={actions?:{label:string;href:string}[];community_offers?:CommunityOffer[];role:'assistant'|'user';text:string;recommendations?:Recommendation[];game_details?:InformationalGame[];comparison?:Comparison;edition_details?:EditionGroup[];offer_groups?:OfferGroup[];sources?:Citation[];library_games?:LibraryCard[]};
const welcome:Message={role:'assistant',text:'Oi! Sou o Radar. Vamos encontrar uma partida com a sua cara? Conte o tipo de experiência que procura. Consulto o catálogo para encontrar opções para você.'};
const initialSuggestions=['Usar meus gostos','Jogos para 4 pessoas','Quero anunciar um jogo'];
const connectionLabel=(type:string)=>type==='thematic'?'Temática':type==='mechanical'?'Mecânica':'Temática e mecânica';
const pendingReview='Revisão editorial pendente';

function InformationCard({detail}:{detail:InformationalGame}){
 const game=gameRepository.byId(detail.id);
 if(!game)return null;
 return <Link className="chat-recommendation chat-information" href={'/jogos/'+game.slug}><div><span>Ficha informativa · não é recomendação</span><strong>{game.name}</strong><p>{detail.description}</p><p>{detail.players.min}–{detail.players.max} jogadores · {detail.duration} min · metadados preliminares.</p>{!detail.eligible_for_preferences&&<span>Não atende às condições atuais da sua busca.</span>}</div><ArrowRight size={15}/></Link>;
}

function ToolResults({message}:{message:Message}){
 return <>{message.comparison&&<div className="chat-table-wrap" tabIndex={0} role="region" aria-label="Comparação de jogos"><table className="chat-table"><caption>Atributos preliminares do catálogo</caption><thead><tr><th scope="col">Atributo</th>{message.comparison.games.map(g=><th scope="col" key={g.id}>{g.name}</th>)}</tr></thead><tbody>{message.comparison.rows.map(r=><tr key={r.attribute}><th scope="row">{r.attribute}</th>{r.values.map((v,i)=><td key={i}>{v}</td>)}</tr>)}</tbody></table></div>}
 {message.edition_details?.map(group=><div className="chat-tool" key={group.game_id}><strong>Edições · {group.game_name}</strong>{group.editions.map(e=><div key={e.id}><p>{e.name}</p><p>{e.language} · {e.type==='base'?'Jogo-base':'Expansão'}</p><small>Identificador: {e.id} · dados a confirmar</small></div>)}</div>)}
 {message.offer_groups?.map(group=><div className="chat-tool" key={group.edition_id}><strong>{group.game_name} · ofertas</strong><p>{displayText(group.edition_name)} · {group.language}</p>{!group.eligible_for_preferences&&<p>O jogo não atende a todas as condições atuais da busca.</p>}{group.offers.length===0?<p>Nenhuma oferta recente e disponível para esta edição.</p>:group.offers.map(o=><div className="chat-offer" key={o.id}><strong>{o.store_name} · {money(o.price_cents)}</strong><small>{o.condition} · sem frete · conferido em {new Date(o.checked_at).toLocaleDateString('pt-BR',{timeZone:'UTC'})}</small>{!o.within_budget&&<span>Acima do seu orçamento</span>}</div>)}<ChatGameActions gameId={group.game_id} editionId={group.edition_id}/></div>)}</>;
}

function SourceResults({sources}:{sources?:Citation[]}){
 if(!sources?.length)return null;
 return <div className="chat-sources" role="group" aria-label="Fontes da resposta">{[...new Map(sources.map(source=>[source.excerpt,source])).values()].map(source=><p className="chat-source-excerpt" key={source.chunk_id}>{source.excerpt}</p>)}<strong>Fontes consultadas</strong>{sources.map(source=><details className="chat-source" key={source.chunk_id}><summary>{source.section}<small>{source.authority==='official'?'Manual/FAQ da edição':'Guia editorial · não é manual'}</small></summary><blockquote>{source.excerpt}</blockquote><p>{source.title} · versão {source.version}</p><p>{source.page!==null?`Página ${source.page} · `:''}{source.section}</p>{source.edition_id&&<p>Edição: {source.edition_id}</p>}<p>Registrado em {source.date.split('-').reverse().join('/')} · {source.license==='project-owned'?'Conteúdo próprio BoardRadar':source.license}</p>{source.url?.startsWith('https://')&&<a href={source.url} target="_blank" rel="noopener noreferrer">Documento original</a>}</details>)}</div>;
}

function LibraryResults({games}:{games?:LibraryCard[]}){
 return <>{games?.map(g=><Link key={g.id} className="chat-recommendation chat-information" href={'/jogos/'+g.slug}><div><strong>{g.name}</strong><p>Ficha BGG · {g.year||'Ano não informado'} · {g.kind==='boardgameexpansion'?'Expansão':'edição a confirmar'}</p><span>Consulta informativa · sem oferta verificada</span></div><ArrowRight size={15}/></Link>)}</>;
}

export default function ChatAssistant({open,onOpenChange,host}:{host?:HTMLElement|null;open:boolean;onOpenChange:(value:boolean)=>void}){
 const router=useRouter();const inline=!!host;const active=open||inline;
 useEffect(()=>{if(inline)setExpanded(false)},[inline]);
 const [messages,setMessages]=useState<Message[]>([welcome]);
 const [expanded,setExpanded]=useState(false);
 const panelRef=useRef<HTMLElement>(null);
 const [input,setInput]=useState('');const [state,setState]=useState<Record<string,unknown>>();
 const [suggestions,setSuggestions]=useState(initialSuggestions);const [pending,setPending]=useState(false);const [error,setError]=useState('');
 const endRef=useRef<HTMLDivElement>(null);const inputRef=useRef<HTMLInputElement>(null);const requestRef=useRef<AbortController|null>(null);const inFlight=useRef(false);const generation=useRef(0);
 useEffect(()=>{const log=endRef.current?.parentElement;log?.scrollTo({top:log.scrollHeight,behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'})},[messages,pending,error,active,inline]);
 useEffect(()=>{if(!active)return;const controller=new AbortController();fetch('/api/account',{cache:'no-store',signal:controller.signal}).then(async r=>{if(!r.ok)return;const b=await r.json();const profile=b.profile||readProfile(b.user.id);setMessages(previous=>previous.length===1&&previous[0].role==='assistant'?[{...welcome,text:b.user.name.split(' ')[0]+', vamos encontrar sua próxima partida? '+(profile?.consent?'Posso partir dos seus estilos e franquias favoritas ou seguir o que você procura hoje.':'Conte o que você gosta ou diga quantas pessoas vão jogar.')}]:previous)}).catch(()=>{});return()=>controller.abort()},[active]);
 useEffect(()=>{if(active)inputRef.current?.focus({preventScroll:true})},[active,inline]);
 useEffect(()=>()=>{generation.current++;requestRef.current?.abort()},[]);
 useEffect(()=>{if(!open||inline)return;function close(e:KeyboardEvent){if(e.key==='Escape'){if(expanded)setExpanded(false);else onOpenChange(false)}}window.addEventListener('keydown',close);return()=>window.removeEventListener('keydown',close)},[open,expanded,onOpenChange,inline]);
 useEffect(()=>{if(!open||!expanded||inline)return;const previous=document.body.style.overflow;document.body.style.overflow='hidden';return()=>{document.body.style.overflow=previous}},[open,expanded,inline]);
 useEffect(()=>{
  if(!open||!expanded||inline)return;
  function keepFocus(event:KeyboardEvent){
   if(event.key!=='Tab')return;
   const panel=panelRef.current;if(!panel)return;
   const controls=[...panel.querySelectorAll<HTMLElement>('button:not([disabled]),a[href],input:not([disabled]),[tabindex="0"]')].filter(e=>e.getClientRects().length>0);
   const first=controls[0],last=controls.at(-1);if(!first||!last)return;
   if(!panel.contains(document.activeElement)){event.preventDefault();first.focus()}
   else if(event.shiftKey&&document.activeElement===first){event.preventDefault();last.focus()}
   else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first.focus()}
  }
  document.addEventListener('keydown',keepFocus);return()=>document.removeEventListener('keydown',keepFocus);
 },[open,expanded,inline]);
 async function send(value=input){
  const message=value.trim();if(!message||inFlight.current)return;
  const version=generation.current;const controller=new AbortController();requestRef.current=controller;inFlight.current=true;
  setError('');setPending(true);setInput('');
  const timeout=setTimeout(()=>controller.abort(),15000);
  setMessages(previous=>[...previous,{role:'user',text:message}]);
  try{
   let local_profile;try{const account=await fetch('/api/account',{cache:'no-store',signal:controller.signal});if(account.ok){const b=await account.json();local_profile=readProfile(b.user.id)||undefined}}catch{}
   const response=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message,state,local_profile}),signal:controller.signal});
   const reply=await response.json();if(!response.ok)throw Error(reply.error||'Não consegui responder agora.');
   if(version!==generation.current)return;
   setState(reply.state);setSuggestions(reply.suggestions||[]);setMessages(previous=>[...previous,{role:'assistant',text:reply.text,actions:reply.actions,recommendations:reply.recommendations,game_details:reply.game_details,comparison:reply.comparison,edition_details:reply.edition_details,offer_groups:reply.offer_groups,sources:reply.sources,library_games:reply.library_games,community_offers:reply.community_offers}]);
  }catch(e){if(version===generation.current){setError(e instanceof Error&&e.name!=='AbortError'?e.message:'A resposta demorou mais que o esperado. Tente novamente.');setInput(message)}}
  finally{clearTimeout(timeout);if(version===generation.current){setPending(false);inFlight.current=false;requestRef.current=null}}
 }
 useEffect(()=>{const clear=()=>reset();window.addEventListener('boardradar-session-changed',clear);return()=>window.removeEventListener('boardradar-session-changed',clear)},[]);
 function cancel(){generation.current++;requestRef.current?.abort();inFlight.current=false;setPending(false);setError('Consulta cancelada. Sua pergunta voltou ao campo para você editar ou reenviar.');setInput(messages.at(-1)?.role==='user'?messages.at(-1)!.text:'');inputRef.current?.focus()}
 function reset(){generation.current++;requestRef.current?.abort();inFlight.current=false;setMessages([welcome]);setState(undefined);setSuggestions(initialSuggestions);setInput('');setPending(false);setError('');inputRef.current?.focus()}
 if(!active)return <button className="chat-launcher" onClick={()=>onOpenChange(true)}><MessageCircle size={22}/><span>Pergunte ao Radar</span><span className="chat-dot"/></button>;
 const panel=<section ref={panelRef} role={!inline&&expanded?'dialog':'region'} aria-modal={!inline&&expanded?true:undefined} className={inline?"chat-panel chat-inline":expanded?"chat-panel chat-expanded":"chat-panel"} aria-label="Assistente Radar"><div className="chat-header"><span className="chat-avatar"><Sparkles size={21}/></span><div><strong>Radar</strong><span>Seu próximo jogo começa nesta conversa</span></div>{inline?<button className="chat-mode-button" onClick={()=>{onOpenChange(true);router.push('/jogos')}}>Usar janela compacta</button>:<><Link className="chat-mode-button" href="/radar-ai">Página do Radar</Link><button className="icon-button" onClick={()=>setExpanded(value=>!value)} aria-label={expanded?"Reduzir chat":"Expandir chat"} title={expanded?"Reduzir chat":"Expandir chat"} aria-pressed={expanded}>{expanded?<Minimize2 size={20}/>:<Maximize2 size={20}/>}</button><button className="icon-button" onClick={()=>{setExpanded(false);onOpenChange(false)}} aria-label="Fechar assistente"><X/></button></>}</div><div className="chat-disclaimer"><Check size={11}/> Descubra jogos com a sua cara</div><div className="chat-messages" role="log" aria-label="Conversa com Radar" aria-live="polite" aria-busy={pending}>{messages.map((m,index)=><div key={index} className={'message '+m.role}><span className="chat-speaker">{m.role==='user'?'Você':'Radar'}</span><p className="chat-response-text">{m.text}</p>{m.actions?.filter(a=>['/vender','/meus-anuncios','/mensagens','/marketplace','/minha-conta?sec=perfil'].includes(a.href)).map(a=><Link className="button light chat-flow-action" key={a.href} href={a.href}>{a.label}<ArrowRight size={15}/></Link>)}{m.recommendations?.map(r=>{const game=gameRepository.byId(r.id);return game?<article key={r.id} className="chat-recommendation"><div><div><strong>{game.name}</strong><p>{r.reason}</p>{r.editorial_links?.map((link,i)=><p className="chat-editorial" key={i}>{link.title}: {link.rationale}<br/><small>{connectionLabel(link.connection_type)} / {pendingReview}</small></p>)}<span>{r.price_cents!==null?money(r.price_cents)+'':'Sem oferta recente'}</span></div><ChatGameActions gameId={game.id}/></div></article>:null})}<LibraryResults games={m.library_games}/>{m.community_offers?.length?<div className="chat-tool"><strong>Anúncios ativos da comunidade</strong><p>Dados informados pelos vendedores; separados das lojas. Confira a disponibilidade e a conservação.</p>{m.community_offers.map(o=><Link className="chat-recommendation" key={o.id} href={'/anuncios/'+o.id}><div><strong>{o.title}</strong><p>{o.edition_name} · {o.language}</p><span>{money(o.price_cents)} · venda de usuário</span></div></Link>)}</div>:null}<ToolResults message={m}/><SourceResults sources={m.sources}/>{m.game_details?.map(detail=><InformationCard key={detail.id} detail={detail}/>)}</div>)}{pending&&<div className="message assistant thinking"><span role="status"><LoaderCircle size={15}/> Consultando o catálogo…</span><button type="button" onClick={cancel}>Cancelar consulta</button></div>}{error&&<div className="chat-error" role="alert">{error}<span>Edite a mensagem no campo abaixo ou envie novamente.</span></div>}<div ref={endRef}/></div><div className="chat-suggestions" aria-label="Sugestões para continuar">{suggestions.map(s=><button key={s} disabled={pending} onClick={()=>send(s)}>{s}</button>)}</div><form className="chat-input" onSubmit={e=>{e.preventDefault();void send()}}><input ref={inputRef} aria-label="Mensagem para Radar" placeholder="Pergunte, compare ou peça uma indicação…" value={input} maxLength={1000} onChange={e=>setInput(e.target.value)}/><button className="button amber" aria-label="Enviar mensagem" disabled={pending||!input.trim()}>{pending?<LoaderCircle className="spin" size={18}/>:<Send size={18}/>}</button></form><button className="chat-reset" onClick={reset}><RotateCcw size={11}/> Recomeçar conversa</button></section>;
 return host?createPortal(panel,host):panel;
}
