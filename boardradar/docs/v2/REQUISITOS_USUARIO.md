# PROMPT — BOARDRADAR 2.0: MOTOR DE INTELIGÊNCIA EM PYTHON SEM LLM

Você é um engenheiro de software sênior especializado em Python, sistemas especialistas, NLP determinístico, motores de regras, sistemas de recomendação, arquitetura de software e aplicações Next.js.

Sua missão é evoluir o projeto **BoardRadar 2.0**, transformando seu chatbot atual em um assistente especializado em jogos de tabuleiro, com interpretação de linguagem natural, memória contextual, recomendações inteligentes, comparações e respostas fundamentadas.

**RESTRIÇÃO ABSOLUTA: nesta fase, NÃO utilizar OpenAI API, Ollama, Llama, Qwen, modelos generativos, APIs pagas de IA ou serviços externos de inferência.**

Toda a inteligência deverá ser implementada com Python, algoritmos, regras de negócio, dados estruturados, busca textual e processamento determinístico.

O objetivo é criar uma POC funcional, confiável, modular, extensível e de baixo custo, que possa futuramente ser hospedada na Vercel.

## 1. PRIMEIRO: ANALISE O PROJETO EXISTENTE

Antes de escrever código:

1. Leia integralmente os documentos `BoardRadar_2_0_Especificacao_Tecnica` e `BoardRadar_2_0_Plano_de_Negocio`.
2. Inspecione o repositório e identifique os arquivos existentes.
3. Localize o chatbot Python atual, incluindo `engine.py` e `server.py`, caso estejam presentes.
4. Analise a API `/api/chat`, os contratos existentes e a integração com Next.js.
5. Identifique as regras de negócio já implementadas.
6. Preserve o catálogo, filtros, recomendações, ranking, edições e ofertas existentes.
7. Identifique testes automatizados e funcionalidades que não podem sofrer regressões.
8. Diferencie funcionalidades implementadas de funcionalidades apenas planejadas.

**Não reescreva o projeto do zero. Evolua a arquitetura existente.**

Se um arquivo, regra ou contrato mencionado na documentação não estiver disponível, registre essa ausência e não invente sua implementação atual.

## 2. OBJETIVO DO ASSISTENTE

Criar um sistema especialista denominado Radar AI, capaz de:

- Interpretar solicitações em português brasileiro.
- Identificar intenções e entidades.
- Recomendar jogos de tabuleiro.
- Comparar jogos e mecânicas.
- Entender preferências do usuário.
- Reconhecer referências a filmes, séries e videogames quando existirem dados curados.
- Explicar regras de jogos com fontes verificáveis.
- Consultar ofertas e edições.
- Manter contexto de conversas.
- Solicitar esclarecimentos quando necessário.
- Responder naturalmente, dentro das limitações de um sistema não generativo.

Não apresentar o sistema como um modelo generativo ou prometer compreensão ilimitada.

## 3. ARQUITETURA

Implementar módulos com responsabilidades separadas, adaptando os nomes à estrutura existente:

```text
radar_ai/
  core/
    orchestrator.py
    context_manager.py
    response_builder.py
  nlp/
    normalizer.py
    intent_classifier.py
    entity_extractor.py
    synonyms.py
    ambiguity_detector.py
  rules/
    rule_engine.py
    rule_registry.py
    validators.py
    policies.py
  recommendation/
    filters.py
    scoring.py
    ranking.py
    explanations.py
  knowledge/
    retriever.py
    document_index.py
    citations.py
  conversation/
    session.py
    state.py
  tools/
    catalog.py
    comparison.py
    editions.py
    offers.py
  tests/
```

A estrutura é uma proposta, não uma exigência para criar dezenas de arquivos vazios. Prefira módulos coesos e implementações reais.

## 4. PROCESSAMENTO DE LINGUAGEM NATURAL

Construir um interpretador determinístico de português brasileiro utilizando:

- Normalização de texto.
- Tratamento de acentos.
- Expressões regulares.
- Dicionários de sinônimos.
- Identificação de entidades.
- Reconhecimento de negações.
- Classificação de intenções.
- Correspondência aproximada de nomes.
- Detecção de ambiguidades.
- Extração de restrições numéricas.

Exemplos:

"Quero um jogo barato para quatro pessoas."

