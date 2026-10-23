import 'server-only';
import {libraryGames,resolveGame,rawGames} from '@/repositories/poc';
import {normalizeRankName} from '@/domain/bgg-ranks';
import type {CatalogSearch} from '@/domain/catalog-search';
export const rankById=resolveGame;
export const rankBySlug=resolveGame;
export function searchRanks(p:CatalogSearch){
 const terms=normalizeRankName(p.q).split(/\s+/).filter(Boolean);
 const selected=p.ids===undefined&&!p.favoritos?null:new Set((p.ids||'').split(',').map(id=>resolveGame(id)?.id));
 const rows=libraryGames.filter(g=>{const raw=rawGames.find(r=>r.game_id===g.curated_game_id)!;return (!selected||selected.has(g.id))&&terms.every(t=>normalizeRankName([g.name,...g.categories,...g.mechanics,...raw.temas,...raw.experiencias].join(' ')).includes(t))&&(!p.players||g.min_players!<=p.players&&g.max_players!>=p.players)&&(!p.duration||g.max_minutes!<=p.duration)&&(p.kind==='all'||p.kind===g.kind)});
 if(p.sort==='name')rows.sort((a,b)=>a.name.localeCompare(b.name,'pt-BR'));
 if(p.sort==='year')rows.sort((a,b)=>(b.year||0)-(a.year||0));
 if(p.sort==='duration')rows.sort((a,b)=>a.max_minutes!-b.max_minutes!);
 const page_count=Math.max(1,Math.ceil(rows.length/p.page_size)),page=Math.min(p.page,page_count);
 return {total:rows.length,page,page_count,page_size:p.page_size,source:'BoardRadar_v3_JSONs',is_demo:true,results:rows.slice((page-1)*p.page_size,page*p.page_size),detailed_records:100};
}
