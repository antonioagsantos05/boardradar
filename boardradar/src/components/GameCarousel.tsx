"use client";
import {useEffect,useRef,useState} from 'react';
import {ChevronLeft,ChevronRight} from 'lucide-react';
import type {ReactNode} from 'react';
export default function GameCarousel({label,children}:{label:string;children:ReactNode}){
 const ref=useRef<HTMLDivElement>(null);const [position,setPosition]=useState({start:true,end:false});
 function sync(){const el=ref.current;if(el)setPosition({start:el.scrollLeft<4,end:el.scrollLeft+el.clientWidth>=el.scrollWidth-4})}
 useEffect(()=>{const el=ref.current;if(!el)return;sync();const observer=new ResizeObserver(sync);observer.observe(el);return()=>observer.disconnect()},[children]);
 function move(direction:number){const el=ref.current;if(el)el.scrollBy({left:direction*(el.clientWidth+20),behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'})}
 return <div className="home-carousel"><div className="carousel-controls"><button type="button" aria-label={'Anteriores: '+label} disabled={position.start} onClick={()=>move(-1)}><ChevronLeft size={20}/></button><button type="button" aria-label={'Próximos: '+label} disabled={position.end} onClick={()=>move(1)}><ChevronRight size={20}/></button></div><div ref={ref} className="home-carousel-track" role="region" aria-label={label} tabIndex={0} onScroll={sync} onKeyDown={e=>{if(e.key==='ArrowRight'||e.key==='ArrowLeft'){e.preventDefault();move(e.key==='ArrowRight'?1:-1)}}}>{children}</div></div>
}
