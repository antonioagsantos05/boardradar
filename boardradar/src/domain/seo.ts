export function siteSettings(value=process.env.BOARDRADAR_SITE_URL){
 const origin=new URL(value||'http://127.0.0.1:3000');
 if(!['http:','https:'].includes(origin.protocol)||origin.username||origin.password||origin.pathname!=='/'||origin.search||origin.hash)throw Error('BOARDRADAR_SITE_URL deve conter somente a origem HTTP/HTTPS do site.');
 const canIndex=Boolean(value)&&origin.protocol==='https:'&&!['localhost','127.0.0.1','[::1]'].includes(origin.hostname);
 return {origin,canIndex};
}
export const privateRobots={index:false,follow:false};
export function seoDescription(text:string){return text.replace(/<[^>]*>/g,' ').replace(/\s+/g,' ').trim().slice(0,160)}
