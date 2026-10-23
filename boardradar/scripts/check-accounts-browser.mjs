import { spawn } from 'node:child_process';
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
import assert from 'node:assert/strict';

const chromePath=process.env.CHROME_EXECUTABLE||'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
assert(existsSync(chromePath),'Chrome não encontrado para validação visual.');
mkdirSync('.qa',{recursive:true});
const server=spawn(process.execPath,['scripts/run.mjs','--port','3101'],{windowsHide:true,stdio:['ignore','pipe','pipe','ipc'],env:{...process.env,RADAR_ACCOUNT_DB:resolve('.qa/account-browser.sqlite3')}});
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
 await evaluate("document.querySelector('.account-game button').click()");await set('.account-columns .account-form input[maxlength="120"]','Jogo editado');await evaluate("document.querySelector('.account-columns .account-form').requestSubmit()");
 await waitFor(()=>evaluate("document.querySelector('.account-game h3')?.textContent==='Jogo editado' && !document.querySelector('fieldset').disabled"),'edited');
 await command('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});
 assert(await evaluate("document.documentElement.scrollWidth<=window.innerWidth"));
 await command('Page.captureScreenshot',{format:'png',captureBeyondViewport:true}).then(r=>writeFileSync('.qa/account-mobile.png',Buffer.from(r.data,'base64')));
 const csrf=await fetch('http://127.0.0.1:3101/api/account',{method:'POST',headers:{'Content-Type':'application/json',Origin:'https://example.invalid'},body:JSON.stringify({action:'logout'})});assert.equal(csrf.status,403);
 await evaluate("[...document.querySelectorAll('.account-top button')].find(b=>b.textContent==='Sair').click()");
 await waitFor(()=>evaluate("!!document.querySelector('input[type=password]') && !document.querySelector('fieldset').disabled"),'logout');
 await set('input[type=email]',email);await set('input[type=password]','test-password-123');await evaluate("document.querySelector('.account-form').requestSubmit()");
 await waitFor(()=>evaluate("document.querySelectorAll('.account-game').length===1 && !document.querySelector('fieldset').disabled"),'login retains game');
 assert.deepEqual(errors,[]);console.log('Account browser passed: registration, HttpOnly session, create/edit, reload persistence, logout/login, CSRF and mobile.');
}finally{
 if(ws?.readyState===1){await command('Browser.close',{},null).catch(()=>{});ws.close()}
 chrome?.kill();
 if(server.connected){server.send('shutdown');await Promise.race([new Promise(r=>server.once('exit',r)),sleep(3000)])}if(server.exitCode===null)server.kill();
 for(const p of pending.values()){clearTimeout(p.timer);p.fail(Error('Browser encerrado'))}
}
