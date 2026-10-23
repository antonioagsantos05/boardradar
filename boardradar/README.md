# BoardRadar

## Catálogo vigente: POC v3 — 21/10/2026

O catálogo público agora usa somente os **11 JSONs fornecidos em `data/`**: 100 jogos, 124 edições, 10 lojas, 300 ofertas e 100 anúncios de vendedores fictícios. Veja a [validação contra a estratégia v3 e as pendências](docs/v3/VALIDACAO_ESTRATEGIA.md).

Verifique com `npm run test:v3`, `npm run typecheck`, `npm run build` e `npm run check:v3`. Catálogo e marketplace funcionam sem Python. As contas e a gestão privada anteriores ainda usam SQLite e precisam de conversão para a demonstração no navegador.

O conteúdo abaixo registra o histórico v2 e não descreve a base vigente.


Interface refinada após a R8: [home, catálogo, Radar, favoritos, conta e exemplos de anúncios](docs/REFINAMENTOS_INTERFACE.md). Verifique com `npm run check:ui` e `npm run audit:ui`. Exemplos locais: `npm run seed:community-demo`.

Redesign **R0–R8 concluído**. Veja a [validação final, acessibilidade, SEO e desempenho](docs/v2/REDESIGN_R8_VALIDACAO.md). Verificação: `npm run check:ui` e `npm run audit:ui` (servidores e bancos de teste isolados).

Fluxos de usuário do PDF (sem login Google): [conta, perfil opcional, anúncios com aceite, mensagens, denúncias, solicitações de catálogo, wishlist e avisos internos](docs/v2/FLUXOS_USUARIO_LOCAL.md). Acesse `/conta` para escolher explorar ou vender. Teste integrado: `node scripts/check-user-flows-browser.mjs`.

Marketplace local: a [fase 3](docs/v2/MARKETPLACE_FASE_3.md) acrescenta `/marketplace`, anúncios aprovados na ficha da edição e controles de reserva, pausa e venda. O guia também registra as pendências do PDF atualizado de fluxos. Teste E2E: `node scripts/check-marketplace-phase3-browser.mjs`.

Marketplace em fases: rascunhos vinculados a jogo/edição e [fase 2 de fotos e moderação](docs/v2/MARKETPLACE_FASE_2.md) implementados. Após entrar, acesse **Meus anúncios** em `/conta`. Moderadores revisam em `/moderacao`; descubra como atribuir a permissão no guia da fase 2. A vitrine local `/marketplace` foi entregue na fase 3. Teste de fotos e revisão: `node scripts/check-marketplace-phase2-browser.mjs`.

Contas locais: acesse **Minha conta** no cabeçalho ou `/conta` para criar uma conta e cadastrar, editar e remover seus jogos pessoais. Dados persistidos em SQLite, sem serviços externos. Consulte [funcionamento, segurança e backup](docs/CONTAS_LOCAIS.md). Validação de navegador: `node scripts/check-accounts-browser.mjs` (usa banco isolado em `.qa/`).

Atualização local de 20/10: [documentos atualizados, entregas e pendências](docs/v2/ATUALIZACAO_2026-10-20.md). A IA agora pesquisa o catálogo completo por categoria/mecânica e restrições usando um índice SQLite derivado. Gere o índice com `python scripts/build-game-index.py`. Veja a [cobertura dos dados](docs/v2/catalog-coverage.json).

O catálogo ampliado reúne **10.682 IDs BGG distintos** dos dois arquivos fornecidos, com busca paginada, fichas informativas e comparação de jogos. A seleção editorial mantém **68 jogos** e suas ofertas DEMO. Consulte a [documentação da importação](docs/IMPORTACAO_CATALOGO.md) e a [validação integrada](docs/catalog-import/summary.json).

## Evolução 2.0 por fases — diretriz vigente

O Radar 2.0 será um sistema especialista Python determinístico, **sem LLM, OpenAI, Ollama, Qwen ou serviços externos de inferência**. A proposta anterior de IA generativa nos documentos de planejamento foi substituída pela instrução atual do usuário.

- [Plano das seis fases](docs/v2/PLANO_POR_FASES.md).
- [Auditoria da Fase 1: estado real, contratos e lacunas](docs/v2/AUDITORIA_FASE_1.md).
- [Evidências reproduzíveis da auditoria](docs/v2/baseline/summary.json).
- [Fase 2: motor de regras e correção das recomendações por nome](docs/v2/FASE_2_MOTOR_DE_REGRAS.md).
- [Fase 3: interpretação de português, entidades e nomes ambíguos](docs/v2/FASE_3_INTERPRETACAO_DE_PORTUGUES.md).
- [Verificação da Fase 3](docs/v2/phase3/summary.json): 147 testes Python, 20 TypeScript e verificações de integração.
- [Fase 4: contexto, comparação, edições, ofertas e entretenimento](docs/v2/FASE_4_CONTEXTO_E_FERRAMENTAS.md).
- [Verificação da Fase 4](docs/v2/phase4/summary.json): 193 testes Python, 20 TypeScript e verificações HTTP/navegador.
- [Fase 5: busca documental, fontes e ingestão autorizada](docs/v2/FASE_5_BUSCA_DOCUMENTAL.md).
- [Verificação da Fase 5](docs/v2/phase5/summary.json): 262 testes Python, 20 TypeScript, build, HTTP e navegador; [14 casos de aceite documental](docs/v2/phase5/retrieval-evaluation.json) aprovados.

