'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Home,Search,Sparkles,Heart,UserRound,LogIn } from 'lucide-react';
export default function MobileNavigation({onRadar,radarOpen,favoritesHref,authenticated=false}:{onRadar:()=>void;radarOpen:boolean;favoritesHref:string;authenticated?:boolean}){
 const path=usePathname();
 function focusSearch(){window.scrollTo({top:0,behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'});document.querySelector<HTMLInputElement>('#site-search-input')?.focus()}
 return <nav className="mobile-navigation" aria-label="Navegação mobile"><Link href="/" aria-current={path==='/'&&!radarOpen?'page':undefined}><Home size={21}/><span>Início</span></Link><button onClick={focusSearch}><Search size={21}/><span>Buscar</span></button><button className="mobile-radar" onClick={onRadar} aria-pressed={radarOpen}><Sparkles size={23}/><span>Radar</span></button><a href={favoritesHref}><Heart size={21}/><span>Favoritos</span></a><Link href={authenticated?"/minha-conta":"/entrar"} aria-current={(path==='/conta'||path==='/minha-conta')?'page':undefined}><UserRound size={21}/><span>Conta</span></Link></nav>;
}
