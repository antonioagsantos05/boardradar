import {notFound} from 'next/navigation';
import LibraryDetail from '@/components/LibraryDetail';
import {library} from '@/server/library';
export async function generateMetadata({params}:{params:Promise<{slug:string}>}){const game=library.bySlug((await params).slug);return {title:game?game.name+' | BoardRadar':'Jogo não encontrado | BoardRadar',description:game?'Informações do jogo, avaliações e comparação de ofertas.':undefined,alternates:game?{canonical:'/jogos/'+game.slug}:undefined}}
export default async function GamePage({params}:{params:Promise<{slug:string}>}){const game=library.bySlug((await params).slug);if(!game)notFound();return <LibraryDetail game={game}/>}
