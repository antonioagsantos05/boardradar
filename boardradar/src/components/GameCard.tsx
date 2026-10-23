'use client';
import Link from 'next/link';
import {ArrowRight,Compass,Heart,Users,Clock} from 'lucide-react';
import type {Game} from '@/domain/models';
import {money,validOffers} from '@/domain/recommendation';

export function GameCover({game,large=false}:{game:Pick<Game,'name'|'category'|'color'>;large?:boolean}){
 return <div className={'game-cover '+(large?'large':'')} role="img" aria-label={'Capa ilustrativa de '+game.name} style={{'--cover':game.color} as React.CSSProperties}><div className="cover-grid"/><Compass className="cover-symbol" strokeWidth={.7}/><span className="cover-edition">BOARDRADAR · CAPA ILUSTRATIVA</span><strong>{game.name}</strong><span className="cover-foot">{game.category}</span></div>;
}
export function WishlistButton({name,saved,onToggle}:{name:string;saved:boolean;onToggle:()=>void}){
 return <button type="button" className={'favorite '+(saved?'liked':'')} aria-pressed={saved} aria-label={(saved?'Remover dos':'Adicionar aos')+' favoritos locais: '+name} onClick={onToggle}><Heart size={19} fill={saved?'currentColor':'none'}/></button>;
}
export function GameMetadata({game}:{game:Game}){
 return <div className="card-meta"><span><Users size={15}/>{game.players.min}–{game.players.max} jogadores</span><span><Clock size={15}/>{game.duration} min</span></div>;
}
export function PriceDisplay({cents,demo=false,unknown=false}:{cents?:number;demo?:boolean;unknown?:boolean}){
 return <div className="price-line"><span>{unknown?'Sem preço verificado':cents===undefined?'Sem oferta atual':demo?'A partir de':'Preço do anúncio'}</span><strong>{cents===undefined?'Consulte a ficha':money(cents)}</strong></div>;
}
export default function GameCard({game,saved,onToggle,reason}:{game:Game;saved:boolean;onToggle:()=>void;reason?:string}){
 const href='/jogos/'+game.slug;
 return <article className="game-card"><div className="card-visual"><Link href={href} aria-label={'Detalhes de '+game.name}><GameCover game={game}/></Link><WishlistButton name={game.name} saved={saved} onToggle={onToggle}/></div><div className="card-body"><span className="card-category">{game.category}</span><h3><Link href={href}>{game.name}</Link></h3><GameMetadata game={game}/>{reason&&<p className="match-reason">{reason}</p>}<PriceDisplay cents={validOffers(game)[0]?.price_cents} demo/><Link className="card-cta" href={href}>Explorar e comparar <ArrowRight size={17}/></Link></div></article>;
}
