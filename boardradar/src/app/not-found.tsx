import Link from 'next/link';
export default function NotFound(){return <main className="container empty-state" style={{marginTop:80}}><h1 style={{fontSize:40}}>Jogo não encontrado</h1><p>Esse jogo ainda não está no nosso radar.</p><Link className="button amber" href="/">Voltar ao catálogo</Link></main>}
