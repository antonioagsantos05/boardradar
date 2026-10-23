import type {LibraryGame,LibrarySummary} from './library';
export type RankRow=[number,string,number|null,number|null,number|null,number|null,number,number,...(number|null)[]];
export const rankingGroups=['Abstratos','Cartas colecionáveis','Infantis','Família','Festa','Estratégia','Temáticos','Guerra'];
export const normalizeRankName=(text:string)=>text.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
export function rankSummary(row:RankRow):LibrarySummary{
 return {id:'bgg-'+row[0],bgg_id:String(row[0]),name:row[1],slug:'bgg-'+row[0],year:row[2],rank:row[3],bayes_average:row[4],rating:row[5],rating_count:row[6],kind:row[7]===1?'boardgameexpansion':'boardgame',categories:[],ranking_groups:rankingGroups.flatMap((name,i)=>row[i+8]?[{name,rank:Number(row[i+8])}]:[]),min_players:null,max_players:null,min_minutes:null,max_minutes:null};
}
export function rankGame(row:RankRow):LibraryGame{
 return {...rankSummary(row),aliases:[],description:'',min_age:null,mechanics:[],designers:[],publishers:[],complexity:null,complexity_votes:null,sources:['bgg_ranks_2026_10_20'],bgg_url:'https://boardgamegeek.com/boardgame/'+row[0]};
}
export function mergeRankDetails(row:RankRow|undefined,detail:LibraryGame|undefined):LibraryGame{
 if(!row){if(!detail)throw Error('Missing game');return {...detail,rank:null,bayes_average:null,rating:null,rating_count:null,ranking_date:undefined,rating_date:undefined,historical_rating:detail.rating,historical_rank:detail.rank}}
 const base=rankGame(row);
 return {...base,...detail,...rankSummary(row),categories:detail?.categories||[],min_players:detail?.min_players??null,max_players:detail?.max_players??null,min_minutes:detail?.min_minutes??null,max_minutes:detail?.max_minutes??null,historical_rating:detail?.rating??null,historical_rank:detail?.rank??null,ranking_date:'2026-10-20',rating_date:'2026-10-20',sources:[...base.sources,...detail?.sources||[]]};
}
