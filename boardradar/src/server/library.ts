import 'server-only';
import {rankById,rankBySlug,searchRanks} from './bgg-ranks';
import {catalogSearchSchema} from '@/domain/catalog-search';
export const library={byId:rankById,bySlug:rankBySlug,byBgg:rankById};
export {normalizeRankName as normalize} from '@/domain/bgg-ranks';
export function searchLibrary(query:string,players?:number,duration?:number,kind='all',page=1,pageSize=24){return searchRanks(catalogSearchSchema.parse({q:query,players,duration,kind,page,page_size:pageSize}))}
export function comparisonItem(id:string){const g=rankById(id);if(!g)return undefined;return {id:g.id,name:g.name,slug:g.slug,year:g.year??'Não informado',rank:g.rank?String(g.rank):'Sem ranking',rating:g.rating!==null?g.rating.toFixed(2)+'/10':'Não informado',bayes_average:g.bayes_average?g.bayes_average.toFixed(2)+'/10':'Não informado',rating_count:String(g.rating_count??0),kind:g.kind==='boardgameexpansion'?'Expansão':'Jogo-base',players:g.min_players&&g.max_players?g.min_players+'–'+g.max_players:'Não informado',duration:g.max_minutes?g.max_minutes+' min':'Não informado',complexity:g.complexity?g.complexity.toFixed(2)+'/5 (2019)':'Não informado',category:g.categories.join(', ')||'Não informado',mechanics:g.mechanics.join(', ')||'Não informado',source:g.sources.join(' + ')}}
