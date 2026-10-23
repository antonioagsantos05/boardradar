# Direção visual própria — BoardRadar

Brief para a R1, não design system já aplicado. As imagens fornecidas pelo usuário inspiram hierarquia, protagonismo das caixas e organização comercial. Não serão copiados layouts, artes, marcas, reviews, textos, gradientes ou preços dos exemplos.

## Conceito

**Descoberta guiada, jogos em primeiro plano.** Uma vitrine clara e acolhedora, com azul-petróleo como estrutura e âmbar para ações prioritárias. O radar aparece em detalhes gráficos próprios: arcos incompletos, pontos e linhas discretas, usados para sugerir descoberta e afinidade.

A identidade vem da marca BoardRadar existente e da combinação catálogo + Radar + comunidade. Não depende de copiar um e-commerce escuro ou de transformar todas as superfícies em painéis administrativos.

## Paleta proposta

| Token proposto | Valor | Uso |
|---|---|---|
| brand.ink | `#082A35` | Marca, títulos e áreas estruturais escuras |
| brand.amber | `#F2A52A` | Ação prioritária, com texto escuro |
| brand.green | `#28756B` | Apoio e ações secundárias, sem competir com o âmbar |
| surface.canvas | `#F7F4ED` | Fundo claro acolhedor |
| surface.card | `#FFFDF8` | Cards e formulários |
| text.primary | `#16262C` | Texto principal |
| text.secondary | `#52646A` | Informações de apoio legíveis |
| border.default | `#E1E5DF` | Separação sutil, com foco destacado independente |

Pares calculados para a proposta: texto principal/canvas 14,19:1; texto secundário/card 6,09:1; ink/amber 7,32:1; card/green 5,37:1. [Cálculo registrado](../redesign/r0/proposed-contrast.json). Não é auditoria de contraste de todos os elementos atuais ou de todos os estados futuros.

## Tipografia, espaço e superfícies

- Manter família sem serifa legível; Inter é a referência atual. R1 decide distribuição local licenciada ou fallback estável, sem depender de importação de fonte em tempo de uso.
- Corpo de leitura: alvo 16 px; controles e labels: 14–16 px; metadados auxiliares: 12–14 px. Títulos com escala responsiva, sem usar fonte minúscula para fazer caber mais cards.
- Escala de espaçamento baseada em 4 px: 4, 8, 12, 16, 24, 32, 48 e 64. R1 transforma em tokens de código.
- Bordas suaves, sombras discretas e poucos níveis de raio. Cards devem valorizar jogos, sem um quadro dentro de vários outros quadros.
- Ícones Lucide coerentes com a aplicação existente. Animações discretas e movimento reduzido preservado.

## Composição

**Header desktop:** busca central utilizável em todas as páginas; navegação comercial clara; wishlist/conta e vender visíveis. Separar linhas quando necessário em vez de apertar todos os links.

**Mobile:** navegação inferior própria e busca fácil. O CTA de venda permanece acessível. Reservar espaço para barra inferior e safe area; Radar e CTA não podem cobrir botões ou o campo de mensagem.

**Home:** hero compacto e direto; categorias reais; seleções limitadas; recomendações explicadas; descoberta por entretenimento; comunidade. O catálogo completo sai da Home e passa a ter destino próprio.

**Cards:** imagem ou fallback honesto, título, jogadores/duração, origem da complexidade quando existente, edição e fonte do preço. Uma ação principal e wishlist acessível. Anúncios usados não ganham aparência de produto novo de loja.

**Ficha:** resumo e edição primeiro, oportunidades de compra em destaque, conteúdo de aprendizado e fontes em seguida. Comparação continua acessível sem empurrar a decisão comercial para o fim.

**Conta e venda:** formulários em etapas ou grupos curtos, status claro, ajuda no ponto de decisão e confirmação explícita para ações destrutivas. Mensagens nativas de confirmação serão substituídas apenas quando o diálogo acessível compartilhado estiver pronto.

## Recursos visuais

Logo SVG existente pode ser reaproveitado. Hoje não há pasta `public` com capas reais próprias: as capas editoriais são composições ilustrativas e as fotos dos anúncios são uploads de usuários. Não apresentar fallback como embalagem oficial nem usar uma foto de anúncio para representar todo o catálogo. Imagens externas, capas e fontes precisam de disponibilidade e direitos de uso adequados antes de serem adicionadas.

## Como avaliar a R1

A primeira tela deve permitir identificar marca, busca e caminhos de explorar, usar o Radar e vender. O sistema deve permanecer reconhecível mesmo sem capa externa, preço ou perfil. Contraste, foco, toque, hierarquia e comportamento mobile serão medidos no código; a semelhança com um exemplo visual não é critério de aceite.
