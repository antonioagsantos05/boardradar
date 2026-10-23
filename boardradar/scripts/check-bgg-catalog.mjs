import {spawn} from 'node:child_process';
import {existsSync,mkdirSync,readFileSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import assert from 'node:assert/strict';
const base='http://127.0.0.1:3105';const folder='docs/catalog-bgg';mkdirSync(folder+'/captures',{recursive:true});mkdirSync('.qa',{recursive:true});
const server=spawn(process.execPath,['scripts/run.mjs','--port','3105'],{windowsHide:true,stdio:['ignore','pipe','pipe','ipc'],env:{...process.env,RADAR_ACCOUNT_DB:resolve('.qa/bgg-'+Date.now()+'.sqlite3')}});
let logs='';server.stdout.on('data',d=>logs+=d);server.stderr.on('data',d=>logs+=d);
let chrome,ws,session;let nextId=1;const pending=new Map(),errors=[];const matrix=[];
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
async function waitFor(fn,label,timeout=25000){const until=Date.now()+timeout;while(Date.now()<until){try{if(await fn())return}catch{}await sleep(150)}throw Error('Timeout: '+label)}
function command(method,params={},sid=session){return new Promise((ok,fail)=>{const id=nextId++;const timer=setTimeout(()=>{pending.delete(id);fail(Error(method+' timeout'))},20000);pending.set(id,{ok,fail,timer});ws.send(JSON.stringify({id,method,params,...sid?{sessionId:sid}:{}}))})}
async function evaluate(expression){const r=await command('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails));return r.result.value}
async function json(path){const r=await fetch(base+path);assert(r.ok,path);return r.json()}
async function post(path,data,cookie=''){const r=await fetch(base+path,{method:'POST',headers:{Origin:base,'Content-Type':'application/json',...(cookie?{Cookie:cookie}:{})},body:JSON.stringify(data)});const b=await r.json();assert(r.ok,path+': '+JSON.stringify(b));return {body:b,cookie:r.headers.getSetCookie()[0]?.split(';')[0]}}
try{
 await waitFor(async()=>{try{return (await fetch(base)).ok}catch{return false}},'server');
 const list=await json('/api/catalog');assert.equal(list.total,182259);assert.equal(list.results[0].bgg_id,'224517');assert.equal(list.results[0].rank,1);assert(!list.results.some(g=>g.curated_game_id));
 const game=await json('/api/games/bgg-161936');assert.equal(game.rating,8.49974);assert.equal(game.historical_rating,8.66878);assert.equal(game.details_date,'2019-09-20');assert(game.description);
 const onlyRank=await json('/api/games/bgg-342942');assert.equal(onlyRank.min_players,null);assert.equal(onlyRank.description,'');
 const onlyDetail=await json('/api/games/bgg-37759');assert.equal(onlyDetail.rank,null);assert.equal(onlyDetail.rating,null);assert(onlyDetail.historical_rating);
 assert.equal((await json('/api/games/g1')).id,'bgg-13');
 assert.equal((await fetch(base+'/api/compare?ids=g1,bgg-13')).status,400);
 assert.equal((await json('/api/compare?ids=bgg-13,bgg-30549')).games.length,2);
 assert.equal((await json('/api/games/g1/offers')).offers.length,0);
 for(const sort of ['rank','name','year','duration']){const r=await json('/api/catalog?players=4&duration=60&page_size=96&sort='+sort);assert(r.results.length>0);assert(r.results.every(g=>g.min_players<=4&&g.max_players>=4&&g.max_minutes<=60))}
 const expansions=await json('/api/catalog?kind=boardgameexpansion');assert.equal(expansions.total,40112);assert(expansions.results.every(g=>g.kind==='boardgameexpansion'));
 assert.equal((await json('/api/catalog?source=editorial')).total,0);
 const catan=await json('/api/catalog?ids=g1,bgg-13&page_size=12');assert.equal(catan.total,1);
 const comparison=(await post('/api/chat',{message:'Compare Catan com Pandemic'})).body;assert(comparison.comparison);assert(comparison.text.includes('2019'));
 const constraint=(await post('/api/chat',{message:'Jogos para 4 pessoas'})).body;assert.equal(constraint.state.preferences.players,4);
 const follow=(await post('/api/chat',{message:'Até 60 minutos',state:constraint.state})).body;assert.equal(follow.state.preferences.players,4);assert.equal(follow.state.preferences.duration,60);
 const buyer=await post('/api/account',{action:'register',data:{name:'Teste BGG',email:'bgg-test@example.local',password:'catalog-test-password'}});
 await post('/api/account',{action:'create_game',data:{name:'Registro pessoal preservado',category:'Pessoal',players:4,duration:60,description:'Jogo da conta, separado das fontes BGG.'}},buyer.cookie);
 const chromePath=process.env.CHROME_EXECUTABLE||'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';assert(existsSync(chromePath));
 chrome=spawn(chromePath,['--headless=new','--remote-debugging-port=0','--no-first-run','--disable-extensions','--user-data-dir='+resolve('.qa/bgg-browser'),'about:blank'],{windowsHide:true,stdio:['ignore','ignore','pipe']});let chromeLog='';chrome.stderr.on('data',d=>chromeLog+=d);let endpoint;await waitFor(()=>endpoint=chromeLog.match(/DevTools listening on (ws:\/\/[^\s]+)/)?.[1],'Chrome');
 ws=new WebSocket(endpoint);await new Promise((ok,fail)=>{ws.addEventListener('open',ok,{once:true});ws.addEventListener('error',fail,{once:true})});
 ws.addEventListener('message',event=>{const r=JSON.parse(event.data);if(r.id&&pending.has(r.id)){const p=pending.get(r.id);pending.delete(r.id);clearTimeout(p.timer);r.error?p.fail(Error(r.error.message)):p.ok(r.result)}if(r.method==='Runtime.exceptionThrown')errors.push(r.params.exceptionDetails.text);if(r.method==='Fetch.requestPaused')void command('Fetch.failRequest',{requestId:r.params.requestId,errorReason:'Failed'}).catch(()=>{})});
 const target=await command('Target.createTarget',{url:'about:blank'},null);session=(await command('Target.attachToTarget',{targetId:target.targetId,flatten:true},null)).sessionId;
 await command('Page.enable');await command('Runtime.enable');await command('Fetch.enable',{patterns:[{urlPattern:'https://cf.geekdo-images.com/*',requestStage:'Request'}]});
 await command('Network.setCookie',{name:'boardradar-session',value:buyer.cookie.split('=')[1],url:base,httpOnly:true,sameSite:'Strict'});
 await command('Page.navigate',{url:base});await waitFor(()=>evaluate('location.origin==='+JSON.stringify(base)),'origin');await evaluate("localStorage.setItem('boardradar-favorites',JSON.stringify(['g1','bgg-342942']));localStorage.removeItem('boardradar-preferences')");
 const pages=[['home','/',"document.querySelectorAll('.home-vitrine .game-card').length===8"],['catalogo','/jogos',"document.querySelectorAll('.catalog-browser .game-card').length===24"],['catan','/jogos/bgg-13',"!!document.querySelector('.library-facts')"],['ark-nova','/jogos/bgg-342942',"!!document.querySelector('.library-facts')"],['favoritos','/favoritos',"document.querySelectorAll('.favorite-game-grid .game-card').length===2"],['colecao','/minha-conta?sec=colecao',"!!document.querySelector('.collection-card')"],['radar','/radar-ai',"!!document.querySelector('.chat-inline')"],['marketplace','/marketplace',"!!document.querySelector('.community-listings') && !document.querySelector('[aria-busy=true]')"]];
 for(const width of [360,390,768,1024,1440]){
  await command('Emulation.setDeviceMetricsOverride',{width,height:1000,deviceScaleFactor:1,mobile:width<768});
  for(const [name,path,ready] of pages){await command('Page.navigate',{url:base+path});await waitFor(()=>evaluate(ready),name+' '+width);await sleep(200);
   const facts=await evaluate('({width:innerWidth,scrollWidth:document.documentElement.scrollWidth,headings:document.querySelectorAll("h1").length})');assert(facts.scrollWidth<=width+1,name+' overflow');assert.equal(facts.headings,1);
   let violations=[];if(process.argv.includes('--a11y')&&[390,1440].includes(width)){await evaluate(readFileSync('node_modules/axe-core/axe.min.js','utf8'));violations=await evaluate("axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa','wcag22aa','best-practice']}}).then(r=>r.violations.map(v=>({id:v.id,nodes:v.nodes.map(n=>({target:n.target,summary:n.failureSummary}))})))")}
   matrix.push({name,width,...facts,violations});
   if([390,1440].includes(width)){const capture=await command('Page.captureScreenshot',{format:'png',captureBeyondViewport:false});writeFileSync(folder+'/captures/'+name+'-'+width+'.png',Buffer.from(capture.data,'base64'))}
  }
 }
 await command('Page.navigate',{url:base+'/jogos/bgg-13'});await waitFor(()=>evaluate("!!document.querySelector('.library-facts') && !!document.querySelector('.game-comparison select option[value=\"bgg-224517\"]')"),'comparison options');
 assert(await evaluate("!document.querySelector('.detail-overview .catalog-real-image img') && !!document.querySelector('.detail-overview .game-cover')"),'failed image has illustrated fallback');
 await evaluate("const select=document.querySelector('.game-comparison select');select.value='bgg-224517';select.dispatchEvent(new Event('change',{bubbles:true}))");await waitFor(()=>evaluate("document.querySelectorAll('.game-comparison td').length>0"),'comparison table');
 await command('Page.navigate',{url:base+'/radar-ai'});await waitFor(()=>evaluate("!!document.querySelector('.chat-input input')"),'Radar');await evaluate("document.querySelector('.chat-input input').focus()");await command('Input.insertText',{text:'Compare Catan com Pandemic'});await evaluate("document.querySelector('.chat-input button').click()");await waitFor(()=>evaluate("!!document.querySelector('.chat-table') && !document.querySelector('.thinking')"),'chat new-source comparison');
 assert.equal(await evaluate("document.querySelector('.chat-error')?.textContent||''"),'');
 const report={date:new Date().toISOString(),source:'BGG ranks 2026 + details 2019',api_checks:'passed',responsive_scenarios:matrix.length,accessibility_scenarios:matrix.filter(r=>[390,1440].includes(r.width)&&process.argv.includes('--a11y')).length,matrix,js_errors:errors,external_images:'Intentionally failed in test to verify fallback',user_database:'Isolated .qa database; no real accounts modified'};writeFileSync(folder+'/browser.json',JSON.stringify(report,null,2)+'\n');
 assert.deepEqual(errors,[]);assert.deepEqual(matrix.filter(r=>r.violations.length).map(r=>({name:r.name,width:r.width,violations:r.violations})),[]);
 console.log(JSON.stringify({responsive_scenarios:matrix.length,accessibility_scenarios:report.accessibility_scenarios,violations:0,js_errors:errors}));
}catch(error){console.error(logs);throw error}finally{
 if(ws?.readyState===1){await command('Browser.close',{},null).catch(()=>{});ws.close()}chrome?.kill();
 if(server.connected){server.send('shutdown');await Promise.race([new Promise(r=>server.once('exit',r)),sleep(3000)])}if(server.exitCode===null)server.kill();
 for(const p of pending.values()){clearTimeout(p.timer);p.fail(Error('Browser closed'))}
}
