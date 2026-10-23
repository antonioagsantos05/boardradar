import type { Metadata } from 'next';
import '../styles/tokens.css';
import './globals.css';
import '../styles/foundation.css';
import '../styles/layout.css';
import '../styles/home.css';
import '../styles/catalog.css';
import '../styles/product.css';
import '../styles/marketplace.css';
import '../styles/account.css';
import '../styles/radar.css';
import {siteSettings} from '@/domain/seo';
import '../styles/accessibility.css';
import '../styles/refinements.css';
import AppShell from '@/components/layout/AppShell';
export const metadata: Metadata = { metadataBase:siteSettings().origin,robots:{index:siteSettings().canIndex,follow:siteSettings().canIndex},title: 'BoardRadar — descubra seu próximo jogo', description: 'Descubra jogos de tabuleiro, compare ofertas e encontre sua próxima partida.' };
export default function RootLayout({children}:Readonly<{children:React.ReactNode}>){return <html lang="pt-BR"><body><AppShell>{children}</AppShell></body></html>}
