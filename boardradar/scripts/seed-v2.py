"""Own editorial seed; no scraped or licensed third-party manual text."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'src' / 'data'


def read(name):
    return json.loads((DATA / (name + '.json')).read_text(encoding='utf-8-sig'))


def write(name, value):
    (DATA / (name + '.json')).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


provenance = {'source': 'Curadoria editorial original BoardRadar', 'license': 'project-owned', 'retrieved_at': '2026-10-19', 'review_status': 'editorial_draft'}
media = [{'id': 'media-' + v['id'], 'title': v['title'], 'aliases': [v['franchise']], 'type': 'videogame', 'year': None, 'tags': v['tags'], 'provenance': provenance} for v in read('videogames')]
relations = [{'media_id': 'media-' + r['videogame_id'], **{k:v for k,v in r.items() if k != 'videogame_id'}, 'connection_type': 'thematic_and_mechanical'} for r in read('game-relations')]
extra = [
    ('dune-film', 'Duna', ['Dune', 'filme Duna'], 'film', ['ficção científica','estratégia','território'], ['g22','g58','g16']),
    ('lotr-film', 'O Senhor dos Anéis', ['Senhor dos Aneis', 'Lord of the Rings', 'LOTR'], 'film', ['fantasia','aventura','cooperativo'], ['g56','g57','g32']),
    ('alien-film', 'Alien', ['Alien: O Oitavo Passageiro'], 'film', ['terror','sobrevivência','ficção científica'], ['g35','g38','g34']),
    ('starwars-film', 'Star Wars', ['Guerra nas Estrelas'], 'film', ['ficção científica','guerra','combate'], ['g53','g54','g44']),
    ('stranger-series', 'Stranger Things', [], 'series', ['terror','dedução','cooperativo'], ['g37','g38','g41']),
    ('thrones-series', 'Game of Thrones', ['Guerra dos Tronos'], 'series', ['fantasia','território','estratégia'], ['g45','g49','g48']),
    ('lastofus-series', 'The Last of Us', ['TLOU'], 'series', ['sobrevivência','terror','cooperativo'], ['g34','g35','g39']),
    ('witcher-series', 'The Witcher (série)', ['serie The Witcher', 'serie do bruxo'], 'series', ['fantasia','exploração','combate'], ['g59','g40','g32']),
]
for key,title,aliases,kind,tags,game_ids in extra:
    mid = 'media-' + key
    media.append({'id':mid,'title':title,'aliases':aliases,'type':kind,'year':None,'tags':tags,'provenance':provenance})
    for i,gid in enumerate(game_ids):
        relations.append({'media_id':mid,'game_id':gid,'weight':round(1-i*.15,2),'rationale':f'Afinidade editorial com {title}: {", ".join(tags[:2])}. A conexão é temática; não implica adaptação oficial nem equivalência de gameplay.','review_status':'editorial_draft','connection_type':'thematic'})
write('media-works',media)
write('media-game-relations',relations)
# policy.json is versioned application configuration, never overwritten by data seeding.
sources = [{'id':'radar-editorial-2','title':'Guia editorial BoardRadar 2.0','game_id':None,'edition_id':None,'license':'project-owned','permission':'owned','url':None,'retrieved_at':'2026-10-19','version':'2.0','type':'editorial','review_status':'reviewed','authority':'editorial'}]
topics = [
    ('demo','Ofertas e demonstração','Na POC, todas as lojas, ofertas e séries de preços são simuladas. Frete não incluído. O botão de oferta não permite compra nem abre loja real.'),
    ('deckbuilding','Conceito: deck-building','Deck-building é uma mecânica em que o conjunto de cartas do jogador é desenvolvido durante a partida. Não é sinônimo de jogo de cartas colecionáveis, cuja montagem do baralho pode ocorrer antes de jogar.'),
    ('coop','Conceito: cooperativo','Em jogos cooperativos, os jogadores normalmente compartilham um objetivo de equipe. A descrição exata de vitória, derrota e ações permitidas depende do manual e da edição.'),
    ('4x','Conceito: 4X','4X é uma classificação editorial ligada a explorar, expandir, explorar recursos e enfrentar adversários. Jogos podem dar pesos diferentes a cada aspecto; a etiqueta não garante a mesma experiência de um videogame.'),
    ('complexity','Como interpretar complexidade','A escala de complexidade usada no catálogo é uma estimativa editorial preliminar de 1 a 5. Ela não mede inteligência, experiência permanente do usuário ou qualidade do jogo.'),
    ('editions','Edições e expansões','Jogo-base, expansão e edição comercial têm identificações distintas. A comparação comercial utiliza o mesmo identificador de edição. Idioma, conteúdo e compatibilidade precisam de conferência antes de qualquer oferta real.'),
    ('dna','DNA de entretenimento','Conectar filmes, séries e videogames a board games é uma analogia editorial de temas, atmosfera e mecânicas. Não significa que o jogo seja uma adaptação oficial da obra nem que reproduza sua experiência.'),
    ('manual','Regras e fontes','Uma resposta sobre ação permitida deve identificar jogo e edição e recuperar material autorizado dessa edição. Sem manual ou FAQ pertinente, o Radar deve explicar a limitação e não inventar regras ou páginas.'),
]
chunks = [{'id':'chunk-'+key,'source_id':'radar-editorial-2','game_id':None,'edition_id':None,'section':title,'page':None,'text':body} for key,title,body in topics]
write('knowledge-sources',sources)
write('knowledge-chunks',chunks)
print(f'V2: {len(media)} obras, {len(relations)} relações, {len(chunks)} trechos editoriais. Nenhum manual oficial incluído.')
