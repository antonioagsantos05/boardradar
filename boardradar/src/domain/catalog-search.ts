import {z} from 'zod';
export const catalogSearchSchema=z.object({
 q:z.string().max(200).default(''),
 favoritos:z.literal('1').optional(),
 ids:z.string().max(20000).optional(),
 source:z.enum(['all','editorial','imported']).default('all'),
 players:z.coerce.number().int().min(1).max(20).optional(),
 duration:z.coerce.number().positive().max(10000).optional(),
 kind:z.enum(['all','boardgame','boardgameexpansion','unclassified']).default('all'),
 sort:z.enum(['rank','name','year','duration']).default('rank'),
 page:z.coerce.number().int().min(1).max(20000).default(1),
 page_size:z.coerce.number().refine(n=>[12,24,48,96].includes(n)).default(24),
});
export type CatalogSearch=z.infer<typeof catalogSearchSchema>;
