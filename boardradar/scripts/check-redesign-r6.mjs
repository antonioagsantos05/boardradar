import { spawn,spawnSync } from 'node:child_process';
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
import assert from 'node:assert/strict';
import sharp from 'sharp';

const chromePath=process.env.CHROME_EXECUTABLE||'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
assert(existsSync(chromePath),'Chrome não encontrado para validação visual.');
mkdirSync('.qa',{recursive:true});
mkdirSync('docs/redesign/r6/captures',{recursive:true});
const dbPath=resolve('.qa/user-flows-'+Date.now()+'.sqlite3');
const server=spawn(process.execPath,['scripts/run.mjs','--port','3103'],{windowsHide:true,stdio:['ignore','pipe','pipe','ipc'],env:{...process.env,RADAR_ACCOUNT_DB:dbPath}});
let serverLog='';server.stdout.on('data',d=>serverLog+=d);server.stderr.on('data',d=>serverLog+=d);
let chrome,ws;let nextId=1;const pending=new Map();let session;const errors=[];
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
async function waitFor(fn,label,timeout=20000){const end=Date.now()+timeout;while(Date.now()<end){try{const value=await fn();if(value)return value}catch{}await sleep(150)}throw Error('Timeout: '+label)}
function command(method,params={},sessionId=session){return new Promise((ok,fail)=>{const id=nextId++;const timer=setTimeout(()=>{pending.delete(id);fail(Error('CDP timeout: '+method))},10000);pending.set(id,{ok,fail,timer});ws.send(JSON.stringify({id,method,params,...sessionId?{sessionId}:{}}))})}
async function evaluate(expression){const data=await command('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});if(data.exceptionDetails)throw Error(data.exceptionDetails.text);return data.result.value}
async function send(text){const before=await evaluate("document.querySelectorAll('.message.assistant:not(.thinking)').length");await evaluate("document.querySelector('.chat-input input').focus()");await command('Input.insertText',{text});await evaluate("document.querySelector('.chat-input button').click()");await waitFor(()=>evaluate(`document.querySelectorAll('.message.assistant:not(.thinking)').length > ${before} && !document.querySelector('.thinking')`),'resposta do assistente');assert.equal(await evaluate("document.querySelector('.chat-error')?.textContent||''"),'')}

try{
 await waitFor(async()=>{try{return(await fetch('http://127.0.0.1:3103')).ok}catch{return false}},'servidor: '+serverLog,30000);
 chrome=spawn(chromePath,['--headless=new','--remote-debugging-port=0','--no-first-run','--no-default-browser-check','--disable-extensions',`--user-data-dir=${resolve('.qa/r6-chrome-profile')}`,'about:blank'],{windowsHide:true,stdio:['ignore','ignore','pipe']});
 let chromeLog='';chrome.stderr.on('data',d=>chromeLog+=d);const endpoint=await waitFor(()=>chromeLog.match(/DevTools listening on (ws:\/\/[^\s]+)/)?.[1],'Chrome DevTools');
 ws=new WebSocket(endpoint);await new Promise((ok,fail)=>{ws.addEventListener('open',ok,{once:true});ws.addEventListener('error',fail,{once:true})});
 ws.addEventListener('message',event=>{const data=JSON.parse(event.data);if(data.id&&pending.has(data.id)){const p=pending.get(data.id);clearTimeout(p.timer);pending.delete(data.id);data.error?p.fail(Error(data.error.message)):p.ok(data.result)}if(data.method==='Runtime.exceptionThrown')errors.push(data.params.exceptionDetails.text)});
 const target=await command('Target.createTarget',{url:'about:blank'},null);const attached=await command('Target.attachToTarget',{targetId:target.targetId,flatten:true},null);session=attached.sessionId;
 await command('Runtime.enable');await command('Page.enable');await command('Emulation.setDeviceMetricsOverride',{width:1280,height:900,deviceScaleFactor:1,mobile:false});await command('Page.navigate',{url:'http://127.0.0.1:3103'});

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
 for(const width of [360,390,768,1024,1440]){
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
   matrix.push({page:item.id,...facts});
   if([390,1440].includes(width)&&['home','conta-nova','cadastro','favoritos','onboarding','entrar-novo','jogo','marketplace','vender','anuncio-publico'].includes(item.id)){
    const capture='docs/redesign/r6/captures/'+item.id+'-'+width+'.png';
    await command('Page.captureScreenshot',{format:'png',captureBeyondViewport:false}).then(r=>writeFileSync(capture,Buffer.from(r.data,'base64')));
   }
  }
 }

 // Real wizard draft, photos, resume, review, owner access and public-only detail.
 const available=await(await fetch(base+'/api/listings?view=detail&id='+approved.id)).json();assert.equal(available.listing.id,approved.id);assert(!('seller_id' in available.listing));assert(!('review_reason' in available.listing));
 const privateRows=(await(await fetch(base+'/api/listings',{headers:{Cookie:seller.cookie}})).json()).listings;
 const privateId=privateRows.find(r=>r.status!=='active').id;assert.equal((await fetch(base+'/api/listings?view=detail&id='+privateId)).status,404);assert.equal((await fetch(base+'/api/listings?view=detail&id=unknown')).status,404);
 await command('Network.setCookie',{name:'boardradar-session',value:seller.cookie.split('=')[1],url:base,httpOnly:true,sameSite:'Strict'});
 await command('Page.navigate',{url:base+'/vender'});await waitFor(()=>evaluate("!!document.querySelector('.sell-panel')"),'wizard ready');
 async function fill(selector,text){await evaluate(`document.querySelector(${JSON.stringify(selector)}).focus();document.querySelector(${JSON.stringify(selector)}).select()`);await command('Input.insertText',{text})}
 async function next(step){await evaluate("document.querySelector('.sell-panel button[type=submit]').click()");await waitFor(()=>evaluate(`document.querySelector('.sell-panel h2')?.textContent.startsWith('${step}.')`),'wizard step '+step)}
 await fill('.sell-panel input','Anuncio criado em etapas');await fill('.sell-panel textarea','Jogo completo para verificar o fluxo local em etapas.');await next(2);
 await fill('.sell-panel textarea','Completo, sem itens ausentes');
 await evaluate("document.querySelectorAll('.sell-panel textarea')[1].focus()");await command('Input.insertText',{text:'Sem defeitos observados'});await next(3);
 await fill('.sell-panel input','170,50');await fill('.sell-panel label:nth-of-type(2) input','Campinas, SP');await evaluate("const s=document.querySelector('.sell-panel select');s.value='pickup';s.dispatchEvent(new Event('change',{bubbles:true}))");await next(4);
 await waitFor(()=>evaluate("!!new URLSearchParams(location.search).get('id') && !!document.querySelector('.photo-upload input')"),'persisted draft ID');
 const wizardId=await evaluate("new URLSearchParams(location.search).get('id')");
 let mine=(await(await fetch(base+'/api/listings',{headers:{Cookie:seller.cookie}})).json()).listings;assert.equal(mine.find(r=>r.id===wizardId).price_cents,17050);assert.equal((await fetch(base+'/api/listings?view=detail&id='+wizardId)).status,404);
 const photoPath=resolve('.qa/r5-wizard-photo.png');writeFileSync(photoPath,original);const doc=await command('DOM.getDocument');const node=await command('DOM.querySelector',{nodeId:doc.root.nodeId,selector:'.photo-upload input'});await command('DOM.setFileInputFiles',{nodeId:node.nodeId,files:[photoPath]});
 await waitFor(()=>evaluate("document.querySelectorAll('.listing-photo-grid img').length===1 && !document.querySelector('.photo-upload input').disabled"),'photo persisted');
 await command('Page.navigate',{url:base+'/vender?id='+wizardId});await waitFor(()=>evaluate("document.querySelectorAll('.listing-photo-grid img').length===1"),'resume saved draft and photo');
 await next(5);assert(await evaluate("document.querySelector('.sell-panel button[type=submit]').disabled"));
 await evaluate("document.querySelector('.sell-check input').click()");await evaluate("document.querySelector('.sell-panel button[type=submit]').click()");await waitFor(()=>evaluate("location.pathname==='/meus-anuncios'"),'submitted wizard');
 mine=(await(await fetch(base+'/api/listings',{headers:{Cookie:seller.cookie}})).json()).listings;const queued=mine.find(r=>r.id===wizardId);assert.equal(queued.status,'pending_review');assert.equal((await fetch(base+'/api/listings?view=detail&id='+wizardId)).status,404);
 await post('/api/listings','approve',{id:wizardId,revision:queued.revision,reason:'Verificacao do fluxo em etapas',edition_confirmed:true},moderator.cookie);
 assert.equal((await fetch(base+'/api/listings?view=detail&id='+wizardId)).status,200);
 let latest=(await(await fetch(base+'/api/listings',{headers:{Cookie:seller.cookie}})).json()).listings.find(r=>r.id===wizardId);
 await post('/api/listings','transition',{id:wizardId,revision:latest.revision,status:'paused'},seller.cookie);assert.equal((await fetch(base+'/api/listings?view=detail&id='+wizardId)).status,404);
 await post('/api/listings','remove',{id:wizardId},seller.cookie);
 // Existing owner regression expects two rows; the wizard fixture is now removed, so scope selectors below to its original fixtures.
 // R6: optional onboarding, explicit local transfer, edition alerts, notification and logout.
 await command('Network.deleteCookies',{name:'boardradar-session',url:base});
 await command('Page.navigate',{url:base+'/cadastro?next=%2Fjogos'});await waitFor(()=>evaluate("!!document.querySelector('.access-page input[name=name]')"),'registration page');
 await fill('.access-page input[name=name]','Comprador R6');await fill('.access-page input[name=email]','buyer-r6@audit.local');await fill('.access-page input[name=password]','audit-test-password');
 await evaluate("document.querySelector('.access-page form').requestSubmit()");await waitFor(()=>evaluate("location.pathname==='/onboarding' && !!document.querySelector('.account-journey fieldset:not(:disabled)')"),'optional onboarding');
 assert.equal(await evaluate("fetch('/api/account').then(r=>r.json()).then(b=>b.profile)"),null);
 await evaluate("[...document.querySelectorAll('.account-panel a')].find(a=>a.textContent==='Pular e continuar').click()");await waitFor(()=>evaluate("location.pathname==='/jogos' && !!document.querySelector('.catalog-count')"),'skip onboarding');
 await command('Page.navigate',{url:base+'/onboarding'});await waitFor(()=>evaluate("!!document.querySelector('.account-journey fieldset:not(:disabled)')"),'profile ready');
 await evaluate("const s=document.querySelector('.account-journey select');s.value='beginner';s.dispatchEvent(new Event('change',{bubbles:true}));document.querySelector('.account-journey .profile-consent input').click()");
 await fill('.account-journey input[maxlength="500"]','Mass Effect');
 await evaluate("[...document.querySelectorAll('.account-journey button')].find(b=>b.textContent==='Salvar prefer\u00eancias').click()");
 await waitFor(()=>evaluate("document.querySelector('.account-journey [role=status]')?.textContent.includes('atualizadas')"),'profile saved');
 assert.equal(await evaluate("fetch('/api/account').then(r=>r.json()).then(b=>b.profile.consent)"),true);
 await evaluate("[...document.querySelectorAll('.account-journey button')].find(b=>b.textContent==='Excluir prefer\u00eancias').click()");
 await waitFor(()=>evaluate("document.querySelector('.account-journey [role=status]')?.textContent.includes('exclu')"),'profile removed');
 assert.equal(await evaluate("fetch('/api/account').then(r=>r.json()).then(b=>b.profile)"),null);
 await evaluate(`localStorage.setItem('boardradar-favorites',JSON.stringify(['g1',${JSON.stringify(imported.id)}]))`);
 await command('Page.navigate',{url:base+'/favoritos'});await waitFor(()=>evaluate("!!document.querySelector('#desejos fieldset:not(:disabled)') && !!document.querySelector('.local-favorites form')"),'separate favorites');
 await evaluate("document.querySelector('.local-favorites form').requestSubmit()");await waitFor(()=>evaluate("document.querySelector('.local-favorites')?.parentElement.textContent.includes('Edi\u00e7\u00e3o adicionada')"),'explicit favorite transfer');
 await waitFor(()=>evaluate("!!document.querySelector('#desejos fieldset:not(:disabled)')"),'wishlist reloaded');
 let wish=await evaluate("fetch('/api/account').then(r=>r.json()).then(b=>b.wishlist.find(w=>w.edition_id==='g1-pt-base'))");assert(wish&&!wish.alert_p2p);assert.equal(await evaluate("JSON.parse(localStorage.getItem('boardradar-favorites')).length"),2);
 await fill('#desejos input[inputmode=decimal]','200,00');await evaluate("document.querySelector('#desejos .profile-consent input').click();document.querySelector('#desejos form').requestSubmit()");
 await waitFor(()=>evaluate("document.querySelector('#desejos').textContent.includes('Alertas ativados')"),'alert consent saved');
 await command('Page.navigate',{url:base+'/favoritos'});await waitFor(()=>evaluate("document.querySelector('#desejos .profile-consent input')?.checked && document.querySelector('#desejos input[inputmode=decimal]')?.value==='200'"),'existing alert and target loaded');
 // Create a genuinely approved matching listing to exercise a real internal notification.
 let candidate=(await post('/api/listings','create',{...draft,title:'Aviso interno R6'},seller.cookie)).payload;
 let notificationRow=candidate.listings.find(r=>r.id===candidate.created_id);
 const upload=await fetch(base+`/api/listing-images?listing_id=${notificationRow.id}&revision=${notificationRow.revision}`,{method:'POST',headers:{Origin:base,Cookie:seller.cookie,'Content-Type':'image/png'},body:original});assert.equal(upload.status,200);notificationRow=(await upload.json()).listings.find(r=>r.id===notificationRow.id);
 notificationRow=(await post('/api/listings','submit',{id:notificationRow.id,revision:notificationRow.revision,terms_accepted:true,terms_version:'local-mvp-2026-10-20-v1'},seller.cookie)).payload.listings.find(r=>r.id===notificationRow.id);
 await post('/api/listings','approve',{id:notificationRow.id,revision:notificationRow.revision,reason:'Notificacao de teste',edition_confirmed:true},moderator.cookie);
 await command('Page.navigate',{url:base+'/minha-conta?sec=avisos'});await waitFor(()=>evaluate("!!document.querySelector('.account-journey a[href^=\"/anuncios/\"]')"),'real notification link');
 await evaluate("[...document.querySelectorAll('.account-journey button')].find(b=>b.textContent==='Marcar avisos como lidos').click()");await waitFor(()=>evaluate("document.querySelector('.account-journey').textContent.includes('Lido')"),'notification read');
 await command('Page.navigate',{url:base+'/favoritos'});await waitFor(()=>evaluate("!!document.querySelector('#desejos fieldset:not(:disabled)')"),'cancel wishlist');
 await evaluate("[...document.querySelectorAll('#desejos button')].find(b=>b.textContent==='Remover / cancelar').click()");await waitFor(()=>evaluate("document.querySelector('#desejos').textContent.includes('Nenhuma edi')"),'wishlist removed');
 assert.equal(await evaluate("fetch('/api/account').then(r=>r.json()).then(b=>b.wishlist.length)"),0);
 await command('Page.navigate',{url:base+'/minha-conta?sec=seguranca'});await waitFor(()=>evaluate("[...document.querySelectorAll('.account-panel button')].some(b=>b.textContent==='Sair da conta')"),'security section');await evaluate("[...document.querySelectorAll('.account-panel button')].find(b=>b.textContent==='Sair da conta').click()");await waitFor(()=>evaluate("!!document.querySelector('a[href^=\"/entrar?next=\"]')"),'logout guest state');
 assert.equal(await evaluate("fetch('/api/account').then(r=>r.status)"),401);assert.equal(await evaluate("JSON.parse(localStorage.getItem('boardradar-favorites')).length"),2);
 await command('Page.navigate',{url:base+'/entrar?next=%2Fvender'});await waitFor(()=>evaluate("!!document.querySelector('.access-page input[name=email]')"),'sign-in form');await fill('.access-page input[name=email]','buyer-r6@audit.local');await fill('.access-page input[name=password]','audit-test-password');await evaluate("document.querySelector('.access-page form').requestSubmit()");await waitFor(()=>evaluate("location.pathname==='/vender' && !!document.querySelector('.sell-panel')"),'login continues to sell without profile');
 assert.equal(await evaluate("fetch('/api/account').then(r=>r.json()).then(b=>b.profile)"),null);
 // Restore the original owner fixture count expected by the legacy regression below.
 await post('/api/listings','remove',{id:notificationRow.id},seller.cookie);
 // Owner dialog: cancel by Escape and then confirm a real removal.
 await command('Network.setCookie',{name:'boardradar-session',value:seller.cookie.split('=')[1],url:base,httpOnly:true,sameSite:'Strict'});await command('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});await command('Page.navigate',{url:base+'/anuncios'});
 await waitFor(()=>evaluate("document.querySelectorAll('.account-game').length===4"),'owner drafts');
 await evaluate("const b=[...document.querySelectorAll('.account-game button')].find(b=>b.textContent==='Remover');b.focus();b.click()");await waitFor(()=>evaluate("!!document.querySelector('dialog[open]')"),'confirmation opened');
 assert.equal(await evaluate("document.activeElement.textContent"),'Cancelar');
 await command('Input.dispatchKeyEvent',{type:'keyDown',key:'Escape',code:'Escape',windowsVirtualKeyCode:27});await command('Input.dispatchKeyEvent',{type:'keyUp',key:'Escape',code:'Escape',windowsVirtualKeyCode:27});
 await waitFor(()=>evaluate("!document.querySelector('dialog[open]')"),'confirmation cancelled');assert.equal(await evaluate("document.activeElement.textContent"),'Remover');
 await evaluate("document.activeElement.click()");await waitFor(()=>evaluate("!!document.querySelector('dialog[open]')"),'confirmation reopened');
 await command('Page.captureScreenshot',{format:'png',captureBeyondViewport:false}).then(r=>writeFileSync('docs/redesign/r6/captures/confirmation-390.png',Buffer.from(r.data,'base64')));
 await evaluate("[...document.querySelectorAll('dialog[open] button')].find(b=>b.textContent==='Remover an\u00fancio').click()");await waitFor(()=>evaluate("[...document.querySelectorAll('.account-game .eyebrow')].some(e=>e.textContent==='Removido')"),'removal persisted');
 await command('Network.deleteCookies',{name:'boardradar-session',url:base});await command('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});await command('Page.navigate',{url:base});await waitFor(()=>evaluate("!!document.querySelector('.chat-launcher')"),'chat');await evaluate("document.querySelector('.mobile-radar').focus();document.querySelector('.mobile-radar').click()");await sleep(150);
 const chat=await evaluate("({dialog_role:document.querySelector('.chat-panel').getAttribute('role'),aria_modal:document.querySelector('.chat-panel').getAttribute('aria-modal'),focused_input:document.activeElement===document.querySelector('.chat-input input')})");
 await command('Page.captureScreenshot',{format:'png',captureBeyondViewport:false}).then(r=>writeFileSync('docs/redesign/r6/captures/chat-390.png',Buffer.from(r.data,'base64')));

 await evaluate("document.querySelector('[aria-label=\"Expandir chat\"]').click()");await waitFor(()=>evaluate("document.querySelector('.chat-panel')?.getAttribute('aria-modal')==='true'"),'expanded semantics');
 await evaluate("[...document.querySelectorAll('.chat-panel button,.chat-panel a[href],.chat-panel input')].filter(e=>e.getClientRects().length).at(-1).focus()");await command('Input.dispatchKeyEvent',{type:'keyDown',key:'Tab',code:'Tab',windowsVirtualKeyCode:9});await command('Input.dispatchKeyEvent',{type:'keyUp',key:'Tab',code:'Tab',windowsVirtualKeyCode:9});assert(await evaluate("document.querySelector('.chat-panel').contains(document.activeElement)"));
 await command('Input.dispatchKeyEvent',{type:'keyDown',key:'Escape',code:'Escape',windowsVirtualKeyCode:27});await command('Input.dispatchKeyEvent',{type:'keyUp',key:'Escape',code:'Escape',windowsVirtualKeyCode:27});await waitFor(()=>evaluate("document.querySelector('.chat-panel')?.getAttribute('role')==='region'"),'chat reduced');
 await send('O que e deck-building?');await evaluate("document.querySelector('.site-footer a[href=\"/marketplace\"]').click()");await waitFor(()=>evaluate("document.querySelector('main h1')?.textContent==='Marketplace de jogos'"),'client navigation');assert(await evaluate("document.querySelector('.chat-messages')?.textContent.toLowerCase().includes('deck-building')"));
 await evaluate("document.querySelector('[aria-label=\"Fechar assistente\"]').click()");await waitFor(()=>evaluate("!document.querySelector('.chat-panel')"),'chat closed');
 await evaluate("document.querySelector('.mobile-navigation>button').click()");assert.equal(await evaluate("document.activeElement.id"),'site-search-input');
 await evaluate("localStorage.removeItem('boardradar-favorites')");await command('Input.insertText',{text:'Catan'});await evaluate("document.querySelector('.site-search').requestSubmit()");await waitFor(()=>evaluate("location.pathname==='/buscar' && location.search==='?q=Catan' && !!document.querySelector('.catalog-count')"),'global search reached catalog');
 await evaluate("document.querySelector('.favorite').click()");await waitFor(()=>evaluate("JSON.parse(localStorage.getItem('boardradar-favorites')||'[]').includes('g1')"),'local favorite saved');await evaluate("document.querySelector('.mobile-navigation a[href*=favoritos]').click()");await waitFor(()=>evaluate("location.pathname==='/favoritos' && !!document.querySelector('.local-favorites')"),'favorites destination');await evaluate("document.querySelector('.local-favorites a').click()");await waitFor(()=>evaluate("location.pathname==='/jogos' && location.search==='?favoritos=1' && document.querySelectorAll('.game-card').length===1"),'guest favorites retained');
 assert.equal(await evaluate("document.querySelectorAll('.game-card').length"),1);
 assert(matrix.every(r=>r.header_count===1&&r.footer_count===1&&r.search_count===1),'Shared shell must be unique on every page');
 assert.equal(matrix.filter(r=>r.overflow).length,0,'Document overflow');assert.deepEqual(errors,[]);
 const summary={date:'2026-10-20',behavior_checks:['registration and optional onboarding','profile save and delete','explicit local favorites transfer','preserved alert form state','real notification and read state','wishlist cancellation and logout','wizard save and resume','photo upload','review consent and moderation','public detail projection','private and inactive listing 404','global search','guest favorites','owner confirmation and Escape','chat focus and expansion','chat retained across client navigation','unique shared shell'],purpose:'R6 account access, optional profile, separate favorites, consent, notifications and responsive regression',fixtures:'Isolated test accounts, listings and photos; no real user data',widths:[360,390,768,1024,1440],matrix,chat,js_errors:errors};
 writeFileSync('docs/redesign/r6/browser-baseline.json',JSON.stringify(summary,null,2)+'\n');
 console.log(JSON.stringify({scenarios:matrix.length,overflow:matrix.filter(x=>x.overflow).map(x=>({page:x.page,width:x.width})),unnamed:matrix.filter(x=>x.unnamed_controls.length).map(x=>({page:x.page,width:x.width,count:x.unnamed_controls.length})),js_errors:errors}));
}finally{
 if(ws?.readyState===1){await command('Browser.close',{},null).catch(()=>{});ws.close()}
 chrome?.kill();
 if(server.connected){server.send('shutdown');await Promise.race([new Promise(r=>server.once('exit',r)),sleep(3000)])}if(server.exitCode===null)server.kill();
 for(const p of pending.values()){clearTimeout(p.timer);p.fail(Error('Browser encerrado'))}
}
