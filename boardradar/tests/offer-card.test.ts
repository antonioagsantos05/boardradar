import test from 'node:test';
import assert from 'node:assert/strict';
import {createElement} from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import OfferCard from '../src/components/OfferCard';
import {offerRepository} from '../src/repositories/catalog';
const original=offerRepository.all()[0];
function render(patch:Partial<typeof original>={},edition=original.edition_id){return renderToStaticMarkup(createElement(OfferCard,{offer:{...original,availability:'in_stock',checked_at:new Date(Date.now()-1000).toISOString(),...patch},editionId:edition,onDemo:()=>{}}))}
test('eligible offer renders its details action and frete disclosure',()=>{
 const html=render();assert(html.includes('Ver oferta'));assert(html.includes('frete não incluído'));assert(!html.includes('disabled=""'));
});
test('wrong edition and non-DEMO offer cannot trigger commercial demonstration',()=>{
 assert(render({},'unrelated-edition').includes('disabled=""'));
 assert(render({is_demo:false}).includes('disabled=""'));
});
test('unavailable, expired and future offers remain disabled in product cards',()=>{
 for(const patch of [{availability:'out_of_stock'},{checked_at:'2000-01-01T00:00:00Z'},{checked_at:'2999-01-01T00:00:00Z'}])assert(render(patch).includes('disabled=""'));
});
