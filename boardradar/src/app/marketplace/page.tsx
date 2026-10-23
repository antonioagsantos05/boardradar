export const metadata={alternates:{canonical:'/marketplace'},description:'Encontre ofertas de lojas e jogos à venda na comunidade BoardRadar.'};
import CommunityListings from '@/components/CommunityListings';
import PocOffers from '@/components/PocOffers';
export default function MarketplacePage(){return <main className="container account-page"><h1>Marketplace</h1><p>Encontre jogos em lojas e anúncios da comunidade.</p><CommunityListings/><PocOffers/></main>}
