import { comparisonItem,library } from '@/server/library';
export async function GET(request:Request){
 const ids=(new URL(request.url).searchParams.get('ids')||'').split(',');
 if(ids.length!==2||new Set(ids).size!==2||ids.some(id=>!/^(g\d+|game_\d+|bgg-\d+)$/.test(id)))return Response.json({error:'Selecione dois jogos diferentes.'},{status:400});
 const canonical=ids.map(id=>library.byId(id)?.id||id);
 if(new Set(canonical).size!==2)return Response.json({error:'Esses registros representam o mesmo jogo.'},{status:400});
 const games=ids.map(comparisonItem);if(games.some(g=>!g))return Response.json({error:'Jogo não encontrado.'},{status:404});
 return Response.json({games,unknown:['Interação detalhada','Variabilidade','Curva de aprendizado'],is_demo:true});
}
