import type {MetadataRoute} from 'next';
import {siteSettings} from '@/domain/seo';
export default function robots():MetadataRoute.Robots{
 const {origin,canIndex}=siteSettings();
 return canIndex?{rules:{userAgent:'*',allow:'/',disallow:['/api/','/out/','/buscar','/conta','/minha-conta','/entrar','/cadastro','/onboarding','/favoritos','/anuncios','/meus-anuncios','/mensagens','/moderacao','/vender']},sitemap:new URL('/sitemap.xml',origin).href}:{rules:{userAgent:'*',disallow:'/'}};
}
