# Redesign BoardRadar — plano por fases

Status: **R0, R1, R2, R3, R4, R5, R6, R7 e R8 concluídas em 20/10/2026**. Veja a [entrega visual da R1](REDESIGN_R1_FUNDACAO.md), o [diagnóstico](REDESIGN_R0_DIAGNOSTICO.md), o [mapa de rotas/contratos](REDESIGN_R0_ROTAS_E_CONTRATOS.md) e a [direção visual própria](REDESIGN_R0_DIRECAO_VISUAL.md). Este plano organiza o prompt em entregas pequenas, com validação independente, sem substituir os serviços existentes.

Use os identificadores **R0–R8** para não confundir com as fases anteriores de implementação do marketplace. Ordem: R0 → R1 → R2 → R3 → R4 → R5 → R6 → R7 → R8.

## Regras comuns

- Preservar Next.js/React/TypeScript, Python determinístico, contratos, contas, sessões, SQLite, dados JSON e arquivos de fotos.
- Continuar local. Login Google está excluído por decisão do usuário. Nenhum checkout, pagamento, provedor LLM ou integração comercial será ativado pelo redesign.
- Lojas e preços simulados permanecem identificados como DEMO. Anúncios são dados informados por usuários e têm apresentação própria.
- Um jogo tem página central, com edição selecionada e fontes de compra separadas. Biblioteca importada não vira curadoria verificada nem recebe preços fictícios.
- Preferências históricas são flexíveis; pedido e filtros atuais prevalecem. Consentimento não pode ser presumido.
- Migrar progressivamente, sem apagar o frontend inteiro. Rotas antigas continuam funcionando por compatibilidade ou redirecionamento adequado.
- Cada fase entrega código funcional, estados de carregamento/erro/vazio, navegação por teclado e verificação mobile e desktop. Não deixar testes e acessibilidade exclusivamente para o fim.

## R0 — Diagnóstico e mapa de migração

**Entregas:** auditoria das páginas, componentes, CSS, acessibilidade básica e fluxos; inventário dos contratos reais; mapa de navegação e baseline dos testes; referência visual dos fluxos atuais.

**Pontos já identificados no inventário inicial:** navegação e cabeçalhos locais duplicados; busca e catálogo concentrados na Home; cards distintos entre seleção editorial e biblioteca importada; formulários e seções extensos na conta/anúncios; estilos globais concentrados; ausência de páginas dedicadas de anúncio público e Radar.

Inspecionar os componentes antes de concluir o diagnóstico, sem tratar o inventário inicial como auditoria visual completa. Classificar cada requisito como suportado, adaptação de frontend ou dependência de contrato/backend.

**Aceite:** diagnóstico e mapa de rotas registrados; jornadas comprar, vender e conversar mapeadas; nenhuma funcionalidade existente removida.

## R1 — Design system e estrutura global

**Entregas:** tokens de cor, tipografia, espaço, borda, sombra e estados; layout compartilhado; header com busca em destaque, footer e navegação mobile própria. Componentes base: Button, FormField, SearchBar, EmptyState, ErrorState, LoadingSkeleton, Toast, ConfirmationDialog e Pagination.

Reaproveitar identidade BoardRadar e recursos locais. Separar estilos por responsabilidade e componentes, sem migração indiscriminada que quebre as páginas ainda antigas.

**Aceite:** estrutura navegável em 360, 390, 768, 1024 e 1440 px, sem rolagem horizontal indevida; foco visível e áreas de toque adequadas; conteúdo não fica escondido por barras fixas.

## R2 — Home como vitrine

**Entregas:** hero curto com busca e CTAs; categorias ligadas a filtros reais ou identificadas como editoriais; recomendações gerais/personalizadas; descoberta por entretenimento; oportunidades válidas; seção da comunidade e apresentação do Radar.

Criar GameCard reutilizável e primeira versão de UserListingCard, PriceDisplay, GameMetadata e WishlistButton. Manter fallbacks de imagem e informar quando a capa é ilustrativa. Não inventar avaliações, descontos, escassez ou ofertas.