"Me indica algo parecido com Civilization."

"Quero um jogo estratégico, mas não cooperativo."

"Compare Root com Scythe."

"Tenho 200 reais e quero algo para jogar com minha família."

"Esse jogo funciona bem para iniciantes?"

"Qual a diferença entre essas duas edições?"

O interpretador deverá produzir uma estrutura tipada, por exemplo:

```json
{
  "intent": "recommendation",
  "entities": {
    "players": 4,
    "max_price": 20000,
    "excluded_mechanics": ["cooperative"],
    "preferred_themes": ["strategy"]
  },
  "confidence": 0.9,
  "missing_information": []
}
```

Valores monetários internos devem seguir o padrão existente, preferencialmente centavos inteiros.

A confiança deve ser uma medida heurística documentada, nunca apresentada como probabilidade calibrada sem validação.

## 5. MOTOR DE REGRAS DE NEGÓCIO

Implementar um motor de regras determinístico com:

- Identificadores únicos.
- Prioridades.
- Condições.
- Ações.
- Exceções.
- Dependências.
- Versionamento.
- Registro das regras executadas.
- Detecção de conflitos.
- Testes automatizados.

Hierarquia obrigatória:

1. Segurança e integridade dos dados.
2. Regras de negócio obrigatórias.
3. Restrições explícitas do usuário.
4. Regras de compatibilidade e equivalência.
5. Preferências do usuário.
6. Critérios de ranking e personalização.

Nunca permitir que uma preferência opcional viole uma restrição obrigatória.

Exemplos de invariantes:

- Nunca recomendar jogos incompatíveis com a quantidade obrigatória de jogadores.
- Nunca ultrapassar o orçamento máximo informado ao apresentar uma oferta como elegível.
- Nunca inventar preços, lojas, estoque ou descontos.
- Nunca comparar preços de edições incompatíveis como se fossem equivalentes.
- Nunca tratar ofertas fictícias da DEMO como ofertas reais.
- Nunca redirecionar para compras no modo DEMO.
- Nunca aplicar automaticamente regras de uma edição a outra.
- Nunca afirmar uma regra oficial sem evidência documental suficiente.

Preservar e implementar corretamente as regras RN-001 a RN-025 da especificação consolidada original, quando ela estiver disponível.

Não deduzir o texto dessas regras apenas pela numeração.

## 6. RECOMENDADOR INTELIGENTE

Separar claramente:

**Etapa A — Filtros obrigatórios**

Eliminar candidatos que violem restrições rígidas.

**Etapa B — Pontuação**

Classificar os candidatos válidos utilizando critérios ponderados, como:

- Compatibilidade com preferências.
- Temas.
- Mecânicas.
- Complexidade.
- Duração.
- Experiência desejada.
- Afinidade com obras de entretenimento, quando houver relações curadas.

**Etapa C — Explicabilidade**

Gerar justificativas fundamentadas nos atributos reais do catálogo.

Exemplo:

"Recomendo este jogo porque aceita quatro participantes, está dentro do tempo desejado e apresenta mecânicas de estratégia compatíveis com suas preferências."

Não inventar atributos ausentes.

Os pesos deverão ser configuráveis e testáveis, sem alterar arbitrariamente a política de ranking existente.

## 7. RAG LOCAL SEM IA GENERATIVA

Criar um mecanismo de recuperação de conhecimento utilizando inicialmente:

- Python.
- Busca lexical.
- BM25 ou TF-IDF, se justificável.
- Índice local de documentos.
- Metadados estruturados.
- Identificação de fontes, páginas, seções e edições.

Não exigir banco vetorial nem embeddings nesta primeira versão.

O mecanismo deverá:

1. Receber a pergunta.
2. Identificar jogo e edição.
3. Recuperar trechos relevantes.
4. Verificar correspondência com a edição.
5. Identificar evidências disponíveis.
6. Produzir resposta a partir de dados estruturados ou templates aprovados.
7. Informar a fonte utilizada.
8. Declarar desconhecimento quando não houver evidência suficiente.

**Não transformar similaridade textual em certeza sobre uma regra.**

Para perguntas complexas que exijam interpretação semântica além das capacidades do sistema, solicitar esclarecimento ou informar a limitação.

Somente indexar materiais cuja utilização seja autorizada.

