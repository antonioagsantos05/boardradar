# Catálogo ampliado e integração dos arquivos BGG

Os dois ZIPs fornecidos pelo usuário foram lidos localmente, sem executar código dos repositórios. A aplicação preserva os 68 jogos selecionados, suas ofertas DEMO e as relações editoriais existentes, e oferece uma base ampliada de 10.682 IDs BGG distintos para pesquisa, consulta de fichas e comparação.

## Resultado da união

| Item | Quantidade |
| --- | ---: |
| Linhas no CSV fornecido | 10.532 |
| Fichas JSON do segundo arquivo | 246 |
| IDs presentes nas duas bases | 96 |
| IDs distintos após a união | 10.682 |
| Registros classificados como jogo pela API de origem | 185 |
| Expansões identificadas pela API de origem | 61 |
| Registros do CSV sem tipo de produto confirmado | 10.436 |
| Jogos selecionados associados por nome primário único | 41 |
| Divergências de campos registradas | 744 |

Essas quantidades representam registros dos snapshots, não 10.682 jogos-base verificados. Um mesmo título pode ter diferentes IDs, e o CSV não informa se todos os seus itens são jogos-base. Não foi feita pesquisa individual na internet para os 10.682 itens. As referências de pesquisa dos 68 jogos selecionados são uma camada separada de visão geral; não validam automaticamente números, regras ou edições do acervo importado.

## Identidade, campos e origem

A união entre as duas bases usa o ID numérico do BoardGameGeek. Títulos iguais com IDs diferentes continuam separados. Nos 96 IDs compartilhados, campos preenchidos do JSON têm prioridade sobre o CSV por oferecerem um registro mais estruturado. Campos ausentes no JSON preservam os valores disponíveis no CSV. Isso é uma política de importação, não uma afirmação de que o JSON contém sempre o dado mais recente ou mais correto.

Cada registro guarda `sources` e `field_sources`; todas as divergências ficam em [field-conflicts.json](catalog-import/field-conflicts.json). O [manifesto](../src/data/library-manifest.json) contém contagens, associação aos jogos selecionados, casos ambíguos e SHA-256 dos ZIPs de entrada. O conteúdo original permanece nos arquivos fornecidos pelo usuário.

As descrições e os nomes alternativos mantêm o idioma da origem. Entidades HTML são decodificadas como texto, sem renderizar HTML executável. Valores ausentes continuam ausentes: complexidade não informada não recebe uma estimativa inventada. Notas e complexidade BGG são identificadas como avaliações da comunidade, separadas da complexidade editorial do catálogo original.

A ligação entre registros importados e a seleção editorial considera somente o nome primário normalizado, com um único candidato e sem classificar uma expansão como jogo-base. Não usa aliases genéricos para ligar produtos diferentes. Por exemplo, o registro Heat de 2015 não foi associado a Heat: Pedal to the Metal. Coup e Love Letter apresentam múltiplos candidatos de nome primário e permanecem sem associação automática. A ligação por nome é uma referência de catálogo sujeita a revisão, não prova de equivalência entre edições comerciais.

O CSV tem nome de arquivo e README referindo 2023, mas o maior ano de lançamento observado nele é 2016. O maior ano de lançamento observado nas fichas JSON é 2021. Esses valores não comprovam as datas de coleta. A aplicação trata ambos como snapshots históricos, sem anunciar atualização atual de notas ou disponibilidade.

## Como usar na aplicação

A página inicial possui a seção **Base ampliada de jogos**, com 24 registros por página. A busca por nome, jogadores e duração consulta essa base; o seletor permite filtrar jogos identificados, expansões e itens cujo tipo ainda precisa ser confirmado. As páginas carregam apenas resumos dos resultados, não todo o arquivo de aproximadamente 26,5 MB no navegador.

As fichas importadas mostram descrição, ano, jogadores, duração, idade, autores, editoras, categorias, mecânicas e avaliações disponíveis. Não oferecem preço nem estoque. Quando um jogo selecionado tem associação BGG, sua ficha também mostra os dados externos em uma seção própria, mantendo a identificação de origem e o aviso sobre edição.

