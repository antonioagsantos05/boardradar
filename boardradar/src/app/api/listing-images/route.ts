import { NextRequest,NextResponse } from 'next/server';
import sharp from 'sharp';
import { marketplace } from '@/server/marketplace';

export const runtime='nodejs';
const busy=new Set<string>();
export async function GET(request:NextRequest){
 try{
  const id=request.nextUrl.searchParams.get('id')||'';if(!/^[a-f0-9]{32}$/.test(id))return NextResponse.json({error:'Foto inválida.'},{status:400});
  let result=await marketplace(request,'public_image',{image_id:id});
  if(result.status!==200&&request.cookies.get('boardradar-session'))result=await marketplace(request,'image',{image_id:id});
  if(result.status!==200)return NextResponse.json(result.body,{status:result.status,headers:{'Cache-Control':'no-store'}});
  return new NextResponse(Buffer.from(result.body.content,'base64'),{headers:{'Content-Type':'image/jpeg','Cache-Control':'private, no-store','X-Content-Type-Options':'nosniff','Content-Security-Policy':"default-src 'none'; sandbox"}});
 }catch{return NextResponse.json({error:'Não foi possível carregar a foto.'},{status:503})}
}
export async function POST(request:NextRequest){
 if(request.headers.get('origin')!==request.nextUrl.protocol+'//'+request.headers.get('host'))return NextResponse.json({error:'Origem inválida.'},{status:403});
 const id=request.nextUrl.searchParams.get('listing_id')||'',revision=Number(request.nextUrl.searchParams.get('revision'));
 if(!/^[a-f0-9]{32}$/.test(id)||!Number.isInteger(revision)||revision<1)return NextResponse.json({error:'Anúncio inválido.'},{status:400});
 const session=request.cookies.get('boardradar-session')?.value||'';
 if(busy.has(session)||busy.size>=3)return NextResponse.json({error:'Aguarde o envio da foto atual.'},{status:429});
 busy.add(session);
 try{
  const allowed=await marketplace(request,'can_upload',{id,revision});if(allowed.status!==200)return NextResponse.json(allowed.body,{status:allowed.status});
  if(!['image/jpeg','image/png','image/webp'].includes(request.headers.get('content-type')||''))return NextResponse.json({error:'Use fotos JPEG, PNG ou WebP.'},{status:400});
  const max=5*1024*1024;
  if(Number(request.headers.get('content-length'))>max)return NextResponse.json({error:'A foto deve ter até 5 MB.'},{status:413});
  const reader=request.body?.getReader();if(!reader)return NextResponse.json({error:'Foto vazia.'},{status:400});
  const chunks:Uint8Array[]=[];let size=0;
  while(true){const {done,value}=await reader.read();if(done)break;size+=value.length;if(size>max){await reader.cancel();return NextResponse.json({error:'A foto deve ter até 5 MB.'},{status:413})}chunks.push(value)}
  let output:Buffer;
  try{
   const image=sharp(Buffer.concat(chunks),{limitInputPixels:16000000,failOn:'warning'});const metadata=await image.metadata();
   if(!metadata.format||!['jpeg','png','webp'].includes(metadata.format)||(metadata.pages||1)>1)throw Error('Formato inválido');
   output=await image.rotate().resize({width:1600,height:1600,fit:'inside',withoutEnlargement:true}).jpeg({quality:85}).toBuffer();
   if(output.length>2000000)throw Error('Foto muito grande');
  }catch{return NextResponse.json({error:'Foto inválida. Use JPEG, PNG ou WebP estático, até 16 megapixels.'},{status:400})}
  const result=await marketplace(request,'add_image',{id,revision,content:output.toString('base64')});
  return NextResponse.json(result.body,{status:result.status,headers:{'Cache-Control':'no-store'}});
 }catch{return NextResponse.json({error:'Não foi possível enviar a foto.'},{status:503})}
 finally{busy.delete(session)}
}
