import {spawn} from 'node:child_process';
import {existsSync} from 'node:fs';
import {resolve} from 'node:path';
import {randomBytes} from 'node:crypto';
import {createInterface} from 'node:readline';
const localPython=resolve('..','.tools','python-3.13.7','python.exe');
const python=process.env.PYTHON_EXECUTABLE||(existsSync(localPython)?localPython:process.platform==='win32'?'python':'python3');
const token=randomBytes(32).toString('hex');
let web,exiting=false,started=false;
const service=spawn(python,['-u',resolve('chatbot/server.py')],{windowsHide:true,stdio:['ignore','pipe','inherit'],env:{...process.env,RADAR_CHAT_TOKEN:token,PYTHONUTF8:'1'}});
function stop(code=0){if(exiting)return;exiting=true;clearTimeout(timer);web?.kill();service.kill();if(process.connected)process.disconnect();process.exitCode=code}
function startWeb(port){
 if(started||exiting)return;if(!port&&process.env.RADAR_REQUIRE_PYTHON==='1'){console.error('Falha ao iniciar o backend Python.');stop(1);return}started=true;clearTimeout(timer);
 const mode=process.argv.includes('--dev')?'dev':'start';
 const portIndex=process.argv.indexOf('--port');const webPort=portIndex>=0?process.argv[portIndex+1]:process.env.PORT||'3000';
 const env={...process.env};delete env.RADAR_CHAT_URL;delete env.RADAR_CHAT_TOKEN;
 if(port){env.RADAR_CHAT_URL=`http://127.0.0.1:${port}`;env.RADAR_CHAT_TOKEN=token;console.log('Radar Python ativo.');}
 else console.log('Python indisponível. Catálogo e marketplace disponíveis; Radar temporariamente indisponível.');
 web=spawn(process.execPath,['node_modules/next/dist/bin/next',mode,'--hostname',process.env.RADAR_HOST||'127.0.0.1','--port',webPort],{windowsHide:true,stdio:'inherit',env});
 web.on('error',e=>{console.error(e.message);stop(1)});web.on('exit',code=>stop(code||0));
}
const timer=setTimeout(()=>{service.kill();startWeb()},15000);timer.unref();
process.on('SIGINT',()=>stop());process.on('SIGTERM',()=>stop());
process.on('message',message=>{if(message==='shutdown')stop()});
if(process.send)process.on('disconnect',()=>stop());
service.on('error',()=>startWeb());
service.on('exit',()=>{if(!exiting){if(!started)startWeb();else if(process.env.RADAR_REQUIRE_PYTHON==='1'){console.error('Backend Python encerrado. Reiniciando o serviço é necessário.');stop(1)}else console.error('Radar indisponível. Reinicie o serviço para restaurar conta e marketplace.')}});
const lines=createInterface({input:service.stdout});
lines.once('line',line=>{try{const ready=JSON.parse(line);if(!ready.ready||!Number.isInteger(ready.port))throw Error();startWeb(ready.port)}catch{service.kill();startWeb()}});
