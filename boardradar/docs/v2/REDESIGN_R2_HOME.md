# R2 — Home como vitrine

A Home apresenta uma seleção inicial de oito jogos, categorias com os filtros existentes, afinidades com videogames, comparação de preços DEMO, uma prévia de até três anúncios ativos da comunidade e acesso direto ao Radar e à venda.

O botão “Explorar todos os jogos e filtros” expande a seleção completa e carrega a biblioteca importada. Busca e favoritos vindos do cabeçalho abrem essa apresentação automaticamente. A separação em rotas de catálogo e busca continua prevista na R3. Nenhum registro foi removido.

## Componentes

- `GameCard.tsx`: GameCard, GameCover, WishlistButton, GameMetadata e PriceDisplay. Capas locais identificadas como ilustrativas, informações existentes de jogadores/duração e preço elegível da edição padrão. Ausência de oferta recebe mensagem própria, sem preço inventado.
- `UserListingCard.tsx`: apresentação compartilhada do anúncio, com foto, conservação, edição, preço informado, entrega e ações existentes. A comunidade mantém carregamento, erro e vazio; somente o retorno público de ativos é apresentado.
- `CommunityListings.tsx`: opção de prévia sem paginação; marketplace e páginas de jogo mantêm os fluxos completos.
- `home.css`: estilos restritos à Home, com grades responsivas e redução de movimento.

Os favoritos dos cards continuam locais ao navegador, identificados nos controles. Não simulam sincronização com a wishlist da conta. A ordenação usa as recomendações reais recebidas da conta quando não há filtros explícitos; ações de sessão atualizam essa ordenação. Categorias e videogames usam o motor existente, sem inferência externa.

As oportunidades mostram os menores preços DEMO elegíveis da seleção atual, sem descontos, estoque ou avaliações inventadas. Anúncios da comunidade ficam em uma seção separada e não recebem preço DEMO.

## Validação

Build de produção com TypeScript e 20 testes das regras de catálogo/recomendação. O script `scripts/check-redesign-r2.mjs` usa banco isolado, contas e anúncios de teste, verifica nove telas/estados em cinco larguras, expansão da vitrine, acesso à biblioteca, busca global, favoritos, confirmação e conversa do Radar. Evidências em `docs/redesign/r2`.

O backend, contratos e dados não foram alterados. A unificação dos registros importados no grid e as URLs de filtros pertencem à R3; a ficha comercial completa pertence à R4. Não há certificação de acessibilidade ou medição de desempenho nesta entrega.
