import {franchises,rawGames,libraryGames,themes as themeLabels,experiences as experienceLabels} from '@/repositories/poc';
import type {RadarProfile} from './profile-storage';
const norm=(s:string)=>s.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/[_-]/g,' ');
const label=(tag:string)=>[...themeLabels,...experienceLabels].find(t=>norm(t.id)===tag)?.nome||tag;
export function personalizedGames(profile:RadarProfile){
 if(!profile.consent)return [];
 const selected=franchises.filter(f=>profile.videogames.includes(f.id));
 const styles=new Set(profile.styles.map(norm));
 const themes=new Set(selected.flatMap(f=>f.temas).map(norm));
 const experiences=new Set(selected.flatMap(f=>f.experiencias).map(norm));
 return rawGames.map((g,index)=>{
  const gameThemes=new Set(g.temas.map(norm));const gameExperiences=new Set(g.experiencias.map(norm));
  const matchedStyles=[...styles].filter(t=>gameExperiences.has(t)||gameThemes.has(t));
  const matchedThemes=[...themes].filter(t=>gameThemes.has(t));const matchedExperiences=[...experiences].filter(t=>gameExperiences.has(t));
  const score=matchedStyles.length*4+matchedThemes.length*3+matchedExperiences.length;
  const matches=selected.map(f=>{const sharedThemes=f.temas.map(norm).filter(t=>gameThemes.has(t));const sharedExperiences=f.experiencias.map(norm).filter(t=>gameExperiences.has(t));return {name:f.nome,tags:[...new Set([...sharedThemes,...sharedExperiences])],weight:sharedThemes.length*3+sharedExperiences.length}}).filter(f=>f.weight>0).sort((a,b)=>b.weight-a.weight);
  const best=matches[0];
  const reason=best?'Porque você gosta de '+best.name:'Seu estilo: '+matchedStyles.map(label).join(', ');
  const explanation=best?'Em comum: '+best.tags.slice(0,3).map(label).join(' · '):'Este jogo combina com os estilos que você escolheu.';
  return {game:libraryGames[index],score,reason,explanation,franchise:best?.name??null};
 }).filter(g=>g.score>0).sort((a,b)=>b.score-a.score).slice(0,8);
}
