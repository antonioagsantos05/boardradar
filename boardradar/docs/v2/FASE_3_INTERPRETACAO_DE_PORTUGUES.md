# Fase 3 — interpretação de português e ambiguidades

Data de referência: 19/10/2026. Implementação determinística em Python; sem LLM, chamadas de inferência, embeddings, GPU ou dependências adicionais.

Status: **concluída e validada**. `phase3/summary.json` registra `passed`: 147 testes Python, 20 testes TypeScript, validação de dados, verificação de tipos, build, smoke HTTP e navegador. Logs e hashes de código estão na mesma pasta. Isso não é uma métrica de precisão de NLP.

## Entrega e limites de escopo

O chatbot usa um interpretador separado, que identifica intenção, entidades, restrições numéricas, negações e nomes. O facade `chatbot/engine.py` preserva `respond(message, state)`, `rank`, `validate_state`, `normalize` e os símbolos de dados usados pelos módulos antigos.

A Fase 2 permanece responsável por elegibilidade e ranking: uma interpretação, confirmação ou preferência nunca autoriza contornar jogadores, orçamento, edição ou validade das ofertas. A política passa a `2.0-phase3.0`, mantendo o perfil de pontuação `1.1-preserved`.

Esta entrega classifica perguntas sobre comparação, regras, edição e ofertas, mas não afirma que as ferramentas completas das fases 4–5 já estejam disponíveis. Comparações ainda mostram fichas; regras sem evidência recebem uma limitação explícita, sem inventar páginas ou ações permitidas.

## Organização do código

| Módulo | Responsabilidade |
| --- | --- |
| `radar_ai/nlp/models.py` | Dataclasses de intenção e entidades; resultado serializável. |
| `radar_ai/nlp/normalizer.py` | Normalização Unicode/acentos, fronteiras de palavras e números por extenso. |
| `radar_ai/nlp/synonyms.py` | Vocabulário curado de gêneros e estilos. |
| `radar_ai/nlp/entities.py` | Jogadores, orçamento, tempo, complexidade, negações, correções e remoções. |
| `radar_ai/nlp/names.py` | Nomes e aliases exatos, maior correspondência e aproximação por difflib. |
| `radar_ai/nlp/intents.py` | Classificador de intenções por padrões e precedência explícita. |
| `radar_ai/nlp/interpreter.py` | Consolida entidades, informações ausentes e ambiguidades; aplica alterações de preferências. |
| `radar_ai/state.py` | Valida estado legado e novos campos opcionais de esclarecimento/exclusão de jogos. |
| `radar_ai/conversation.py` | Adapta a interpretação às respostas existentes e ao motor de regras. |

Nenhum arquivo é um placeholder. O estado ainda trafega no JSON e não depende de memória do processo Python; não foi implementado TTL de sessão nesta fase.

## Contrato de interpretação

Todas as respostas do chat incluem o campo adicional `interpretation`:

```json
{
  "intent": "recommendation",
  "entities": {
    "players": 4,
    "max_price_cents": 20000,
    "preferred_tags": ["família"],
    "excluded_tags": [],
    "game_ids": [],
    "edition_ids": [],
    "videogame_ids": [],
    "excluded_game_ids": [],
    "remove": []
  },
  "confidence": 0.9,
  "confidence_kind": "heuristic_not_calibrated",
  "missing_information": [],
  "ambiguities": [],
  "errors": [],
  "version": "nlp-3.0"
}
```

O exemplo omite os slots nulos de duração, complexidade e modo para facilitar leitura; a implementação serializa todos os campos da dataclass. `max_price_cents` é inteiro. O adaptador preserva `preferences.budget` em reais no contrato legado. Dinheiro é interpretado com Decimal; não usa ponto flutuante para extrair centavos.

Intenções: recomendação, refinamento, informação, comparação, regra, edição, oferta, explicação, saudação, agradecimento, reset, comércio, desconhecida e esclarecimento. A classificação é finita e por padrões; não é compreensão ilimitada.

O classificador prioriza pergunta de regra sobre a simples presença da palavra “edição”. Uma pergunta sobre ser adequado a iniciantes não transforma automaticamente o usuário em iniciante nem cria um perfil permanente.

## Exemplos implementados

| Mensagem | Resultado esperado |
| --- | --- |
| “Tenho 200 reais e quero algo para minha família.” | Teto de 20.000 centavos e categoria família. |
| “Até duzentos e cinquenta reais.” | Teto de 25.000 centavos. |
| “Meu orçamento é R$ 1.000,50.” | Teto de 100.050 centavos. |
| “Até uma hora e meia.” / “1h30” | Duração de 90 minutos; sem confundir com orçamento. |
| “Quero estratégia, mas não cooperativo.” | Estratégia incluída, cooperativo excluído, modo competitivo. |
| “Não gosto de terror nem fantasia, prefiro estratégia.” | Escopo de negação em terror/fantasia; estratégia positiva. |
| “Para quatro pessoas, melhor seis pessoas.” | Correção para seis, sem acumular valores conflitantes. |
| “Até 100 ou 200 reais.” | Pergunta de esclarecimento, sem escolher um teto silenciosamente. |
| “Remova o orçamento.” | Remove apenas orçamento; jogadores, tempo e estilo são preservados. |
| “Não remova o orçamento.” | Mantém o teto atual. |
| “Limpar orçamento.” | Remoção específica; não reinicia a conversa inteira. |
| “Recomende Gloomhaven: Jaws of the Lion.” | Identifica apenas esse título, sem agregar o Gloomhaven base por substring. |
| “Recomende 7 Wonders Duel.” | Identifica apenas Duel. |
| “Recomende Termforming Mars.” | Sugere Terraforming Mars e aguarda confirmação; não recomenda automaticamente. |
| “Recomende 7 Wonders D.” | Pede escolha entre candidatos; não pressupõe qual edição/jogo foi solicitado. |
| “Não quero Catan, recomende Azul.” | Exclui Catan e avalia Azul pelo motor de regras. |
| “Qual regra uso na edição g45-pt-base?” | Identifica a edição interna e seu jogo; ainda recusa afirmar regra sem fonte autorizada. |

