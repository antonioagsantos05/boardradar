# R1 — fundação visual e navegação compartilhada

Concluída em 20/10/2026. Esta fase aplica a identidade própria definida na R0 e estrutura as páginas existentes. A Home completa, os cards e as rotas dedicadas de catálogo serão redesenhados nas próximas fases.

## Entrega visível

- Cabeçalho único em todas as páginas, com logo, busca central, favoritos, conta e CTA de venda.
- Navegação desktop para explorar, marketplace, estilos, entretenimento e Radar.
- Navegação mobile própria: Início, Buscar, Radar, Favoritos e Conta; venda continua no topo.
- Rodapé único, identificação DEMO e separação conceitual dos anúncios da comunidade.
- Paleta azul-petróleo, âmbar e superfícies claras; fontes de sistema estáveis, sem importação de fonte externa em tempo de uso.
- Botões e controles de base com áreas de toque, foco e espaçamento padronizados. O tratamento de movimento reduzido foi preservado.
- Confirmações de remoção e venda usam diálogo acessível, foco inicial em Cancelar, Escape, restauração de foco e bloqueio de rolagem do fundo.

Não foram copiados layouts ou artes das referências enviadas. O logo SVG e os recursos ilustrativos próprios existentes permanecem reutilizados.

## Estrutura introduzida

```text
src/styles/tokens.css       paleta, tipografia, espaços, raios, sombras e estados
src/styles/foundation.css   componentes e aliases para o frontend legado
src/styles/layout.css       header, busca, footer e navegação mobile
src/components/layout/     AppShell, Header, SearchBar, Footer, MobileNavigation
src/components/ui/         Button, FormField, States, Pagination, ConfirmationDialog
```

O layout raiz aplica AppShell sem transformar os serviços Python ou alterar os contratos das APIs. Cabeçalhos e rodapés locais duplicados foram removidos. Os estilos de features ainda não migradas continuam em `globals.css`, com aliases para tokens, para evitar um corte único de toda a aplicação.

Componentes de estado e paginação já são usados na comunidade. FormField é usado na busca global. Formulários longos serão divididos nas fases de marketplace e conta; não foram simuladas novas etapas sem persistência.

## Busca e favoritos durante a transição

Como `/jogos` e `/buscar` pertencem à R3, a busca do header usa formulário GET real para `/?q=…`; a Home aplica a consulta aos mecanismos existentes. Uma busca nova do cabeçalho substitui filtros anteriores. O termo é refletido no campo global e as âncoras de catálogo continuam disponíveis.

Essa busca recarrega a página nesta fase. Não equivale a histórico de chat persistido. Os links internos do Next preservam o AppShell, mas um reload completo não preserva a conversa em memória.

Visitante sem conta acessa seus favoritos locais por `/?favoritos=1#catalogo`. Usuário identificado acessa a wishlist da conta em `/conta#desejos`. Não houve migração silenciosa entre IDs de jogos locais e edições com alertas da conta. A apresentação definitiva de favoritos e wishlist será tratada na R6.

## Radar global e diálogos

AppShell mantém uma única instância do chat, acessível por qualquer página. Os botões locais existentes passam pelo mesmo contexto. Mensagens e rascunho são preservados durante navegação por links internos; não se afirma histórico persistido de conta.

No mobile o botão do Radar fica na navegação inferior, evitando duplicação com o launcher flutuante. O painel compacto é região não modal; expandido usa semântica de diálogo modal, captura de Tab, Escape para reduzir e restauração de foco ao fechar. A barra inferior tem espaço reservado e safe area para não esconder o final do conteúdo.

ConfirmationDialog usa `dialog.showModal()` nativo. Vender e remover continuam chamando exatamente as ações de backend e verificações de propriedade/revisão anteriores; somente a confirmação visual mudou.

## Compatibilidade e limites

- Slugs, rotas existentes, seleção de edição, login/logout, dados, perfil, publicação, fotos, wishlist, avisos, mensagens e moderação permanecem funcionais.
- Nenhum backend ou endpoint foi reescrito: 58 arquivos protegidos de Python/APIs têm o mesmo SHA-256 da R0.
- Google, pagamentos, LLM, redirecionamentos comerciais reais e recuperação de senha por e-mail não foram introduzidos.
- Cards, hero e volume da Home ainda são da experiência anterior. R2 reduz a vitrine e padroniza cards; R3 move catálogo e busca para páginas dedicadas.
- Dados de conta ainda são consultados em alguns componentes de feature além do header. Centralizar cache/contratos de conta fica na R6; a R1 não declara essa otimização pronta.
- Não há script de lint configurado. Acessibilidade foi verificada nas interações descritas, sem alegação de auditoria WCAG completa ou metas de desempenho medidas.

## Verificação

[Resumo de aceite](../redesign/r1/summary.json), [matriz de navegador](../redesign/r1/browser-baseline.json), [capturas](../redesign/r1/captures/), [regressão](../redesign/r1/tests.log), [jornada com três contas](../redesign/r1/user-flows.log), [HTTP](../redesign/r1/http.log) e [build](../redesign/r1/build.log).

- 20 testes TypeScript + 327 Python passaram.
- Build e TypeScript passaram; regressão HTTP passou.
- Fluxo completo de comprador, vendedor e moderador passou com confirmação visual real para marcar vendido.
- 45 cenários de navegador nas larguras 360, 390, 768, 1024 e 1440: um header, um footer e uma busca global por página; sem overflow horizontal do documento ou exceções JavaScript.
- Testes específicos de busca global, favoritos anônimos, confirmação/cancelamento por Escape, foco do chat expandido e preservação de conversa em navegação interna passaram.

Scripts: `node scripts/check-redesign-r1.mjs`, `node scripts/check-user-flows-browser.mjs`, `node scripts/smoke.mjs` e `npm test`. Os cenários usam portas e bancos de teste isolados, sem alterar o banco real ou o servidor habitual em 3000.

Próxima fase: **R2 — Home como vitrine e cards compartilhados**, seguindo a direção visual já aplicada à estrutura global.
