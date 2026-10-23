import type {LibraryGame} from '@/domain/library';
export default function LibraryFacts({game:g}:{game:LibraryGame}){
 const facts=[['Ano',g.year],['Nota BGG · 2019',g.rating?.toFixed(2)+'/10'],['Jogadores',g.min_players+'–'+g.max_players],['Duração',g.max_minutes+' min'],['Complexidade',g.complexity+'/5'],['Categorias',g.categories.join(', ')],['Mecânicas',g.mechanics.join(', ')],['Autores',g.designers.join(', ')],['Editoras',g.publishers.join(', ')]];
 return <section className="detail-section library-facts"><h2>Informações do jogo</h2><p>Avaliações BGG com referência de setembro de 2019.</p><dl>{facts.map(([label,value])=><div key={label}><dt>{label}</dt><dd>{value??'Não informado'}</dd></div>)}</dl><a href={g.bgg_url} target="_blank" rel="noopener noreferrer">Referência no BoardGameGeek</a></section>;
}
