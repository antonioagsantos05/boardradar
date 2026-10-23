# R8 — Validação final e refinamento

A etapa fecha o redesign R0–R8 com revisão das jornadas, contraste, navegação por teclado, SEO e desempenho do catálogo. A aplicação continua local.

## Entregas

- Contraste de textos, categorias, preços, fontes e mensagens do Radar ajustado; grupos e regiões recebem semântica acessível e os títulos mantêm uma hierarquia coerente.
- Formulários e grids respeitam a largura no celular. Movimento reduzido é respeitado e o link de pular para o conteúdo foi verificado por teclado.
- Fotos de anúncios recebem dimensões e carregamento adequado. A área principal reserva espaço durante o carregamento.
- O catálogo prepara seu índice de busca e suas ordenações uma vez por processo, mantendo filtros antes da paginação, IDs e vínculos explícitos com a curadoria.
- Metadados, canonical, robots e sitemap foram adicionados. O padrão local usa `noindex, nofollow`, bloqueio de rastreamento e sitemap vazio. A variável opcional `BOARDRADAR_SITE_URL`, com origem HTTPS pública, deve ser definida antes do build para habilitar indexação pública em uma futura hospedagem. Páginas de conta, busca, anúncios e administração continuam sem indexação. Robots não substitui autenticação.

## Verificação reproduzível

Na pasta `boardradar`, com Node no PATH:

```text
npm test
npm run validate-data
npm run build
npm run check:ui
npm run audit:ui
```

Foram aprovados 32 testes TypeScript e 332 Python, além da validação dos dados e do build com TypeScript. O projeto não tem ESLint configurado; nenhum resultado de lint é alegado.

A regressão de navegador cobre 105 cenários responsivos em cinco larguras, além de jornadas com visitante, comprador, vendedor e moderador: cadastro, preferências opcionais, wishlist e consentimento, publicação moderada com fotos, avisos internos, navegação e Radar compartilhado. Os testes usam banco e servidores isolados, sem alterar as contas reais.

A auditoria axe cobre 42 combinações de páginas/larguras e quatro estados adicionais: Radar preenchido, Radar expandido, filtros móveis e confirmação. Também verifica teclado, movimento reduzido, SEO e contratos do catálogo. Evidências: [auditoria](../redesign/r8/audit.json), [regressão](../redesign/r8/flows/browser-baseline.json) e capturas nas pastas correspondentes.

## Desempenho e limites

A medição de API usa 20 requisições sequenciais aquecidas por endpoint em localhost. A amostra anterior está em [baseline.json](../redesign/r8/baseline.json), e a final em `audit.json`. O p95 anterior do catálogo padrão foi 53,48 ms; o p95 final foi 4,79 ms nessa execução local. Catálogo e cadastro registraram CLS zero nas duas larguras auditadas após a reserva de espaço. As medições de LCP e CLS são amostras de Chrome headless local sem limitação de CPU/rede, não Web Vitals de usuários reais nem teste de carga. O campo legado `cold_ms` da baseline é a primeira amostra após a navegação, não uma inicialização fria do processo.

Zero violações automáticas não significa certificação WCAG: itens `incomplete`, leitura com tecnologias assistivas e avaliação humana continuam necessários. Consulte a [documentação oficial do axe](https://www.deque.com/axe/core-documentation/api-documentation/).

As lojas, ofertas e históricos continuam DEMO. Permanecem pendentes verificação editorial dos metadados importados, manuais autorizados, recuperação de senha, histórico persistente de conversa e integrações comerciais. Nenhum serviço externo de IA, analytics, checkout ou login Google foi ativado.