**Aceite:** o visitante encontra rapidamente catálogo, Radar e venda; usuário com perfil vê personalização real; visitante sem perfil recebe sugestões gerais; estados sem oferta ou anúncio funcionam sem preencher a tela com conteúdo fictício.

## R3 — Catálogo, busca e filtros

**Entregas:** `/jogos` e `/buscar`; busca central com estado na URL; grid padronizado; filtros ativos removíveis; limpar filtros; contagem, ordenação suportada, paginação e quantidade por página; sidebar desktop e drawer mobile.

Usar contratos existentes e explicitar diferenças de cobertura entre seleção editorial e registros importados. Unificar apresentação sem duplicar identidades por título; manter BGG ID, vínculo editorial e slug canônico. Ausência de complexidade ou edição não vira valor presumido.

**Aceite:** filtros e paginação combinam corretamente, URLs podem ser compartilhadas e navegação voltar/avançar funciona; cada filtro visível tem suporte real; preço e disponibilidade não excluem silenciosamente registros sem dados verificáveis.

## R4 — Página central de jogo e decisão de compra

**Entregas:** cabeçalho do produto, metadados e descrição objetiva; seleção clara de edição; bloco “Onde comprar” em destaque com lojas DEMO e comunidade separadas; wishlist; comparação, conteúdo editorial e relacionados sem esconder as ofertas. CTA mobile acessível quando apropriado.

Componentes: OfferCard, resumo comercial e apresentação padronizada das fontes. Resumo “Por que jogar?” usa conteúdo editorial disponível; não simula análise gerada que o backend não fez.

**Aceite:** anúncio de uma edição não aparece na outra; jogo-base não é misturado à expansão; itens usados são identificados; nenhuma saída comercial bloqueada pela POC é apresentada como compra real.

## R5 — Marketplace e venda em etapas

**Entregas:** vitrine de anúncios, filtros suportados, detalhe `/anuncios/[id]`, fluxo `/vender` com Stepper e salvamento real de rascunho, e `/meus-anuncios` com gestão de status.

Etapas: jogo/edição → condição, idioma, componentes e defeitos → fotos → preço, negociação, região e entrega → revisão e aceite. Reaproveitar upload privado, versões de revisão, moderação, contato protegido e denúncias. Solicitar inclusão quando não houver identidade validada.

**Aceite:** vendedor consegue salvar, retomar, enviar, corrigir e gerir anúncio; alterações invalidam a aprovação conforme a regra existente; somente ativos aparecem como disponíveis; detalhe não expõe dados de conta ou fotos privadas.

## R6 — Conta, onboarding, wishlist e notificações

**Entregas:** separar visualmente entrar/cadastrar, personalização opcional e área da conta; navegação simples entre dados, perfil, wishlist, anúncios, conversas, avisos e segurança. Página dedicada `/favoritos` usa a wishlist persistida, com edição, preço-alvo e consentimento separado para alertas internos.

Comprar/explorar leva à vitrine; vender pode pular preferências e ir ao anúncio. Resolver a distinção entre favoritos locais antigos e wishlist da conta sem perda silenciosa nem sincronização simulada. Recuperação de acesso só aparece como funcional quando existir serviço real.

**Aceite:** cadastro não exige preferências; perfil pode ser pulado, retomado, editado e excluído; usuário compra e vende na mesma conta; cancelar avisos funciona; alertas de lojas indisponíveis não parecem ativos. Login Google continua fora do escopo.

## R7 — Radar integrado à experiência comercial

**Entregas:** página `/radar-ai`, janela compacta coerente com ela, leitura confortável, sugestões, cards de recomendação, comparação, fontes, wishlist e ações para detalhes/ofertas. Reaproveitar o estado e os contratos do chat existente.

Sem duplicar motores ou sessões por apresentação. Manter cancelamento, timeout, reinício e acessibilidade. Histórico só é apresentado como persistente se realmente houver suporte; hoje a conversa da interface não equivale a histórico de conta persistido.

**Aceite:** perguntas e casos de regressão continuam funcionando; pedido atual prevalece sobre perfil; nenhum preço/estoque é gerado; lojas e anúncios são distinguidos; não há alegação de LLM integrada.

## R8 — Validação final e refinamento

