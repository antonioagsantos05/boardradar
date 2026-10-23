import { searchLibrary } from '@/server/library';
import { z } from 'zod';
const schema=z.object({q:z.string().max(200).default(''),players:z.coerce.number().int().min(1).max(20).optional(),duration:z.coerce.number().positive().max(10000).optional(),kind:z.enum(['all','boardgame','boardgameexpansion','unclassified']).default('all'),page:z.coerce.number().int().min(1).max(20000).default(1),page_size:z.coerce.number().refine(n=>[12,24,48,96].includes(n)).default(24)});
export async function GET(request:Request){
 const parsed=schema.safeParse(Object.fromEntries(new URL(request.url).searchParams));
 if(!parsed.success)return Response.json({error:'Filtros inválidos'},{status:400});
 const p=parsed.data;return Response.json(searchLibrary(p.q,p.players,p.duration,p.kind,p.page,p.page_size));
}
