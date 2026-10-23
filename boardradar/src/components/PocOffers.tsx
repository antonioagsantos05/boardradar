import {displayText} from '@/domain/presentation';
import Link from 'next/link';
import {rawOffers,rawEditions,rawStores,rawListings} from '@/repositories/poc';
export default function PocOffers({gameId}:{gameId?:string}){
 const offers=rawOffers.filter(o=>!gameId||o.game_id===gameId);
 const listings=rawListings.filter(l=>!gameId||l.game_id===gameId);
 const money=(n:number)=>n.toLocaleString('pt-BR',{style:'currency',currency:'BRL'});
 return <section className="detail-section" id="ofertas"><h2>Ofertas de lojas</h2><div className="community-grid">{offers.map(o=><article className="account-game" key={o.offer_id}><span className="eyebrow">Loja</span><h3>{rawStores.find(s=>s.store_id===o.store_id)?.nome}</h3><p>{displayText(rawEditions.find(e=>e.edition_id===o.edition_id)?.nome_edicao||'')}</p><strong>{money(o.preco_brl)}</strong><p>{o.condicao} · frete não informado</p><small>Edição: {o.edition_id}</small></article>)}</div>{gameId&&<><h2 id="comunidade">Vendedores da comunidade</h2><div className="community-grid">{listings.map(l=><article className="account-game" key={l.listing_id}><span className="eyebrow">Vendedor</span><h3>{displayText(l.titulo)}</h3><strong>{money(l.preco_brl)}</strong><p>{l.condicao} · {l.cidade} / {l.uf}</p>{displayText(l.descricao_anuncio)&&<p>{displayText(l.descricao_anuncio)}</p>}<small>Edição: {l.edition_id}</small><p><Link href={'/anuncios/'+l.listing_id}>Ver anúncio</Link></p></article>)}</div></>}</section>;
}
