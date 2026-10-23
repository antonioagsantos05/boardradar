'use client';
import { useEffect,useId,useRef } from 'react';
import Button from './Button';
export type Confirmation={title:string;description:string;confirmLabel?:string};
export default function ConfirmationDialog({request,onDecision}:{request:Confirmation|null;onDecision:(answer:boolean)=>void}){
 const ref=useRef<HTMLDialogElement>(null);const id=useId();
 useEffect(()=>{
  if(!request)return;const dialog=ref.current;const previous=document.activeElement instanceof HTMLElement?document.activeElement:null;
  const overflow=document.body.style.overflow;document.body.style.overflow='hidden';
  dialog?.showModal();dialog?.querySelector<HTMLButtonElement>('[data-cancel]')?.focus();
  return()=>{dialog?.close();document.body.style.overflow=overflow;if(previous?.isConnected)previous.focus()};
 },[request]);
 return <dialog ref={ref} className="ui-dialog" aria-labelledby={id+'-title'} aria-describedby={id+'-description'} onCancel={e=>{e.preventDefault();onDecision(false)}}>
  {request&&<><h2 id={id+'-title'}>{request.title}</h2><p id={id+'-description'}>{request.description}</p><div className="ui-dialog-actions"><Button variant="secondary" data-cancel onClick={()=>onDecision(false)}>Cancelar</Button><Button onClick={()=>onDecision(true)}>{request.confirmLabel||'Confirmar'}</Button></div></>}
 </dialog>;
}