**Entregas:** revisão das jornadas completas, acessibilidade, SEO das páginas públicas, imagens, desempenho e consistência; contratos faltantes e limitações documentados; instrumentação de eventos apenas conforme contrato e consentimento definidos.

Executar testes apropriados, TypeScript e build. O projeto não tem script de lint configurado no inventário inicial; definir uma configuração real antes de prometer esse check. Validar as cinco larguras indicadas no prompt e manter evidências dos fluxos com visitante, comprador, vendedor e moderador em banco de teste isolado.

**Aceite:** descobrir → entender → comparar → consultar loja DEMO ou conversar com vendedor funciona; vender → revisar → moderar → publicar → reservar/pausar/vender funciona; funcionalidades anteriores preservadas; limitações reais explícitas; sem erros de console ou overflow relevante nos fluxos verificados.

## Mapa de rotas proposto

| Destino | Rota proposta | Migração / compatibilidade |
|---|---|---|
| Home | `/` | Redesenhar a vitrine existente |
| Catálogo | `/jogos` | Nova página; preservar entradas antigas por âncora durante a transição |
| Busca | `/buscar` | Nova apresentação com parâmetros na URL |
| Jogo | `/jogos/[slug]` | Preservar slugs e parâmetro de edição |
| Radar | `/radar-ai` | Nova página sobre o motor existente |
| Marketplace | `/marketplace` | Redesenhar a rota atual |
| Anúncio público | `/anuncios/[id]` | Nova página; leitura pública por ID precisa de contrato |
| Vender | `/vender` | Novo fluxo de apresentação sobre persistência existente |
| Meus anúncios | `/meus-anuncios` | Gerência atual em `/anuncios`; manter compatibilidade |
| Entrar / cadastrar | `/entrar`, `/cadastro` | Separar apresentação sobre a API atual |
| Personalizar | `/onboarding` | Reutilizar perfil consentido existente |
| Conta | `/minha-conta` | `/conta` continua válida |
| Wishlist | `/favoritos` | Reutilizar dados da conta; definir tratamento dos favoritos locais |
| Conversas | `/mensagens` | Preservar a rota atual |
| Moderação | `/moderacao` | Preservar proteção por papel e fluxos atuais |

Rotas novas não são autorização para quebrar links antigos. Nome final e redirects devem constar da auditoria R0 antes da implementação.

## Contratos conhecidos e lacunas a confirmar na R0

Existentes: `/api/account` com sessão, perfil, wishlist e avisos; `/api/chat`; `/api/games`; `/api/library`; `/api/compare`; ofertas e histórico por jogo/edição; `/api/listings` com ações e busca pública; `/api/listing-images`; conversas e moderação por ações de listings.

Lacunas identificadas no inventário:

- Detalhe público de anúncio por ID: não confundir consulta pública de ativos com leitura privada de rascunhos.
- Apelido/identificação pública de vendedor: a projeção atual evita expor dados da conta; não publicar nome completo/e-mail apenas para preencher um componente.
- Filtros estruturados adicionais de anúncios (condição, região, preço) e cobertura de filtros no catálogo: implementar somente após confirmar suporte, sem aplicar só aos primeiros 24 resultados como se fosse filtro global.
- Recuperação de senha, edição de dados pessoais e controles de segurança além de sair: não há serviço completo identificado.
- Wishlist em nível de jogo e preferência/alertas de lojas: o suporte atual é por edição e novos anúncios internos. Não mascarar essa diferença.
- Histórico persistente do Radar e rastreamento de eventos: precisam de contratos e decisões de consentimento/retenção.
- Solicitação de inclusão é persistida e moderada, mas não cria edição comercial automaticamente.

Essas lacunas viram tarefas pontuais, não uma reescrita do backend. Cada fase deve declarar o que fica disponível, condicionado ou indisponível.

## Entregáveis e acompanhamento

Cada fase registra: arquivos/rotas alterados, componentes criados, contratos usados/alterados, validação executada, capturas mobile/desktop quando úteis e pendências. Uma fase só é concluída quando seu aceite passar; implementação parcial não recebe status de concluída.

Redesign **R0–R8 concluído**. Veja a [validação final da R8](REDESIGN_R8_VALIDACAO.md).