O chat usa regras versionadas e NLP determinístico em `chatbot/radar_ai`, com filtros antes do score, diagnósticos de rejeição e separação de fichas informativas. Reconhece orçamento como “tenho 200 reais”, números por extenso e negações; nomes aproximados pedem confirmação. A política compartilha pesos e validade de ofertas com o TypeScript, preservando as diferenças de ranking anteriores. A fase 4 conecta relações editoriais de entretenimento, comparações e ofertas ao chat, com contexto portátil que expira em 30 minutos. A fase 5 acrescenta busca documental local e trechos com fontes. A base atual contém dez explicações editoriais próprias, sem manuais oficiais; perguntas sobre ações de jogo continuam exigindo documentação autorizada da edição correta. O chat consulta as fichas adicionais como metadados informativos, sem transformar avaliações BGG em regras oficiais. Hospedagem e avaliação de latência ficam para a fase 6.

POC em Next.js e TypeScript com assistente conversacional em Python, seleção JSON de 68 jogos, base adicional de 10.682 registros BGG, índice SQLite local de busca, 13 videogames, 10 lojas fictícias, 236 ofertas demonstrativas e 61 dias de histórico sintético por oferta. Com autenticação local; sem Docker ou integração comercial. Entre os registros BGG, 61 são expansões identificadas e 10.436 têm tipo de produto a confirmar; a quantidade total não representa somente jogos-base verificados.

## Executar no Windows

Na pasta `boardradar`, com Node.js 22 disponível no PATH:

```text
npm install
npm run build
npm start
```

Acesse http://localhost:3000. Depois de alterar o código, execute `npm run build` novamente antes de `npm start`. Para desenvolvimento com atualização automática, use `npm run dev`.

`npm start` e `npm run dev` iniciam o site e o serviço Python juntos. O serviço usa uma porta local escolhida pelo sistema e um token efêmero gerado a cada execução; apenas a API Next.js conversa com ele. Nenhuma chave paga é necessária. Python 3.13.7 portátil está em `../.tools/python-3.13.7`. Em outra máquina, instale Python 3.10+ ou defina `PYTHON_EXECUTABLE` com o caminho do interpretador. O serviço não usa pacotes externos nem precisa de pip. Encerre com Ctrl+C.

## Verificar

```text
npm run validate-data
npm test
npm run typecheck
npm run build
```

## Fluxos implementados

- Busca por nome, alias, categoria e tags; filtros combinados por jogadores, duração, orçamento e estilo.
- Preferência de complexidade e videogames afeta o ranking determinístico; restrições obrigatórias são aplicadas antes da pontuação.
- Preferências e favoritos opcionais no localStorage. A opção “Limpar filtros” remove as preferências; os favoritos podem ser removidos individualmente.
- Ficha por slug, seleção de edição, ofertas recentes ordenadas por menor preço, ofertas antigas e indisponíveis sinalizadas e histórico explicitamente sintético.
- Assistente Radar em Python com contexto por conversa, perguntas de refinamento e sugestões de próximas mensagens. Reconhece luta/combate, franquias, modos cooperativo/competitivo, negações, orçamento, jogadores por extenso, duração e pedidos de alternativas ou explicações. Uma resposta curta como “2” completa a pergunta sobre jogadores. Não usa LLM nem serviços externos; linguagem fora dos padrões conhecidos recebe uma pergunta de esclarecimento.
- Chat com carregamento, bloqueio de envio duplicado, tratamento de erro, reenvio, rolagem automática, reset com cancelamento e explicação por jogo recomendado.
- APIs de catálogo, ofertas, histórico, recomendação e chat. `/out/{offerId}` retorna 403 em qualquer situação.
- Capas gráficas originais geradas com CSS/SVG; não representam as caixas oficiais. Marca vetorial aproximada da referência visual fornecida.

## APIs

- `GET /api/games?q=azul&players=4`
- `GET /api/games/{id-ou-slug}`
- `GET /api/games/{id}/offers?edition={editionId}`
- `GET /api/games/{id}/price-history?edition={editionId}`
- `POST /api/recommendations` com filtros JSON, incluindo `videogames: ["v11"]`.
- `POST /api/chat` com `message` obrigatório e `state` opcional. Reenvie o `state` retornado na próxima mensagem para manter contexto. `preferences` é aceito como contexto inicial legado.

## Conversa de exemplo

