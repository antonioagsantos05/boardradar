import { spawn } from 'node:child_process';
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
import assert from 'node:assert/strict';

const chromePath=process.env.CHROME_EXECUTABLE||'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
assert(existsSync(chromePath),'Chrome não encontrado para validação visual.');
mkdirSync('.qa',{recursive:true});
const server=spawn(process.execPath,['scripts/run.mjs','--port','3101'],{windowsHide:true,stdio:['ignore','pipe','pipe','ipc']});
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
 await send('Gosto de jogos de luta');
 const names=await evaluate("[...[...document.querySelectorAll('.message.assistant')].at(-1).querySelectorAll('.chat-recommendation strong')].map(x=>x.textContent)");
 const all=JSON.parse(readFileSync('src/data/games.json','utf8'));assert(names.length>0);assert(names.every(name=>all.find(g=>g.name===name)?.tags.includes('combate')));
 await send('2');assert((await evaluate("[...document.querySelectorAll('.message.assistant')].at(-1).textContent")).includes('2 pessoa'));
 await send('Sem limite de orçamento');
 await command('Page.captureScreenshot',{format:'png',captureBeyondViewport:false}).then(r=>writeFileSync('.qa/chat-desktop.png',Buffer.from(r.data,'base64')));
 await command('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});await sleep(300);
 const box=await evaluate("(()=>{const r=document.querySelector('.chat-panel').getBoundingClientRect();return {x:r.x,y:r.y,right:r.right,bottom:r.bottom}})()");assert(box.x>=0&&box.y>=0&&box.right<=390&&box.bottom<=844);
 await command('Page.captureScreenshot',{format:'png',captureBeyondViewport:false}).then(r=>writeFileSync('.qa/chat-mobile.png',Buffer.from(r.data,'base64')));
 await evaluate("document.querySelector('.chat-reset').click()");assert.equal(await evaluate("document.querySelectorAll('.message').length"),1);
 await send('Gosto de jogos de corrida');assert.equal(await evaluate("[...document.querySelectorAll('.message.assistant')].at(-1).querySelectorAll('.chat-recommendation').length"),0);
 await evaluate("document.querySelector('.chat-reset').click()");
 await send('Recomende Gloomhaven para 8 pessoas até R$ 1');assert.equal(await evaluate("[...document.querySelectorAll('.message.assistant')].at(-1).querySelectorAll('.chat-recommendation').length"),0);
 await send('Fale sobre Gloomhaven para 8 pessoas');assert.equal(await evaluate("[...document.querySelectorAll('.message.assistant')].at(-1).querySelectorAll('.chat-information').length"),1);assert((await evaluate("[...document.querySelectorAll('.message.assistant')].at(-1).textContent")).includes('Não atende'));
 await command('Page.captureScreenshot',{format:'png',captureBeyondViewport:false}).then(r=>writeFileSync('.qa/chat-phase2-information.png',Buffer.from(r.data,'base64')));
 await evaluate("document.querySelector('.chat-reset').click()");
 await send('Recomende Termforming Mars para quatro pessoas até R$ 1000');assert.equal(await evaluate("[...document.querySelectorAll('.message.assistant')].at(-1).querySelectorAll('.chat-recommendation').length"),0);assert((await evaluate("[...document.querySelectorAll('.message.assistant')].at(-1).textContent")).includes('Confirme'));
 await command('Page.captureScreenshot',{format:'png',captureBeyondViewport:false}).then(r=>writeFileSync('.qa/chat-phase3-clarification.png',Buffer.from(r.data,'base64')));
 const beforeConfirmation=await evaluate("document.querySelectorAll('.message.assistant:not(.thinking)').length");await evaluate("[...document.querySelectorAll('.chat-suggestions button')].find(b=>b.textContent==='Terraforming Mars').click()");await waitFor(()=>evaluate(`document.querySelectorAll('.message.assistant:not(.thinking)').length > ${beforeConfirmation} && !document.querySelector('.thinking')`),'confirmação de nome');
 assert.equal(await evaluate("[...document.querySelectorAll('.message.assistant')].at(-1).querySelector('.chat-recommendation strong')?.textContent"),'Terraforming Mars');
 await command('Page.captureScreenshot',{format:'png',captureBeyondViewport:false}).then(r=>writeFileSync('.qa/chat-phase3-confirmed.png',Buffer.from(r.data,'base64')));
 await evaluate("document.querySelector('.chat-reset').click()");await send('Tenho 200 reais e quero jogar com quatro pessoas da minha família');assert((await evaluate("[...document.querySelectorAll('.message.assistant')].at(-1).textContent")).includes('200'));
 await evaluate("document.querySelector('.chat-reset').click()");
 await send('Compare Root');await send('Scythe');
 assert.equal(await evaluate("[...document.querySelectorAll('.message.assistant')].at(-1).querySelectorAll('.chat-table tbody tr').length"),10);
 assert((await evaluate("[...document.querySelectorAll('.message.assistant')].at(-1).textContent")).includes('Não cadastrado'));
 assert(await evaluate("document.documentElement.scrollWidth<=window.innerWidth"));
 await command('Page.captureScreenshot',{format:'png',captureBeyondViewport:false}).then(r=>writeFileSync('.qa/chat-phase4-comparison-mobile.png',Buffer.from(r.data,'base64')));
 await send('edições deles');assert.equal(await evaluate("[...document.querySelectorAll('.message.assistant')].at(-1).querySelectorAll('.chat-tool').length"),2);
 await send('Ofertas g1-pt-base');assert((await evaluate("[...document.querySelectorAll('.message.assistant')].at(-1).textContent")).includes('sem frete'));
 await command('Page.captureScreenshot',{format:'png',captureBeyondViewport:false}).then(r=>writeFileSync('.qa/chat-phase4-offers-mobile.png',Buffer.from(r.data,'base64')));
 await evaluate("document.querySelector('.chat-reset').click()");await send('Gosto do filme Duna');
 assert(await evaluate("[...document.querySelectorAll('.message.assistant')].at(-1).querySelectorAll('.chat-editorial').length>0"));
 await command('Emulation.setDeviceMetricsOverride',{width:1280,height:900,deviceScaleFactor:1,mobile:false});
 await command('Page.captureScreenshot',{format:'png',captureBeyondViewport:false}).then(r=>writeFileSync('.qa/chat-phase4-media-desktop.png',Buffer.from(r.data,'base64')));
 await evaluate("document.querySelector('.chat-reset').click()");await send('O que é deck-building?');
 assert(await evaluate("[...document.querySelectorAll('.message.assistant')].at(-1).querySelectorAll('.chat-source').length>0"));
 await evaluate("[...document.querySelectorAll('.message.assistant')].at(-1).querySelector('.chat-source summary').click()");
 assert((await evaluate("[...document.querySelectorAll('.message.assistant')].at(-1).querySelector('.chat-source blockquote').textContent")).includes('Deck-building'));
 assert((await evaluate("[...document.querySelectorAll('.message.assistant')].at(-1).textContent")).includes('não é manual'));
 await command('Page.captureScreenshot',{format:'png',captureBeyondViewport:false}).then(r=>writeFileSync('.qa/chat-phase5-source-desktop.png',Buffer.from(r.data,'base64')));
 await command('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});await sleep(300);
 assert(await evaluate("document.documentElement.scrollWidth<=window.innerWidth"));
 await command('Page.captureScreenshot',{format:'png',captureBeyondViewport:false}).then(r=>writeFileSync('.qa/chat-phase5-source-mobile.png',Buffer.from(r.data,'base64')));
 await send('Posso atacar?');await send('Root');await send('g45-pt-base');
 assert((await evaluate("[...document.querySelectorAll('.message.assistant')].at(-1).textContent")).includes('evidência documental autorizada suficiente'));
 assert.equal(await evaluate("[...document.querySelectorAll('.message.assistant')].at(-1).querySelectorAll('.chat-source').length"),0);
 await command('Page.captureScreenshot',{format:'png',captureBeyondViewport:false}).then(r=>writeFileSync('.qa/chat-phase5-insufficient-mobile.png',Buffer.from(r.data,'base64')));
 await evaluate("document.querySelector('[aria-label=\"Fechar assistente\"]').click()");
 await command('Emulation.setDeviceMetricsOverride',{width:1280,height:900,deviceScaleFactor:1,mobile:false});
 await evaluate("document.querySelector('.filters input').scrollIntoView({block:'center'});document.querySelector('.filters input').focus()");await command('Input.insertText',{text:'Die Macher'});
 await waitFor(()=>evaluate("[...document.querySelectorAll('.library-card h3')].some(h=>h.textContent==='Die Macher')"),'busca da base ampliada');
 await evaluate("[...document.querySelectorAll('.library-card')].find(a=>a.querySelector('h3')?.textContent==='Die Macher').click()");
 await waitFor(()=>evaluate("!!document.querySelector('.library-facts') && !!document.querySelector('.game-comparison select option[value=\"g1\"]')"),'ficha externa e seletor');
 await evaluate("(()=>{const s=document.querySelector('.game-comparison select');s.value='g1';s.dispatchEvent(new Event('change',{bubbles:true}));document.querySelector('.game-comparison').scrollIntoView()})()");
 await waitFor(()=>evaluate("!!document.querySelector('.game-comparison table')"),'comparação com jogo importado');
 await evaluate("(()=>{const r=document.querySelector('.game-comparison').getBoundingClientRect();window.scrollTo({top:window.scrollY+r.top-100,behavior:'instant'})})()");
 await command('Page.captureScreenshot',{format:'png',captureBeyondViewport:false}).then(r=>writeFileSync('.qa/library-comparison-desktop.png',Buffer.from(r.data,'base64')));
 await command('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});await sleep(250);
 await evaluate("(()=>{const r=document.querySelector('.game-comparison').getBoundingClientRect();window.scrollTo({top:window.scrollY+r.top-90,behavior:'instant'})})()");
 assert(await evaluate("document.documentElement.scrollWidth<=window.innerWidth"));
 await command('Page.captureScreenshot',{format:'png',captureBeyondViewport:false}).then(r=>writeFileSync('.qa/library-comparison-mobile.png',Buffer.from(r.data,'base64')));
 await command('Page.navigate',{url:'http://127.0.0.1:3101/jogos/nemesis'});
 await waitFor(()=>evaluate("!!document.querySelector('.game-comparison select option[value=\"g22\"]')"),'comparar na ficha editorial');
 await evaluate("(()=>{const s=document.querySelector('.game-comparison select');s.value='g22';s.dispatchEvent(new Event('change',{bubbles:true}));document.querySelector('.game-comparison').scrollIntoView()})()");
 await waitFor(()=>evaluate("document.querySelector('.game-comparison table')?.textContent.includes('Dune: Imperium')"),'Nemesis e Dune na ficha');
 assert.deepEqual(errors,[]);console.log('Browser aprovado: regressões, base ampliada, fichas importadas e comparação entre catálogo editorial e BGG no desktop/mobile.');
}finally{
 if(ws?.readyState===1){await command('Browser.close',{},null).catch(()=>{});ws.close()}
 chrome?.kill();
 if(server.connected){server.send('shutdown');await Promise.race([new Promise(r=>server.once('exit',r)),sleep(3000)])}if(server.exitCode===null)server.kill();
 for(const p of pending.values()){clearTimeout(p.timer);p.fail(Error('Browser encerrado'))}
}