As fichas possuem **Comparar com outro jogo**, tanto para os jogos selecionados quanto para os registros importados. O comparador mostra jogadores, tempo, complexidade, categorias e etiquetas/mecânicas disponíveis. Identificadores e ano ajudam a distinguir títulos iguais. Dados não cadastrados, como curva de aprendizado medida, continuam indicados como desconhecidos. A API recusa comparar dois IDs que já tenham sido ligados ao mesmo jogo selecionado. A tabela compara atributos de jogos, sem somar preços ou equiparar produtos de edições diferentes.

O chat reconhece nomes exatos dos registros adicionais e apresenta fichas informativas, inclusive em comparações. Nomes importados ambíguos pedem identificação pela ficha. Os dados importados não são manuais oficiais e não fundamentam respostas sobre ações permitidas. A recomendação com pontuação, filtros editoriais e afinidades com videogames continua usando os jogos selecionados; o restante do acervo é uma base informativa pesquisável. Os filtros de orçamento e afinidade não são anunciados como aplicados aos itens importados sem ofertas ou curadoria.

Exemplos para conferir:

- `Fale sobre Die Macher` no chat, seguido de `Ofertas dele`: consulta informativa sem criar uma oferta.
- `Compare o Nemesis com o Duna Imperium`: mantém os dois jogos e não troca a consulta por uma analogia com o filme.
- `O que é deck-building?` seguido de `me fale outra mecanica`: resposta em texto corrido com continuidade de conceito.
- `O que é 4X?` seguido de `Isso significa que tem combate?`: esclarecimento conceitual, sem converter a pergunta em preferência de combate.
- Na ficha de Nemesis, selecionar Dune: Imperium em **Comparar com outro jogo**.

## Dados excluídos e limites

O importador usa somente o CSV de jogos e os arquivos `boardgames/boardgame-<id>.json`. Não incorpora históricos pessoais de partidas, vencedores, contas, planilhas, credenciais ou configurações AWS do repositório. Não há checkout ou sincronização comercial. Imagens ficam como referências na base, sem download ou exibição automática na interface.

As licenças declaradas para código nos repositórios não são interpretadas como licença dos textos ou imagens de terceiros. Os snapshots permanecem identificados como externos, sem serem publicados no índice de manuais autorizados ou reclassificados como conteúdo próprio. A integração é local; não houve publicação ou deploy por esta tarefa.

## Comandos reproduzíveis

A partir da pasta `boardradar`, para reconstruir a união com os arquivos fornecidos:

```powershell
..\.tools\python-3.13.7\python.exe scripts/import-boardgame-archives.py --csv-zip "C:\Users\antonio.agsantos\Downloads\bgg_dataset-main.zip" --api-zip "C:\Users\antonio.agsantos\Downloads\boardgames-api-main.zip"
```

O comando atualiza `library.json`, o manifesto, as associações BGG nos jogos selecionados e o relatório de divergências. Não gera preços nem altera os parâmetros de pontuação. As associações automáticas antigas são removidas antes de recalcular os candidatos, evitando conservar referências que deixem de existir no novo lote.

Para validar a integração:

```powershell
..\.tools\python-3.13.7\python.exe scripts/verify-catalog-import.py --browser
```

O verificador executa os casos de recuperação documental, dados, testes Python/TypeScript, tipos, build, HTTP e navegador. Logs, hashes e contagens reais ficam em [summary.json](catalog-import/summary.json); relatórios históricos das fases anteriores são preservados. Capturas locais ficam em `.qa/library-comparison-desktop.png` e `.qa/library-comparison-mobile.png`.

Para executar a aplicação após as alterações, use `npm start` na pasta `boardradar`. O build atualizado é preparado pela verificação. A fase 6 de avaliação de latência e preparação de hospedagem continua pendente.
