import Link from 'next/link';
import Brand from '@/components/Brand';
export default function Footer({authenticated=false}:{authenticated?:boolean}){return <footer className="site-footer"><div><Brand/><p>Encontre a próxima história para sua mesa.</p></div><nav aria-label="Links do rodapé"><Link href="/jogos">Explorar jogos</Link><Link href="/radar-ai">Radar</Link><Link href="/marketplace">Comunidade</Link><Link href="/vender">Vender um jogo</Link>{authenticated&&<Link href="/minha-conta">Minha conta</Link>}</nav><small>BoardRadar · Encontre sua próxima partida.</small></footer>}
