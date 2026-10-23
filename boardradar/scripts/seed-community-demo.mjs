import sharp from 'sharp';
import {readFileSync,existsSync} from 'node:fs';
import {resolve} from 'node:path';
import {spawnSync} from 'node:child_process';
const games=JSON.parse(readFileSync('src/data/games.json','utf8'));
const names=['Catan','Azul','Dixit','Wingspan','Carcassonne','Ticket to Ride','Splendor','Pandemic'];
const colors=['#b77832','#327d8c','#7d597e','#647c48','#64817b','#a35538','#725d94','#3b7281'];
const rows=[];
for(let i=0;i<names.length;i++){
 const game=games.find(g=>g.name===names[i]);if(!game)throw Error('Game missing: '+names[i]);
 const escaped=game.name.replaceAll('&','&amp;').replaceAll('<','&lt;');
 // Code-native illustration, explicitly marked as a fixture, not a photograph of an item.
 const svg=`<svg xmlns="http://www.w3.org/2000/svg" width="960" height="720"><defs><linearGradient id="bg" x2="1" y2="1"><stop stop-color="#092e39"/><stop offset="1" stop-color="${colors[i]}"/></linearGradient></defs><rect width="960" height="720" fill="#e9ece1"/><ellipse cx="480" cy="590" rx="285" ry="42" fill="#082a3520"/><rect x="220" y="95" width="520" height="490" rx="20" fill="url(#bg)"/><rect x="240" y="115" width="480" height="450" rx="12" fill="none" stroke="#ffffff55"/><circle cx="480" cy="305" r="110" fill="none" stroke="#ffffff55" stroke-width="2"/><path d="M480 220L520 305L480 390L440 305Z" fill="#ffbe55"/><text x="480" y="160" text-anchor="middle" font-family="Arial,sans-serif" font-size="16" fill="#f4e2be" letter-spacing="3">BOARDRADAR · EXEMPLO</text><text x="480" y="475" text-anchor="middle" font-family="Arial,sans-serif" font-size="32" font-weight="700" fill="#fffdf8">${escaped}</text><text x="480" y="530" text-anchor="middle" font-family="Arial,sans-serif" font-size="16" fill="#e2e9df">IMAGEM ILUSTRATIVA · ITEM FICTÍCIO</text><rect x="296" y="627" width="368" height="42" rx="21" fill="#fffdf8"/><text x="480" y="654" text-anchor="middle" font-family="Arial,sans-serif" font-size="16" fill="#123e49">DEMONSTRAÇÃO · NÃO ESTÁ À VENDA</text></svg>`;
 const image=await sharp(Buffer.from(svg)).jpeg({quality:85}).toBuffer();
 rows.push({edition_id:game.editions[0].id,title:'[DEMO] '+game.name+' — anúncio de exemplo',price_cents:9000+i*2700,content:image.toString('base64')});
}
const bundled=resolve('..','.tools','python-3.13.7','python.exe');
const result=spawnSync(process.env.PYTHON_EXECUTABLE||(existsSync(bundled)?bundled:process.platform==='win32'?'python':'python3'),['scripts/seed-community-demo.py'],{input:JSON.stringify(rows),encoding:'utf8',windowsHide:true,env:{...process.env,PYTHONUTF8:'1'}});
if(result.status!==0)throw Error(result.stderr||result.error?.message||'Demo seed failed');
process.stdout.write(result.stdout);
