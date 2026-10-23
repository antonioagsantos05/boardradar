import {Suspense} from 'react';
import SellWizard from '@/components/SellWizard';
import {LoadingSkeleton} from '@/components/ui/States';
export const metadata={title:'Vender um jogo | BoardRadar'};
export default function SellPage(){return <Suspense fallback={<LoadingSkeleton label="Carregando venda…"/>}><SellWizard/></Suspense>}
