'use client';
import { Search,ArrowRight } from 'lucide-react';
import {useEffect,useState} from 'react';
import {useSearchParams} from 'next/navigation';
import Button from '@/components/ui/Button';
import FormField from '@/components/ui/FormField';
export default function SearchBar(){
 const params=useSearchParams();const term=params.get('q')||'';const [query,setQuery]=useState(term);useEffect(()=>{setQuery(term)},[term]);
 return <form action="/buscar" method="get" className="site-search" role="search" aria-label="Busca no catálogo"><Search size={20} aria-hidden="true"/><FormField id="site-search-input" label="Buscar jogos, estilos ou temas" labelHidden><input id="site-search-input" name="q" value={query} onChange={e=>setQuery(e.target.value)} type="search" maxLength={200} placeholder="Busque seu próximo jogo" autoComplete="off"/></FormField><Button type="submit" aria-label="Buscar no catálogo"><span>Buscar</span><ArrowRight size={18} aria-hidden="true"/></Button></form>;
}
