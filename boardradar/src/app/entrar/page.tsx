import {Suspense} from 'react';
import AccountAccess from '@/components/AccountAccess';
import {LoadingSkeleton} from '@/components/ui/States';
export const metadata={title:'Entrar | BoardRadar'};
export default function Page(){return <Suspense fallback={<LoadingSkeleton label="Carregando conta..."/>}><AccountAccess/></Suspense>}
