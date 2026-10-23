'use client';
import {Store} from 'lucide-react';
import {eligibleOffer,isFresh} from '@/domain/offer-policy';
import {money} from '@/domain/recommendation';
import {offerRepository} from '@/repositories/catalog';
import type {Offer} from '@/domain/models';
import Button from './ui/Button';
export default function OfferCard({offer:o,editionId,onDemo}:{offer:Offer;editionId:string;onDemo:()=>void}){
 const store=offerRepository.stores().find(s=>s.id===o.store_id);
 const available=eligibleOffer(o,editionId,new Set(offerRepository.stores().filter(s=>s.is_demo).map(s=>s.id)));
 return <article className="offer-card" data-edition={o.edition_id}><div><span className="offer-source"><Store size={19}/>{store?.name||'Loja não identificada'}</span><span className="offer-demo">Loja</span></div><div><strong className="offer-price">{money(o.price_cents)}</strong><span>Produto · frete não incluído</span><span>Condição: {o.condition}</span></div><div><span className={available?'offer-available':'offer-unavailable'}>{available?'Oferta cadastrada':o.availability!=='in_stock'?'Indisponível':'Oferta desatualizada ou inelegível'}</span><span>Atualizado em: {new Date(o.checked_at).toLocaleDateString('pt-BR',{timeZone:'America/Sao_Paulo'})}</span><span>{isFresh(o.checked_at)?'Atualização recente':'Desatualizada'}</span></div><Button disabled={!available} onClick={onDemo}>Ver oferta</Button></article>;
}
