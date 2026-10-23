'use client';
import Link from 'next/link';
import {useAppShell} from './layout/AppShell';
export default function RadarPage(){
 const {registerRadarHost}=useAppShell();
 return <main className="container radar-page"><div className="radar-page-heading"><div><span className="eyebrow dark">SEU RADAR DE DESCOBERTAS</span><h1>Vamos encontrar a próxima partida?</h1><p>Conte o que gosta e refine por jogadores, tempo ou orçamento. Compare jogos e confira as fontes e edições.</p></div><Link className="button light" href="/jogos">Explorar catálogo</Link></div><div className="radar-page-layout"><aside className="radar-guide"><h2>Uma conversa, muitos caminhos</h2><p><strong>Descubra.</strong> Comece pelo nome de um jogo, categoria ou mecânica.</p><p><strong>Compare.</strong> Peça diferenças entre dois jogos ou consulte uma mecânica.</p><p><strong>Escolha.</strong> Abra a ficha e confira edição, fontes dos dados e anúncios da comunidade.</p><p className="radar-session-note">A conversa fica nesta sessão da página, inclusive ao alternar para a janela. Recarregar ou recomeçar limpa o histórico. Ela não é um histórico salvo na conta.</p></aside><div id="radar-page-host" ref={registerRadarHost}/></div></main>;
}
