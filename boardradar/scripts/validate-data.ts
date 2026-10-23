import { historyRepository } from '@/repositories/history';
import { z } from 'zod';
import { gameRepository, offerRepository, recommendationRepository } from '../src/repositories/catalog';
const games=gameRepository.all(), offers=offerRepository.all(), stores=offerRepository.stores(), videos=recommendationRepository.videogames(), relations=recommendationRepository.relations();
const id=z.string().min(1);const cents=z.number().int().positive();
function unique(values:string[],name:string){if(new Set(values).size!==values.length)throw Error('IDs duplicados em '+name)}
function assert(test:boolean,message:string){if(!test)throw Error(message)}
unique(games.map(g=>g.id),'games');unique(games.map(g=>g.slug),'slugs');unique(offers.map(o=>o.id),'offers');unique(stores.map(s=>s.id),'stores');unique(videos.map(v=>v.id),'videogames');
const editions=games.flatMap(g=>g.editions);unique(editions.map(e=>e.id),'editions');
const gameSchema=z.object({id,slug:id,name:id,aliases:z.array(z.string()),players:z.object({min:z.number().int().positive(),max:z.number().int().positive()}),duration:z.number().positive(),complexity:z.number().min(1).max(5),tags:z.array(id).min(1),editorialQuality:z.number().min(0).max(1),provenance:z.object({source:id,status:id}),editions:z.array(z.object({id,name:id,language:id,type:z.enum(['base','expansion'])})).min(1)});
games.forEach(g=>{gameSchema.parse(g);assert(g.players.min<=g.players.max,'Faixa de jogadores inválida: '+g.id)});
offers.forEach(o=>{z.object({id,edition_id:id,store_id:id,price_cents:cents,currency:z.literal('BRL'),condition:id,availability:z.enum(['in_stock','out_of_stock']),checked_at:z.string().datetime(),is_demo:z.literal(true)}).parse(o);assert(editions.some(e=>e.id===o.edition_id),'Edição órfã');assert(stores.some(s=>s.id===o.store_id&&s.is_demo),'Loja inválida')});
stores.forEach(s=>assert(s.is_demo===true,'Loja não demonstrativa'));
unique(relations.map(r=>r.videogame_id+':'+r.game_id),'relations');relations.forEach(r=>{assert(games.some(g=>g.id===r.game_id),'Relação órfã de jogo');assert(videos.some(v=>v.id===r.videogame_id),'Relação órfã de videogame');assert(r.weight>=0&&r.weight<=1,'Peso inválido')});
const observations:string[]=[];offers.forEach(o=>historyRepository.forOffer(o.id).forEach(h=>{cents.parse(h.price_cents);z.string().datetime().parse(h.observed_at);assert(h.data_origin==='synthetic'&&h.is_demo,'Histórico sem origem sintética');observations.push(h.offer_id+':'+h.observed_at)}));unique(observations,'history');
assert(games.length>=68&&videos.length===13&&stores.length===10&&offers.length>=150,'Contagem fora do escopo');
console.log(`Dados íntegros: ${games.length} jogos, ${videos.length} videogames, ${stores.length} lojas, ${offers.length} ofertas, ${observations.length} observações sintéticas.`);
console.log('Atenção editorial: metadados e edições ainda aguardam conferência em fontes primárias.');
