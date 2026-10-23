import { spawn,spawnSync } from 'node:child_process';
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
import assert from 'node:assert/strict';
import sharp from 'sharp';

const chromePath=process.env.CHROME_EXECUTABLE||'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
assert(existsSync(chromePath),'Chrome não encontrado para validação visual.');
mkdirSync('.qa',{recursive:true});
const dbPath=resolve('.qa/user-flows-'+Date.now()+'.sqlite3');
const server=spawn(process.execPath,['scripts/run.mjs','--port','3101'],{windowsHide:true,stdio:['ignore','pipe','pipe','ipc'],env:{...process.env,RADAR_ACCOUNT_DB:dbPath}});
let serverLog='';server.stdout.on('data',d=>serverLog+=d);server.stderr.on('data',d=>serverLog+=d);
let chrome,ws;let nextId=1;const pending=new Map();let session;const errors=[];
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
async function waitFor(fn,label,timeout=20000){const end=Date.now()+timeout;while(Date.now()<end){try{const value=await fn();if(value)return value}catch{}await sleep(150)}throw Error('Timeout: '+label)}
function command(method,params={},sessionId=session){return new Promise((ok,fail)=>{const id=nextId++;const timer=setTimeout(()=>{pending.delete(id);fail(Error('CDP timeout: '+method))},10000);pending.set(id,{ok,fail,timer});ws.send(JSON.stringify({id,method,params,...sessionId?{sessionId}:{}}))})}
async function evaluate(expression){const data=await command('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});if(data.exceptionDetails)throw Error(data.exceptionDetails.text);return data.result.value}
async function send(text){const before=await evaluate("document.querySelectorAll('.message.assistant:not(.thinking)').length");await evaluate("document.querySelector('.chat-input input').focus()");await command('Input.insertText',{text});await evaluate("document.querySelector('.chat-input button').click()");await waitFor(()=>evaluate(`document.querySelectorAll('.message.assistant:not(.thinking)').length > ${before} && !document.querySelector('.thinking')`),'resposta do assistente');assert.equal(await evaluate("document.querySelector('.chat-error')?.textContent||''"),'')}

try{
 await waitFor(async()=>{try{return(await fetch('http://127.0.0.1:3101')).ok}catch{return false}},'servidor: '+serverLog,30000);
 chrome=spawn(chromePath,['--headless=new','--remote-debugging-port=0','--no-first-run','--no-default-browser-check','--disable-extensions',`--user-data-dir=${resolve('.qa/chrome-profile')}`,'about:blank'],{windowsHide:true,stdio:['ignore','ignore','pipe']});
 let chromeLog='';chrome.stderr.on('data',d=>chromeLog+=d);const endpoint=await waitFor(()=>chromeLog.match(/DevTools listening on (ws:\/\/[^\s]+)/)?.[1],'Chrome DevTools');
 ws=new WebSocket(endpoint);await new Promise((ok,fail)=>{ws.addEventListener('open',ok,{once:true});ws.addEventListener('error',fail,{once:true})});
 ws.addEventListener('message',event=>{const data=JSON.parse(event.data);if(data.id&&pending.has(data.id)){const p=pending.get(data.id);clearTimeout(p.timer);pending.delete(data.id);data.error?p.fail(Error(data.error.message)):p.ok(data.result)}if(data.method==='Runtime.exceptionThrown')errors.push(data.params.exceptionDetails.text)});
 const target=await command('Target.createTarget',{url:'about:blank'},null);const attached=await command('Target.attachToTarget',{targetId:target.targetId,flatten:true},null);session=attached.sessionId;
 await command('Runtime.enable');await command('Page.enable');await command('Emulation.setDeviceMetricsOverride',{width:1280,height:900,deviceScaleFactor:1,mobile:false});await command('Page.navigate',{url:'http://127.0.0.1:3101'});
 await waitFor(()=>evaluate("!!document.querySelector('.chat-launcher')"),'home hidratada');await sleep(500);await evaluate("document.querySelector('.chat-launcher').click()");


 await command('Page.navigate',{url:'http://127.0.0.1:3101/conta'});
 await waitFor(()=>evaluate("document.querySelector('.account-form fieldset') && !document.querySelector('.account-form fieldset').disabled"),'account ready');
 async function set(selector,value){await evaluate(`(()=>{const e=document.querySelector(${JSON.stringify(selector)});Object.getOwnPropertyDescriptor(e.tagName==='TEXTAREA'?HTMLTextAreaElement.prototype:HTMLInputElement.prototype,'value').set.call(e,${JSON.stringify(value)});e.dispatchEvent(new Event('input',{bubbles:true}))})()`)}
 const email='browser-'+Date.now()+'@example.local';
 await evaluate("document.querySelector('.account-form button[type=button]').click()");
 await set('input[autocomplete=name]','Browser Test');await set('input[type=email]',email);await set('input[type=password]','test-password-123');
 await evaluate("document.querySelector('.account-form').requestSubmit()");
 await waitFor(()=>evaluate("document.querySelector('.account-page h1').textContent==='Minha conta' && !document.querySelector('fieldset').disabled"),'registered').catch(async e=>{console.log(await evaluate("document.querySelector('.account-page').innerText"));throw e});
 assert.equal(await evaluate("document.cookie.includes('boardradar-session')"),false);
 await evaluate("document.querySelector('.account-columns').closest('details').open=true");await set('.account-columns .account-form input[maxlength="120"]','Jogo de teste');await set('.account-columns .account-form input[maxlength="100"]','Estrategia');
 await evaluate("document.querySelector('.account-columns .account-form').requestSubmit()");
 await waitFor(()=>evaluate("document.querySelectorAll('.account-game').length===1 && !document.querySelector('fieldset').disabled"),'game created');
 await evaluate("location.reload()");await waitFor(()=>evaluate("document.querySelectorAll('.account-game').length===1 && !document.querySelector('fieldset').disabled"),'persisted after reload');
 await evaluate("[...document.querySelectorAll('.account-game button')].find(b=>b.textContent==='Editar').click()");await set('.account-columns .account-form input[maxlength="120"]','Jogo editado');await evaluate("document.querySelector('.account-columns .account-form').requestSubmit()");
 await waitFor(()=>evaluate("document.querySelector('.account-game h3')?.textContent==='Jogo editado' && !document.querySelector('fieldset').disabled"),'edited');
 await command('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});
 assert(await evaluate("document.documentElement.scrollWidth<=window.innerWidth"));
 await command('Page.captureScreenshot',{format:'png',captureBeyondViewport:true}).then(r=>writeFileSync('.qa/account-mobile.png',Buffer.from(r.data,'base64')));
 const csrf=await fetch('http://127.0.0.1:3101/api/account',{method:'POST',headers:{'Content-Type':'application/json',Origin:'https://example.invalid'},body:JSON.stringify({action:'logout'})});assert.equal(csrf.status,403);
 await evaluate("[...document.querySelectorAll('.account-top button')].find(b=>b.textContent==='Sair').click()");
 await waitFor(()=>evaluate("!!document.querySelector('input[type=password]') && !document.querySelector('fieldset').disabled"),'logout');
 await set('input[type=email]',email);await set('input[type=password]','test-password-123');await evaluate("document.querySelector('.account-form').requestSubmit()");
 await waitFor(()=>evaluate("document.querySelectorAll('.account-game').length===1 && !document.querySelector('fieldset').disabled"),'login retains game');

 await command('Page.navigate',{url:'http://127.0.0.1:3101/anuncios'});
 await waitFor(()=>evaluate("!!document.querySelector('.account-form fieldset') && !document.querySelector('fieldset').disabled"),'listing page');
 await set('.account-form input[maxlength="120"]','Catan para venda');
 await set('.account-form textarea[maxlength="3000"]','Jogo de teste completo e conservado.');
 await set('.account-form input[inputmode=decimal]','150,50');
 await set('.account-form input[placeholder*="Campinas"]','Campinas, SP');
 await set('.account-form textarea[name=components]','Completo, sem componentes ausentes.');
 await set('.account-form textarea[name=defects]','Sem defeitos observados.');await evaluate("[...document.querySelectorAll('.account-form select')].find(e=>e.querySelector('[value=pickup]')).value='pickup';[...document.querySelectorAll('.account-form select')].find(e=>e.querySelector('[value=pickup]')).dispatchEvent(new Event('change',{bubbles:true}))");
 await evaluate("document.querySelector('.account-form').requestSubmit()");
 await waitFor(()=>evaluate("document.querySelectorAll('.account-game').length===1 && !document.querySelector('fieldset').disabled"),'listing created');
 assert(await evaluate("document.querySelector('.account-game').textContent.includes('150,50')"));
 const stored=await evaluate("fetch('/api/listings').then(r=>r.json())");assert.equal(stored.listings[0].status,'draft');
 const denied=await evaluate(`fetch('/api/listings',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action:'submit',data:{id:'${stored.listings[0].id}'}})}).then(r=>r.status)`);assert.equal(denied,400);
 await evaluate("[...document.querySelectorAll('.account-game button')].find(b=>b.textContent==='Editar').click()");await set('.account-form input[inputmode=decimal]','125,00');await evaluate("document.querySelector('.account-form').requestSubmit()");
 await waitFor(()=>evaluate("document.querySelector('.account-game').textContent.includes('125,00') && !document.querySelector('fieldset').disabled"),'listing updated');
 await evaluate('location.reload()');await waitFor(()=>evaluate("document.querySelector('.account-game')?.textContent.includes('125,00') && !document.querySelector('fieldset').disabled"),'listing persisted');
 assert(await evaluate("document.documentElement.scrollWidth<=innerWidth"));
 await command('Page.captureScreenshot',{format:'png',captureBeyondViewport:true}).then(r=>writeFileSync('.qa/marketplace-phase1-mobile.png',Buffer.from(r.data,'base64')));
 assert.equal((await fetch('http://127.0.0.1:3101/api/listings')).status,401);

 const base='http://127.0.0.1:3101';
 const sellerCookies=await command('Network.getCookies',{urls:[base]});
 const sellerCookie='boardradar-session='+sellerCookies.cookies.find(c=>c.name==='boardradar-session').value;

 await command('Page.navigate',{url:base+'/conta'});
 await waitFor(()=>evaluate("document.querySelector('.account-journey')?.getAttribute('aria-busy')==='false'"),'account choices');
 assert(await evaluate("[...document.querySelectorAll('.journey-options a')].some(a=>a.textContent==='Vender um jogo')"));
 await evaluate("document.querySelector('.account-journey details').open=true;const e=document.querySelector('.account-journey details select');Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype,'value').set.call(e,'advanced');e.dispatchEvent(new Event('change',{bubbles:true}));document.querySelector('.profile-checks input').click();document.querySelector('.account-journey details .profile-consent input').click()");
 await set('.account-journey input[maxlength="500"]','Duna e Mass Effect');
 await evaluate("document.querySelector('.account-journey details form').requestSubmit()");
 await waitFor(()=>evaluate("document.querySelector('.account-journey [role=status]')?.textContent.includes('atualizadas')"),'profile saved');
 const profileData=await(await fetch(base+'/api/account',{headers:{Cookie:sellerCookie}})).json();assert.equal(profileData.profile.experience,'advanced');assert(profileData.recommended_ids.length>0);
 await command('Page.captureScreenshot',{format:'png',captureBeyondViewport:true}).then(r=>writeFileSync('.qa/user-account-journey-mobile.png',Buffer.from(r.data,'base64')));
 await command('Page.navigate',{url:base+'/anuncios'});await waitFor(()=>evaluate("document.querySelectorAll('.account-game').length===1"),'seller listing again');
 const original=await sharp({create:{width:240,height:180,channels:3,background:'#da9c33'}}).withMetadata({exif:{IFD0:{Artist:'Private metadata'}}}).png().toBuffer();
 const photoPath=resolve('.qa/listing-photo-fixture.png');writeFileSync(photoPath,original);
 const current=await evaluate("fetch('/api/listings').then(r=>r.json())");const lid=current.listings[0].id;
 const bad=await fetch(base+`/api/listing-images?listing_id=${lid}&revision=${current.listings[0].revision}`,{method:'POST',headers:{Origin:base,Cookie:sellerCookie,'Content-Type':'image/png'},body:Buffer.from('<svg>invalid</svg>')});assert.equal(bad.status,400);
 const dom=await command('DOM.getDocument');const node=await command('DOM.querySelector',{nodeId:dom.root.nodeId,selector:'.account-game input[type=file]'});
 await command('DOM.setFileInputFiles',{nodeId:node.nodeId,files:[photoPath]});
 await waitFor(()=>evaluate("document.querySelectorAll('.listing-photo-grid img').length===1"),'photo upload');
 const uploaded=await evaluate("fetch('/api/listings').then(r=>r.json())");const imageId=uploaded.listings[0].images[0].id;
 const image=await fetch(base+'/api/listing-images?id='+imageId,{headers:{Cookie:sellerCookie}});assert.equal(image.status,200);assert.equal(image.headers.get('content-type'),'image/jpeg');
 const meta=await sharp(Buffer.from(await image.arrayBuffer())).metadata();assert.equal(meta.exif,undefined);assert.equal(meta.icc,undefined);
 assert.equal((await fetch(base+'/api/listing-images?id='+imageId)).status,404);

 const buyerEmail='buyer-'+Date.now()+'@example.local';
 const buyerRegister=await fetch(base+'/api/account',{method:'POST',headers:{Origin:base,'Content-Type':'application/json'},body:JSON.stringify({action:'register',data:{name:'Comprador',email:buyerEmail,password:'test-password-123'}})});assert.equal(buyerRegister.status,200);
 const buyerCookie=buyerRegister.headers.getSetCookie()[0].split(';')[0];
 await command('Network.setCookie',{name:'boardradar-session',value:buyerCookie.split('=')[1],url:base,httpOnly:true,sameSite:'Strict'});await command('Page.navigate',{url:base+'/conta'});
 await waitFor(()=>evaluate("document.querySelector('.account-journey')?.getAttribute('aria-busy')==='false'"),'buyer account');
 await evaluate("document.querySelector('#desejos').open=true;document.querySelector('#desejos .profile-consent input').click()");await set('#desejos input[inputmode=decimal]','200,00');await evaluate("document.querySelector('#desejos form').requestSubmit()");
 await waitFor(()=>evaluate("document.querySelector('#desejos').textContent.includes('Alertas ativados')"),'wishlist subscribed');
 await command('Network.setCookie',{name:'boardradar-session',value:sellerCookie.split('=')[1],url:base,httpOnly:true,sameSite:'Strict'});await command('Page.navigate',{url:base+'/anuncios'});await waitFor(()=>evaluate("document.querySelectorAll('.listing-photo-grid img').length===1"),'return seller');
 const modEmail='moderator-'+Date.now()+'@example.local';
 const registration=await fetch(base+'/api/account',{method:'POST',headers:{Origin:base,'Content-Type':'application/json'},body:JSON.stringify({action:'register',data:{name:'Moderator',email:modEmail,password:'test-password-123'}})});assert.equal(registration.status,200);
 const modCookie=registration.headers.getSetCookie()[0].split(';')[0];
 assert.equal((await fetch(base+'/api/listing-images?id='+imageId,{headers:{Cookie:modCookie}})).status,404);
 assert.equal((await fetch(base+'/api/listings?view=queue',{headers:{Cookie:modCookie}})).status,403);
 const python=resolve('..','.tools','python-3.13.7','python.exe');const grant=spawnSync(python,['scripts/set-moderator.py',modEmail],{windowsHide:true,env:{...process.env,PYTHONUTF8:'1',RADAR_ACCOUNT_DB:dbPath}});assert.equal(grant.status,0);
 await evaluate("document.querySelector('.listing-review').open=true;document.querySelector('.listing-review input').click()");await evaluate("[...document.querySelectorAll('.account-game button')].find(b=>b.textContent==='Enviar para revis\u00e3o').click()");
 await waitFor(()=>evaluate("document.querySelector('.account-game .eyebrow')?.textContent==='Em revis\u00e3o'"),'submitted');
 await command('Network.setCookie',{name:'boardradar-session',value:modCookie.split('=')[1],url:base,httpOnly:true,sameSite:'Strict'});
 await command('Page.navigate',{url:base+'/moderacao'});
 await waitFor(()=>evaluate("document.querySelectorAll('.moderation-card').length===1 && !document.querySelector('.moderation-card button').disabled===false"),'moderation queue');
 await set('.moderation-card textarea','Fotos e edicao conferidas.');await evaluate("document.querySelector('.moderation-confirm input').click()");
 await evaluate("[...document.querySelectorAll('.moderation-card button')].find(b=>b.textContent==='Aprovar').click()");
 await waitFor(()=>evaluate("document.querySelectorAll('.moderation-card').length===0 && document.querySelector('[role=status]')?.textContent.includes('aprovado')"),'approved');
 let sellerData=await(await fetch(base+'/api/listings',{headers:{Cookie:sellerCookie}})).json();assert.equal(sellerData.listings[0].status,'active');

 const approvedRow=sellerData.listings[0];
 const communityChat=await(await fetch(base+'/api/chat',{method:'POST',headers:{'Content-Type':'application/json',Cookie:buyerCookie},body:JSON.stringify({message:'Ofertas de Catan'})})).json();assert(communityChat.community_offers?.some(o=>o.id===lid));
 const buyerNotified=await(await fetch(base+'/api/account',{headers:{Cookie:buyerCookie}})).json();assert.equal(buyerNotified.notifications.length,1);
 await command('Network.setCookie',{name:'boardradar-session',value:buyerCookie.split('=')[1],url:base,httpOnly:true,sameSite:'Strict'});await command('Page.navigate',{url:base+'/marketplace'});await waitFor(()=>evaluate("document.querySelectorAll('.community-card').length===1"),'buyer marketplace');
 await evaluate("document.querySelector('.community-actions details').open=true");await set('.community-actions details textarea','Ola, aceita retirada em Campinas?');await evaluate("document.querySelector('.community-actions details form').requestSubmit()");
 await waitFor(()=>evaluate("document.querySelector('.community-actions [role=status]')?.textContent.includes('Mensagem enviada')"),'buyer inquiry');
 await command('Page.navigate',{url:base+'/mensagens'});await waitFor(()=>evaluate("document.querySelectorAll('.inbox-message').length===1"),'buyer inbox');
 await set('.account-form textarea','Posso retirar no fim de semana.');await evaluate("document.querySelector('.account-form form').requestSubmit()");await waitFor(()=>evaluate("document.querySelectorAll('.inbox-message').length===2"),'buyer reply');
 assert.equal((await(await fetch(base+'/api/listings?view=inbox',{headers:{Cookie:modCookie}})).json()).conversations.length,0);
 await command('Network.setCookie',{name:'boardradar-session',value:sellerCookie.split('=')[1],url:base,httpOnly:true,sameSite:'Strict'});await command('Page.navigate',{url:base+'/mensagens'});await waitFor(()=>evaluate("document.querySelectorAll('.inbox-message').length===2"),'seller inbox');await set('.account-form textarea','Sim, podemos combinar pelo chat.');await evaluate("document.querySelector('.account-form form').requestSubmit()");await waitFor(()=>evaluate("document.querySelectorAll('.inbox-message').length===3"),'seller reply');
 const request=await fetch(base+'/api/listings',{method:'POST',headers:{Origin:base,Cookie:sellerCookie,'Content-Type':'application/json'},body:JSON.stringify({action:'request_game',data:{name:'Jogo ainda ausente',edition:'Edicao brasileira','notes':'Preciso anunciar.'}})});assert.equal(request.status,200);
 const requests=await(await fetch(base+'/api/listings?view=requests',{headers:{Cookie:modCookie}})).json();const requestRow=requests.requests.find(r=>r.name==='Jogo ainda ausente');assert(requestRow);
 const decision=await fetch(base+'/api/listings',{method:'POST',headers:{Origin:base,Cookie:modCookie,'Content-Type':'application/json'},body:JSON.stringify({action:'decide_request',data:{record_id:requestRow.id,status:'reviewed',reason:'Dados solicitados ao vendedor'}})});assert.equal(decision.status,200);
 const report=await fetch(base+'/api/listings',{method:'POST',headers:{Origin:base,Cookie:buyerCookie,'Content-Type':'application/json'},body:JSON.stringify({action:'report',data:{id:lid,reason:'Solicito revisao das informacoes'}})});assert.equal(report.status,200);
 const reports=await(await fetch(base+'/api/listings?view=reports',{headers:{Cookie:modCookie}})).json();const reportRow=reports.reports.find(r=>r.listing_id===lid);assert(reportRow);
 const resolved=await fetch(base+'/api/listings',{method:'POST',headers:{Origin:base,Cookie:modCookie,'Content-Type':'application/json'},body:JSON.stringify({action:'resolve_report',data:{record_id:reportRow.id,reason:'Revisado sem irregularidade',remove:false}})});assert.equal(resolved.status,200);
 const cancel=await fetch(base+'/api/account',{method:'POST',headers:{Origin:base,Cookie:buyerCookie,'Content-Type':'application/json'},body:JSON.stringify({action:'delete_wishlist',data:{edition_id:approvedRow.edition_id}})});assert.equal(cancel.status,200);
 await command('Network.setCookie',{name:'boardradar-session',value:modCookie.split('=')[1],url:base,httpOnly:true,sameSite:'Strict'});

 let publicData=await(await fetch(base+'/api/listings?view=public&edition_id='+approvedRow.edition_id)).json();assert.equal(publicData.total,1);assert(!('seller_id' in publicData.listings[0]));
 assert.equal((await fetch(base+'/api/listing-images?id='+imageId)).status,200);
 await command('Page.navigate',{url:base+'/marketplace'});await waitFor(()=>evaluate("document.querySelectorAll('.community-card').length===1"),'marketplace discovery');
 await set('.community-search input','Catan');await waitFor(()=>evaluate("document.querySelectorAll('.community-card').length===1 && document.querySelector('.community-grid').getAttribute('aria-busy')==='false'"),'marketplace search');
 assert(await evaluate("document.documentElement.scrollWidth<=innerWidth"));
 await command('Page.captureScreenshot',{format:'png',captureBeyondViewport:true}).then(r=>writeFileSync('.qa/marketplace-phase3-mobile.png',Buffer.from(r.data,'base64')));
 await command('Page.navigate',{url:base+'/jogos/catan?edition='+approvedRow.edition_id+'#comunidade'});await waitFor(()=>evaluate("document.querySelectorAll('#comunidade .community-card').length===1"),'product page community separated');
 assert(await evaluate("!!document.querySelector('#ofertas .offer-card')"));
 let revision=approvedRow.revision;
 for(const status of ['reserved','active','paused','active']){
  const response=await fetch(base+'/api/listings',{method:'POST',headers:{Origin:base,Cookie:sellerCookie,'Content-Type':'application/json'},body:JSON.stringify({action:'transition',data:{id:lid,revision,status}})});assert.equal(response.status,200);const body=await response.json();revision=body.listings[0].revision;
  assert.equal((await(await fetch(base+'/api/listings?view=public&edition_id='+approvedRow.edition_id)).json()).total,status==='active'?1:0);
  assert.equal((await fetch(base+'/api/listing-images?id='+imageId)).status,status==='active'?200:404);
 }
 sellerData=await(await fetch(base+'/api/listings',{headers:{Cookie:sellerCookie}})).json();
 const row=sellerData.listings[0];
 const edit=await fetch(base+'/api/listings',{method:'POST',headers:{Origin:base,Cookie:sellerCookie,'Content-Type':'application/json'},body:JSON.stringify({action:'update',data:{...row,sealed:!!row.sealed,negotiable:!!row.negotiable,title:'Catan atualizado'}})});assert.equal(edit.status,200);
 sellerData=await edit.json();assert.equal(sellerData.listings[0].status,'draft');
 const resubmit=await fetch(base+'/api/listings',{method:'POST',headers:{Origin:base,Cookie:sellerCookie,'Content-Type':'application/json'},body:JSON.stringify({action:'submit',data:{id:lid,revision:sellerData.listings[0].revision,terms_accepted:true,terms_version:'local-mvp-2026-10-20-v1'}})});assert.equal(resubmit.status,200);
 await command('Page.navigate',{url:base+'/moderacao'});await waitFor(()=>evaluate("document.querySelectorAll('.moderation-card').length===1"),'resubmitted');
 await set('.moderation-card textarea','Adicione foto dos componentes.');await evaluate("[...document.querySelectorAll('.moderation-card button')].find(b=>b.textContent==='Rejeitar').click()");
 await waitFor(()=>evaluate("document.querySelectorAll('.moderation-card').length===0"),'rejected');
 sellerData=await(await fetch(base+'/api/listings',{headers:{Cookie:sellerCookie}})).json();assert.equal(sellerData.listings[0].status,'rejected');assert.equal(sellerData.listings[0].review_reason,'Adicione foto dos componentes.');
 await command('Network.setCookie',{name:'boardradar-session',value:sellerCookie.split('=')[1],url:base,httpOnly:true,sameSite:'Strict'});await command('Page.navigate',{url:base+'/anuncios'});
 await waitFor(()=>evaluate("document.querySelectorAll('.listing-photo-grid img').length===1"),'seller photos retained');assert(await evaluate("document.documentElement.scrollWidth<=innerWidth"));
 await command('Page.captureScreenshot',{format:'png',captureBeyondViewport:true}).then(r=>writeFileSync('.qa/marketplace-phase2-mobile.png',Buffer.from(r.data,'base64')));

 let currentRow=sellerData.listings[0];
 let submission=await fetch(base+'/api/listings',{method:'POST',headers:{Origin:base,Cookie:sellerCookie,'Content-Type':'application/json'},body:JSON.stringify({action:'submit',data:{id:lid,revision:currentRow.revision,terms_accepted:true,terms_version:'local-mvp-2026-10-20-v1'}})});assert.equal(submission.status,200);currentRow=(await submission.json()).listings[0];
 const approval=await fetch(base+'/api/listings',{method:'POST',headers:{Origin:base,Cookie:modCookie,'Content-Type':'application/json'},body:JSON.stringify({action:'approve',data:{id:lid,revision:currentRow.revision,reason:'Fotos conferidas novamente',edition_confirmed:true}})});assert.equal(approval.status,200);
 await command('Page.navigate',{url:base+'/anuncios'});await waitFor(()=>evaluate("[...document.querySelectorAll('.account-game button')].some(b=>b.textContent==='Marcar vendido')"),'seller availability controls');
 await evaluate("[...document.querySelectorAll('.account-game button')].find(b=>b.textContent==='Marcar vendido').click()");await waitFor(()=>evaluate("!!document.querySelector('dialog[open]')"),'sale confirmation');await evaluate("[...document.querySelectorAll('dialog[open] button')].find(b=>b.textContent==='Marcar vendido').click()");
 await waitFor(()=>evaluate("document.querySelector('.account-game .eyebrow')?.textContent==='Vendido'"),'marked sold');
 assert.equal((await(await fetch(base+'/api/listings?view=public&edition_id='+currentRow.edition_id)).json()).total,0);
 assert.equal((await fetch(base+'/api/listing-images?id='+imageId)).status,404);
 assert.deepEqual(errors,[]);console.log('User flows approved (except intentionally excluded Google): profile, consent, wishlist notifications, messages and privacy, catalog requests, reports; phase 3: public search, product edition, separate merchant/community sections, safe projection, mobile, reserve/pause/reactivate/sell and photo visibility; phase 2 regressions passed.');
}finally{
 if(ws?.readyState===1){await command('Browser.close',{},null).catch(()=>{});ws.close()}
 chrome?.kill();
 if(server.connected){server.send('shutdown');await Promise.race([new Promise(r=>server.once('exit',r)),sleep(3000)])}if(server.exitCode===null)server.kill();
 for(const p of pending.values()){clearTimeout(p.timer);p.fail(Error('Browser encerrado'))}
}
