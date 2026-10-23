# R5 — Marketplace e venda em etapas

## Entrega

- `/vender`: jogo/edição e descrição → conservação, idioma, componentes e defeitos → preço, região e entrega → fotos → revisão e aceite.
- `/vender?id=...`: retoma um anúncio da própria conta, com fotos e versão salvas no banco.
- `/meus-anuncios`: gestão dos estados existentes, acesso à edição em etapas, fotos, moderação e solicitação de inclusão de jogo/edição.
- `/anuncios/[id]`: detalhe público com fotos, preço e dados declarados pelo vendedor, conversa protegida, wishlist e denúncia.
- Cards públicos agora ligam ao detalhe. Entradas de venda no cabeçalho, Home e comunidade apontam ao novo fluxo.

`/anuncios` continua disponível com o formulário anterior por compatibilidade. Gestão e fluxo novo reutilizam as mesmas contas, registros, upload e ações. Não há migração destrutiva de dados.

## Rascunho real e ordem das etapas

Preço e entrega vêm antes das fotos porque o contrato existente exige dados básicos válidos para criar o anúncio ao qual as fotos são anexadas. O fluxo não inventa preços temporários ou cria produtos incompletos para satisfazer essa exigência.

Antes de concluir preço/entrega, as alterações ficam no formulário e são identificadas como não salvas. Ao concluir essa etapa, `create`/`update` grava o rascunho no SQLite e a URL recebe o ID. Fotos são salvas pelo upload existente e podem ser retomadas. Não há promessa de autosave das primeiras etapas ou de recuperação de alterações ainda não enviadas.

O envio exige foto, entrega, dados válidos e aceite explícito da versão das regras. O backend continua validando a revisão e o estado. Editar dados/fotos invalida a publicação conforme o comportamento anterior. Conflitos informam a necessidade de recarregar. A foto em upload bloqueia o avanço/envio até a resposta.

## Contratos

`GET /api/listings?view=detail&id=...` encaminha à nova ação Python `public_detail`. Usa a mesma projeção permitida da vitrine, filtrada pelo ID antes de paginar. Só retorna registros que satisfazem os critérios públicos atuais: ativos, com aceite vigente e entrega informada. Desconhecidos, rascunhos, anúncios em revisão, reservados, pausados, vendidos e removidos não são revelados; o endpoint retorna 404 inclusive para o dono.

Não são expostos ID de vendedor, e-mail, notas privadas de revisão ou revisão interna. Não foi criado um apelido fictício para preencher a identificação pública do vendedor. Fotos mantêm autorização e visibilidade existentes. Contato e denúncias continuam nos contratos protegidos.

A resposta autenticada de `create` ganhou o campo aditivo `created_id`, para identificar o anúncio recém-criado sem depender da ordenação de títulos ou datas. A gestão anterior continua recebendo `listings` normalmente.

## Componentes e apresentação

`SellWizard`, `ListingsManager`, `PublicListingDetail` e `marketplace.css` organizam o frontend. `ListingPhotos` informa quando um envio/remoção está em andamento ao fluxo pai. `UserListingCard` permanece compartilhado entre vitrine e detalhe. Preços de usuários continuam separados das lojas DEMO.

O marketplace conserva busca por texto/jogo/região e paginação suportadas. Não foram apresentados filtros de conservação/preço/região estruturada sem suporte real. Não há checkout, pagamento, frete ou garantia integrada.

## Validação

Build de produção e TypeScript; 26 testes TypeScript e 332 testes Python. Os novos testes cobrem projeção pública, parâmetros, edição que invalida publicação e estados indisponíveis.

`scripts/check-redesign-r5.mjs` usa banco e arquivos de teste isolados. Verifica 75 cenários em 360, 390, 768, 1024 e 1440 px; fluxo real de criação, preço em centavos, upload, retomada de foto/rascunho, aceite, submissão, aprovação e indisponibilidade após pausa. Também verifica regressões de navegação, favoritos, confirmação e Radar. Matriz e capturas em `docs/redesign/r5`.

A ordem das etapas é uma adaptação explícita ao contrato existente. Nenhuma integração comercial ou autenticação externa foi ativada. A próxima fase é R6: conta, onboarding, wishlist e notificações.
