# Fase 1 — auditoria do estado real

Data de referência: 19/10/2026. Escopo: inventário, leitura documental, diagnóstico e baseline de regressão. Não altera a lógica do chatbot, o catálogo ou o ranking.

## 1. Precedência dos requisitos

1. Pedido atual: implementar por fases um sistema especialista Python **sem LLM, Ollama, Qwen, OpenAI ou serviço de inferência**.
2. Prompt anexado “Motor de inteligência em Python sem LLM”: especifica capacidades, seis fases e meta final de 100 cenários.
3. Especificação técnica e plano de negócio 2.0: visão de produto; suas propostas de LLM estão substituídas pela decisão atual.
4. Especificação consolidada original: fonte literal das regras RN-001 a RN-025, preservadas em `baseline/business-rules-original.json` com hash do DOCX.

Os dois documentos 2.0 foram lidos integralmente e suas cópias permanecem na pasta `teste`. As extrações textuais e hashes estão em `baseline/source-documents.json`. Não foram instalados Ollama nem modelos durante a transição; a inspeção anterior consultou disponibilidade, sem executar instalação.

## 2. Inventário funcional

| Componente | Arquivos relevantes | Situação constatada |
| --- | --- | --- |
| Interface do catálogo | `src/components/BoardRadar.tsx`, `src/app/page.tsx` | Busca, estilos, filtros, favoritos locais e videogames |
| Fichas e comparação de ofertas | `src/components/GameDetail.tsx`, `src/app/jogos/[slug]/page.tsx` | Edição identificada, tabelas DEMO, histórico sintético e relacionadas |
| Interface do chat | `src/components/ChatAssistant.tsx` | Fetch JSON, contexto em memória, loading, reset, cancelamento e erros; sem streaming |
| API do chat | `src/app/api/chat/route.ts` | Validação Zod, proxy privado, timeout e mensagens de erro |
| Transporte Python | `chatbot/server.py` | HTTP em loopback, porta aleatória, token efêmero, limite de corpo; importa somente `engine.respond` |
| Motor atual | `chatbot/engine.py` | Regras e regex em módulo único; contexto, filtros, ranking e templates |
| Inicialização | `scripts/run.mjs` | `npm start`/`npm run dev` iniciam Python e Next.js; encerramento dos subprocessos |
| Recomendações da navegação | `src/domain/recommendation.ts` | Filtros e ranking TypeScript; política parcialmente diferente da Python |
| Repositórios | `src/repositories/catalog.ts`, `history.ts` | JSONs locais; histórico carregado por API nas fichas |
| Protótipo documental | `chatbot/knowledge.py` | Busca lexical por sobreposição; não conectado ao chatbot HTTP nem validado por testes próprios |
| Protótipo de ferramentas | `chatbot/tools.py` | Allowlist e funções de leitura; não conectado ao chatbot HTTP nem coberto pela suíte atual |
| Seeds novos | `scripts/seed-v2.py` e JSONs adicionais | 21 obras, 63 relações e 8 trechos editoriais; não usados na interface atual |
| Política candidata | `src/data/policy.json` | Usada pelo protótipo de ferramentas; **não** unifica engine Python e TypeScript |
| Validação de dados | `scripts/validate-data.ts` | Valida catálogo e seis JSONs originais; não cobre integralmente os novos arquivos de mídia/conhecimento |
| Suítes | `tests/recommendation.test.ts`, `chatbot/test_engine.py` | 6 testes TS e 17 testes Python |
| Integração e navegador | `scripts/smoke.mjs`, `scripts/check-chat-browser.mjs` | Rotas, contexto, combate, reset e viewport mobile nos cenários escritos |

Não há `/api/chat/v2`, sessão com TTL, registro de regras versionadas, classificação de intenções tipada, matching aproximado com esclarecimento, ingestão autorizada de manuais, índice BM25/TF-IDF, trilha de regras ou deploy serverless validado. Não há evidência de que os 100 cenários já existam.

## 3. Dados disponíveis

Catálogo original: 60 jogos, 13 videogames, 10 lojas fictícias, 236 ofertas e 14.396 observações sintéticas. Contagens atuais calculadas em `baseline/data-counts.json`.

