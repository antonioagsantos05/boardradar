import { NextRequest, NextResponse } from 'next/server';
import { z } from 'zod';

const cookieName='boardradar-session';
const actions=z.enum(['register','login','logout','create_game','update_game','delete_game','save_profile','delete_profile','save_wishlist','delete_wishlist','read_notifications']);
const attempts:number[]=[];

async function forward(request:NextRequest,action:string,data:Record<string,unknown>={}){
 const url=process.env.RADAR_CHAT_URL,token=process.env.RADAR_CHAT_TOKEN;
 if(!url||!token)return NextResponse.json({error:'Inicie o projeto com npm start.'},{status:503});
 try{
  const result=await fetch(url+'/account',{method:'POST',headers:{Authorization:'Bearer '+token,'Content-Type':'application/json'},body:JSON.stringify({action,data,session_token:request.cookies.get(cookieName)?.value||''}),signal:AbortSignal.timeout(10000),cache:'no-store'});
  const body=await result.json();const session=body.session_token;delete body.session_token;
  const response=NextResponse.json(body,{status:result.status,headers:{'Cache-Control':'no-store'}});
  if(session)response.cookies.set(cookieName,session,{httpOnly:true,sameSite:'strict',secure:request.nextUrl.protocol==='https:',path:'/',maxAge:604800});
  if(action==='logout'||result.status===401)response.cookies.set(cookieName,'',{httpOnly:true,sameSite:'strict',path:'/',maxAge:0});
  return response;
 }catch{return NextResponse.json({error:'Serviço local indisponível. Tente novamente.'},{status:503})}
}

export async function GET(request:NextRequest){return forward(request,'me')}
export async function POST(request:NextRequest){
 const expectedOrigin=request.nextUrl.protocol+'//'+request.headers.get('host');
 if(request.headers.get('origin')!==expectedOrigin)return NextResponse.json({error:'Origem inválida.'},{status:403});
 try{
  const raw=await request.text();if(raw.length>10000)return NextResponse.json({error:'Cadastro muito grande.'},{status:413});
  const input=z.object({action:actions,data:z.record(z.unknown()).default({})}).strict().safeParse(JSON.parse(raw));
  if(!input.success)return NextResponse.json({error:'Dados inválidos.'},{status:400});
  if(['login','register'].includes(input.data.action)){
   const cutoff=Date.now()-900000;while(attempts.length&&attempts[0]<cutoff)attempts.shift();
   if(attempts.length>=20)return NextResponse.json({error:'Muitas tentativas. Aguarde alguns minutos.'},{status:429});
   attempts.push(Date.now());
  }
  return forward(request,input.data.action,input.data.data);
 }catch{return NextResponse.json({error:'Dados inválidos.'},{status:400})}
}
