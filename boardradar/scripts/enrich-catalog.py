"""Apply original overview notes after publisher research; preserve edition caveats."""
import json
from pathlib import Path
import re
import unicodedata

DATA=Path(__file__).resolve().parents[1]/'src/data'
SUMMARIES='''
Construa estradas, povoados e cidades em uma ilha, negociando recursos com os outros participantes. O jogo-base tem sua própria configuração; expansões para mais pessoas são produtos separados.
Colecione cartas de trem para conectar cidades e completar bilhetes de destino em um mapa ferroviário da América do Norte. Os outros mapas da série têm configurações próprias.
Monte uma paisagem com peças de cidades, estradas e campos e posicione seus seguidores para pontuar. O conteúdo incluído varia entre edições.
Escolha azulejos de uma oferta compartilhada e organize padrões em seu painel. O planejamento considera tanto as peças desejadas quanto as que você não conseguirá aproveitar.
Interprete ilustrações e crie pistas para que os demais encontrem sua carta. A descrição da editora atual contempla uma edição para até oito pessoas; confira a caixa da sua versão.
Duas equipes tentam identificar suas palavras usando pistas dadas por seus líderes. A seleção de palavras e a comunicação são o centro da experiência.
Desenvolva uma civilização escolhendo cartas e passando as restantes aos vizinhos. As escolhas ocorrem simultaneamente ao longo de três eras.
Administre uma guilda de mercadores, reunindo gemas e adquirindo cartas de desenvolvimento que facilitam compras posteriores.
Trabalhe em equipe para conter doenças no mapa e pesquisar suas curas. Cada personagem oferece habilidades diferentes para o planejamento coletivo.
Encontre rapidamente o símbolo em comum entre cartas. O produto oferece variantes de partidas centradas em observação e reflexos.
Combine cores ou números para esvaziar a mão em um jogo de cartas familiar. Cartas especiais e composição do baralho dependem da versão adquirida.
Blefe sobre os personagens que você controla e desafie as declarações dos adversários para preservar sua influência.
Escolha uma carta de comida e passe a mão adiante, tentando reunir combinações que rendam pontos. Não confundir com o produto maior Sushi Go Party!.
Selecione dominós de terreno e organize um pequeno reino, conectando áreas e aproveitando as coroas para pontuar.
Use informações limitadas e os efeitos de personagens para proteger sua carta e descobrir as dos adversários. Existem edições com quantidades diferentes de jogadores.
Lidere uma corporação em projetos para transformar Marte, desenvolvendo produção e disputando espaço no planeta. Expansões e versões independentes não são o mesmo produto.
Reúna aves em habitats que ativam combinações de ações em seu painel. O foco está na construção de um motor de cartas com tema de observação de aves.
Planeje um zoológico moderno, construa recintos e apoie projetos de conservação. A gestão de ações e de cartas organiza o desenvolvimento do parque.
Desenvolva uma fazenda, distribua trabalhadores e planeje a alimentação de sua família. A edição original e a revisada têm configurações diferentes de participantes.
Administre uma economia de produção e exportação escolhendo papéis e desenvolvendo construções. A edição Puerto Rico 1897 tem apresentação própria e exige conferência da caixa.
Desenvolva indústrias e redes de transporte na região de Birmingham. O planejamento econômico considera recursos, conexões e oportunidades compartilhadas.
Combine construção de baralho com alocação de trabalhadores em uma disputa política ambientada em Duna. Dune: Imperium e Uprising são produtos distintos.
Dispute o desenvolvimento de uma civilização em um confronto exclusivo para duas pessoas, com caminhos de progresso científico, militar e civil.
Construa uma cidade de animais da floresta combinando cartas e enviando trabalhadores para obter recursos ao longo das estações.
Organize uma vinícola na Toscana, distribuindo trabalhadores entre atividades de cultivo, produção e atendimento de pedidos. Essential Edition e expansões devem ser identificadas separadamente.
Desenvolva um domínio medieval usando dados para escolher ações e posicionar peças. A Special Edition pesquisada tem conteúdo próprio; não presuma equivalência com todas as caixas anteriores.
Conduza gado por uma rota até Kansas City, melhorando suas possibilidades econômicas no caminho. A segunda edição e os títulos Argentina e Nova Zelândia são produtos distintos.
Desenvolva a economia de sua facção em uma Europa alternativa, combinando expansão territorial, produção e presença militar.
Construa habitats e distribua animais para formar padrões de pontuação. A seleção de peças e marcadores cria um quebra-cabeça espacial ligado à natureza.
Explore uma ilha combinando construção de baralho, alocação de trabalhadores e gestão de recursos. As escolhas de exploração e pesquisa disputam suas ações disponíveis.
Participe de uma campanha de fantasia com combate tático e decisões sobre cartas de ação. A editora mantém materiais separados para as diferentes edições.
Uma campanha independente no universo de Gloomhaven, com cenários apresentados em livro e uma introdução gradual à experiência de combate tático.
Controle espíritos com poderes diferentes e coopere para defender uma ilha contra invasores. O desenvolvimento das habilidades sustenta o planejamento coletivo.
Enfrente uma infestação de zumbis em missões cooperativas. Zombicide é uma família de produtos: cenário, personagens e regras variam conforme a caixa.
Sobreviva em uma nave infestada, administrando perigos e objetivos que podem entrar em conflito com os interesses dos demais tripulantes. É uma proposta semicooperativa.
Complete missões em equipe em um jogo de cartas de vazas com limitações de comunicação. O desafio muda conforme a missão escolhida.
Investigue um mistério em equipe interpretando cartas de visão fornecidas pelo fantasma. O grupo precisa relacionar as pistas às opções da investigação.
Coopere para enfrentar monstros clássicos, com desafios específicos para cada criatura. Esta pesquisa trata do produto Universal Monsters, não de todas as versões Horrified.
Sobreviva como parte de um grupo de náufragos, organizando abrigo, exploração e recursos em uma ilha perigosa.
Explore Terrinoth em uma campanha cooperativa de fantasia conduzida por aplicativo. Não é uma expansão de Descent: Journeys in the Dark.
Investigue mistérios de horror em uma campanha cooperativa de cartas. O conjunto inicial, as expansões e as edições revisadas precisam ser identificados separadamente.
Explore uma mansão que se transforma durante a partida e descubra um cenário de horror. A terceira edição possui seu próprio conjunto de cenários e materiais.
Conduza uma facção espacial em uma grande disputa de impérios, envolvendo política, economia e conflitos. O foco desta entrada é a quarta edição.
Explore o espaço e desenvolva sua civilização em uma disputa 4X. Second Dawn for the Galaxy é a versão pesquisada, distinta da edição de 2011.
Dispute o controle de uma floresta com facções de funcionamento diferente. O jogo-base é anunciado para duas a quatro pessoas; modos com autômatos dependem de conteúdo adicional.
Dispute territórios em um mapa de conquista global usando exércitos e dados. As diversas versões de Risk devem ser conferidas antes de comparar produtos.
Conquiste regiões combinando povos de fantasia e poderes especiais em um mundo com pouco espaço para todos.
Lidere um clã viking rumo ao Ragnarök em uma disputa de glória e confrontos. Expansões e variantes não são automaticamente parte da caixa-base.
Lidere uma tribo em um cenário de inspiração celta e dispute condições de vitória ligadas à presença e à liderança na ilha.
Comande deuses e exércitos em um Egito mitológico, adquirindo poderes e disputando posições no tabuleiro.
Desenvolva uma civilização por meio de cartas, administrando população, produção, tecnologia, cultura e poder militar ao longo das eras.
Explore e desenvolva uma civilização, construindo cidades e ampliando seu alcance. A pesquisa trata da Monumental Edition.
Recrie a disputa entre Império e Aliança Rebelde com objetivos e recursos diferentes para os lados em conflito.
Monte um baralho e enfrente adversários em um jogo de cartas colecionáveis de Star Wars. Os formatos e os produtos iniciais precisam ser identificados separadamente.
Assuma o papel de heróis Marvel em confrontos cooperativos de cartas contra vilões. Cada cenário e conjunto de herói adiciona possibilidades próprias.
Forme uma sociedade de aventureiros em campanhas cooperativas na Terra-média com apoio de aplicativo.
Viva aventuras cooperativas com baralhos de personagens e cenários da Terra-média. O conjunto revisado e os ciclos de expansão não são equivalentes entre si.
Dispute o controle de Arrakis no conflito entre Atreides e Harkonnen. Há materiais específicos para diferentes modos e conteúdos adicionais.
Viaje pelo mundo de The Witcher como caçador de monstros, cumprindo missões, enfrentando criaturas e desenvolvendo seu baralho.
Monte um baralho de Pokémon e participe de batalhas de cartas. Esta entrada trata do jogo físico; Pokémon TCG Pocket e as adaptações digitais são produtos diferentes.
Desenvolva seu baralho durante a partida, comprando cartas de ação, tesouro e vitória. A seleção de cartas disponíveis muda as combinações entre partidas.
Controle sua velocidade e o aquecimento do carro por meio da gestão da mão em corridas de automobilismo. O jogo-base inclui seis carros.
Dispute um quebra-cabeça para duas pessoas, comprando e posicionando retalhos em um tabuleiro de colcha e administrando botões e tempo.
Escolha dados e organize um vitral, respeitando as restrições de posicionamento e buscando objetivos de pontuação.
Explore a masmorra de um dragão enquanto desenvolve seu baralho e decide até onde arriscar antes de escapar com seus tesouros.
Use um pequeno conjunto de artefatos mágicos para transformar recursos e conquistar locais de poder. É um jogo de combinações e eficiência de cartas.
Monte uma colcha com peças de cores e padrões para atender objetivos e atrair gatos. A organização espacial das peças cria o desafio central.
Reúna combinações de cartas com ilustrações de origami e decida o momento de encerrar a rodada, equilibrando pontuação e risco.
'''.strip().splitlines()

