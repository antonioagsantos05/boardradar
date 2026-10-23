import {Suspense} from 'react';
import AccountArea from '@/components/AccountArea';
import {LoadingSkeleton} from '@/components/ui/States';
export const metadata={title:'Seu perfil | BoardRadar'};
export default function Page(){return <Suspense fallback={<LoadingSkeleton label="Carregando conta..."/>}><AccountArea mode="onboarding"/></Suspense>}
