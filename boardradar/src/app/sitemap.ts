import type {MetadataRoute} from 'next';
import {siteSettings} from '@/domain/seo';

export default function sitemap():MetadataRoute.Sitemap{
 const {origin,canIndex}=siteSettings();if(!canIndex)return [];
 return ['/','/jogos','/marketplace','/radar-ai'].map(path=>({url:new URL(path,origin).href}));
}
