import { gameRepository, offerRepository, recommendationRepository } from '@/repositories/catalog';
import type { Game, Preferences } from './models';
import policy from '@/config/policy.json';
import { budgetToCents, eligibleOffer } from './offer-policy';
export { isFresh } from './offer-policy';
export const normalize=(s:string)=>s.normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/[’‘]/g,"'").toLowerCase();
export const money=(cents:number)=>new Intl.NumberFormat('pt-BR',{style:'currency',currency:'BRL'}).format(cents/100);
export function validOffers(game:Game,edition=game.editions[0].id,now=Date.now()){
 const canonical=gameRepository.byId(game.id);
 if(!canonical||!canonical.editions.some(e=>e.id===edition))return [];
 const offers=offerRepository.all(),stores=offerRepository.stores();
 const editionIds=new Set(gameRepository.all().flatMap(g=>g.editions.map(e=>e.id)));
 const storeIds=new Set(stores.map(s=>s.id));
 if(new Set(offers.map(o=>o.id)).size!==offers.length||offers.some(o=>!editionIds.has(o.edition_id)||!storeIds.has(o.store_id)))return [];
 const demoStores=new Set(stores.filter(s=>s.is_demo).map(s=>s.id));
 return offerRepository.forEdition(edition).filter(o=>eligibleOffer(o,edition,demoStores,now)).sort((a,b)=>a.price_cents-b.price_cents);
}
export function recommend(p:Preferences,now=Date.now()){
 const chosen=recommendationRepository.videogames().filter(v=>p.videogames?.includes(v.id));
 return gameRepository.all().filter(g=>{
 if(p.query&&!normalize([g.name,...g.aliases,...g.tags,g.category].join(' ')).includes(normalize(p.query)))return false;
 if(p.players&&(g.players.min>p.players||g.players.max<p.players))return false;
 if(p.duration&&g.duration>p.duration)return false;
 if(p.style&&!normalize(g.tags.join(' ')+' '+g.category).includes(normalize(p.style)))return false;
 if(p.budget!==undefined){const price=validOffers(g,g.editions[0].id,now)[0]?.price_cents;if(price===undefined||price>budgetToCents(p.budget))return false;}
 return true;
 }).map(game=>{
 const related=recommendationRepository.relations().filter(r=>r.game_id===game.id&&p.videogames?.includes(r.videogame_id));
 const themes=chosen.flatMap(v=>v.tags);const matches=game.tags.filter(t=>themes.includes(t));
 const theme=themes.length?Math.min(1,matches.length/3):0;
 const style=p.style?1:0;const affinity=related.length?Math.max(...related.map(r=>r.weight)):0;
 const complexity=p.complexity?Math.max(0,1-Math.abs(game.complexity-p.complexity)/4):policy.ranking.typescript.default_complexity_affinity;
 const weights=policy.ranking.weights;
 const score_breakdown={themes:weights.themes*theme,style:weights.style*style,videogame:weights.videogame*affinity,complexity:weights.complexity*complexity,editorial:weights.editorial*game.editorialQuality};
 const score=Math.round(Object.values(score_breakdown).reduce((sum,v)=>sum+v,0));
 const reasons=related.map(r=>r.rationale);if(matches.length)reasons.push('Afinidade em '+matches.slice(0,3).join(', ')+'.');
 if(!reasons.length)reasons.push('Seleção editorial de '+game.category.toLowerCase()+'.');
 const rule_trace=[{rule_id:'USR-PLAYERS-001',status:p.players?'passed':'exempt'},{rule_id:'USR-DURATION-001',status:p.duration?'passed':'exempt'},{rule_id:'USR-BUDGET-001',status:p.budget!==undefined?'passed':'exempt'},{rule_id:'USR-STYLE-001',status:p.style?'passed':'exempt'},{rule_id:'RANK-SCORE-001',status:'applied'}];
 return {game,score,reasons,score_breakdown,rule_trace,policy_version:policy.version,ranking_version:policy.ranking.version,ranking_profile:'typescript'};
 }).sort((a,b)=>b.score-a.score||a.game.name.localeCompare(b.game.name,'pt-BR'));
}
