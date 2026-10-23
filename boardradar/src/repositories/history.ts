const history:{offer_id:string;price_cents:number;observed_at:string;data_origin:string;is_demo:boolean}[]=[];
export const historyRepository={all:()=>history,forOffer:(id:string)=>history.filter(h=>h.offer_id===id)};
