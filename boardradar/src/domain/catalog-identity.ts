import {resolveGame} from '@/repositories/poc';
export function canonicalCatalogId(id:string){return resolveGame(id)?.id||id}
