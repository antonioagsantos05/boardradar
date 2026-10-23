# R0 — diagnóstico do frontend e migração

Concluída em 20/10/2026. Esta entrega audita o produto existente; não aplica o design novo nem modifica funcionalidades, APIs ou dados de usuários.

## Base verificada

- 7 padrões de páginas: Home, jogo, marketplace, conta, anúncios, mensagens e moderação.
- 11 padrões de endpoints em `/api`, além da saída comercial bloqueada em `/out/[offerId]`.
- Catálogo editorial: 68 jogos, 13 videogames, 10 lojas, 236 ofertas e 14.396 observações sintéticas. Validação de dados passou, preservando o aviso de revisão editorial.
- Biblioteca adicional: consulta server-side paginada, identidade BGG e associação a jogos editoriais quando conhecida. Não equivale a catálogo comercial integralmente revisado.
- 20 testes TypeScript e 327 testes Python passaram. Build Next.js, incluindo TypeScript, passou. Não há script de lint configurado.
- 45 cenários de navegador: 9 páginas/estados × 360, 390, 768, 1024 e 1440 px. Sem overflow horizontal do documento ou exceção JavaScript nos cenários observados.

Evidências: [resumo de aceite](../redesign/r0/summary.json), [inventário](../redesign/r0/inventory.json), [matriz de navegador](../redesign/r0/browser-baseline.json), [testes](../redesign/r0/tests.log), [jornada com três contas](../redesign/r0/user-flows.log), [build](../redesign/r0/build.log), [dados](../redesign/r0/data-validation.log) e [capturas](../redesign/r0/captures/). Script reproduzível: `node scripts/audit-redesign-r0.mjs`. A jornada completa também passou novamente pelo script `scripts/check-user-flows-browser.mjs`.

A auditoria usa servidor próprio em 3102 e banco isolado em `.qa/`, com contas e anúncios fictícios identificados como teste. Não interfere na sessão de uso normal em 3000 nem atribui permissões no banco real.

## Diagnóstico com prioridades

| Prioridade | Constatação | Evidência / impacto | Tratamento |
|---|---|---|---|
| Alta | Busca e catálogo concentrados na Home | `BoardRadar.tsx`: preferências e busca locais; inexistem `/jogos` e `/buscar` | R1 navegação; R3 páginas dedicadas e estado na URL |
| Alta | Home extensa e com duas apresentações de catálogo | 20.593 px de documento a 390 px e 11.316 px a 1440 px, nesta amostra; cards de `BoardRadar` e `ImportedCatalog` diferentes | R2 Home com seleções limitadas; R3 catálogo completo com identidade canônica |
| Alta | Navegação muda de página para página | Header completo na Home, cabeçalhos reduzidos no jogo e barras locais em conta/marketplace | R1 layout e navegação compartilhados |
| Alta | Catálogo visual e identidade de dados precisam ser separados | 68 jogos editoriais e biblioteca importada com cobertura diferente; busca/atributos não têm o mesmo alcance | R3 adaptador tipado e comunicação de proveniência, sem inventar preços/categorias |
| Alta | Decisão comercial vem depois de conteúdo extenso na ficha | `GameDetail` apresenta referências, comparação e relações antes do bloco de ofertas; o CTA de âncora já existe | R4 colocar “Onde comprar” após resumo e seleção de edição; manter fontes e comparação acessíveis |
| Alta | Criar anúncio é um formulário longo ao lado da gestão | `/anuncios`: dados, fotos, revisão, solicitações e listagem na mesma página | R5 separar venda em etapas e gestão, mantendo rascunho e revisão no backend |
| Alta | Listagem de comunidade faz também o papel de detalhe | `CommunityListings` inclui descrição, defeitos, componentes e formulários em cada card; inexiste `/anuncios/[id]` | R5 cards resumidos e página pública de detalhe com contrato seguro |
| Média | Favoritos e wishlist são modelos distintos | Home usa IDs de jogos em localStorage; conta usa edições persistidas com alertas | R1 botão com contexto explícito; R6 migração consentida ou apresentação separada, sem perda silenciosa |
| Média | Tipografia auxiliar e alvos de interação pequenos | CSS tem tamanhos de 5–11 px em capas/legendas; heurística detectou controles abaixo de 24 px em várias telas | R1 escala legível e áreas de toque; validar contexto, não considerar toda legenda decorativa uma falha automática |
| Média | Semântica da expansão do chat precisa de decisão | Painel enfoca a entrada ao abrir, mas não possui `role=dialog` nem `aria-modal`; não foi comprovado controle completo de foco | R1 contratos de diálogo; R7 definir chat modal ou região dedicada e validar Escape, foco e retorno |
| Média | Componentes acumulam responsabilidades | `BoardRadar` ~13 KB, `ChatAssistant` ~12 KB e página de anúncios ~12 KB; apresentação, fetch e regras de formulário juntos | R1 base compartilhada; dividir por feature nas fases correspondentes |
| Média | Estilo global dificulta migração localizada | 31.517 bytes em 24 linhas, seletores globais de header/nav/títulos e 8 media queries | R1 tokens + estilos com escopo, mantendo compatibilidade durante a migração |
| Média | Fonte depende da rede apesar de execução local | `globals.css` importa Inter do Google; há fallback, mas não há pasta `public` nem fontes locais próprias | R1 definir fonte local licenciada ou fallback estável; não criar dependência de imagens externas |
| Média | Acesso a dados e tipos repetidos | Chamadas de conta em página e `AccountJourney`; tipos de listing replicados; callback de fotos usa `unknown[]` e cast | R0 define contratos; R5/R6 adapters/hooks tipados e estado compartilhado |
| Média | SEO específico só está parcialmente preparado | Jogo possui `generateMetadata`; demais páginas herdam metadados globais | R3–R5 metadados por página; R8 revisão sem inventar avaliação ou oferta no schema |

