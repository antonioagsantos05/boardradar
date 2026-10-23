import PublicListingDetail from '@/components/PublicListingDetail';
export const metadata={title:'Anúncio da comunidade | BoardRadar'};
export default async function ListingPage({params}:{params:Promise<{id:string}>}){return <PublicListingDetail id={(await params).id}/>}
