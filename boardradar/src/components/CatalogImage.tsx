'use client';
import {useState} from 'react';
import {GameCover} from './GameCard';
export default function CatalogImage({name,url,category='',large=false}:{name:string;url?:string|null;category?:string;large?:boolean}){
 const [failed,setFailed]=useState(false);
 const safe=typeof url==='string'&&url.startsWith('https://cf.geekdo-images.com/');
 return safe&&!failed?<div className={'catalog-real-image '+(large?'large':'')}><img loading={large?'eager':'lazy'} decoding="async" width={large?600:360} height={large?600:360} src={url!} referrerPolicy="no-referrer" alt={'Capa de '+name} onError={()=>setFailed(true)}/><span>Imagem da base histórica de 2019</span></div>:<GameCover large={large} game={{name,category:category||'BGG · dados do catálogo',color:'#516d72'}}/>;
}
