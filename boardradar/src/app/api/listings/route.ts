import { NextRequest,NextResponse } from 'next/server';
import { z } from 'zod';
import {listings} from '@/repositories/poc';
import {normalizeRankName} from '@/domain/bgg-ranks';

async function proxy(request:NextRequest,action:string,data:Record<string,unknown>={}){
 const service=process.env.RADAR_CHAT_URL,token=process.env.RADAR_CHAT_TOKEN;
 if(!service||!token)return NextResponse.json({error:'Inicie o projeto com npm start.'},{status:503});
 try{
  const r=await fetch(service+'/marketplace',{method:'POST',headers:{Authorization:'Bearer '+token,'Content-Type':'application/json'},body:JSON.stringify({action,data,session_token:request.cookies.get('boardradar-session')?.value||''}),cache:'no-store',signal:AbortSignal.timeout(10000)});
  return NextResponse.json(await r.json(),{status:r.status,headers:{'Cache-Control':'no-store'}});
 }catch{return NextResponse.json({error:'Serviço local indisponível.'},{status:503})}
}
export async function GET(request:NextRequest){
 const view=request.nextUrl.searchParams.get('view')||'mine';
 if(view==='detail'){
  const id=z.string().min(1).max(80).safeParse(request.nextUrl.searchParams.get('id'));
  if(!id.success)return NextResponse.json({error:'Identificador invalido.'},{status:400});
  const listing=listings.find(l=>l.id===id.data);
  if(listing)return NextResponse.json({listing,is_demo:true});
  if(!/^[a-f0-9]{32}$/.test(id.data))return NextResponse.json({error:'Anúncio indisponível.'},{status:404});
  return proxy(request,'public_detail',{id:id.data});
 }
 if(view==='public'){
  const parsed=z.object({q:z.string().max(120).default(''),edition_id:z.string().max(80).default(''),page:z.coerce.number().int().min(1).max(10000).default(1)}).safeParse(Object.fromEntries(request.nextUrl.searchParams));
  if(!parsed.success)return NextResponse.json({error:'Busca inválida.'},{status:400});
  const {q,edition_id,page:requested}=parsed.data;
  const terms=normalizeRankName(q).split(/\s+/).filter(Boolean);
  const rows=listings.filter(l=>(!edition_id||l.edition_id===edition_id)&&terms.every(t=>normalizeRankName([l.title,l.game_name,l.region].join(' ')).includes(t)));
  let live:{listings:unknown[];total:number;page:number;page_count:number}={listings:[],total:0,page:1,page_count:1};
  try{const response=await proxy(request,'browse',{q,edition_id,page:1});if(response.ok)live=await response.json();}catch{}
  const total=live.total+rows.length,page_count=Math.max(1,Math.ceil(total/12)),page=Math.min(requested,page_count),offset=(page-1)*12;
  let current:unknown[]=[];
  if(offset<live.total){const livePage=Math.floor(offset/24)+1;if(livePage!==1){const response=await proxy(request,'browse',{q,edition_id,page:livePage});if(!response.ok)return response;live=await response.json();}current=live.listings.slice(offset%24,offset%24+12);}
  const staticOffset=Math.max(0,offset-live.total);
  current.push(...rows.slice(staticOffset,staticOffset+12-current.length));
  return NextResponse.json({listings:current,total,page,page_count,is_demo:true},{headers:{'Cache-Control':'no-store'}});
 }
 if(!['mine','queue','inbox','reports','requests'].includes(view))return NextResponse.json({error:'Consulta inválida.'},{status:400});
 return proxy(request,view);
}
export async function POST(request:NextRequest){
 if(request.headers.get('origin')!==request.nextUrl.protocol+'//'+request.headers.get('host'))return NextResponse.json({error:'Origem inválida.'},{status:403});
 try{
  const raw=await request.text();if(raw.length>10000)return NextResponse.json({error:'Dados muito grandes.'},{status:413});
  const result=z.object({action:z.enum(['create','update','remove','submit','approve','reject','delete_image','transition','inquire','reply','report','resolve_report','request_game','decide_request']),data:z.record(z.unknown())}).strict().safeParse(JSON.parse(raw));
  if(!result.success)return NextResponse.json({error:'Dados inválidos.'},{status:400});
  return proxy(request,result.data.action,result.data.data);
 }catch{return NextResponse.json({error:'Dados inválidos.'},{status:400})}
}
