import test from 'node:test';
import assert from 'node:assert/strict';
import {catalogSearchSchema} from '../src/domain/catalog-search';
test('catalog query accepts shared filters and supported page sizes',()=>{
 const p=catalogSearchSchema.parse({q:'ação',players:'4',duration:'60',page:'2',page_size:'48',kind:'boardgameexpansion',sort:'year'});
 assert.equal(p.players,4);assert.equal(p.page_size,48);assert.equal(p.q,'ação');
});
test('catalog query rejects invalid, unbounded or unsupported input',()=>{
 for(const input of [{q:'x'.repeat(201)},{players:0},{players:1.5},{duration:-1},{page:0},{page:20001},{page_size:13},{sort:'price'},{kind:'fake'},{source:'fake'}])assert.equal(catalogSearchSchema.safeParse(input).success,false);
});
test('catalog defaults and empty local favorites remain distinct from no favorite filter',()=>{
 const p=catalogSearchSchema.parse({});assert.equal(p.page,1);assert.equal(p.page_size,24);assert.equal(p.source,'all');assert.equal(p.ids,undefined);
 assert.equal(catalogSearchSchema.parse({favoritos:'1',ids:''}).ids,'');
});
