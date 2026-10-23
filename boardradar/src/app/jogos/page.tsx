import {Suspense} from 'react';
import CatalogBrowser from '@/components/CatalogBrowser';
import {LoadingSkeleton} from '@/components/ui/States';
export const metadata={alternates:{canonical:'/jogos'},description:'Explore jogos e compare suas próximas partidas.',title:'Catálogo de jogos | BoardRadar'};
export default function GamesPage(){return <Suspense fallback={<LoadingSkeleton label="Carregando catálogo…"/>}><CatalogBrowser/></Suspense>}
