import test from 'node:test';
import assert from 'node:assert/strict';
import {personalizedGames} from '../src/domain/personalized-games';
import {franchises,rawGames} from '../src/repositories/poc';
import {displayText} from '../src/domain/presentation';
const profile={experience:'',styles:[],videogames:[],references:'',budget:null,consent:true};
test('Franchise choices rank existing games by thematic overlap',()=>{for(const name of ['Alien','Duna']){const f=franchises.find(f=>f.nome===name)!;const result=personalizedGames({...profile,videogames:[f.id]});assert.ok(result.length>0);for(const item of result){const g=rawGames.find(g=>g.game_id===item.game.curated_game_id)!;assert.ok([...g.temas,...g.experiencias].some(t=>[...f.temas,...f.experiencias].includes(t)));assert.ok(item.reason)}}});
test('Combat recommendations match catalog experience and have no duplicates',()=>{const result=personalizedGames({...profile,styles:['combate']});assert.ok(result.length>0);assert.equal(new Set(result.map(g=>g.game.id)).size,result.length);for(const item of result){const raw=rawGames.find(g=>g.game_id===item.game.curated_game_id)!;assert.ok([...raw.temas,...raw.experiencias].includes('combate'))}});
test('No personalization without consent or preferences',()=>{assert.deepEqual(personalizedGames({...profile,styles:['combate'],consent:false}),[]);assert.deepEqual(personalizedGames(profile),[])});
test('Presentation removes example title suffix and boilerplate',()=>{assert.equal(displayText('[DEMO] Pandemic — anúncio de exemplo'),'Pandemic');assert.equal(displayText('ANÚNCIO FICTÍCIO DE DEMONSTRAÇÃO. Não representa um item.'),'');assert.equal(displayText('Caixa em bom estado'),'Caixa em bom estado')});

test('Each franchise match names the selected franchise and explains shared tags',()=>{const f=franchises.find(f=>f.nome==='Alien')!;const result=personalizedGames({...profile,styles:['combate'],videogames:[f.id]});const matches=result.filter(g=>g.franchise);assert.ok(matches.length>0);for(const item of matches){assert.equal(item.franchise,'Alien');assert.equal(item.reason,'Porque você gosta de Alien');assert.ok(item.explanation.startsWith('Em comum: '));assert.ok(!item.explanation.includes('_'))}});
