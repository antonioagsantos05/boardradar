'use client';
import Link from 'next/link';
import {ArrowRight,Users,Clock,CalendarDays,Star} from 'lucide-react';
import type {LibrarySummary} from '@/domain/library';
import {WishlistButton,PriceDisplay} from './GameCard';
import CatalogImage from './CatalogImage';
import {rawOffers,rawListings} from '@/repositories/poc';
export default function ImportedGameCard({game:g,saved,onToggle}:{game:LibrarySummary;saved:boolean;onToggle:()=>void}){
 const category=g.categories.slice(0,2).join(' · ')||(g.kind==='boardgameexpansion'?'Expansão':'Jogo de tabuleiro');
 const prices=[...rawOffers,...rawListings].filter(o=>o.game_id===g.curated_game_id).map(o=>Math.round(o.preco_brl*100));
 const href='/jogos/'+g.slug;
 const time=g.max_minutes?(g.min_minutes&&g.min_minutes!==g.max_minutes?`${g.min_minutes}–${g.max_minutes}`:String(g.max_minutes))+' min':'Tempo não informado';
 return <article className="game-card imported-game-card" data-game-id={g.id}><div className="card-visual"><Link href={href} aria-label={'Detalhes de '+g.name}><CatalogImage name={g.name} category={category} url={g.thumbnail||g.image}/></Link><WishlistButton name={g.name} saved={saved} onToggle={onToggle}/></div><div className="card-body"><span className="card-category">{category}</span><h3><Link href={href}>{g.name}</Link></h3><div className="catalog-highlights">{g.year&&<span className="catalog-year"><CalendarDays size={15} aria-hidden="true"/>{g.year}</span>}{g.rating!==null&&g.rating!==undefined&&<span className="catalog-score" aria-label={'Nota BGG: '+g.rating.toFixed(2)+' de 10'}><Star size={15} fill="currentColor" aria-hidden="true"/><strong>{g.rating.toFixed(2)}</strong><small>/10 BGG</small></span>}</div><div className="card-meta"><span><Users size={15}/>{g.min_players&&g.max_players?`${g.min_players}–${g.max_players} jogadores`:'Jogadores não informados'}</span><span><Clock size={15}/>{time}</span></div><PriceDisplay cents={prices.length?Math.min(...prices):undefined} demo/><Link className="card-cta" href={href}>Explorar e comparar <ArrowRight size={17}/></Link></div></article>;
}
