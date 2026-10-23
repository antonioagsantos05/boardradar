import { writeFileSync } from 'node:fs';
const rows=`Catan|Família / estratégia|3|4|90|2|estratégia,negociação,construção
Ticket to Ride|Família / rotas|2|5|60|2|família,rotas,estratégia
Carcassonne|Colocação de peças|2|5|45|2|família,construção,peças
Azul|Abstrato / estratégia|2|4|45|2|família,abstrato,estratégia
Dixit|Criatividade / festa|3|6|30|1|festa,criatividade,cartas
Codenames|Palavras / festa|2|8|15|1|festa,dedução,palavras
7 Wonders|Civilizações|3|7|30|2|civilizações,cartas,estratégia
Splendor|Desenvolvimento econômico|2|4|30|2|economia,coleção,estratégia
Pandemic|Cooperativo|2|4|45|2|cooperativo,gestão,estratégia
Dobble (Spot It!)|Reflexos / festa|2|8|15|1|festa,família,reflexos
UNO|Cartas / família|2|10|30|1|cartas,família
Coup|Blefe|2|6|15|1|blefe,cartas,dedução
Sushi Go!|Cartas / família|2|5|15|1|cartas,família,coleção
Kingdomino|Colocação de peças|2|4|15|1|construção,família,peças
Love Letter|Dedução / cartas|2|6|20|1|dedução,cartas
Terraforming Mars|Estratégia / ficção científica|1|5|120|3|ficção científica,construção,gestão,estratégia
Wingspan|Construção de motor|1|5|70|2|natureza,coleção,construção
Ark Nova|Estratégia / animais|1|4|150|4|natureza,gestão,construção,coleção
Agricola|Gestão de recursos|1|4|120|3|gestão,construção,estratégia
Puerto Rico|Estratégia econômica|3|5|150|3|economia,gestão,história
Brass: Birmingham|Economia / indústria|2|4|120|4|economia,gestão,história
Dune: Imperium|Estratégia / deck-building|1|4|120|3|ficção científica,cartas,estratégia
7 Wonders Duel|Estratégia para dois|2|2|30|2|civilizações,estratégia,cartas
Everdell|Construção de cidade|1|4|80|3|construção,natureza,gestão
Viticulture|Gestão / vinicultura|1|6|90|3|gestão,construção,economia
The Castles of Burgundy|Estratégia / dados|2|4|90|3|construção,dados,história
Great Western Trail|Estratégia / logística|1|4|150|4|gestão,economia,estratégia
Scythe|Estratégia / território|1|5|115|3|território,gestão,estratégia
Cascadia|Natureza / peças|1|4|45|2|natureza,peças,família
Lost Ruins of Arnak|Exploração / deck-building|1|4|120|3|exploração,aventura,cartas
Gloomhaven|Fantasia / combate tático|1|4|120|4|fantasia,tático,cooperativo,combate
Gloomhaven: Jaws of the Lion|Fantasia / cooperativo|1|4|120|3|fantasia,tático,cooperativo,combate
Spirit Island|Cooperativo / estratégia|1|4|120|4|cooperativo,estratégia,fantasia
Zombicide|Zumbis / combate|1|6|60|2|terror,sobrevivência,combate,cooperativo
Nemesis|Terror / sobrevivência|1|5|180|4|terror,sobrevivência,ficção científica
The Crew: The Quest for Planet Nine|Cooperativo / cartas|2|5|20|2|cooperativo,cartas,ficção científica
Mysterium|Dedução / mistério|2|7|42|2|dedução,cooperativo,terror
Horrified|Terror / cooperativo|1|5|60|2|terror,cooperativo,sobrevivência
Robinson Crusoe: Adventures on the Cursed Island|Sobrevivência|1|4|120|4|sobrevivência,exploração,cooperativo
Descent: Legends of the Dark|Fantasia / aventura|1|4|180|3|fantasia,aventura,tático,cooperativo
Arkham Horror: The Card Game|Terror / investigação|1|4|120|3|terror,cartas,cooperativo,dedução
Betrayal at House on the Hill|Terror / exploração|3|6|60|2|terror,exploração,sobrevivência
Twilight Imperium: Fourth Edition|4X / ficção científica|3|6|480|5|4X,ficção científica,estratégia,exploração
Eclipse: Second Dawn for the Galaxy|4X / exploração espacial|2|6|120|4|4X,ficção científica,exploração,combate
Root|Controle de área / assimetria|2|4|90|4|território,estratégia,combate
Risk|Conquista / guerra|2|6|120|2|guerra,território,estratégia
Small World|Controle de território|2|5|80|2|fantasia,território,estratégia
Blood Rage|Guerra / mitologia|2|4|90|3|guerra,fantasia,combate
Inis|Controle de área / mitologia|2|4|90|3|território,fantasia,estratégia
Kemet: Blood and Sand|Guerra / mitologia|2|5|120|3|guerra,fantasia,combate
Through the Ages: A New Story of Civilization|Civilizações|2|4|240|4|civilizações,gestão,estratégia
Clash of Cultures: Monumental Edition|Civilizações / 4X|2|4|240|4|civilizações,4X,exploração,construção
Star Wars: Rebellion|Estratégia / Star Wars|2|4|240|4|ficção científica,guerra,estratégia
Star Wars: Unlimited|Cartas colecionáveis|2|2|20|2|ficção científica,cartas,coleção,combate
Marvel Champions: The Card Game|Super-heróis / cooperativo|1|4|90|3|cooperativo,cartas,combate
The Lord of the Rings: Journeys in Middle-earth|Fantasia / aventura|1|5|120|3|fantasia,aventura,exploração,cooperativo
The Lord of the Rings: The Card Game|Fantasia / cartas|1|4|90|3|fantasia,cartas,cooperativo
Dune: War for Arrakis|Guerra / ficção científica|1|4|120|4|guerra,ficção científica,estratégia
The Witcher: Old World|Fantasia / exploração|1|5|150|3|fantasia,exploração,aventura,combate
Pokémon Trading Card Game|Cartas colecionáveis|2|2|20|2|coleção,cartas,combate`;
const colors=['#cf7733','#237f85','#6e7b41','#366d9e','#9d5471','#6c587f'];
const games=rows.split('\n').map((row,i)=>{const [name,category,min,max,duration,complexity,tags]=row.split('|');const id='g'+(i+1);const slug=name.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/-$/,'');return {id,slug,name,aliases:i===9?['Dobble','Spot It']:[],category,players:{min:+min,max:+max},duration:+duration,complexity:+complexity,tags:tags.split(','),description:`Explore ${category.toLowerCase()} em ${name}. Uma seleção para quem gosta de ${tags.split(',').slice(0,3).join(', ')}. Consulte as regras da edição antes de escolher sua próxima partida.`,color:colors[i%colors.length],editorialQuality:0.8,provenance:{source:'Lista fornecida pelo cliente; metadados preliminares editoriais',status:'pending_verification'},editions:[{id:id+'-pt-base',name:i===53?'Spark of Rebellion — Two-Player Starter':i===59?'Battle Academy — caixa de demonstração':i===40?'Revised Core Set':i===56?'Revised Core Set':'Jogo-base — edição de demonstração',language:'pt-BR (a confirmar)',type:'base'}]}});
const refs=[['The Witcher','The Witcher 3: Wild Hunt','fantasia,exploração,aventura','g59,g56,g40'],['Resident Evil','Resident Evil 4','terror,sobrevivência,combate','g34,g35,g38'],['Age of Empires','Age of Empires II','civilizações,estratégia,construção','g52,g51,g7'],['Pokémon','Pokémon Scarlet / Violet','coleção,combate,natureza','g60,g17,g18'],['Civilization','Civilization VI','civilizações,gestão,estratégia','g51,g52,g23'],['The Sims','The Sims 4','construção,gestão,economia','g24,g19,g25'],['Diablo','Diablo IV','fantasia,combate,tático','g31,g32,g40'],['Minecraft','Minecraft','construção,exploração,sobrevivência','g14,g3,g39'],["Assassin’s Creed","Assassin’s Creed II",'histoire,exploração,aventura','g30,g26,g20'],['The Legend of Zelda','Breath of the Wild','aventura,exploração,fantasia','g30,g56,g59'],['Mass Effect','Mass Effect','ficção científica,exploração,combate','g53,g44,g43'],["No Man’s Sky","No Man’s Sky",'ficção científica,exploração,construção','g44,g43,g16'],['XCOM','XCOM 2','tático,combate,gestão','g31,g32,g33']];
const videogames=refs.map((r,i)=>({id:'v'+(i+1),franchise:r[0],title:r[1],tags:r[2].replace('histoire','história').split(',')}));
const relations=refs.flatMap((r,i)=>r[3].split(',').map((game_id,j)=>({videogame_id:'v'+(i+1),game_id,weight:1-j*.15,rationale:`Para quem gosta de ${r[1]}: afinidade editorial com ${r[2].replace('histoire','história').split(',').slice(0,2).join(' e ')}. A experiência e as regras são diferentes do videogame.`,review_status:'editorial_draft'})));
const stores=['Meeple Aurora','Dados & Destinos','Órbita Lúdica','Toca do Tabuleiro','Carta na Mesa','Reino dos Dados','Estação Meeple','Planeta da Jogada','Ponto de Vitória','Guilda Lúdica'].map((name,i)=>({id:'s'+(i+1),name,is_demo:true}));
const offers=games.filter((_,i)=>i!==58).flatMap((g,i)=>Array.from({length:4},(_,j)=>({id:`o${i+1}-${j}`,edition_id:g.editions[0].id,store_id:stores[(i+j*3)%10].id,price_cents:Math.round((i<15?6990+i*830:18990+i*1310)*(1+j*.07)),currency:'BRL',condition:j===1?'PIX':'À vista',availability:j===3?'out_of_stock':'in_stock',checked_at:j===2?'2026-09-01T12:00:00Z':'2026-10-15T12:00:00Z',is_demo:true})));
const history=offers.flatMap(o=>Array.from({length:61},(_,d)=>({offer_id:o.id,observed_at:new Date(Date.UTC(2026,7,16+d)).toISOString(),price_cents:Math.round(o.price_cents*(1+Math.sin(d*.12)*.09+(60-d)*.001)),data_origin:'synthetic',is_demo:true})));
for(const [file,data] of Object.entries({'games':games,'videogames':videogames,'game-relations':relations,'stores':stores,'offers':offers,'price-history':history}))writeFileSync('src/data/'+file+'.json',JSON.stringify(data,null,2)+'\n');
console.log(`${games.length} jogos, ${videogames.length} videogames, ${stores.length} lojas, ${offers.length} ofertas. Metadados aguardam verificação.`);
