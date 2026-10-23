export function accountDestination(value:string|null){return value&&(['/','/jogos','/vender','/minha-conta','/favoritos','/meus-anuncios','/mensagens'].includes(value)||/^\/vender\?id=[A-Za-z0-9_-]+$/.test(value)||/^\/jogos\/[a-z0-9]+(?:-[a-z0-9]+)*(?:\?edition=[A-Za-z0-9_-]+)?$/.test(value))?value:'/minha-conta'}
export function targetPrice(value:string):number|null{
 const text=value.trim().replace(',','.');if(!text)return null;
 if(!/^\d+(\.\d{1,2})?$/.test(text))throw Error('Informe um preço-alvo com até duas casas decimais.');
 const [whole,fraction='']=text.split('.');const cents=Number(whole)*100+Number((fraction+'00').slice(0,2));
 if(!Number.isSafeInteger(cents)||cents<1||cents>100000000)throw Error('Preço-alvo fora do limite permitido.');
 return cents;
}
