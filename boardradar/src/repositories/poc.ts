import {displayText} from '@/domain/presentation';
// Only the supplied JSONs contain catalogue facts; adapters are computed in memory.
import rawGames from '../../data/games.json';
import rawEditions from '../../data/editions.json';
import rawOffers from '../../data/store_offers.json';
import rawStores from '../../data/stores.json';
import rawListings from '../../data/user_listings.json';
import users from '../../data/users.json';
import themes from '../../data/themes.json';
import experiences from '../../data/experiences.json';
import franchises from '../../data/franchises.json';
import metadata from '../../data/metadata.json';
import type {Game,Offer} from '@/domain/models';
import type {LibraryGame} from '@/domain/library';
export {rawGames,rawEditions,rawOffers,rawStores,rawListings,users,themes,experiences,franchises,metadata};
export const games:Game[]=rawGames.map(g=>({id:g.game_id,slug:'bgg-'+g.bgg_id,name:g.nome,aliases:[],category:g.categorias[0]||'Jogo de tabuleiro',players:{min:g.jogadores_min,max:g.jogadores_max},duration:g.duracao_minutos,complexity:g.complexidade.valor,tags:[...g.temas,...g.experiencias,...g.mecanicas],description:g.descricao_pt,color:'#d99c35',editorialQuality:0,provenance:{source:g.origem,status:'editorial_poc'},editions:rawEditions.filter(e=>e.game_id===g.game_id).map(e=>({id:e.edition_id,name:displayText(e.nome_edicao),language:e.idioma,type:e.tipo}))}));
export const stores=rawStores.map(s=>({id:s.store_id,name:s.nome,is_demo:s.ficticia,url:s.site}));
export const offers:Offer[]=rawOffers.map(o=>({id:o.offer_id,edition_id:o.edition_id,store_id:o.store_id,price_cents:Math.round(o.preco_brl*100),currency:o.moeda,condition:o.condicao,availability:o.disponibilidade,checked_at:metadata.gerado_em+'T00:00:00Z',is_demo:o.ficticia}));
export const libraryGames:LibraryGame[]=rawGames.map(g=>({id:'bgg-'+g.bgg_id,bgg_id:String(g.bgg_id),slug:'bgg-'+g.bgg_id,curated_game_id:g.game_id,name:g.nome,aliases:[],description:g.descricao_pt,year:g.ano_publicacao,min_players:g.jogadores_min,max_players:g.jogadores_max,min_minutes:g.duracao_minutos,max_minutes:g.duracao_minutos,min_age:g.idade_minima,categories:g.categorias,mechanics:g.mecanicas,designers:g.designers,publishers:g.editoras,rating:g.avaliacao_bgg_2019.average,rating_count:null,complexity:g.complexidade.valor,complexity_votes:null,kind:'boardgame',sources:['BoardRadar_v3_JSONs'],bgg_url:'https://boardgamegeek.com/boardgame/'+g.bgg_id,image:g.imagem,thumbnail:g.miniatura,details_date:g.data_referencia,rating_date:g.data_referencia,rank:null,bayes_average:g.avaliacao_bgg_2019.bayesAverage,historical_rating:g.avaliacao_bgg_2019.average}));
export function resolveGame(id:string){return libraryGames.find(g=>[g.id,g.bgg_id,g.curated_game_id].includes(id))}
export const listings=rawListings.map(l=>({id:l.listing_id,edition_id:l.edition_id,title:displayText(l.titulo),description:displayText(l.descricao_anuncio),game_id:l.game_id,game_name:rawGames.find(g=>g.game_id===l.game_id)!.nome,edition_name:displayText(rawEditions.find(e=>e.edition_id===l.edition_id)!.nome_edicao),language:l.idioma,condition:({novo:'new',como_novo:'like_new',bom:'good',regular:'fair'} as Record<string,string>)[l.condicao]||l.condicao,price_cents:Math.round(l.preco_brl*100),region:l.cidade+' / '+l.uf,components:l.completo?'Completo':'Consultar descrição',updated_at:Date.parse(metadata.gerado_em+'T00:00:00Z')/1000,delivery:'both',negotiable:0,sealed:0,defects:displayText(l.pecas_faltando.join(', '))||'Não informado',images:[],is_demo:true,reference_image:l.imagem_referencia_jogo,seller_name:users.find(u=>u.user_id===l.seller_user_id)!.nome_exibicao}));
