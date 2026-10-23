export interface LibraryGame {
 image?:string|null;thumbnail?:string|null;details_date?:string;rating_date?:string;ranking_date?:string;historical_rating?:number|null;historical_rank?:number|null;
 rank?:number|null;bayes_average?:number|null;ranking_groups?:{name:string;rank:number}[];
 id:string;bgg_id:string;name:string;slug:string;aliases:string[];description:string;year:number|null;
 min_players:number|null;max_players:number|null;min_minutes:number|null;max_minutes:number|null;min_age:number|null;
 categories:string[];mechanics:string[];designers:string[];publishers:string[];rating:number|null;rating_count:number|null;
 complexity:number|null;complexity_votes:number|null;kind:string;sources:string[];bgg_url:string;curated_game_id?:string;
}
export type LibrarySummary=Pick<LibraryGame,'id'|'bgg_id'|'name'|'slug'|'year'|'min_players'|'max_players'|'min_minutes'|'max_minutes'|'kind'|'curated_game_id'|'categories'|'rank'|'bayes_average'|'ranking_groups'|'rating'|'rating_count'|'image'|'thumbnail'|'details_date'|'rating_date'|'ranking_date'>;
