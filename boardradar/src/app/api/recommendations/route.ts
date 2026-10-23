import {preferencesSchema} from '@/domain/preferences';
import {recommend} from '@/domain/recommendation';
import {resolveGame} from '@/repositories/poc';
export async function POST(request:Request){try{const parsed=preferencesSchema.safeParse(await request.json());if(!parsed.success)return Response.json({error:'Preferências inválidas.'},{status:400});const results=recommend(parsed.data).filter(r=>!parsed.data.complexity||r.game.complexity<=parsed.data.complexity).slice(0,3).map(r=>({...resolveGame(r.game.id),reasons:r.reasons}));return Response.json({is_demo:true,results,source:'BoardRadar_v3_JSONs',notice:'Afinidades editoriais; ofertas, edições e vendedores fictícios.'})}catch{return Response.json({error:'JSON inválido.'},{status:400})}}