“Tenho 16 anos” não vira orçamento ou quantidade de jogadores. Valores negativos, zero monetário, formatos malformados e frações de pessoas pedem esclarecimento. As correções usam a ordem textual das ocorrências; a ordem dos regex não determina o valor escolhido.

## Matching aproximado e esclarecimento

1. Buscar nomes/aliases exatos com fronteiras de palavras.
2. Preferir a maior correspondência para impedir nomes contidos em outros títulos.
3. Considerar apenas segmentos que se parecem com nomes; vocabulário genérico conhecido não dispara matching de qualquer trecho arbitrário.
4. Usar SequenceMatcher apenas para formar candidatos: limiar 0,84 para segmentos com várias palavras e 0,87 para uma palavra. Candidatos próximos até 0,08 do melhor são mantidos, limitados a cinco.
5. Devolver pergunta e sugestões com títulos cadastrados; nenhuma recomendação é emitida antes da confirmação.

O usuário pode confirmar pelo título, por “sim” quando existe um único candidato, ou pelo índice apresentado. “Não”/“cancelar” descarta o esclarecimento. Jogadores e orçamento explicitamente extraídos são preservados durante esse fluxo; confirmar um nome não aprova oferta fora do teto.

O estado opcional `pending_clarification` contém apenas tipos e IDs de candidatos, intenção anterior e entidades já resolvidas. Títulos e referências são recuperados do catálogo; IDs adulterados são rejeitados. `excluded_games` guarda exclusões explícitas de IDs, avaliadas por `USR-GAME-EXCLUDED-001`. São campos opcionais e compatíveis com clientes antigos.

## Confiança heurística

Os valores são indicadores de reconhecimento definidos por regras: 0,95 para nomes exatos e intenções diretas de controle; 0,90 para restrições numéricas reconhecidas; 0,80 para sinônimos/outros slots; 0,60 para intenção reconhecida sem entidade suficiente; 0,45 para nome aproximado que exige confirmação; 0,35 para valores conflitantes/inválidos; 0 para entrada sem reconhecimento.

Essa escala não foi calibrada estatisticamente e não representa probabilidade de a resposta estar correta. Similaridade de nome não prova identidade; confiança de intenção não prova regra de jogo. O frontend não exibe um percentual de “certeza”.

## Integração e validação

`POST /api/chat` foi estendido apenas para aceitar os novos campos opcionais de estado. A rota mantém limite de corpo, validação Zod, proxy privado, timeout e ausência de cache. Os campos antigos de resposta e o modo DEMO são preservados.

O conjunto `tests/fixtures/nlp-cases.json` contém cenários versionados, com expectativas explícitas de entidades, intenções, erros e candidatos de esclarecimento. Os testes adicionais cobrem turnos, confirmação, correção, remoção, estado adulterado, consulta de regras e regressões das fases anteriores.

Execução reproduzível, na pasta `boardradar`:

```text
npm test
npm run typecheck
npm run build
node scripts/smoke.mjs
node scripts/check-chat-browser.mjs
```

Verificador da fase, sem sobrescrever evidências anteriores:

```text
../.tools/python-3.13.7/python.exe scripts/verify-phase3.py --browser
```

Resultados, contagens executadas, exemplos e hashes ficam em `docs/v2/phase3/summary.json` e logs adjacentes. O navegador testa uma mensagem com nome digitado incorretamente e o clique na sugestão de confirmação; capturas ficam em `.qa/chat-phase3-clarification.png` e `.qa/chat-phase3-confirmed.png`.

Tempo de execução de teste ou comando não é métrica de latência do assistente. Contagem de testes não é porcentagem de compreensão de linguagem nem evidência de funcionamento para todas as frases possíveis.

## Pendências preservadas

- Contexto com TTL, comparação aprofundada e conexão completa com filmes/séries: Fase 4.
- Ingestão autorizada, recuperação documental e respostas com trechos/páginas: Fase 5.
- Avaliação consolidada, medições sob condições definidas e adaptação serverless/deploy: Fase 6.
- Metadados e identificação das edições continuam preliminares. Nenhum preço é real e não há checkout.

As limitações reconhecidas incluem frases fora do vocabulário, ironia, negações aninhadas complexas e nomes não cadastrados. Nesses casos, o sistema deve pedir esclarecimento, não inventar atributos, fontes ou ofertas. A interface explicita que a conversa não usa IA generativa.
