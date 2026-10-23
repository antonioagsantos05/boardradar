'use client';
import { Suspense,useEffect,useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Heart,UserRound,Sparkles } from 'lucide-react';
import Brand from '@/components/Brand';
import Button,{buttonClass} from '@/components/ui/Button';
import SearchBar from './SearchBar';
export default function Header({onRadar,onSession}:{onRadar:()=>void;onSession:(value:boolean)=>void}){
 const path=usePathname();const [name,setName]=useState<string|null>(null);
 useEffect(()=>{
  let alive=true;const load=async()=>{try{const r=await fetch('/api/account',{cache:'no-store'});const data=r.ok?await r.json():null;if(alive){setName(data?.user?.name||null);onSession(!!data?.user)}}catch{if(alive){setName(null);onSession(false)}}};
  void load();window.addEventListener('boardradar-session-changed',load);return()=>{alive=false;window.removeEventListener('boardradar-session-changed',load)};
 },[path,onSession]);
 return <><header className="site-header"><div className="site-header-main"><Link className="site-brand" href="/" aria-label="BoardRadar início"><Brand/></Link><Suspense fallback={<div className="site-search">Carregando busca...</div>}><SearchBar/></Suspense><div className="site-header-actions"><a className="site-action" href="/favoritos" title={name?'Wishlist da sua conta':'Favoritos deste navegador'}><Heart size={21} aria-hidden="true"/><span>Favoritos</span></a><Link className={buttonClass()+' site-account-cta'} href={name?'/minha-conta':'/entrar'}><UserRound size={19} aria-hidden="true"/><span>Minha conta</span></Link></div></div><div className="site-header-nav"><nav aria-label="Navegação principal"><Link href="/jogos" aria-current={path==='/jogos'?'page':undefined}>Explorar jogos</Link><Link href="/marketplace" aria-current={path==='/marketplace'?'page':undefined}>Marketplace</Link><Link href="/radar-ai"><Sparkles size={17} aria-hidden="true"/>Descobrir com o Radar</Link></nav><span className="site-nav-note">Um jogo. Novas possibilidades.</span></div></header></>;
}
