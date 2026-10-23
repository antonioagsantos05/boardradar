'use client';
import { displayText } from "@/domain/presentation";
import Link from 'next/link';
import CommunityActions from './CommunityActions';
import {gameRepository} from '@/repositories/catalog';
import type {Listing} from './CommunityListings';
const conditions:Record<string,string>={new:'Novo',like_new:'Como novo',good:'Bom estado',fair:'Com desgaste'};
export default function UserListingCard({item,hideGameLink=false}:{item:Listing;hideGameLink?:boolean}){return <article className="account-game community-card">{item.images[0]&&<img loading="lazy" decoding="async" width={640} height={480} src={'/api/listing-images?id='+item.images[0].id} alt={'Foto de '+item.title}/>}<span className="eyebrow">{'Venda de usuário · '+(conditions[item.condition]||item.condition)}</span><h3><Link href={'/anuncios/'+item.id}>{displayText(item.title)}</Link></h3><p>{item.game_name} · {displayText(item.edition_name)}</p><p>{item.language} · {item.region}</p><strong>{(item.price_cents/100).toLocaleString('pt-BR',{style:'currency',currency:'BRL'})}</strong><p>{item.sealed?'Lacrado · ':''}{item.negotiable?'Negociável · ':''}{{pickup:'Retirada',shipping:'Envio a combinar',both:'Envio ou retirada',unspecified:'Entrega não informada'}[item.delivery]}</p><CommunityActions id={item.id} editionId={item.edition_id}/>{!hideGameLink&&<Link className="button light" href={'/jogos/'+gameRepository.byId(item.game_id)?.slug+'?edition='+encodeURIComponent(item.edition_id)+'#comunidade'}>Ver jogo e comparar</Link>}</article>}