NEW=[
('Dominion','Cartas / deck-building',2,4,30,2,['cartas','estratégia','deck-building']),
('Heat: Pedal to the Metal','Corrida / gestão de mão',1,6,60,2,['corrida','cartas','estratégia']),
('Patchwork','Abstrato / para dois',2,2,30,2,['abstrato','peças','estratégia']),
('Sagrada','Abstrato / dados',1,4,45,2,['abstrato','dados','estratégia']),
('Clank! A Deck-Building Adventure','Aventura / deck-building',2,4,60,3,['aventura','exploração','cartas','deck-building']),
('Res Arcana','Fantasia / construção de motor',2,4,45,3,['fantasia','cartas','gestão']),
('Calico','Abstrato / colocação de peças',1,4,45,2,['natureza','peças','abstrato']),
('Sea Salt & Paper','Cartas / coleção',2,4,30,1,['cartas','coleção','família'])]


def main():
    path=DATA/'games.json';games=json.loads(path.read_text(encoding='utf-8-sig'))
    research={r['game_id']:r for r in json.loads((DATA/'game-research.json').read_text(encoding='utf-8'))}
    for i,(name,category,minimum,maximum,duration,complexity,tags) in enumerate(NEW,61):
        gid=f'g{i}'
        if any(g['id']==gid for g in games):continue
        slug=re.sub('[^a-z0-9]+','-',unicodedata.normalize('NFKD',name).encode('ascii','ignore').decode().lower()).strip('-')
        games.append({'id':gid,'slug':slug,'name':name,'aliases':[],'category':category,'players':{'min':minimum,'max':maximum},
                      'duration':duration,'complexity':complexity,'tags':tags,'description':'','color':'#348577','editorialQuality':.5,
                      'provenance':{'source':'Pesquisa de visão geral em fonte da editora; complexidade editorial; edição comercial a confirmar','status':'pending_verification'},
                      'editions':[{'id':gid+'-pt-base','name':'Jogo-base — identificação de demonstração','language':'a confirmar','type':'base'}]})
    for i,g in enumerate(games):
        g['description']=SUMMARIES[i];g['research']=research[g['id']]
    aliases={'g22':['Duna Imperium','Duna: Imperium','Duna:Imperium','Dune Imperium'],
             'g35':['Nêmesis'],'g62':['Heat'],'g65':['Clank','Clank!']}
    for g in games:g['aliases']=list(dict.fromkeys([*g['aliases'],*aliases.get(g['id'],[])]))
    path.write_text(json.dumps(games,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'{len(games)} games with overview notes and publisher references; no new commercial offers.')


if __name__=='__main__':main()