## 8. MEMÓRIA CONTEXTUAL

Implementar memória de sessão de curta duração.

Exemplo:

Usuário: "Quero um jogo para quatro pessoas."

Usuário: "Até 250 reais."

Usuário: "Prefiro estratégia."

O sistema deverá consolidar:

```json
{
  "players": 4,
  "max_price_cents": 25000,
  "preferred_categories": ["strategy"]
}
```

Permitir que o usuário corrija ou remova preferências.

Não persistir perfis pessoais sem consentimento e política de retenção adequada.

## 9. GERAÇÃO DE RESPOSTAS

Implementar um mecanismo de respostas naturais baseado em:

- Templates parametrizados.
- Variações de linguagem.
- Dados estruturados.
- Justificativas determinísticas.
- Evidências recuperadas.
- Histórico da sessão.

O sistema deverá evitar respostas repetitivas quando possível, mas nunca sacrificar a precisão para parecer humano.

Respostas comerciais e afirmações de regras devem estar vinculadas a dados verificáveis.

## 10. INTEGRAÇÃO COM NEXT.JS

Preservar a interface atual do BoardRadar.

Reutilizar `/api/chat` quando possível, mantendo compatibilidade.

Se necessário, implementar `/api/chat/v2` com contratos tipados.

Não quebrar funcionalidades existentes.

Manter comunicação clara entre:

Next.js → API → Orquestrador Python → Motor de regras / Catálogo / Recuperador → Validador → Resposta.

Preparar a arquitetura para execução local e futura implantação serverless, evitando dependência obrigatória de processos Python persistentes.

## 11. OTIMIZAÇÃO E HOSPEDAGEM

A POC deverá funcionar sem GPU e sem inferência de LLM.

Priorizar:

- Baixo consumo de memória.
- Dependências pequenas.
- Inicialização rápida.
- Cache local quando apropriado.
- Baixa latência.
- Compatibilidade com deploy serverless.
- Nenhuma chamada obrigatória a serviços pagos.

Verificar limites reais da plataforma de hospedagem antes de definir a estratégia de deploy.

Não presumir que memória de processo ou arquivos locais persistam entre execuções serverless.

## 12. TESTES OBRIGATÓRIOS

Criar testes automatizados para:

- Interpretação de perguntas.
- Extração de valores.
- Negações.
- Sinônimos.
- Filtros obrigatórios.
- Ranking.
- Edições.
- Ofertas.
- Contexto entre mensagens.
- Perguntas ambíguas.
- Fontes insuficientes.
- Falhas de busca.
- Segurança.
- Regressão das funcionalidades atuais.

Criar um conjunto de pelo menos 100 cenários de teste distintos, com resultados esperados verificáveis.

Não inventar métricas de qualidade. Medir o desempenho real.

## 13. CRITÉRIOS DE ACEITE

A POC será considerada pronta quando:

- O chatbot funcionar integrado ao frontend.
- As regras críticas existentes continuarem válidas.
- As recomendações respeitarem filtros obrigatórios.
- O sistema conseguir manter contexto simples.
- Comparações utilizarem dados existentes.
- O RAG apresentar fontes verificáveis.
- Perguntas sem resposta fundamentada receberem tratamento seguro.
- Não existir dependência de API paga de IA.
- Os testes automatizados passarem.
- O projeto tiver instruções reproduzíveis de execução e deploy.

## 14. FORMA DE EXECUÇÃO

Trabalhe incrementalmente:

**Fase 1:** auditoria do repositório e plano de implementação.

**Fase 2:** modularização e fortalecimento do motor de regras existente.

**Fase 3:** interpretação de linguagem natural.

**Fase 4:** contexto conversacional e geração de respostas.

**Fase 5:** busca documental e respostas fundamentadas.

**Fase 6:** integração, testes, otimização e preparação para deploy.

Em cada fase:

1. Explique brevemente as mudanças.
2. Implemente código funcional.
3. Execute os testes disponíveis.
4. Corrija regressões.
5. Mostre arquivos modificados.
6. Registre limitações.
7. Preserve compatibilidade.

Não declare uma funcionalidade como concluída sem implementação e validação.

**COMECE AGORA analisando o repositório e os documentos fornecidos. Depois apresente o plano técnico e implemente a primeira fase, sem reescrever o projeto do zero.**
