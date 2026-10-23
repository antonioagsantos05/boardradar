import policy from '@/config/policy.json';
import type { Offer } from './models';

export function isFresh(checked:string,now=Date.now()){
 if(typeof checked!=='string'||!/(Z|[+-]\d{2}:\d{2})$/.test(checked))return false;
 const parts=checked.match(/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.\d+)?(Z|[+-]\d{2}:\d{2})$/);
 if(!parts)return false;
 const [year,month,day,hour,minute,second]=parts.slice(1,7).map(Number);
 const calendar=new Date(Date.UTC(year,month-1,day));
 if(calendar.getUTCFullYear()!==year||calendar.getUTCMonth()!==month-1||calendar.getUTCDate()!==day||hour>23||minute>59||second>59)return false;
 const timestamp=Date.parse(checked);
 return Number.isFinite(timestamp)&&timestamp<=now&&now-timestamp<=policy.max_offer_age_days*86400000;
}

export function budgetToCents(value:number){
 if(typeof value!=='number'||!Number.isFinite(value)||value<=0||value>100000)throw Error('Orçamento inválido');
 const text=value.toString().includes('e')?value.toFixed(20):value.toString();
 const [whole,fraction='']=text.split('.');
 return Number(whole)*100+Number((fraction+'00').slice(0,2));
}

export function eligibleOffer(offer:Offer,editionId:string,demoStoreIds:Set<string>,now=Date.now()){
 return policy.demo_mode===true&&offer.edition_id===editionId&&demoStoreIds.has(offer.store_id)&&offer.is_demo===true&&offer.currency==='BRL'&&Number.isSafeInteger(offer.price_cents)&&offer.price_cents>0&&(offer.availability==='simulada'||offer.availability==='in_stock'&&isFresh(offer.checked_at,now));
}
