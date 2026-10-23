import {Suspense} from 'react';
import CatalogBrowser from '@/components/CatalogBrowser';
import {LoadingSkeleton} from '@/components/ui/States';
export const metadata={title:'Buscar jogos | BoardRadar'};
export default function SearchPage(){return <Suspense fallback={<LoadingSkeleton label="Carregando busca…"/>}><CatalogBrowser/></Suspense>}
