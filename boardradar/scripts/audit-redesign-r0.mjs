import { spawn,spawnSync } from 'node:child_process';
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
import assert from 'node:assert/strict';
import sharp from 'sharp';

const chromePath=process.env.CHROME_EXECUTABLE||'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
assert(existsSync(chromePath),'Chrome não encontrado para validação visual.');
mkdirSync('.qa',{recursive:true});
mkdirSync('docs/redesign/r0/captures',{recursive:true});
const dbPath=resolve('.qa/user-flows-'+Date.now()+'.sqlite3');
const server=spawn(process.execPath,['scripts/run.mjs','--port','3102'],{windowsHide:true,stdio:['ignore','pipe','pipe','ipc'],env:{...process.env,RADAR_ACCOUNT_DB:dbPath}});
let serverLog='';server.stdout.on('data',d=>serverLog+=d);server.stderr.on('data',d=>serverLog+=d);
let chrome,ws;let nextId=1;const pending=new Map();let session;const errors=[];
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
async function waitFor(fn,label,timeout=20000){const end=Date.now()+timeout;while(Date.now()<end){try{const value=await fn();if(value)return value}catch{}await sleep(150)}throw Error('Timeout: '+label)}
function command(method,params={},sessionId=session){return new Promise((ok,fail)=>{const id=nextId++;const timer=setTimeout(()=>{pending.delete(id);fail(Error('CDP timeout: '+method))},10000);pending.set(id,{ok,fail,timer});ws.send(JSON.stringify({id,method,params,...sessionId?{sessionId}:{}}))})}
async function evaluate(expression){const data=await command('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});if(data.exceptionDetails)throw Error(data.exceptionDetails.text);return data.result.value}
async function send(text){const before=await evaluate("document.querySelectorAll('.message.assistant:not(.thinking)').length");await evaluate("document.querySelector('.chat-input input').focus()");await command('Input.insertText',{text});await evaluate("document.querySelector('.chat-input button').click()");await waitFor(()=>evaluate(`document.querySelectorAll('.message.assistant:not(.thinking)').length > ${before} && !document.querySelector('.thinking')`),'resposta do assistente');assert.equal(await evaluate("document.querySelector('.chat-error')?.textContent||''"),'')}

try{
 await waitFor(async()=>{try{return(await fetch('http://127.0.0.1:3102')).ok}catch{return false}},'servidor: '+serverLog,30000);
 chrome=spawn(chromePath,['--headless=new','--remote-debugging-port=0','--no-first-run','--no-default-browser-check','--disable-extensions',`--user-data-dir=${resolve('.qa/r0-chrome-profile')}`,'about:blank'],{windowsHide:true,stdio:['ignore','ignore','pipe']});
 let chromeLog='';chrome.stderr.on('data',d=>chromeLog+=d);const endpoint=await waitFor(()=>chromeLog.match(/DevTools listening on (ws:\/\/[^\s]+)/)?.[1],'Chrome DevTools');
 ws=new WebSocket(endpoint);await new Promise((ok,fail)=>{ws.addEventListener('open',ok,{once:true});ws.addEventListener('error',fail,{once:true})});
 ws.addEventListener('message',event=>{const data=JSON.parse(event.data);if(data.id&&pending.has(data.id)){const p=pending.get(data.id);clearTimeout(p.timer);pending.delete(data.id);data.error?p.fail(Error(data.error.message)):p.ok(data.result)}if(data.method==='Runtime.exceptionThrown')errors.push(data.params.exceptionDetails.text)});
 const target=await command('Target.createTarget',{url:'about:blank'},null);const attached=await command('Target.attachToTarget',{targetId:target.targetId,flatten:true},null);session=attached.sessionId;
 await command('Runtime.enable');await command('Page.enable');await command('Emulation.setDeviceMetricsOverride',{width:1280,height:900,deviceScaleFactor:1,mobile:false});await command('Page.navigate',{url:'http://127.0.0.1:3102'});

 const base='http://127.0.0.1:3102';
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
  {id:'home',path:'/',cookie:'',ready:"document.querySelectorAll('.game-card').length>0 && document.querySelectorAll('.library-card').length>0"},
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
    return {width:innerWidth,scroll_width:document.documentElement.scrollWidth,overflow:document.documentElement.scrollWidth>innerWidth+1,overflow_elements:overflowing,h1_count:document.querySelectorAll('h1').length,unnamed_controls:unnamed,controls_below_24px:tiny,title:document.title,body_height:document.body.scrollHeight};
   })()`);
   matrix.push({page:item.id,...facts});
   if([390,1440].includes(width)&&['home','jogo','marketplace','conta','anuncios'].includes(item.id)){
    const capture='docs/redesign/r0/captures/'+item.id+'-'+width+'.png';
    await command('Page.captureScreenshot',{format:'png',captureBeyondViewport:false}).then(r=>writeFileSync(capture,Buffer.from(r.data,'base64')));
   }
  }
 }
 await command('Network.deleteCookies',{name:'boardradar-session',url:base});await command('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});await command('Page.navigate',{url:base});await waitFor(()=>evaluate("!!document.querySelector('.chat-launcher')"),'chat');await evaluate("document.querySelector('.chat-launcher').click()");await sleep(150);
 const chat=await evaluate("({dialog_role:document.querySelector('.chat-panel').getAttribute('role'),aria_modal:document.querySelector('.chat-panel').getAttribute('aria-modal'),focused_input:document.activeElement===document.querySelector('.chat-input input')})");
 await command('Page.captureScreenshot',{format:'png',captureBeyondViewport:false}).then(r=>writeFileSync('docs/redesign/r0/captures/chat-390.png',Buffer.from(r.data,'base64')));
 const summary={date:'2026-10-20',purpose:'Read-only frontend baseline before redesign R1',fixtures:'Isolated test accounts, listings and photos; no real user data',widths:[360,390,768,1024,1440],matrix,chat,js_errors:errors};
 writeFileSync('docs/redesign/r0/browser-baseline.json',JSON.stringify(summary,null,2)+'\n');
 console.log(JSON.stringify({scenarios:matrix.length,overflow:matrix.filter(x=>x.overflow).map(x=>({page:x.page,width:x.width})),unnamed:matrix.filter(x=>x.unnamed_controls.length).map(x=>({page:x.page,width:x.width,count:x.unnamed_controls.length})),js_errors:errors}));
}finally{
 if(ws?.readyState===1){await command('Browser.close',{},null).catch(()=>{});ws.close()}
 chrome?.kill();
 if(server.connected){server.send('shutdown');await Promise.race([new Promise(r=>server.once('exit',r)),sleep(3000)])}if(server.exitCode===null)server.kill();
 for(const p of pending.values()){clearTimeout(p.timer);p.fail(Error('Browser encerrado'))}
}