Referências de código: [Home](../../src/components/BoardRadar.tsx), [CSS](../../src/app/globals.css), [jogo](../../src/components/GameDetail.tsx), [catálogo importado](../../src/components/ImportedCatalog.tsx), [comunidade](../../src/components/CommunityListings.tsx), [anúncios](../../src/app/anuncios/page.tsx), [conta](../../src/app/conta/page.tsx), [chat](../../src/components/ChatAssistant.tsx).

## O que já funciona e deve ser preservado

Autenticação local e cookie HttpOnly; senhas com hash; perfil opcional e consentido; precedência de filtros; wishlist por edição; avisos internos opt-in; imagens normalizadas e leitura pública apenas para anúncios ativos; rascunho persistido; aceite versionado; autorização por proprietário; moderação com revisão e justificativa; bloqueio de autoaprovação; reserva/pausa/venda; mensagens privadas; denúncias; solicitações de inclusão; fontes do conhecimento; comparações; bloqueio de redirecionamentos DEMO.

Não se substituirá um desses recursos por mock ou estado apenas no navegador para acelerar o redesign. O papel de moderador continua sendo atribuído explicitamente pelo operador local.

## Jornadas atuais e futuras

**Comprar hoje:** Home → filtros locais ou biblioteca importada → ficha → edição → ofertas DEMO e/ou comunidade → contato protegido → mensagens. **Depois da migração:** busca global → catálogo/resultados com URL → ficha central → fontes separadas → detalhe de anúncio → conversa.

**Vender hoje:** conta → meus anúncios → formulário completo → salvar → fotos → revisão/aceite → fila → decisão → ativo → disponibilidade. **Depois:** conta → vender em etapas, com rascunho recuperável → revisão/aceite → mesma moderação → meus anúncios para gerir status. Não se muda a máquina de estados para fazer o Stepper.

**Radar hoje:** abertura pela Home → chat compacto/expandido → recomendação/ficha/oferta/comparação. **Depois:** acesso global e página própria, reaproveitando o mesmo motor e componentes. Não se apresenta persistência de histórico de conta que não existe.

**Conta hoje:** `/conta` combina autenticação, escolhas de intenção, preferências, wishlist, avisos e coleção recolhida. **Depois:** acessos claros e páginas específicas, mantendo a personalização opcional, a mesma conta para comprar/vender e links antigos válidos.

## Acessibilidade e qualidade: limites da R0

Na amostra, todas as telas tinham um H1, e a heurística de nome de controles não encontrou controles sem identificação. Isso não equivale a validação completa por leitor de tela, contraste de todos os elementos, foco em todos os estados ou conformidade WCAG. Tabelas podem ter rolagem interna apropriada; o resultado sem overflow se refere ao documento.

Já há foco visível em botões, links, inputs e selects, além de tratamento de movimento reduzido. Esses recursos devem ser preservados e ampliados, incluindo textarea, diálogos e drawer. A R0 não mediu LCP, p95, carga concorrente ou tamanho de bundle; não declara essas metas cumpridas.

## Decisão de migração

1. R1 cria layout, tokens e componentes base sem remover páginas atuais. Header passa a ter busca central, navegação comercial e CTA de venda; mobile terá composição própria.
2. R2 monta a nova Home com seleções limitadas e componentes compartilhados. Não manter toda a biblioteca na vitrine inicial.
3. R3 move catálogo completo e busca para rotas próprias, conservando os pontos de entrada antigos e slugs por identidade.
4. R4 reorganiza a ficha central por edição, com as duas fontes comerciais separadas.
5. R5 introduz detalhe de anúncio e fluxo em etapas, com alterações pontuais de contrato quando necessárias.
6. R6 separa conta, onboarding e wishlist sem mudar a segurança da sessão ou transformar favoritos locais em edições por suposição.
7. R7 aplica a linguagem visual ao Radar e integra o acesso global; R8 consolida as jornadas e checks finais.

Cada fase registra diferenças e valida as jornadas afetadas. Não se fará corte único de todas as telas. Próxima etapa preparada: **R1 — design system e estrutura global**.
