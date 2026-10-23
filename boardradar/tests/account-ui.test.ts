import test from 'node:test';
import assert from 'node:assert/strict';
import {accountDestination,targetPrice} from '../src/domain/account-ui';
test('account continuation only allows internal supported destinations',()=>{
 for(const value of ['https://example.com','//example.com','javascript:alert(1)','/admin',null])assert.equal(accountDestination(value),'/minha-conta');
 assert.equal(accountDestination('/vender'),'/vender');assert.equal(accountDestination('/favoritos'),'/favoritos');
 assert.equal(accountDestination('/jogos/catan?edition=g1-pt-base'),'/jogos/catan?edition=g1-pt-base');assert.equal(accountDestination('/jogos//example.com'),'/minha-conta');
});
test('wishlist target preserves cents and optional empty value',()=>{
 assert.equal(targetPrice(''),null);assert.equal(targetPrice('  '),null);assert.equal(targetPrice('150,50'),15050);assert.equal(targetPrice('0.01'),1);assert.equal(targetPrice('1000000'),100000000);
});
test('wishlist target rejects ambiguous, fractional-cent and out-of-range values',()=>{
 for(const value of ['0','-1','0.001','1e3','1,2,3','1000000.01','Infinity','abc'])assert.throws(()=>targetPrice(value));
});

 test('sale draft return path remains local and preserves draft identity',()=>{
 assert.equal(accountDestination('/vender?id=draft_123'),'/vender?id=draft_123');
 assert.equal(accountDestination('/vender?id=https://example.com'),'/minha-conta');
 assert.equal(accountDestination('/vender?id=one&next=//example.com'),'/minha-conta');
 });
