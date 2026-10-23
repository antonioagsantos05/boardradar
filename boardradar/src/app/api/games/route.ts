import {catalogSearchSchema} from '@/domain/catalog-search';
import {searchCatalog} from '@/server/catalog-search';
export async function GET(request:Request){const parsed=catalogSearchSchema.safeParse(Object.fromEntries(new URL(request.url).searchParams));return parsed.success?Response.json({...searchCatalog(parsed.data),is_demo:true}):Response.json({error:'Filtros inválidos.'},{status:400})}
