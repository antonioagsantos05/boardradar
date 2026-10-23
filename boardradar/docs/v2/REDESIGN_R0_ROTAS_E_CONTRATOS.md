# R0 — mapa de rotas, componentes e contratos

Planejamento de migração, não rotas já implementadas. Backend, sessão e dados atuais são a base.

## Navegação proposta

| Destino | Rota canônica proposta | Entrada atual / preservação | Fase |
|---|---|---|---|
| Home | `/` | Preservar `/`; âncoras antigas continuam com destino útil durante a transição | R2 |
| Catálogo | `/jogos` | `/#catalogo` e `/#base-ampliada` não serão abandonados silenciosamente | R3 |
| Resultados | `/buscar?q=…` | Busca local da Home vira estado compartilhável por URL | R3 |
| Jogo | `/jogos/[slug]?edition=…` | Preservar slugs, edição e âncoras de ofertas/comunidade/comparação | R4 |
| Radar | `/radar-ai` | Preservar abertura compacta e expansão durante migração | R7 |
| Marketplace | `/marketplace` | Preservar rota atual | R5 |
| Anúncio público | `/anuncios/[id]` | Rota nova, limitada aos dados públicos autorizados | R5 |
| Criar/retomar anúncio | `/vender` | Hoje a criação está em `/anuncios`; rascunho permanece no servidor | R5 |
| Gerir anúncios | `/meus-anuncios` | `/anuncios` continua válida por compatibilidade | R5 |
| Autenticação | `/entrar`, `/cadastro` | Preservar acesso por `/conta`, sessão e erros reais | R6 |
| Preferências | `/onboarding` | Mesmo perfil opcional persistido, com pular/excluir | R6 |
| Conta | `/minha-conta` | `/conta` continua válida; redirect deve preservar retorno local seguro | R6 |
| Wishlist | `/favoritos` | Separar favoritos locais de wishlist da conta explicitamente | R6 |
| Conversas | `/mensagens` | Preservar rota e privacidade dos participantes | R6 |
| Revisão | `/moderacao` | Preservar papel, fila, denúncias e solicitações | R5/R6 |

Desktop: logo + busca central + wishlist/conta/vender; navegação catálogo, marketplace e Radar. Mobile: Início, Buscar, Radar, Favoritos e Conta; vender permanece no topo ou nos destinos comerciais. Rodapé e barras fixas devem respeitar safe area e não cobrir conteúdo ou entrada do chat.

## Componentes e responsabilidades

Estrutura proposta, a introduzir progressivamente, sem renomear todos os arquivos existentes de uma vez:

```text
src/components/layout/   Header, MobileNavigation, Footer, AppShell
src/components/ui/       Button, FormField, Dialog, Toast, Pagination, estados
src/features/catalog/    GameCard, metadados, filtros, adaptadores de fonte
src/features/offers/     OfferCard, PriceDisplay, grupo por edição/origem
src/features/marketplace/ UserListingCard, formulário em etapas, gestão
src/features/account/    autenticação, perfil opcional e navegação da conta
src/features/wishlist/   botão, lista, consentimento e alertas
src/features/radar/      apresentação compartilhada do chat e cards
src/lib/api/             clientes tipados e mapeamento de erros existentes
```

R1 começa por layout/ui, sem substituir os módulos Python. `GameCover` sai da dependência da Home para um componente próprio quando os cards forem extraídos. Acesso a dados não deve ser duplicado em cada card. Formulários usam as validações existentes e não escolhem status, proprietário ou papel de usuário no cliente.

## Contratos disponíveis

| Contrato | Suporte atual | Limite para o redesign |
|---|---|---|
| `GET /api/games` | Ranking editorial por busca, jogadores, duração, orçamento e estilo | Não é busca comercial global da biblioteca. Validar parâmetros de forma consistente com o POST ao ampliar |
| `POST /api/recommendations` | Preferências validadas, filtros antes do ranking | Não converter dados importados em curadoria automaticamente |
| `GET /api/library` | q, players, duration, kind, page e page_size 12/24/48/96 | Não suporta todos os filtros de complexidade, mecânica, preço e estoque como campos estruturados |
| `GET /api/games/[id]` | Ficha editorial | Ficha importada vem da camada server-side da biblioteca |
| `GET /api/compare` | Dois IDs válidos e atributos disponíveis | Campos ausentes permanecem ausentes; não inferir interação ou aprendizado |
| `GET /api/games/[id]/offers` | Ofertas DEMO por edição | Nenhum parceiro real ou checkout |
| `GET /api/games/[id]/price-history` | Série sintética identificada | Não usar como menor preço real ou desconto |
| `GET/POST /api/account` | Conta, sessão, perfil, wishlist e avisos internos | Sem recuperação de senha, edição completa de identidade ou wishlist genérica por jogo |
| `POST /api/chat` | Motor determinístico, contexto, perfil consentido, fontes, cards e anúncios ativos | Sem LLM, streaming ou histórico persistente de conta |
| `GET /api/listings?view=public` | Busca pública de ativos por q, edição e página | Sem detalhe público por ID ou filtros globais de condição/preço/região |
| `GET/POST /api/listings` | Gerência, revisão, disponibilidade, mensagens, denúncias e solicitações | Ações tipadas por whitelist; preserve autenticação, origem e revisões |
| `GET/POST /api/listing-images` | Upload normalizado e leitura por autorização/status | Não mover fotos privadas para `public/`; previews não equivalem a persistência |
| `GET /out/[offerId]` | Bloqueio 403 DEMO_MODE | Não substituir por link comercial supostamente funcional |

## Tarefas pontuais de contrato

1. **Detalhe público de anúncio (R5):** definir consulta por ID, projeção pública e resposta para indisponível; não reutilizar leitura de anúncio privado com bypass de sessão.
2. **Identificação pública (R5):** definir apelido público e controle do usuário; não expor nome completo ou e-mail da conta por conveniência visual.
3. **Filtros globais (R3/R5):** condição, faixa de preço, disponibilidade e ordenação precisam acontecer no conjunto inteiro, antes da paginação. Não filtrar apenas os 24 itens recebidos.
4. **Wishlist (R6):** suporte atual é por edição. Favoritos sem conta são IDs locais de jogos; não migrar silenciosamente nem cancelar opt-in ao clicar no card.
5. **Segurança da conta (R6):** recuperação de acesso, termos/privacidade do cadastro e edição de identidade precisam de contrato e política reais. Não desenhar fluxo concluído com mock.
6. **Eventos/histórico (R7/R8):** decidir dados mínimos, consentimento, retenção e armazenamento antes de registrar buscas ou conversas. Métrica de clique não é venda.

As tarefas são levantadas nesta fase; nenhum desses contratos novos foi implementado na R0. Recuperação por e-mail, parceiros, autenticação Google, pagamentos e serviços externos continuam fora desta entrega local.

## Regras de identidade e apresentação

- Cada resultado usa ID canônico e proveniência. Associação BGG/editorial conhecida converge para a ficha editorial; não unir por nome nem criar dois jogos comerciais para o mesmo vínculo conhecido.
- Mesmo componente visual pode exibir dados editoriais ou importados, com diferenças de confiança explícitas e sem preço quando ausente.
- Preço tem centavos, moeda, edição, origem e condição. A contagem de ofertas não pode ser fabricada a partir de um recorte de busca.
- Card de anúncio é um item de venda daquele jogo/edição, não um novo registro de catálogo.
- Histórico/favoritos anônimos e perfil de conta não ganham autorização implícita de sincronização.
