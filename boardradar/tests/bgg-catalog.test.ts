import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {mergeRankDetails,rankSummary,type RankRow} from '../src/domain/bgg-ranks';
import type {LibraryGame} from '../src/domain/library';
const ranks=JSON.parse(readFileSync('src/data/bgg-ranks.json','utf8')) as RankRow[];
const details=JSON.parse(readFileSync('src/data/bgg-details.json','utf8')) as LibraryGame[];
test('approved sources join only by BGG ID without discarding the details-only game',()=>{
 const ids=new Set(ranks.map(r=>String(r[0])));assert.equal(ids.size,182258);assert.equal(details.length,1000);assert.equal(details.filter(g=>ids.has(g.bgg_id)).length,999);assert.deepEqual(details.filter(g=>!ids.has(g.bgg_id)).map(g=>g.bgg_id),['37759']);
});
test('current rank and rating win while historical detail/rating keep their date',()=>{
 const row=ranks.find(r=>r[0]===161936)!;const detail=details.find(g=>g.bgg_id==='161936')!;const g=mergeRankDetails(row,detail);
 assert.equal(g.rating,row[5]);assert.notEqual(g.rating,detail.rating);assert.equal(g.historical_rating,detail.rating);assert.equal(g.details_date,'2019-09-20');assert.equal(g.rating_date,'2026-10-20');assert.equal(g.min_players,detail.min_players);assert.equal(g.description,detail.description);
});
test('rank-only records never inherit old player counts or invented descriptions',()=>{
 const g=mergeRankDetails(ranks.find(r=>r[0]===342942)!,undefined);assert.equal(g.rank,2);assert.equal(g.min_players,null);assert.equal(g.max_minutes,null);assert.equal(g.description,'');assert.deepEqual(g.mechanics,[]);
});
test('details-only record has no invented 2026 rating or rank',()=>{
 const detail=details.find(g=>g.bgg_id==='37759')!;const g=mergeRankDetails(undefined,detail);assert.equal(g.rank,null);assert.equal(g.rating,null);assert.equal(g.ranking_date,undefined);assert.equal(g.historical_rating,detail.rating);
});
test('zero CSV ranks are unknown and expansion classification is preserved',()=>{
 assert.equal(ranks.filter(r=>r[7]===1).length,40112);assert(ranks.every(r=>r[3]===null||r[3]>0));assert.equal(rankSummary(ranks.find(r=>r[7]===1)!).kind,'boardgameexpansion');
});