A fase 4 acrescenta comparações no chat (`Compare Root` → `Scythe`), consulta de edições e ofertas (`Fale sobre Catan` → `ofertas dele`) e referências editoriais de filmes/séries (`Gosto do filme Duna`). O contexto expira em 30 minutos. Dados ausentes não são inventados, e ofertas continuam fictícias. Detalhes e validação: [Fase 4](docs/v2/FASE_4_CONTEXTO_E_FERRAMENTAS.md).

1. “Gosto de jogos de luta” → recomenda apenas jogos com combate e pergunta quantas pessoas vão jogar.
2. “2” → preserva o interesse em combate, filtra por duas pessoas e pergunta o orçamento.
3. “Até R$ 600” → mantém o contexto e usa apenas ofertas recentes na simulação.
4. “Não quero cooperativo” → exclui jogos cooperativos.
5. “Outras opções” → evita repetir sugestões anteriores.
6. “Por que esse?” → explica uma sugestão anterior com dados do catálogo.

O motor está em `chatbot/engine.py`; o transporte HTTP privado em `chatbot/server.py`; a interface em `src/components/ChatAssistant.tsx`. `npm test` executa testes TypeScript e Python; `npm run test:python` verifica apenas a conversa. O transporte é para a POC local; hospedagem futura exige um processo Python próprio e configuração do proxy.

Para verificação integrada, execute `node scripts/smoke.mjs` após o build. `node scripts/check-chat-browser.mjs` verifica o chat em Chrome headless, incluindo conversa com contexto, modo mobile e reset; usa Chrome instalado e salva capturas em `.qa/`. Ambos iniciam e encerram seus próprios serviços de teste. O cenário de combate favorece confronto tático sobre combate incidental de jogos colecionáveis; essa curadoria não é equivalência com gameplay de luta em tempo real.

Valores monetários são armazenados em centavos inteiros. Validade de oferta: sete dias desde o timestamp, sem aceitar datas futuras. A amostra possui timestamps fixos e envelhece naturalmente; regenere com `npx tsx scripts/seed.ts` para recriar os arquivos originais da demonstração, sem sugerir coleta real.

## Limites editoriais e pendências para produção

Os nomes dos jogos e videogames foram fornecidos pelo cliente. Quantidade de jogadores, duração, complexidade, descrições e identificação de edições são preliminares, não conferidos em fontes primárias. A interface informa esse estado. Não alegar catálogo verificado antes de revisão humana e registro de fonte, licença e data por jogo. Os nomes de produtos colecionáveis precisam de validação de idioma, SKU e edição; as ofertas atuais não são ofertas comerciais reais. Não há comparações entre expansões e jogos-base.

Fontes comerciais, pagamentos, login, autorização administrativa, importação, sincronização, tracking, wishlist sincronizada e alertas ficam para evolução posterior. LLM está fora do escopo vigente. Não há painel administrativo persistente: os JSONs são somente leitura durante a execução. Google Fonts é opcional e usa fallback local quando indisponível.

## Roteiro de demonstração

1. Buscar “Azul”; limpar e selecionar quatro jogadores.
2. Selecionar Mass Effect e observar as justificativas; combinar com orçamento.
3. Abrir uma ficha e conferir edição, preços DEMO, oferta antiga e oferta indisponível.
4. Tentar abrir a demonstração de oferta e confirmar ausência de redirecionamento.
5. Abrir The Witcher: Old World para ver o estado sem ofertas.
6. Conversar com Radar: “Gosto de XCOM 2”, depois “para 4 pessoas até R$ 1000”.
7. Conferir histórico sintético, favoritos e persistência local das preferências.


### Radar: preferências e conversa

O assistente ativo (`chatbot/radar_ai/poc_catalog.py`) usa o catálogo JSON atual. As recomendações consideram estilos e franquias do perfil com consentimento; pedidos e filtros da conversa têm prioridade. A resposta identifica a franquia e os temas em comum, sem presumir uma licença oficial. O orçamento do perfil influencia a ordenação; o orçamento informado na conversa filtra os resultados.

Experimente: “Usar meus gostos”, “Gosto de Duna”, “Jogos para 4 pessoas até R$ 300”, “Por que esses jogos?”, “Compare esses jogos”, “Mostrar mais” e “Quero anunciar um jogo”. O Radar oferece atalhos para criar anúncios, gerenciar anúncios, abrir conversas e editar preferências. Não publica anúncios nem envia mensagens a vendedores por conta própria.

O perfil autenticado é a fonte principal; na ausência dele, o chat pode recuperar as escolhas locais da mesma conta. A troca de sessão limpa a conversa atual. As respostas continuam sendo geradas por regras e dados do catálogo, sem chamada a um modelo externo. Regras de jogos sem manual disponível não são inventadas.

Validação: `python -m unittest discover -s chatbot -p test_chat_evolution.py` e `python -m unittest discover -s chatbot -p test_poc_v3.py`. O script `scripts/check-chat-evolution.py` verifica API e interface com Playwright contra um servidor de teste na porta 3001 e banco isolado em `.qa/account-workspace-flow.sqlite3`.
