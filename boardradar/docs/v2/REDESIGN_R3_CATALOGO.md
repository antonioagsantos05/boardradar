# R3 — Catálogo, busca e filtros

Entregue em 20/10/2026.

## Navegação e apresentação

`/jogos` apresenta o catálogo unificado e `/buscar` recebe a busca do cabeçalho. As duas páginas usam `CatalogBrowser`, com cards compartilhados, filtros ativos removíveis, limpar filtros, contagem, ordenação por nome/ano/duração e páginas de 12, 24, 48 ou 96 registros. Desktop usa sidebar; mobile usa diálogo de filtros com cancelamento por Escape e retorno do foco. Estado fica na URL, com suporte a voltar, avançar e acesso direto.

A origem pode ser todas, seleção editorial ou base importada. Busca textual consulta nomes, aliases, categorias, mecânicas e tags existentes. Jogadores, duração máxima e formato são aplicados ao conjunto completo antes da paginação. Ano/duração ausentes ficam no final das respectivas ordenações.

Não há filtro geral por preço, disponibilidade, complexidade ou afinidade: a cobertura da base importada não permite tratá-los como completos. A Home mantém suas ferramentas editoriais antigas por compatibilidade. Os filtros ausentes não são substituídos por valores presumidos.

## Identidades e dados

Nova API local `GET /api/catalog` usa o snapshot existente no servidor e os vínculos `curated_game_id`. Registros vinculados aparecem uma vez, com ID e slug editoriais canônicos e BGG ID preservado. Não há deduplicação por semelhança de título. Registros distintos ou sem vínculo explícito permanecem distintos. A consulta atual reúne 10.709 identidades, incluindo registros cujo formato pode ser expansão ou não informado.

Cards importados mantêm categorias da origem, identificação BGG, dados conhecidos de jogadores/duração e capa gráfica explicitamente ilustrativa. Mostram “Sem preço verificado”; não recebem ofertas simuladas de outro jogo. Cards editoriais continuam usando ofertas DEMO elegíveis da edição padrão. Os detalhes e APIs anteriores não foram removidos.

## Favoritos

Cards das duas origens podem ser salvos neste navegador. Visitantes acessam `/jogos?favoritos=1`; os IDs locais são enviados à consulta para filtrar antes da paginação. Não entram na URL compartilhável e não representam wishlist de conta. Pessoas autenticadas continuam acessando a wishlist por edição em `/conta#desejos`. A integração entre esses dois recursos pertence à R6.

## Arquivos principais

- `src/components/CatalogBrowser.tsx`, `ImportedGameCard.tsx` e componentes existentes `GameCard`/`Pagination`.
- `src/server/catalog-search.ts`, `src/domain/catalog-search.ts` e `src/app/api/catalog/route.ts`.
- `src/app/jogos/page.tsx`, `src/app/buscar/page.tsx` e `src/styles/catalog.css`.
- Cabeçalho/rodapé apontam ao novo catálogo; busca global aponta a `/buscar`. URLs antigas da Home continuam válidas.

## Validação e limites

Build de produção com TypeScript; 23 testes TypeScript; script `scripts/check-redesign-r3.mjs` com banco isolado, testes da API e 55 cenários responsivos em 360, 390, 768, 1024 e 1440 px. Verifica identidade editorial, combinação de filtros antes de paginar, formatos, ordenação, vazio, parâmetros inválidos, limite de página, histórico do navegador, painel mobile, favoritos, busca global, diálogo de confirmação e preservação da conversa do Radar.

Matriz e capturas em `docs/redesign/r3`. Nenhuma alteração no Python, banco de contas ou snapshots. Não há certificação de acessibilidade ou medição de desempenho nesta fase. A próxima entrega é a R4: página central do jogo e decisão de compra.
