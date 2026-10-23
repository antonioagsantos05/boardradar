import test from 'node:test';
import assert from 'node:assert/strict';
import fixtures from './fixtures/recommendation-invariants.json';
import { recommend, validOffers } from '../src/domain/recommendation';
import { isFresh,budgetToCents,eligibleOffer } from '../src/domain/offer-policy';
import { gameRepository,offerRepository } from '../src/repositories/catalog';
import type { Preferences } from '../src/domain/models';

const now=Date.parse(fixtures.now);
for(const scenario of fixtures.cases){
 test('invariante compartilhada: '+scenario.id,()=>{
  const ids=new Set(recommend(scenario.preferences as Preferences,now).map(r=>r.game.id));
  for(const id of scenario.include||[])assert(ids.has(id),id+' deve ser incluído');
  for(const id of scenario.exclude||[])assert(!ids.has(id),id+' deve ser excluído');
  if(scenario.empty)assert.equal(ids.size,0);
 });
}
test('conversão de orçamento preserva centavos sem arredondar teto para cima',()=>{
 assert.equal(budgetToCents(.29),29);assert.equal(budgetToCents(1000.50),100050);assert.equal(budgetToCents(100.009),10000);
 for(const value of [0,-1,NaN,Infinity])assert.throws(()=>budgetToCents(value));
});
test('oferta elegível exige dados comerciais íntegros',()=>{
 const original=offerRepository.all()[0];const stores=new Set([original.store_id]);
 assert(eligibleOffer(original,original.edition_id,stores,now));
 for(const patch of [{price_cents:0},{price_cents:-1},{price_cents:1.5},{currency:'USD'},{is_demo:false},{availability:'out_of_stock'},{edition_id:'foreign'},{checked_at:'invalid'},{store_id:'unknown'}]){
  assert.equal(eligibleOffer({...original,...patch},original.edition_id,stores,now),false,JSON.stringify(patch));
 }
});
test('validade de oferta respeita limite e rejeita data sem timezone ou impossível',()=>{
 assert(isFresh('2026-10-12T12:00:00Z',now));assert(!isFresh('2026-10-12T11:59:59Z',now));
 assert(!isFresh('2026-10-19T12:00:01Z',now));assert(!isFresh('2026-10-19T12:00:00',now));
 assert(!isFresh('2026-02-30T00:00:00Z',Date.parse('2026-03-03T00:00:00Z')));
});
test('perfil TypeScript mantém score anterior e informa versão',()=>{
 const result=recommend({query:'Azul'},now)[0];assert.equal(result.game.id,'g4');assert.equal(result.score,16);
 assert.equal(result.ranking_profile,'typescript');assert.equal(result.ranking_version,'1.1-preserved');assert(result.rule_trace.length>0);
});
test('preço nunca é consultado na edição de outro jogo',()=>{
 assert.deepEqual(validOffers(gameRepository.byId('g31')!,'g1-pt-base',now),[]);
});
