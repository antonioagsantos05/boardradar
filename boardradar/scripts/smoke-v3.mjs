import {spawn} from 'node:child_process';
import assert from 'node:assert/strict';
const port=3213;
const server=spawn(process.execPath,['scripts/run.mjs','--port',String(port)],{windowsHide:true,stdio:['ignore','pipe','pipe','ipc'],env:process.argv.includes('--without-python')?{...process.env,PYTHON_EXECUTABLE:'Z:/missing-python.exe'}:process.env});
let output='';server.stdout.on('data',d=>output+=d);server.stderr.on('data',d=>output+=d);
const base=`http://127.0.0.1:${port}`;
const get=(path,options={})=>fetch(base+path,{...options,signal:AbortSignal.timeout(10000)});
try{
 let ready=false;
 for(let i=0;i<60;i++){try{if((await get('/api/catalog')).ok){ready=true;break}}catch{}await new Promise(r=>setTimeout(r,250))}
 assert(ready,output);
 const catalog=await (await get('/api/catalog?page_size=96')).json();assert.equal(catalog.total,100);assert.equal(catalog.results.length,96);
 const filtered=await (await get('/api/catalog?players=4&duration=60')).json();assert(filtered.results.every(g=>g.min_players<=4&&g.max_players>=4&&g.max_minutes<=60));
 const game=catalog.results[0];assert.equal((await get('/jogos/'+game.slug)).status,200);
 const compare=await get('/api/compare?ids='+game.id+','+catalog.results[1].curated_game_id);assert.equal(compare.status,200);assert.equal((await compare.json()).games.length,2);
 assert.equal((await get('/api/compare?ids='+game.id+','+game.curated_game_id)).status,400);
 assert.equal((await get('/api/games/bgg-999999999')).status,404);
 const offers=await (await get('/api/games/'+game.id+'/offers')).json();assert.equal(offers.offers.length,3);assert(offers.offers.every(o=>o.ficticia&&o.game_id===game.curated_game_id));
 assert.equal((await get('/api/games/'+game.id+'/offers?edition=edition_100_base')).status,400);
 const community=await (await get('/api/listings?view=public')).json();assert.equal(community.total,100);assert(community.listings.every(l=>l.is_demo));
 const listing=await (await get('/api/listings?view=detail&id=listing_001')).json();assert.equal(listing.listing.id,'listing_001');
 const detail=await (await get('/jogos/'+game.slug)).text();assert(detail.includes('Ofertas de lojas fictícias'));assert(detail.includes('Vendedores simulados'));
 const market=await (await get('/marketplace')).text();assert(market.includes('Marketplace de demonstração'));
 const chat=await get('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:'Jogos para 4 pessoas'})});
 if(process.argv.includes('--without-python'))assert.equal(chat.status,503);
 else{assert.equal(chat.status,200);const body=await chat.json();assert.equal(body.engine,'python-poc-v3');assert.equal(body.ids.length,3);}
 console.log(JSON.stringify({status:'passed',python:!process.argv.includes('--without-python'),catalog:100,listings:100,offers_for_first_game:3,checks:'catalogue, filters, detail, offers, invalid edition, simulated listings, marketplace, chat availability'}));
}finally{
 if(server.connected)server.send('shutdown');else server.kill();
 await new Promise(resolve=>{if(server.exitCode!==null)return resolve();server.once('exit',resolve);setTimeout(resolve,5000).unref()});
}
