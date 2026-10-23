import test from 'node:test';
import assert from 'node:assert/strict';
import {games,libraryGames,rawGames,rawEditions,rawOffers,rawListings,listings,resolveGame} from '../src/repositories/poc';
import {gameRepository,offerRepository} from '../src/repositories/catalog';
import {eligibleOffer} from '../src/domain/offer-policy';

test('all catalogue identities resolve exclusively to the supplied 100 games',()=>{
 assert.equal(games.length,100);assert.equal(libraryGames.length,100);
 for(const raw of rawGames){
  const id='bgg-'+raw.bgg_id;
  assert.equal(resolveGame(id)?.curated_game_id,raw.game_id);
  assert.equal(resolveGame(raw.game_id)?.description,raw.descricao_pt);
  assert.equal(gameRepository.byId(raw.game_id)?.slug,id);
  assert.equal(resolveGame(id)?.rank,null);
  assert.equal(resolveGame(id)?.rating_date,'2019-09-20');
 }
 assert.equal(resolveGame('bgg-999999999'),undefined);
});

test('commercial adapters preserve edition, price and simulation provenance',()=>{
 assert.equal(rawEditions.length,124);assert.equal(rawOffers.length,300);assert.equal(rawListings.length,100);
 assert.equal(listings.length,100);
 const demoStores=new Set(offerRepository.stores().filter(s=>s.is_demo).map(s=>s.id));
 for(const raw of rawOffers){
  const offer=offerRepository.all().find(o=>o.id===raw.offer_id)!;
  assert.equal(offer.price_cents,Math.round(raw.preco_brl*100));
  assert.equal(offer.edition_id,raw.edition_id);
  assert(eligibleOffer(offer,raw.edition_id,demoStores,Date.UTC(2030,0,1)));
  assert(!eligibleOffer(offer,'other-edition',demoStores));
 }
 for(const listing of listings){assert(listing.is_demo);assert(!listing.title.includes('[DEMO]'));assert(!listing.description.includes('fictício'));assert(resolveGame(listing.game_id));}
});
