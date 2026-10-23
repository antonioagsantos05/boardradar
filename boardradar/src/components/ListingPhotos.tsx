'use client';
import { useState } from 'react';
import {ImagePlus,Trash2,Check} from 'lucide-react';
type Photo={id:string};
export default function ListingPhotos({listing,disabled,onChange,onError,editable=true,onBusyChange}:{listing:{id:string;revision:number;images:Photo[]};disabled:boolean;onChange:(items:unknown[])=>void;onError:(message:string)=>void;editable?:boolean;onBusyChange?:(busy:boolean)=>void}){
 const [uploading,setUploading]=useState(false);
 async function upload(file:File){
  setUploading(true);onBusyChange?.(true);onError('');
  try{
   if(!['image/jpeg','image/png','image/webp'].includes(file.type))throw Error('Use uma foto JPEG, PNG ou WebP.');
   if(file.size>5*1024*1024)throw Error('A foto deve ter até 5 MB.');
   const response=await fetch(`/api/listing-images?listing_id=${listing.id}&revision=${listing.revision}`,{method:'POST',headers:{'Content-Type':file.type},body:file});const body=await response.json();
   if(!response.ok)throw Error(body.error);onChange(body.listings);
  }catch(e){onError(e instanceof Error?e.message:'Não foi possível enviar a foto.')}finally{setUploading(false);onBusyChange?.(false)}
 }
 async function remove(image_id:string){
  setUploading(true);onBusyChange?.(true);onError('');
  try{const response=await fetch('/api/listings',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action:'delete_image',data:{id:listing.id,revision:listing.revision,image_id}})});const body=await response.json();if(!response.ok)throw Error(body.error);onChange(body.listings)}
  catch(e){onError(e instanceof Error?e.message:'Não foi possível remover a foto.')}finally{setUploading(false);onBusyChange?.(false)}
 }
 return <div className="listing-photos"><div className="listing-photos-heading"><b>Fotos do exemplar</b><span>{listing.images.length} de 6 fotos</span></div><div className="listing-photo-grid">{listing.images.map((photo,index)=><div key={photo.id}><span className="photo-cover-badge">{index===0?"Capa":"Foto "+(index+1)}</span><a href={'/api/listing-images?id='+photo.id} target="_blank" rel="noreferrer"><img loading="lazy" decoding="async" width={160} height={120} src={'/api/listing-images?id='+photo.id} alt="Foto do jogo anunciada pelo vendedor"/></a>{editable&&<button className="button light" type="button" disabled={disabled||uploading} onClick={()=>void remove(photo.id)}><Trash2 size={13}/> Remover foto</button>}</div>)}</div>{editable&&<label className="photo-upload"><ImagePlus size={27}/><strong>{uploading?'Enviando sua foto…':'Adicionar uma foto do jogo'}</strong><span>Mostre a caixa, os componentes e os detalhes do exemplar.</span><input aria-label="Adicionar foto ao anúncio" type="file" accept="image/jpeg,image/png,image/webp" disabled={disabled||uploading||listing.images.length>=6} onChange={e=>{const file=e.target.files?.[0];e.target.value='';if(file)void upload(file)}}/><small>JPEG, PNG ou WebP · até 5 MB por foto. Alterar fotos exige nova revisão.</small></label>}</div>;
}