O catálogo tem metadados e edições preliminares. Há identificadores de edições, mas nenhuma auditoria de SKU, editora, idioma ou equivalência comercial real. Sem fontes licenciadas de manuais oficiais. A fonte de conhecimento existente é editorial própria; não comprova regras de Root ou qualquer outro jogo.

Os preços foram gerados com timestamps fixos. Envelhecem de acordo com o relógio e deixam de ser elegíveis após sete dias. Não atualizar o timestamp para simular coleta real. Os testes futuros devem fixar relógio e usar fixtures para não depender de ofertas sempre recentes.

## 4. Contrato de compatibilidade a preservar

`POST /api/chat` aceita `message` obrigatório (1–1000 caracteres), `state` opcional e `preferences` inicial legado. `state` contém preferências, interesses, exclusões, últimos IDs, pergunta pendente e indicador de orçamento sem limite.

Resposta atual: `text`, `state`, `preferences`, `ids`, `recommendations`, `suggestions`, `is_demo: true` e `engine: "python-catalog"`. Cada recomendação tem `id`, `name`, `reason`, `price_cents` e, quando proveniente do ranking, `score`.

O orçamento legado é em **reais** (`preferences.budget`); os preços de ofertas são em **centavos inteiros**. O novo modelo interno deverá usar centavos e converter nos limites do contrato. Não renomear ou mudar a unidade silenciosamente.

O frontend envia o estado a cada turno; não há sessão persistida no servidor. Fechar o painel preserva a conversa enquanto o componente existe. Reset cancela a requisição e limpa o contexto. O proxy faz autenticação entre processos locais, mas não implementa conta, autorização de usuário ou rate limit de produção.

## 5. Lacunas reproduzidas por leitura e sondas

As respostas reais das sondas estão em `baseline/diagnostic-probes.json`. Elas são diagnósticos, não testes de aceite aprovados.

| ID | Prioridade | Observação | Fase responsável |
| --- | --- | --- | --- |
| GAP-01 | Alta | Caminho de jogo mencionado retorna cards informativos antes dos filtros do ranking. Uma solicitação de recomendação pode receber jogo incompatível com jogadores/orçamento. | 2 |
| GAP-02 | Alta | Política de ranking duplicada em TS/Python; bônus de combate, complexidade e tratamento de preferências diferem. Preservar baseline e versionar mudanças. | 2 |
| GAP-03 | Média | “Tenho 200 reais” não captura orçamento; parser depende de “até”, “R$” ou “orçamento”. | 3 |
| GAP-04 | Média | “Compare Root com Scythe” retorna fichas resumidas, sem comparação estruturada de atributos. | 3–4 |
| GAP-05 | Alta | Pergunta sobre regras de um jogo nomeado segue descrição do catálogo, sem resolução de edição/evidência. Não afirma regra oficial específica, mas também não entrega o fluxo seguro solicitado. | 3–5 |
| GAP-06 | Alta | Não há condições/dependências/exceções registradas com ID e versão; impossível auditar quais regras dispararam. | 2 |
| GAP-07 | Média | Sem confiança heurística, matching aproximado ou detector explícito de ambiguidade. | 3 |
| GAP-08 | Média | Estado não tem TTL ou contrato serverless; preferências não possuem modelo de remoção universal. | 4 |
| GAP-09 | Alta | Protótipos de fontes e ferramentas ainda sem validação global, integração ou testes. Correspondência textual não pode provar uma regra. | 4–5 |
| GAP-10 | Alta | Meta de 100 cenários ainda não atendida; 23 testes unitários existentes, com várias asserções internas. Não contar asserções como cenários distintos. | 2–6 |
| GAP-11 | Média | Lançador local exige processos persistentes. Ainda não há adaptador serverless independente nem configuração de hospedagem verificada. | 6 |
| GAP-12 | Média | Sem evidência de teste de carga, p95 definido, avaliação calibrada de compreensão ou auditoria completa de acessibilidade. | 6 |

## 6. Regras originais: rastreabilidade

Texto literal de cada RN disponível no JSON extraído do DOCX original. Esta tabela descreve cobertura parcial e limites, sem inferir regras pela numeração.

