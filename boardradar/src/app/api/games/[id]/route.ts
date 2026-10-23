import {library} from '@/server/library';
export async function GET(_request:Request,{params}:{params:Promise<{id:string}>}){const {id}=await params;const game=library.byId(id)||library.bySlug(id);return game?Response.json(game):Response.json({error:'Jogo não encontrado'},{status:404})}
