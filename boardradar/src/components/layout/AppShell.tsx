'use client';
import { createContext,useCallback,useContext,useEffect,useRef,useState,type ReactNode } from 'react';
import Header from './Header';
import Footer from './Footer';
import MobileNavigation from './MobileNavigation';
import ChatAssistant from '@/components/ChatAssistant';
import ConfirmationDialog,{type Confirmation} from '@/components/ui/ConfirmationDialog';
type ShellContext={openRadar:()=>void;registerRadarHost:(node:HTMLDivElement|null)=>void;confirm:(request:Confirmation)=>Promise<boolean>};
const Context=createContext<ShellContext|null>(null);
export function useAppShell(){const context=useContext(Context);if(!context)throw Error('AppShell ausente');return context}
export default function AppShell({children}:{children:ReactNode}){
 const [radarHost,setRadarHost]=useState<HTMLDivElement|null>(null);
 const registerRadarHost=useCallback((node:HTMLDivElement|null)=>{setRadarHost(node);if(node)setOpen(false)},[]);
 const [open,setOpen]=useState(false);const [request,setRequest]=useState<Confirmation|null>(null);
 const [authenticated,setAuthenticated]=useState(false);
 const previousFocus=useRef<HTMLElement|null>(null);const pending=useRef<((answer:boolean)=>void)|null>(null);
 const changeRadar=useCallback((value:boolean)=>{if(value){previousFocus.current=document.activeElement instanceof HTMLElement?document.activeElement:null;setOpen(true);requestAnimationFrame(()=>document.querySelector<HTMLInputElement>('.chat-input input')?.focus())}else{setOpen(false);requestAnimationFrame(()=>previousFocus.current?.isConnected&&previousFocus.current.focus())}},[]);
 const openRadar=useCallback(()=>{if(radarHost){radarHost.querySelector<HTMLInputElement>('.chat-input input')?.focus({preventScroll:true});return}changeRadar(true)},[changeRadar,radarHost]);
 const confirm=useCallback((next:Confirmation)=>{if(pending.current)return Promise.resolve(false);setRequest(next);return new Promise<boolean>(resolve=>{pending.current=resolve})},[]);
 function decide(answer:boolean){const resolve=pending.current;pending.current=null;setRequest(null);resolve?.(answer)}
 useEffect(()=>()=>{pending.current?.(false)},[]);
 return <Context.Provider value={{openRadar,registerRadarHost,confirm}}><div className="app-shell"><a className="skip-link" href="#page-content">Pular para o conteúdo</a><Header onRadar={openRadar} onSession={setAuthenticated}/><div id="page-content" tabIndex={-1}>{children}</div><Footer authenticated={authenticated}/><MobileNavigation authenticated={authenticated} onRadar={openRadar} radarOpen={open} favoritesHref="/favoritos"/><ChatAssistant host={radarHost} open={open} onOpenChange={changeRadar}/><ConfirmationDialog request={request} onDecision={decide}/></div></Context.Provider>;
}
