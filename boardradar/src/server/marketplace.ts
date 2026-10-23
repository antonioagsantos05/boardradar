import 'server-only';
import type { NextRequest } from 'next/server';
export async function marketplace(request:NextRequest,action:string,data:Record<string,unknown>={}){
 const service=process.env.RADAR_CHAT_URL,token=process.env.RADAR_CHAT_TOKEN;
 if(!service||!token)throw Error('Serviço indisponível');
 const response=await fetch(service+'/marketplace',{method:'POST',headers:{Authorization:'Bearer '+token,'Content-Type':'application/json'},body:JSON.stringify({action,data,session_token:request.cookies.get('boardradar-session')?.value||''}),cache:'no-store',signal:AbortSignal.timeout(10000)});
 return {status:response.status,body:await response.json()};
}
