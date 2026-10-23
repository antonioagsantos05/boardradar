import Link from 'next/link';
import LibraryFacts from './LibraryFacts';
import GameComparison from './GameComparison';
import PocOffers from './PocOffers';
import type {LibraryGame} from '@/domain/library';
import CatalogImage from './CatalogImage';
export default function LibraryDetail({game}:{game:LibraryGame}){
 return <main className="container detail-main product-page"><div className="breadcrumbs"><Link href="/">Início</Link><span>›</span><Link href="/jogos">Jogos</Link><span>›</span><span>{game.name}</span></div><section className="library-overview detail-overview"><CatalogImage large name={game.name} category={game.categories.slice(0,2).join(' · ')} url={game.image}/><div className="detail-info"><div className="eyebrow dark">BGG #{game.bgg_id}</div><h1>{game.name}</h1><p>{game.description}</p><div className="product-actions"><a className="button amber" href="#comparar">Comparar jogos</a><a className="button light" href="#ofertas">Comparar ofertas</a></div></div></section><PocOffers gameId={game.curated_game_id}/><LibraryFacts game={game}/><GameComparison gameId={game.id}/></main>;
}
