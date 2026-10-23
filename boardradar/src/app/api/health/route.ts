export const dynamic='force-dynamic';
export async function GET(){
 const url=process.env.RADAR_CHAT_URL,token=process.env.RADAR_CHAT_TOKEN;
 if(!url||!token)return Response.json({status:'unavailable'},{status:503});
 try{const response=await fetch(url+'/chat',{method:'POST',headers:{'Content-Type':'application/json',Authorization:'Bearer '+token},body:JSON.stringify({message:'oi'}),signal:AbortSignal.timeout(4000),cache:'no-store'});if(!response.ok)throw Error();return Response.json({status:'ok'},{headers:{'Cache-Control':'no-store'}})}catch{return Response.json({status:'unavailable'},{status:503})}
}
