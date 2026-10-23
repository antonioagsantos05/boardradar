import { z } from 'zod';
import { NextRequest } from 'next/server';
const preferenceSchema=z.object({players:z.number().int().min(1).max(20).optional(),budget:z.number().positive().max(100000).optional(),duration:z.number().positive().max(10000).optional(),complexity:z.number().min(1).max(5).optional(),mode:z.enum(['cooperative','competitive']).optional(),videogames:z.array(z.string().max(30)).max(30).optional()}).strict();
const clarificationSchema=z.object({kind:z.literal('name'),candidates:z.array(z.object({entity_type:z.enum(['game','videogame']),id:z.string().max(30)}).strict()).min(1).max(5),intent:z.enum(['recommendation','refinement','information','comparison','rule','edition','offer','explanation']),game_ids:z.array(z.string().max(30)).max(3).optional(),videogame_ids:z.array(z.string().max(30)).max(30).optional()}).strict();
const contextIds=z.array(z.string().max(60)).max(3);
const pendingRuleSchema=z.object({query:z.string().trim().min(1).max(1000),game_id:z.string().max(30).nullable()}).strict();
const stateSchema=z.object({preferences:preferenceSchema.optional(),interests:z.array(z.string().max(40)).max(100).optional(),excluded:z.array(z.string().max(40)).max(100).optional(),excluded_games:z.array(z.string().max(30)).max(60).optional(),last_ids:z.array(z.string().max(30)).max(100).optional(),waiting_for:z.enum(['players','budget','interest']).nullable().optional(),budget_unlimited:z.boolean().optional(),pending_clarification:clarificationSchema.optional(),last_topic:z.string().max(100).optional(),library_subject_ids:contextIds.optional(),pending_rule:pendingRuleSchema.optional(),subject_ids:contextIds.optional(),pending_comparison:contextIds.optional(),subject_edition_ids:contextIds.optional(),media_ids:z.array(z.string().max(60)).max(21).optional(),session:z.object({version:z.literal(1),issued_at:z.number().int().nonnegative(),expires_at:z.number().int().nonnegative()}).strict().optional()}).strict();
const localProfileSchema=z.object({experience:z.string().max(30),styles:z.array(z.string().max(60)).max(12),videogames:z.array(z.string().max(30)).max(30),references:z.string().max(1000),budget:z.number().positive().max(100000).nullable(),consent:z.boolean()}).strict();
const schema=z.object({local_profile:localProfileSchema.optional(),message:z.string().trim().min(1).max(1000),state:stateSchema.optional(),preferences:preferenceSchema.optional()}).strict();
export async function POST(request:NextRequest){
 let input;
 try{
  if(Number(request.headers.get('content-length'))>20000)return Response.json({error:'Mensagem muito grande'},{status:413});
  const text=await request.text();if(text.length>20000)return Response.json({error:'Mensagem muito grande'},{status:413});
  const parsed=schema.safeParse(JSON.parse(text));
  if(!parsed.success)return Response.json({error:'Mensagem ou contexto inválido'},{status:400});
  input=parsed.data;
 }catch{return Response.json({error:'JSON inválido'},{status:400})}
 const url=process.env.RADAR_CHAT_URL,token=process.env.RADAR_CHAT_TOKEN;
 if(!url||!token)return Response.json({error:'O assistente Python não está ativo. Inicie o projeto com npm start ou npm run dev.'},{status:503});
 try{
  const response=await fetch(url+'/chat',{method:'POST',headers:{'Content-Type':'application/json',Authorization:'Bearer '+token},body:JSON.stringify({session_token:request.cookies.get('boardradar-session')?.value||'',local_profile:input.local_profile,message:input.message,state:input.state||(input.preferences?{preferences:input.preferences}:undefined)}),signal:AbortSignal.timeout(10000),cache:'no-store'});
  if(!response.ok)return Response.json({error:response.status===400?'Mensagem ou contexto inválido':'O assistente está temporariamente indisponível.'},{status:response.status===400?400:503});
  return Response.json(await response.json(),{headers:{'Cache-Control':'no-store'}});
 }catch{return Response.json({error:'Não consegui falar com o assistente Python. Tente novamente em instantes.'},{status:503})}
}
