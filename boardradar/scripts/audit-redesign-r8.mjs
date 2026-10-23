import { spawn,spawnSync } from 'node:child_process';
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
import assert from 'node:assert/strict';
import sharp from 'sharp';

const chromePath=process.env.CHROME_EXECUTABLE||'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
assert(existsSync(chromePath),'Chrome não encontrado para validação visual.');
mkdirSync('.qa',{recursive:true});
mkdirSync('docs/redesign/r8/captures',{recursive:true});
const dbPath=resolve('.qa/user-flows-'+Date.now()+'.sqlite3');
const server=spawn(process.execPath,['scripts/run.mjs','--port','3103'],{windowsHide:true,stdio:['ignore','pipe','pipe','ipc'],env:{...process.env,RADAR_ACCOUNT_DB:dbPath}});
let serverLog='';server.stdout.on('data',d=>serverLog+=d);server.stderr.on('data',d=>serverLog+=d);
let chrome,ws;let nextId=1;const pending=new Map();let session;const errors=[];const intercepted=[];
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
async function waitFor(fn,label,timeout=20000){const end=Date.now()+timeout;while(Date.now()<end){try{const value=await fn();if(value)return value}catch{}await sleep(150)}throw Error('Timeout: '+label)}
function command(method,params={},sessionId=session){return new Promise((ok,fail)=>{const id=nextId++;const timer=setTimeout(()=>{pending.delete(id);fail(Error('CDP timeout: '+method))},10000);pending.set(id,{ok,fail,timer});ws.send(JSON.stringify({id,method,params,...sessionId?{sessionId}:{}}))})}
async function evaluate(expression){const data=await command('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});if(data.exceptionDetails)throw Error(data.exceptionDetails.text);return data.result.value}
async function send(text){const before=await evaluate("document.querySelectorAll('.message.assistant:not(.thinking)').length");await evaluate("document.querySelector('.chat-input input').focus()");await command('Input.insertText',{text});await evaluate("document.querySelector('.chat-input button').click()");await waitFor(()=>evaluate(`document.querySelectorAll('.message.assistant:not(.thinking)').length > ${before} && !document.querySelector('.thinking')`),'resposta do assistente');assert.equal(await evaluate("document.querySelector('.chat-error')?.textContent||''"),'')}

try{
 await waitFor(async()=>{try{return(await fetch('http://127.0.0.1:3103')).ok}catch{return false}},'servidor: '+serverLog,30000);
 chrome=spawn(chromePath,['--headless=new','--remote-debugging-port=0','--no-first-run','--no-default-browser-check','--disable-extensions',`--user-data-dir=${resolve('.qa/r8-audit-profile')}`,'about:blank'],{windowsHide:true,stdio:['ignore','ignore','pipe']});
 let chromeLog='';chrome.stderr.on('data',d=>chromeLog+=d);const endpoint=await waitFor(()=>chromeLog.match(/DevTools listening on (ws:\/\/[^\s]+)/)?.[1],'Chrome DevTools');
 ws=new WebSocket(endpoint);await new Promise((ok,fail)=>{ws.addEventListener('open',ok,{once:true});ws.addEventListener('error',fail,{once:true})});
 ws.addEventListener('message',event=>{const data=JSON.parse(event.data);if(data.id&&pending.has(data.id)){const p=pending.get(data.id);clearTimeout(p.timer);pending.delete(data.id);data.error?p.fail(Error(data.error.message)):p.ok(data.result)}if(data.method==='Fetch.requestPaused')intercepted.push(data.params.requestId);if(data.method==='Runtime.exceptionThrown')errors.push(data.params.exceptionDetails.text)});
 const target=await command('Target.createTarget',{url:'about:blank'},null);const attached=await command('Target.attachToTarget',{targetId:target.targetId,flatten:true},null);session=attached.sessionId;
 await command('Runtime.enable');await command('Page.enable');await command('Page.addScriptToEvaluateOnNewDocument',{source:"window.__vitals={lcp:0,cls:0,long_tasks_ms:0};for(const type of ['largest-contentful-paint','layout-shift','longtask'])try{new PerformanceObserver(list=>{for(const e of list.getEntries()){if(type==='largest-contentful-paint')window.__vitals.lcp=e.startTime;if(type==='layout-shift'&&!e.hadRecentInput)window.__vitals.cls+=e.value;if(type==='longtask')window.__vitals.long_tasks_ms+=e.duration}}).observe({type,buffered:true})}catch{}"});await command('Emulation.setDeviceMetricsOverride',{width:1280,height:900,deviceScaleFactor:1,mobile:false});await command('Page.navigate',{url:'http://127.0.0.1:3103'});

 const base='http://127.0.0.1:3103';
 await waitFor(()=>evaluate("location.origin==='http://127.0.0.1:3103'"),'test origin');
 await evaluate("localStorage.removeItem('boardradar-favorites');localStorage.removeItem('boardradar-preferences')");
 async function post(path,action,data,cookie=''){
  const response=await fetch(base+path,{method:'POST',headers:{Origin:base,'Content-Type':'application/json',...(cookie?{Cookie:cookie}:{})},body:JSON.stringify({action,data})});
  const payload=await response.json();assert(response.ok,action+': '+payload.error);return {payload,cookie:response.headers.getSetCookie()[0]?.split(';')[0]};
 }
 const seller=await post('/api/account','register',{name:'Auditoria R0',email:'seller@audit.local',password:'audit-test-password'});
 const moderator=await post('/api/account','register',{name:'Moderacao R0',email:'moderator@audit.local',password:'audit-test-password'});
 const python=resolve('..','.tools','python-3.13.7','python.exe');const grant=spawnSync(python,['scripts/set-moderator.py','moderator@audit.local'],{windowsHide:true,env:{...process.env,PYTHONUTF8:'1',RADAR_ACCOUNT_DB:dbPath}});assert.equal(grant.status,0);
 const original=await sharp({create:{width:320,height:240,channels:3,background:'#e8b256'}}).png().toBuffer();
 const draft={edition_id:'g1-pt-base',title:'Catan - dados de teste R0',description:'Anuncio de teste para auditoria visual local. Nao representa uma venda real.',condition:'good',language:'Portugues',price_cents:15000,region:'Cidade de teste',components:'Completo conforme dados de teste',delivery:'pickup',negotiable:true,sealed:false,defects:'Marcas ilustrativas para teste'};
 let approved;
 for(let i=0;i<2;i++){
  let row=(await post('/api/listings','create',{...draft,title:draft.title+' '+(i+1)},seller.cookie)).payload.listings.find(x=>x.title===draft.title+' '+(i+1));
  const upload=await fetch(base+`/api/listing-images?listing_id=${row.id}&revision=${row.revision}`,{method:'POST',headers:{Origin:base,Cookie:seller.cookie,'Content-Type':'image/png'},body:original});assert.equal(upload.status,200);row=(await upload.json()).listings.find(r=>r.id===row.id);
  row=(await post('/api/listings','submit',{id:row.id,revision:row.revision,terms_accepted:true,terms_version:'local-mvp-2026-10-20-v1'},seller.cookie)).payload.listings.find(r=>r.id===row.id);
  if(i===0){await post('/api/listings','approve',{id:row.id,revision:row.revision,reason:'Registro aprovado apenas para auditoria de interface',edition_confirmed:true},moderator.cookie);approved=row}
 }
 await post('/api/listings','inquire',{id:approved.id,message:'Mensagem de teste para verificar o fluxo visual.'},moderator.cookie);
 const imported=(await(await fetch(base+'/api/library?q=Die%20Macher')).json()).results.find(g=>g.name==='Die Macher');assert(imported);
 const cases=[
  {id:'catalogo',path:'/jogos',cookie:'',ready:"!!document.querySelector('.catalog-count') && document.querySelectorAll('.game-card').length===24"},
  {id:'busca',path:'/buscar?q=Catan',cookie:'',ready:"!!document.querySelector('.catalog-count')"},
  {id:'vender-visitante',path:'/vender',cookie:'',ready:"!!document.querySelector('.sell-page h1')"},
  {id:'vender',path:'/vender',cookie:seller.cookie,ready:"!!document.querySelector('.sell-panel')"},
  {id:'meus-anuncios',path:'/meus-anuncios',cookie:seller.cookie,ready:"document.querySelectorAll('.account-game').length===2"},
  {id:'anuncio-publico',path:'/anuncios/'+approved.id,cookie:'',ready:"!!document.querySelector('.listing-detail .community-card')"},
  {id:'entrar-novo',path:'/entrar',cookie:'',ready:"!!document.querySelector('.access-page input[name=email]')"},
  {id:'cadastro',path:'/cadastro',cookie:'',ready:"!!document.querySelector('.access-page input[name=name]')"},
  {id:'conta-nova',path:'/minha-conta',cookie:seller.cookie,ready:"!!document.querySelector('.account-sections')"},
  {id:'onboarding',path:'/onboarding',cookie:seller.cookie,ready:"!!document.querySelector('.account-journey fieldset:not(:disabled)')"},
  {id:'favoritos',path:'/favoritos',cookie:seller.cookie,ready:"!!document.querySelector('#desejos fieldset:not(:disabled)')"},
  {id:'radar',path:'/radar-ai',cookie:'',ready:"!!document.querySelector('#radar-page-host .chat-inline')"},
  {id:'home',path:'/',cookie:'',ready:"document.querySelectorAll('.home-catalog-preview .game-card').length===8 && !document.querySelector('.imported-catalog')"},
  {id:'jogo',path:'/jogos/catan',cookie:'',ready:"!!document.querySelector('#comunidade .community-card')"},
  {id:'importado',path:'/jogos/'+imported.slug,cookie:'',ready:"!!document.querySelector('.library-overview')"},
  {id:'marketplace',path:'/marketplace',cookie:'',ready:"!!document.querySelector('.community-card')"},
  {id:'entrar',path:'/conta',cookie:'',ready:"!!document.querySelector('input[type=password]') && !document.querySelector('fieldset').disabled"},
  {id:'conta',path:'/conta',cookie:seller.cookie,ready:"document.querySelector('.account-journey')?.getAttribute('aria-busy')==='false'"},
  {id:'anuncios',path:'/anuncios',cookie:seller.cookie,ready:"document.querySelectorAll('.account-game').length===2"},
  {id:'mensagens',path:'/mensagens',cookie:seller.cookie,ready:"!!document.querySelector('.inbox-message')"},
  {id:'moderacao',path:'/moderacao',cookie:moderator.cookie,ready:"!!document.querySelector('.moderation-card')"}
 ];
 const matrix=[];
 for(const width of [390,1440]){
  await command('Emulation.setDeviceMetricsOverride',{width,height:900,deviceScaleFactor:1,mobile:width<768});
  for(const item of cases){
   if(item.cookie){await command('Network.setCookie',{name:'boardradar-session',value:item.cookie.split('=')[1],url:base,httpOnly:true,sameSite:'Strict'})}else await command('Network.deleteCookies',{name:'boardradar-session',url:base});
   await command('Page.navigate',{url:base+item.path});await waitFor(()=>evaluate(item.ready),item.id+' '+width);await sleep(150);
   const facts=await evaluate(`(()=>{
    const visible=e=>{const r=e.getBoundingClientRect();return r.width>0&&r.height>0&&getComputedStyle(e).visibility!=='hidden'};
    const nodes=[...document.querySelectorAll('body *')].filter(visible);
    const overflowing=nodes.filter(e=>{const r=e.getBoundingClientRect();return r.right>innerWidth+2||r.left < -2}).slice(0,10).map(e=>({tag:e.tagName,class:e.className,position:getComputedStyle(e).position}));
    const controls=[...document.querySelectorAll('button,a,input,select,textarea')].filter(visible);
    const unnamed=controls.filter(e=>!e.textContent?.trim()&&!e.getAttribute('aria-label')&&!e.getAttribute('title')&&!e.getAttribute('placeholder')&&!e.labels?.length&&!e.querySelector('img[alt]')).map(e=>e.outerHTML.slice(0,160));
    const tiny=controls.filter(e=>{const r=e.getBoundingClientRect();return r.height<24||r.width<24}).length;
    return {width:innerWidth,scroll_width:document.documentElement.scrollWidth,overflow:document.documentElement.scrollWidth>innerWidth+1,overflow_elements:overflowing,h1_count:document.querySelectorAll('h1').length,unnamed_controls:unnamed,controls_below_24px:tiny,title:document.title,body_height:document.body.scrollHeight,header_count:document.querySelectorAll('header.site-header').length,footer_count:document.querySelectorAll('footer.site-footer').length,search_count:document.querySelectorAll('.site-search').length};
   })()`);
   await sleep(750);
   const vitals=await evaluate("({...window.__vitals,navigation:performance.getEntriesByType('navigation').map(n=>({ttfb_ms:n.responseStart-n.requestStart,dom_content_loaded_ms:n.domContentLoadedEventEnd,load_ms:n.loadEventEnd})),resources:performance.getEntriesByType('resource').reduce((r,e)=>({count:r.count+1,transfer_bytes:r.transfer_bytes+e.transferSize,decoded_bytes:r.decoded_bytes+e.decodedBodySize}),{count:0,transfer_bytes:0,decoded_bytes:0}),seo:{description:document.querySelector('meta[name=description]')?.content||'',robots:document.querySelector('meta[name=robots]')?.content||'',canonical:document.querySelector('link[rel=canonical]')?.href||''}})");
   await evaluate(readFileSync('node_modules/axe-core/axe.min.js','utf8'));
   const a11y=await evaluate("axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa','wcag22aa','best-practice']}}).then(r=>({violations:r.violations.map(v=>({id:v.id,impact:v.impact,help:v.help,nodes:v.nodes.map(n=>({target:n.target,summary:n.failureSummary,html:n.html}))})),incomplete:r.incomplete.map(v=>({id:v.id,nodes:v.nodes.length})),passes:r.passes.length}))");
   matrix.push({page:item.id,requested_width:width,...facts,vitals,a11y});
   if([390,1440].includes(width)&&['radar','home','conta-nova','cadastro','favoritos','onboarding','jogo','marketplace','vender','anuncio-publico'].includes(item.id)){
    const capture='docs/redesign/r8/captures/'+item.id+'-'+width+'.png';
    await command('Page.captureScreenshot',{format:'png',captureBeyondViewport:false}).then(r=>writeFileSync(capture,Buffer.from(r.data,'base64')));
   }
  }
 }

 const stateAudits=[];
 async function scanState(page){await sleep(200);await evaluate(readFileSync('node_modules/axe-core/axe.min.js','utf8'));const a11y=await evaluate("axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa','wcag22aa','best-practice']}}).then(r=>({violations:r.violations.map(v=>({id:v.id,impact:v.impact,help:v.help,nodes:v.nodes.map(n=>({target:n.target,summary:n.failureSummary,html:n.html}))})),incomplete:r.incomplete.map(v=>({id:v.id,nodes:v.nodes.length}))}))");stateAudits.push({page,a11y})}
 await command('Emulation.setDeviceMetricsOverride',{width:390,height:900,deviceScaleFactor:1,mobile:true});
 await command('Page.navigate',{url:base+'/radar-ai'});await waitFor(()=>evaluate("!!document.querySelector('.chat-inline')"),'Radar audit');await send('O que e deck-building?');await send('Gosto de Mass Effect');await scanState('radar-com-fontes-e-recomendacoes');
 await evaluate("document.querySelector('.chat-mode-button').click()");await waitFor(()=>evaluate("!!document.querySelector('.chat-panel:not(.chat-inline)')"),'compact audit');await evaluate("document.querySelector('[aria-label=\"Expandir chat\"]').click()");await scanState('radar-expandido');
 await command('Page.navigate',{url:base+'/jogos'});await waitFor(()=>evaluate("!!document.querySelector('.catalog-filter-toggle') && !!document.querySelector('.catalog-count')"),'filters audit');await evaluate("document.querySelector('.catalog-filter-toggle').click()");await scanState('filtros-mobile');
 await command('Network.setCookie',{name:'boardradar-session',value:seller.cookie.split('=')[1],url:base,httpOnly:true,sameSite:'Strict'});await command('Page.navigate',{url:base+'/meus-anuncios'});await waitFor(()=>evaluate("document.querySelectorAll('.account-game').length===2"),'owner audit');await evaluate("[...document.querySelectorAll('.account-game button')].find(b=>b.textContent==='Remover').click()");await waitFor(()=>evaluate("!!document.querySelector('dialog[open]')"),'dialog audit');await scanState('confirmacao');
 // Keyboard checks supplement the automated DOM scan.
 await command('Page.navigate',{url:base+'/jogos'});await waitFor(()=>evaluate("!!document.querySelector('.catalog-count')"),'keyboard catalogue');
 await evaluate("document.activeElement.blur();window.scrollTo({top:0,behavior:'instant'})");
 await command('Input.dispatchKeyEvent',{type:'keyDown',key:'Tab',code:'Tab',windowsVirtualKeyCode:9});await command('Input.dispatchKeyEvent',{type:'keyUp',key:'Tab',code:'Tab',windowsVirtualKeyCode:9});assert(await evaluate("document.activeElement.classList.contains('skip-link')"));
 await command('Input.dispatchKeyEvent',{type:'keyDown',key:'Enter',code:'Enter',windowsVirtualKeyCode:13});await command('Input.dispatchKeyEvent',{type:'keyUp',key:'Enter',code:'Enter',windowsVirtualKeyCode:13});assert.equal(await evaluate('document.activeElement.id'),'page-content');
 await command('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-motion',value:'reduce'}]});assert.equal(await evaluate("getComputedStyle(document.documentElement).scrollBehavior"),'auto');await command('Emulation.setEmulatedMedia',{features:[]});
 // HTTP contracts and SEO; robots directives are not an authorization mechanism.
 assert((await(await fetch(base+'/robots.txt')).text()).includes('Disallow: /'));
 assert(!(await(await fetch(base+'/sitemap.xml')).text()).includes('/conta'));
 for(const path of ['/','/jogos','/marketplace','/radar-ai','/entrar','/cadastro','/minha-conta','/favoritos','/moderacao']){const html=await(await fetch(base+path)).text();assert(/name="robots" content="noindex, nofollow"/.test(html),path+' robots');}
 assert.equal((await fetch(base+'/api/catalog?page_size=13')).status,400);assert.equal((await fetch(base+'/out/any')).status,403);
 const editorial=await(await fetch(base+'/api/catalog?source=editorial&page_size=96')).json();assert.equal(editorial.total,JSON.parse(readFileSync('src/data/games.json','utf8')).length);assert(editorial.results.every(g=>g.curated_game_id));
 for(const sort of ['name','year','duration']){const r=await(await fetch(base+'/api/catalog?players=4&duration=60&kind=boardgame&page_size=96&sort='+sort)).json();assert(r.results.every(g=>g.min_players<=4&&g.max_players>=4&&g.max_minutes<=60&&g.kind==='boardgame'));}
 const rawGames=JSON.parse(readFileSync('src/data/games.json','utf8'));const rawLibrary=JSON.parse(readFileSync('src/data/library.json','utf8'));const curatedIds=new Set(rawGames.map(g=>g.id));const importedCount=rawLibrary.filter(g=>!curatedIds.has(g.curated_game_id)).length;
 const totals=await(await fetch(base+'/api/catalog')).json();assert.equal(totals.total,importedCount+rawGames.length);
 const catan=await(await fetch(base+'/api/catalog?q=Catan&page_size=96')).json();assert.equal(catan.results.filter(g=>g.curated_game_id==='g1').length,1);
 for(const sort of ['name','year','duration']){const rows=(await(await fetch(base+'/api/catalog?page_size=96&sort='+sort)).json()).results;assert(rows.every((g,i)=>!i||(sort==='name'?rows[i-1].name.localeCompare(g.name,'pt-BR')<=0:sort==='year'?(rows[i-1].year??-Infinity)>=(g.year??-Infinity):(rows[i-1].max_minutes||Infinity)<=(g.max_minutes||Infinity))));}
 const latencies={};
 for(const query of ['/api/catalog?page_size=24','/api/catalog?q=Catan&players=4','/api/library?q=Azul']){const samples=[];for(let n=0;n<21;n++){const start=performance.now();const r=await fetch(base+query);assert(r.ok);await r.json();samples.push(performance.now()-start)}const warm=samples.slice(1).sort((a,b)=>a-b);latencies[query]={first_sample_ms:samples[0],p50_ms:warm[Math.ceil(warm.length*.5)-1],p95_ms:warm[Math.ceil(warm.length*.95)-1],samples:20};}
 const report={date:new Date().toISOString(),environment:'Chrome headless, localhost, no CPU or network throttling; one browser per run. Not field Web Vitals.',matrix,stateAudits,latencies,js_errors:errors};
 writeFileSync('docs/redesign/r8/'+(process.argv.includes('--baseline')?'baseline':'audit')+'.json',JSON.stringify(report,null,2)+'\n');
 console.log(JSON.stringify({scenarios:matrix.length+stateAudits.length,violations:[...matrix,...stateAudits].filter(r=>r.a11y.violations.length).map(r=>({page:r.page,width:r.width,rules:r.a11y.violations.map(v=>v.id)})),overflow:matrix.filter(r=>r.overflow).length,latencies,js_errors:errors}));
 if(process.argv.includes('--strict')){assert.equal([...matrix,...stateAudits].filter(r=>r.a11y.violations.length).length,0,'Accessibility violations');assert.equal(matrix.filter(r=>r.overflow||r.width>r.requested_width+1).length,0);assert.deepEqual(errors,[]);}
}finally{
 if(ws?.readyState===1){await command('Browser.close',{},null).catch(()=>{});ws.close()}
 chrome?.kill();
 if(server.connected){server.send('shutdown');await Promise.race([new Promise(r=>server.once('exit',r)),sleep(3000)])}if(server.exitCode===null)server.kill();
 for(const p of pending.values()){clearTimeout(p.timer);p.fail(Error('Browser encerrado'))}
}