| Regra | Evidência e situação |
| --- | --- |
| RN-001 | Páginas e APIs públicas sem autenticação: implementado na POC. |
| RN-002 | Preferências opcionais/editáveis no catálogo e contexto do chat: implementado, com remoção universal ainda pendente. |
| RN-003 | Arrays de tags no catálogo: implementado; classificação completa de temas/mecânicas/franquias ainda é preliminar. |
| RN-004 | `games[].editions` possui IDs/tipo. Catálogo não contém cenário completo de expansão separado para comprovar todos os casos: parcial. |
| RN-005 | APIs verificam edição do jogo e comparam por ID. Equivalência explícita entre edições não existe; metadados comerciais ainda não conferidos: parcial. |
| RN-006 | Preços e disponibilidade vêm de `offers.json`; não há inferência nem geração de ofertas pelo chat: implementado no demo. |
| RN-007 | Ficha sinaliza desatualização; rank exclui oferta fora da validade: implementado. |
| RN-008 | Ofertas elegíveis ordenadas por preço nas fichas e frete não incluído informado; fluxos novos deverão reutilizar a política: implementado nos fluxos atuais. |
| RN-009 | Filtros precedem ranking, mas resposta por nome ignora esse caminho: parcial, GAP-01. |
| RN-010 | The Witcher: Old World exemplifica jogo sem ofertas; descoberta continua disponível: implementado. |
| RN-011 | Sem patrocínio ou monetização ativa. Não há ordenação paga; funcionalidade comercial futura. |
| RN-012 | Redirecionamento e rastreamento comercial não estão ativos. Fora do fluxo DEMO. |
| RN-013 | Histórico atual é sintético e identificado; observações comerciais reais ainda não existem. Requisito de produção pendente. |
| RN-014 | Não há importador externo ativo. Conteúdo editorial próprio não substitui análise de licenças de manuais e metadados futuros: parcial. |
| RN-015 | Sem conta; contexto temporário pode ser limpo. Exclusão formal de conta/exportação não está implementada. |
| RN-016 | Sem painel administrativo e sem escrita de associações via API. Autorização de administrador não implementada. |
| RN-017 | Seeds têm indicação de origem, mas importações autorizadas e logs de aquisição não existem. |
| RN-018 | IDs internos `g*`, `v*`, `s*` e IDs de edição; sem substituição por IDs externos no catálogo atual. |
| RN-019 | Sem integração/importação externa. Idempotência de importações é requisito futuro, não validação de seed apenas. |
| RN-020 | Edições e relações editoriais marcadas preliminares; fila operacional de revisão de correspondências não existe. |
| RN-021 | Sem publicação de manuais externos; capas gráficas próprias. Direitos de dados externos deverão ser validados antes de ingestão. |
| RN-022 | JSONs somente leitura na execução; sem fonte externa que sobrescreva curadoria. Política de merge/importação futura. |
| RN-023 | Edição com ID válida tecnicamente na POC; confiabilidade comercial factual não comprovada. Nunca usar essa amostra como oferta real. |
| RN-024 | `is_demo`, origem sintética e avisos visuais em preços/histórico: implementado. |
| RN-025 | `/out/{offerId}` sempre 403 e botão demonstrativo sem checkout/redirecionamento: implementado e coberto por smoke. |

## 7. Evidências e limites da conclusão

O script `scripts/audit-phase1.py` gera os resultados atuais em `baseline/checks.json`, logs individuais e `baseline/summary.json`. Os tempos registrados são duração de comandos, **não** latência de requisições, p95 ou benchmark de NLP. O inventário guarda hashes dos arquivos de código e documentos; não contém segredos ou arquivos `.env`.

Verificações selecionadas: integridade dos seis JSONs originais, 6 testes TS, 17 testes Python, TypeScript, build, smoke HTTP e cenário de navegador. Checagem de imports proibidos cobre imports Python declarados; não é análise completa de tráfego de rede ou de dependências transitivas.

A Fase 1 estará concluída quando `summary.json` tiver `status: passed`, os documentos estiverem presentes e as lacunas acima estiverem registradas. Os problemas encontrados devem ser resolvidos nas fases correspondentes; a auditoria não os oculta nem declara o motor 2.0 pronto.

## 8. Próxima entrega

Fase 2: registro versionado de regras, separação de filtros e scoring, trilha de execução e correção do bypass de filtros por jogo nomeado. Critérios detalhados em `PLANO_POR_FASES.md`.
