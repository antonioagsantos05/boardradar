import test from 'node:test';
import assert from 'node:assert/strict';
import {listingPriceCents} from '../src/domain/listing-ui';
import {accountDestination} from '../src/domain/account-ui';
test('listing prices preserve cents and accept Brazilian decimal comma',()=>{for(const [input,cents] of [['150,50',15050],['0.01',1],[' 250 ',25000],['1000000.00',100000000]] as const)assert.equal(listingPriceCents(input),cents);});
test('listing prices reject fractional cents, nonpositive and out-of-range values',()=>{for(const input of ['','0','-1','0.001','1e3','Infinity','1000000.01','150,2,3'])assert.throws(()=>listingPriceCents(input));});
test('account return destinations include home, listings and conversations',()=>{for(const target of ['/','/meus-anuncios','/mensagens'])assert.equal(accountDestination(target),target);for(const target of ['//example.com','https://example.com','/mensagens?next=//example.com'])assert.equal(accountDestination(target),'/minha-conta');});
