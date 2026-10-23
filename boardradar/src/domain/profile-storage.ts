export type RadarProfile={experience:string;styles:string[];videogames:string[];references:string;budget:number|null;consent:boolean};
const key=(id:string)=>'boardradar-profile:'+id;
export function readProfile(id:string):RadarProfile|null{try{const p=JSON.parse(localStorage.getItem(key(id))||'null');return p&&Array.isArray(p.styles)&&Array.isArray(p.videogames)?p:null}catch{return null}}
export function storeProfile(id:string,p:RadarProfile|null){try{if(p)localStorage.setItem(key(id),JSON.stringify(p));else localStorage.removeItem(key(id))}catch{}}
